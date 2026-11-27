// HOOKS: the entry of the mod. Each hook translates an engine event into a `dispatch` (the rules in
// rules.ts decide what it means) and, where an event may have ended something, asks for a
// reconcile. No rule lives here. Reading order of the mod: rules.ts (header) -> this file.
import type { EngineInterface, Register } from 'claude-code'

import type { TaskRow } from './model'
import { dbgOnce, noteRender } from './debug'
import { draw, fitted } from './draw'
import { paneTree } from './pane'
import { endedTaskOfRow, isFollowedAgent, monitorDeadlineMs, parseTaskEnd, spawnKind, squash, stoppedTaskOf, taskIdOf, tokensOf } from './rules'
import { armLiveRefresh, armReconcile, requestReconcile } from './schedule'
import { bindPicture, dispatch, getState, markEnded, paneView, pickedFigure, pickFigure } from './state'
import { hasSection, HOST_CHECKS_MS, hostPresent, placeSection } from './stack-guest'
import type { StackHook } from './stack-guest'

const PANE = 'flow-panel'
const PLUGIN = 'flow-panel' // the name in .claude-plugin/plugin.json: also our section name in the side-stack pane

// The store compares pictures (to skip a redraw that would look the same) with the same drawing.
bindPicture((v, now, selfId) => draw(v, now, 'cost', selfId))

export const register: Register = (on, options) => {
  // Dots are pinned to the wall clock, so a redraw does not restart them; still there is no steady
  // timer: the cadence is in schedule.ts.
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'flow-panel',
      description: 'Open the animated flow pane',
    })
    // FLOW_PANEL=0 in the env block of a settings file turns the panel off:
    // ~/.claude/settings.json for everywhere, a project's .claude/settings.json
    // (or settings.local.json) for one project; the project value wins.
    if ((await $.env.get('FLOW_PANEL')) !== '0') {
      void openOwnPane($)
    }
    const { rateLimits } = await $.session.usage()
    await dispatch($, { type: 'limit', win: rateLimits.find(r => r.kind === 'five_hour') })
    armReconcile($)

    return next(e)
  })

  // Every prompt brings the panel back if it was closed (unless switched off).
  on('prompt.submit', async ($, e, next) => {
    armReconcile($)
    // A background task's notification is not the owner's prompt: it must neither
    // clear the panel nor restart the prompt's cost. It only ends the task it names.
    if (e.origin?.kind === 'task-notification') {
      await onTaskNotification($, e.text)

      return next(e)
    }
    // Open only when it is not up: a repeated open re-seats the pane.
    if ((await $.env.get('FLOW_PANEL')) !== '0') {
      const isUp = (await $.ui.panes()).some(pane => pane.id === PANE)
      if (!isUp) void openOwnPane($)
    }
    await dispatch($, { type: 'prompt', usd: (await $.session.usage()).cost?.usd ?? 0 })

    return next(e)
  })

  // The command opens it by hand even where the panel is switched off.
  on('command.run', { command: 'flow-panel' }, async $ => {
    await $.ui.open({ id: PANE, title: 'Flow' })

    return { text: 'Flow pane opened.' }
  })

  // A closing or archived session marks its file, so the session that started it
  // stops drawing it.
  on('session.end', async ($, e, next) => {
    await markEnded($)

    return next(e)
  })

  // Off by default (option guardedHooks): on a Team or Enterprise login an organisation's guard skips classic.* hooks
  // with a notice in the chat each time. Without the hook the task end comes from the transcript row (ui.render below).
  if (options?.guardedHooks === true || options?.guardedHooks === 'true') {
    // The one place the engine lists its background tasks: the Stop event carries them. The reconcile
    // closes the tasks this process follows that the list no longer holds (or ends).
    on('classic.Stop', async ($, e, next) => {
      try {
        const rows = (e as { background_tasks?: TaskRow[] }).background_tasks
        await dispatch($, { type: 'stop', now: await $.clock.now(), rows })
        armReconcile($)
        void requestReconcile($)
      } catch {
        // no list: the tasks stay as they are
      }

      return next(e)
    })
  }

  on('turn.start', async ($, e, next) => {
    armReconcile($)
    const now = await $.clock.now()
    if (e.agentId !== undefined && isFollowedAgent(getState(), e.agentId)) void armLiveRefresh($)
    await dispatch($, { type: 'turn-start', now, agentId: e.agentId })

    return next(e)
  })

  on('turn.complete', async ($, e, next) => {
    const usd = (await $.session.usage()).cost?.usd ?? 0
    await dispatch($, { type: 'turn-complete', now: await $.clock.now(), agentId: e.agentId, usage: e.usage, usd })

    return next(e)
  })

  on('agent.spawn', async ($, e, next) => {
    const started = await next(e)
    const id = 'agentId' in started ? started.agentId : undefined
    if (id) {
      const now = await $.clock.now()
      const spawn = { fork: e.fork, toolUseId: e.tool_use_id, background: e.background, isTeammate: e.isTeammate }
      const kind = spawnKind(spawn)
      if (kind.isSide || kind.isBackground) void armLiveRefresh($)
      await dispatch($, { type: 'agent-spawn', now, agentId: id, subagentType: e.subagentType, ...spawn })
    }

    return started
  })

  // Pushed when the engine measures the session: after each main turn and
  // whenever a rate-limit window moves a whole point.
  on('session.measure', async ($, e, next) => {
    const { rateLimits } = await $.session.usage()
    await dispatch($, { type: 'limit', win: rateLimits.find(r => r.kind === 'five_hour') })

    return next(e)
  })

  on('tool.call', async ($, e, next) => {
    const now = await $.clock.now()
    const tool = String(e.tool)
    const args = e as unknown as Record<string, unknown>
    armReconcile($)
    void armLiveRefresh($)
    await dispatch($, { type: 'tool-start', now, tool, args })

    let failed = false
    let resultTokens = 0
    let taskId: string | undefined
    let monitorDeadline = 0
    const requestTokens = tokensOf(args)
    try {
      const ran = await next(e)
      resultTokens = tokensOf(ran)
      // A command that went to the background, or a Monitor, stays as a running block.
      taskId = taskIdOf(tool, ran)
      monitorDeadline = tool === 'Monitor' ? monitorDeadlineMs(ran) : 0
      if (tool === 'TaskStop') {
        const stopped = stoppedTaskOf(args, ran)
        if (stopped) void dispatch($, { type: 'task-ended', now: await $.clock.now(), id: stopped, reason: 'task-stop', status: 'killed', withAgent: false })
      }

      return ran
    } catch (err) {
      failed = true
      throw err
    } finally {
      const end = await $.clock.now()
      await dispatch($, { type: 'tool-end', now: end, startedAt: now, tool, args, failed, resultTokens, requestTokens })
      if (taskId && !failed) {
        const id = taskId
        await dispatch($, { type: 'task-start', now: end, startedAt: now, id, tool, args })
        // A finite Monitor ends at its deadline; the engine says so too, this is a backstop.
        if (monitorDeadline > 0) {
          $.clock.after(monitorDeadline, async () =>
            dispatch($, { type: 'task-ended', now: await $.clock.now(), id, reason: 'monitor-deadline', status: 'timeout', withAgent: false }),
          )
        }
      }
    }
  })

  // A notification that reaches a running turn does not always raise `prompt.submit`, and
  // the Stop event can be skipped by an earlier plugin: the transcript row is the one place
  // the end is always drawn. The row names the task and how it ended.
  on('ui.render', { component: 'UserMessage' }, async ($, e, next) => {
    try {
      const ended = endedTaskOfRow(e)
      if (ended) await dispatch($, { type: 'row-ended', now: await $.clock.now(), id: ended.id, status: ended.status })
    } catch {
      // drawing the row must never fail because of this
    }

    return next(e)
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => drawFlow($, e))

  // side-stack (optional host, https://github.com/lucas-saldanha-werneck/side-stack): draw our section in its Stack pane.
  // Without side-stack installed nothing here does anything. Claude Code 2.1.327+ hears only a plugin's own drawings
  // unless the matcher names `plugin`; older builds run the second registration. hasSection keeps it to one drawing.
  on('ui.render', { component: 'Pane', requestId: 'side-stack', plugin: '*' }, drawInStack)
  on('ui.render', { component: 'Pane', requestId: 'side-stack' }, drawInStack)
}

// Our section of the Stack pane: the same drawing as our own pane.
const drawInStack: StackHook = async ($, e, next) => {
  const below = await next(e)
  if (hasSection(below, PLUGIN)) return below

  return placeSection($, e, below, PLUGIN, await drawFlow($, e).catch(() => null))
}

type Resolvable = Parameters<EngineInterface['ui']['resolve']>[0]

// The drawing of the pane, shared by our own pane and our section of the Stack pane.
const drawFlow = async ($: EngineInterface, e: Resolvable) => {
  const elements = $.ui.resolve(e)
  const { view, selfId } = await paneView($)
  armReconcile($) // the pane loaded: reconcile now, then on the cadence
  const now = await $.clock.now()
  const figure = await pickedFigure($)
  const source = fitted(view, now, figure, selfId)
  await noteRender($, source)

  return paneTree(elements, source, figure, f => {
    void pickFigure($, f)
  })
}

// Opens our own pane unless side-stack is there to show the flow in its Stack pane. Plugin load order is not
// known, so the host is looked for again later: where it turns up after our pane opened, the pane is closed.
async function openOwnPane($: EngineInterface): Promise<void> {
  if (await hostPresent($)) return
  await $.ui.open({ id: PANE, title: 'Flow' })
  for (const ms of HOST_CHECKS_MS) $.clock.after(ms, () => void closeWhenStacked($))
}

async function closeWhenStacked($: EngineInterface): Promise<void> {
  if (!(await hostPresent($))) return
  if ((await $.ui.panes()).some(pane => pane.id === PANE)) await $.ui.close({ id: PANE })
}

// The engine's message that a background task ended arrives as a prompt flagged as a task
// notification. The first of each kind is written to the debug log (once), so its real shape can
// be compared with what /tasks shows.
async function onTaskNotification($: EngineInterface, text: string): Promise<void> {
  const parsed = parseTaskEnd(text)
  const sample = `notification ${JSON.stringify(squash(text).slice(0, 600))}`
  if (parsed?.isEnded) await dbgOnce($, 'end', `task end ${sample} -> id=${parsed.id} status=${parsed.status}`)
  else await dbgOnce($, 'other', `task notification without end ${sample}`)
  if (!parsed?.isEnded) return
  await dispatch($, { type: 'task-ended', now: await $.clock.now(), id: parsed.id, reason: 'notification', status: parsed.status, withAgent: true })
}
