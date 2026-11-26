// RULES: every decision of the mod lives here, as pure functions (no I/O, no clock reads:
// the time is always passed in as `now`). To change what the panel does, edit a rule below.
//
// Layers (imports only go downwards):
//   register.tsx   hooks     engine event -> `nextState` call, asks for a reconcile      (no rules)
//   schedule.ts    cadence   reads the sources, calls `reconcile`, owns the timers      (no rules)
//   state.ts       state     the one store; the only place the state is replaced
//   rules.ts       rules     this file
//   sources.ts     sources   read-only truth: desktop store, agent list, shared files
//   draw.ts etc.   view      draws from the state, decides nothing about status
//
// Life cycle of a followed background task or agent (WorkEntry):
//
//   tool returns a task id / agent spawns
//                 |
//                 v
//            running ---- (any rule of CLOSE_RULES) ----> closed(reason)
//
// Life cycle of a sub-session tile: it exists while the desktop app's store lists it
// (VISIBILITY_RULES); a child without an engine id yet shows as "(starting)".
//
// Cadence (who calls `reconcile`, see schedule.ts):
//   - at init: the first hook or pane render that fires arms it and reconciles once;
//   - every RECONCILE_MS (30 s) after that;
//   - debounced RECONCILE_DEBOUNCE_MS (2 s) after an event that may have ended something (Stop).
// Events (`nextState`) only update the state optimistically; none of them is the only way a
// state ends: `reconcile` closes what the real sources no longer confirm.
import type { FlowNode, FlowView, NodeKind, SubTree } from '../types'
import {
  CHARS_PER_TOKEN,
  ERROR_MS,
  MAX_NODES,
  MONITOR_BACKSTOP_MS,
  RESULT_WEIGHT,
  WEIGHT,
  type CloseReason,
  type FlowState,
  type Ring,
  type Stored,
  type StoredNode,
  type TaskRow,
  type Usage,
  type WorkEntry,
} from './model'

// ================================================================ the rule tables

const TASK_GRACE_MS = 30000 // a freshly started item is not judged by the sources this long
const TASK_MISSES = 2 // reconciles in a row without the item in the real source
const TASK_ENDED = ['completed', 'failed', 'killed', 'stopped', 'cancelled', 'canceled', 'error']

// Why a followed task or agent is closed. One line per rule; the code that applies it is named.
export const CLOSE_RULES: Record<CloseReason, string> = {
  'task-stop': 'a TaskStop call returned and names the task: closed at once (hooks: tool.call)',
  'monitor-deadline': 'a finite Monitor reached its timeout + MONITOR_BACKSTOP_MS: closed (hooks: tool.call timer)',
  notification: 'a task-notification prompt with an ended status names the task: closed at once (hooks: prompt.submit)',
  'transcript-row': 'the transcript row of such a notification (ui.render UserMessage) names a followed task: closed at once',
  'ended-status': 'the real source (agent list or Stop list) lists it as completed/failed/killed/...: closed at once, even inside the grace',
  'missed-reconciles': `the real source does not list it in ${TASK_MISSES} reconciles in a row (the Stop list for shells and monitors, the agent list for agents): closed`,
  'unseen-after-restart': 'a task node running in the saved view that this process never saw start: closed by the next reconcile',
}

// Which sub-sessions are shown below this session (treeBelow / composeTiles):
//   - children are found by `spawnedFrom` = this session's local id, recursively (children of children);
//   - archived sessions are hidden, with their subtrees;
//   - forks (a side chat the person forked) are hidden, with their subtrees;
//   - a child with no engine id yet is shown as a "(starting)" tile;
//   - a session already seen on the way down is skipped (cycles), and the depth is capped;
//   - there is no age cutoff and no silence timeout: an idle live session stays.
const MAX_TREE_DEPTH = 8
const isShownChild = (e: Stored, parent: string, seen: ReadonlySet<string>): boolean =>
  e.from === parent && !e.isFork && !e.isArchived && !seen.has(e.local)

// ================================================================ events

type LimitWindow = { percentUsed: number; resetsAt?: string }

export type FlowEvent =
  | { type: 'limit'; win: LimitWindow | undefined } // session.start, session.measure
  | { type: 'prompt'; usd: number } // a real prompt of the owner: a fresh view
  | { type: 'turn-start'; now: number; agentId?: string }
  | { type: 'turn-complete'; now: number; agentId?: string; usage?: Usage; usd: number }
  | {
      type: 'agent-spawn'
      now: number
      agentId: string
      subagentType: string
      fork?: boolean
      toolUseId?: string
      background?: boolean
      isTeammate?: boolean
    }
  | { type: 'tool-start'; now: number; tool: string; args: Record<string, unknown> }
  | {
      type: 'tool-end'
      now: number // when the call ended
      startedAt: number
      tool: string
      args: Record<string, unknown>
      failed: boolean
      resultTokens: number
      requestTokens: number
    }
  | { type: 'task-start'; now: number; startedAt: number; id: string; tool: string; args: Record<string, unknown> }
  | { type: 'task-ended'; now: number; id: string; reason: CloseReason; status: string; withAgent: boolean }
  | { type: 'row-ended'; now: number; id: string; status: string } // transcript row of a notification
  | { type: 'stop'; now: number; rows: readonly TaskRow[] | undefined }
  | { type: 'title'; title: string }
  | { type: 'tick' } // forces a redraw (a running time needs fresh labels)

// ================================================================ nextState

// The next state after one engine event. Pure: the same state and event give the same answer.
export const nextState = (s: FlowState, e: FlowEvent): FlowState => {
  switch (e.type) {
    case 'limit':
      return withView(s, applyLimit(s.view, e.win))
    case 'prompt':
      return onPrompt(s, e.usd)
    case 'turn-start':
      return onTurnStart(s, e)
    case 'turn-complete':
      return onTurnComplete(s, e)
    case 'agent-spawn':
      return onAgentSpawn(s, e)
    case 'tool-start':
      return onToolStart(s, e)
    case 'tool-end':
      return onToolEnd(s, e)
    case 'task-start':
      return onTaskStart(s, e)
    case 'task-ended':
      return closeAgentToo(closeTask(s, e.id, e.reason, e.status, e.now), e)
    case 'row-ended':
      // The row names a task or agent; only one this process follows is closed.
      return isFollowed(s, e.id) ? closeBoth(s, e.id, 'transcript-row', e.status, e.now) : s
    case 'stop':
      return e.rows ? { ...s, lastStop: { at: e.now, rows: e.rows } } : s
    case 'title':
      return s.view.title === e.title ? s : withView(s, { ...s.view, title: e.title })
    case 'tick':
      return withView(s, { ...s.view, tick: s.view.tick + 1 })
  }
}

const withView = (s: FlowState, view: FlowView): FlowState => ({ ...s, view })
const withNodes = (s: FlowState, nodes: FlowNode[]): FlowState => withView(s, { ...s.view, nodes })
const withEntry = (s: FlowState, entry: WorkEntry): FlowState => {
  const work = new Map(s.work).set(entry.id, entry)
  const done = [...work.values()].filter(w => w.phase === 'closed')
  if (done.length > MAX_CLOSED_KEPT) work.delete(done[0]!.id) // oldest closed first (insertion order of the first close)

  return { ...s, work }
}
const MAX_CLOSED_KEPT = 50 // closed entries are kept only for the record, never judged again

// A new prompt starts a fresh view: only segments used since then show. Background agents and
// tasks that still work stay (their branch, running, grey).
const onPrompt = (s: FlowState, usd: number): FlowState => {
  const v = s.view
  const agentKeys = new Set(runningOf(s, 'agent').map(a => a.key))
  const isFollowedNode = (n: FlowNode): boolean => (!!n.taskId && isRunning(s, n.taskId, 'task')) || agentKeys.has(n.key)

  return withView(s, {
    ...v,
    nodes: v.nodes.filter(n => n.running > 0 && isFollowedNode(n)),
    agentNode: Object.fromEntries(Object.entries(v.agentNode).filter(([id]) => isRunning(s, id, 'agent'))),
    promptUsd: usd,
    lastUsd: usd,
    baseUsd: v.baseUsd ?? usd, // the ledger before this mod saw any turn
  })
}

const onTurnStart = (s: FlowState, e: { now: number; agentId?: string }): FlowState => {
  const turns = new Map(s.turns).set(e.agentId ?? '', e.now)
  const next = { ...s, turns }
  if (e.agentId === undefined) return withView(next, { ...s.view, mainRunning: true, isWaiting: false })
  const live = runningEntry(s, e.agentId, 'agent')

  return live ? withNodes(next, s.view.nodes.map(n => (n.key === live.key ? { ...n, at: e.now } : n))) : next
}

// A turn's exact usage: it counts toward the calibration, and a sub-agent's turn is also
// charged to that agent's own path.
const onTurnComplete = (s: FlowState, e: Extract<FlowEvent, { type: 'turn-complete' }>): FlowState => {
  const v = s.view
  const id = e.agentId ?? ''
  const cost = weigh(e.usage)
  const began = s.turns.get(id) // pace of this turn: fresh tokens (not cache reads) over its wall time
  const tps = began === undefined ? undefined : paceOf(freshTokens(e.usage), e.now - began)
  const side = e.agentId === undefined ? undefined : s.forks.get(e.agentId)
  const turns = new Map(s.turns)
  turns.delete(id)
  const forks = new Map(s.forks)
  if (e.agentId !== undefined) forks.delete(e.agentId)
  const key = e.agentId === undefined ? undefined : v.agentNode[e.agentId]
  const delta = Math.max(0, e.usd - (v.lastUsd ?? e.usd)) // the ledger growth is charged to the agent's path
  const endedAt = e.now
  const moved: FlowView = {
    ...v,
    wTotal: v.wTotal + cost,
    allW: (v.allW ?? 0) + cost,
    lastUsd: e.usd,
    nodes: key
      ? v.nodes.map(n =>
          n.key === key
            ? {
                ...n,
                usd: (n.usd ?? 0) + delta,
                tps: tps ?? n.tps,
                tok: (n.tok ?? 0) + freshTokens(e.usage),
                // A foreground Agent call is still running and counts the whole run itself;
                // a background agent and a command's fork have no call to count it.
                ms: (n.ms ?? 0) + (key === sideTarget.key ? endedAt - (side ?? endedAt) : n.running === 0 && began !== undefined ? endedAt - began : 0),
                ...(key === sideTarget.key
                  ? {
                      running: Math.max(0, n.running - 1),
                      startSum: n.running > 1 ? (n.startSum ?? 0) - (side ?? endedAt) : 0,
                      isBackground: n.running > 1,
                      at: endedAt,
                    }
                  : {}),
              }
            : n,
        )
      : v.nodes,
    ...(e.agentId === undefined ? { mainRunning: false, isWaiting: true, mainTps: tps ?? v.mainTps } : {}),
  }

  return { ...s, turns, forks, view: calibrate(moved) }
}

// A sub-agent's id, so its own turns can be charged to its node. A command's fork (/btw ...) and
// a background agent keep their node running from the spawn (no tool call marks them).
const onAgentSpawn = (s: FlowState, e: Extract<FlowEvent, { type: 'agent-spawn' }>): FlowState => {
  const { isSide, isBackground } = spawnKind(e)
  const target = isSide ? sideTarget : agentTarget(e.subagentType)
  let next = s
  if (isSide) next = { ...next, forks: new Map(next.forks).set(e.agentId, e.now) }
  if (isBackground) next = withEntry(next, { id: e.agentId, kind: 'agent', key: target.key, startedAt: e.now, misses: 0, phase: 'running' })
  const marks = isSide || isBackground

  return withView(next, {
    ...s.view,
    agentNode: { ...s.view.agentNode, [e.agentId]: target.key },
    nodes: touch(s.view.nodes, target, e.now, n => ({
      ...n,
      at: e.now,
      running: n.running + (marks ? 1 : 0),
      startSum: (n.startSum ?? 0) + (marks ? e.now : 0),
      isBackground: marks || n.isBackground,
    })),
  })
}

const onToolStart = (s: FlowState, e: Extract<FlowEvent, { type: 'tool-start' }>): FlowState => {
  const isBackground = e.args.run_in_background === true

  return withNodes(
    s,
    touch(s.view.nodes, classify(e.tool, e.args), e.now, n => ({
      ...n,
      at: e.now,
      running: n.running + 1,
      startSum: (n.startSum ?? 0) + e.now,
      isBackground: isBackground || n.isBackground,
    })),
  )
}

const onToolEnd = (s: FlowState, e: Extract<FlowEvent, { type: 'tool-end' }>): FlowState => {
  const c = classify(e.tool, e.args)
  const end = e.now

  return withNodes(
    s,
    s.view.nodes.map(n =>
      n.key === c.key
        ? {
            ...n,
            at: end,
            running: Math.max(0, n.running - 1),
            startSum: n.running - 1 > 0 ? (n.startSum ?? 0) - e.startedAt : 0,
            isBackground: n.running - 1 > 0 ? n.isBackground : false,
            errorAt: e.failed ? end : n.errorAt,
            w: n.w + e.resultTokens * RESULT_WEIGHT,
            calls: (n.calls ?? 0) + 1,
            tok: (n.tok ?? 0) + e.resultTokens + e.requestTokens,
            ms: (n.ms ?? 0) + (end - e.startedAt),
            tps: paceOf(e.resultTokens, end - e.startedAt) ?? n.tps,
            tpsIn: paceOf(e.requestTokens, end - e.startedAt) ?? n.tpsIn,
          }
        : n,
    ),
  )
}

// A command that went to the background, or a Monitor, stays as a running block until a rule closes it.
const onTaskStart = (s: FlowState, e: Extract<FlowEvent, { type: 'task-start' }>): FlowState => {
  const next = withEntry(s, { id: e.id, kind: 'task', key: '', startedAt: e.now, misses: 0, phase: 'running' })
  if (s.view.nodes.some(n => n.taskId === e.id)) return next
  const label = taskNameOf(e.tool, e.args)
  const target: Target = { key: `task:${e.id}`, label, kind: 'tool' }

  return withNodes(
    next,
    touch(s.view.nodes, target, e.now, n => ({
      ...n,
      at: e.now,
      taskId: e.id,
      taskName: label,
      hasUsage: false,
      running: 1,
      startSum: e.startedAt,
      isBackground: true,
      calls: 1,
    })),
  )
}

// ---- closing

const closeAgentToo = (s: FlowState, e: { id: string; reason: CloseReason; now: number; withAgent: boolean }): FlowState =>
  e.withAgent ? closeAgent(s, e.id, e.reason, e.now) : s
const closeBoth = (s: FlowState, id: string, reason: CloseReason, status: string, now: number): FlowState =>
  closeAgent(closeTask(s, id, reason, status, now), id, reason, now)

const asClosed = (w: WorkEntry, reason: CloseReason): WorkEntry => ({ ...w, phase: 'closed', reason })

// A background task is over: the block stops running and the time it ran is booked. Idempotent.
// A failed one gets the red ring for a few seconds.
const closeTask = (s: FlowState, id: string, reason: CloseReason, status: string, end: number): FlowState => {
  const entry = runningEntry(s, id, 'task')
  const next = entry ? withEntry(s, asClosed(entry, reason)) : s

  return withNodes(
    next,
    s.view.nodes.map(n =>
      n.taskId === id && n.running > 0
        ? {
            ...n,
            at: end,
            running: 0,
            startSum: 0,
            isBackground: false,
            errorAt: status === 'failed' ? end : n.errorAt,
            ms: (n.ms ?? 0) + Math.max(0, end - (n.startSum ?? end)),
          }
        : n,
    ),
  )
}

// A background agent is over: its branch stops running (grey ring off) and the time since its start is booked.
const closeAgent = (s: FlowState, id: string, reason: CloseReason, end: number): FlowState => {
  const cur = runningEntry(s, id, 'agent')
  if (!cur) return s

  return withNodes(
    withEntry(s, asClosed(cur, reason)),
    s.view.nodes.map(n =>
      n.key === cur.key
        ? {
            ...n,
            at: end,
            running: Math.max(0, n.running - 1),
            startSum: n.running - 1 > 0 ? (n.startSum ?? 0) - cur.startedAt : 0,
            isBackground: n.running - 1 > 0 ? n.isBackground : false,
            ms: (n.ms ?? 0) + (end - cur.startedAt),
          }
        : n,
    ),
  )
}

// ---- reading the work cache

const runningEntry = (s: FlowState, id: string, kind: WorkEntry['kind']): WorkEntry | undefined => {
  const w = s.work.get(id)

  return w && w.kind === kind && w.phase === 'running' ? w : undefined
}
const isRunning = (s: FlowState, id: string, kind: WorkEntry['kind']): boolean => !!runningEntry(s, id, kind)
const runningOf = (s: FlowState, kind: WorkEntry['kind']): WorkEntry[] =>
  [...s.work.values()].filter(w => w.kind === kind && w.phase === 'running')
const isFollowed = (s: FlowState, id: string): boolean => isRunning(s, id, 'task') || isRunning(s, id, 'agent')

// Whether a background agent with this id is followed now (its turns light its node).
export const isFollowedAgent = (s: FlowState, id: string): boolean => isRunning(s, id, 'agent')

// ================================================================ reconcile

// What the real sources say right now. `agents`: `$.agent.list()` (undefined = could not be read).
// `entries` and `shared`: the desktop store and the shared trees of the sessions in it
// (`entries` undefined = there is no store to read, the tree is left as it is).
export type Truth = {
  agents: readonly TaskRow[] | undefined
  entries?: readonly Stored[]
  shared?: ReadonlyMap<string, SubTree | undefined> // shared tree by engine session id
}

// Rebuilds what is shown from the real sources: first the background work (closing what no
// source confirms any more), then the sub-session tree.
export const reconcile = (state: FlowState, truth: Truth, now: number): FlowState => {
  const work = reconcileWork(state, truth, now)

  return truth.entries ? reconcileTree(work, truth.entries, truth.shared ?? new Map()) : work
}

const reconcileWork = (state: FlowState, truth: Truth, now: number): FlowState => {
  const running = [...state.work.values()].filter(w => w.phase === 'running')
  const verdict = reconcileTasks(
    new Map(running.map((w): [string, number] => [w.id, w.startedAt])),
    new Map(running.map((w): [string, number] => [w.id, w.misses])),
    new Set(running.filter(w => w.kind === 'agent').map(w => w.id)),
    { agents: truth.agents, stop: state.lastStop },
    now,
  )
  let s = state
  for (const w of running) {
    const misses = verdict.misses.get(w.id)
    if (misses !== undefined) s = withEntry(s, { ...w, misses })
  }
  for (const id of verdict.close) s = closeBoth(s, id, verdict.reasons.get(id) ?? 'missed-reconciles', 'completed', now)
  const isKnown = (id: string): boolean => isRunning(s, id, 'task')
  if (!s.view.nodes.some(n => isStaleTask(n, isKnown))) return s

  return withNodes(s, closeStaleTasks(s.view.nodes, isKnown))
}

// The sessions below this one, from the store: the whole tree, children of children included.
const reconcileTree = (s: FlowState, entries: readonly Stored[], shared: ReadonlyMap<string, SubTree | undefined>): FlowState => {
  const { localId, mine, nodes } = visibleSessions(entries, s.selfId, s.localId)
  const next = { ...s, localId }
  if (!mine) return next // not a desktop session, or the app has not written it yet: nothing is guessed

  return withView(next, {
    ...s.view,
    title: mine.title || s.view.title,
    sessionIds: nodes.map(n => n.entry.cli).filter(Boolean),
    subs: composeTiles(nodes, shared),
  })
}

// The session's own row in the store and what it started (see VISIBILITY_RULES).
export const visibleSessions = (
  entries: readonly Stored[],
  selfId: string,
  knownLocal: string,
): { localId: string; mine: Stored | undefined; nodes: StoredNode[] } => {
  const localId = localIdOf(entries, selfId, knownLocal)
  const mine = entries.find(e => e.local === localId)

  return { localId, mine, nodes: mine ? treeBelow(entries, localId) : [] }
}

// Engine ids of the sessions whose shared tree is worth reading (those with an engine id yet).
export const sharedIdsOf = (nodes: readonly StoredNode[]): string[] =>
  nodes.flatMap(n => [...(n.entry.cli ? [n.entry.cli] : []), ...sharedIdsOf(n.kids)])

// A tile for one store node: the child's own shared tree when it has written one, an empty
// "starting" tile while it has no engine id yet; its children come from the store, not from
// whatever its own file says.
export const composeTiles = (nodes: readonly StoredNode[], shared: ReadonlyMap<string, SubTree | undefined>): SubTree[] =>
  nodes.map(node => {
    const { entry } = node
    const file = entry.cli ? shared.get(entry.cli) : undefined
    const base: SubTree = file ?? { id: '', nodes: [], subs: [], mainRunning: false, isWaiting: false, wTotal: 0, k: 0 }
    const title = entry.title || base.title || 'Session'

    return { ...base, id: entry.cli || entry.local, title: entry.cli ? title : `${title} (starting)`, subs: composeTiles(node.kids, shared) }
  })

// ================================================================ session tree
// <tree>
// This session's local id. A known one is kept (the engine id can change under it); else
// the store entry that carries our engine id, as current, as last answered, or as earlier id.
export const localIdOf = (entries: readonly Stored[], selfId: string, known: string): string => {
  if (known) return known
  const byCli = entries.find(e => e.cli === selfId)
  const byHistory = entries.find(e => e.lastCli === selfId || e.prior.includes(selfId))

  return (byCli ?? byHistory)?.local ?? ''
}

// Everything the root started, children of children included: not archived, not a fork. A
// child that has no engine id yet is in the tree (its tile says it is starting).
export const treeBelow = (entries: readonly Stored[], rootLocal: string): StoredNode[] => {
  const seen = new Set([rootLocal])
  const grow = (parent: string, depth: number): StoredNode[] => {
    if (depth > MAX_TREE_DEPTH) return []
    const kids = entries.filter(e => isShownChild(e, parent, seen)).sort((a, b) => a.created - b.created)
    kids.forEach(k => seen.add(k.local))

    return kids.map(entry => ({ entry, kids: grow(entry.local, depth + 1) }))
  }

  return grow(rootLocal, 1)
}
// </tree>

// ================================================================ background tasks
// <tasks>
// A background command (Bash run_in_background, Ctrl+B, a timeout that moved it to
// the background) or a Monitor shows as a block of its own for as long as it runs.
// It has no token or cost data, so it is drawn without dots.
const TASK_NAME_CHARS = 200
export const squash = (v: unknown): string => (typeof v === 'string' ? v.replace(/\s+/g, ' ').trim() : '')

// The name /tasks lists: Bash its description, else its command; Monitor its description.
export const taskNameOf = (tool: string, input: Record<string, unknown>): string =>
  (squash(input.description) || squash(input.command)).slice(0, TASK_NAME_CHARS) || tool

// The tool call's own record: from `tool.call` it is `{ result }`, a bare record also works.
const recordOf = (ran: unknown): Record<string, unknown> => {
  const r = (ran as { result?: unknown } | undefined)?.result ?? ran

  return r && typeof r === 'object' ? (r as Record<string, unknown>) : {}
}

// The id of the task a finished tool call started: Bash returns `backgroundTaskId`
// only when the command went to the background, Monitor always returns `taskId`.
export const taskIdOf = (tool: string, ran: unknown): string | undefined => {
  const r = recordOf(ran)
  const id = tool === 'Bash' ? r.backgroundTaskId : tool === 'Monitor' ? r.taskId : undefined

  return typeof id === 'string' && id !== '' ? id : undefined
}

// How long a finite Monitor may run (0 = no limit); the engine reports the expiry
// itself, this is only a backstop.
export const monitorTimeoutMs = (ran: unknown): number => {
  const r = recordOf(ran)

  return r.persistent === true || typeof r.timeoutMs !== 'number' || !(r.timeoutMs > 0) ? 0 : r.timeoutMs
}

// When the backstop closes a finite Monitor (0 = never).
export const monitorDeadlineMs = (ran: unknown): number => {
  const ms = monitorTimeoutMs(ran)

  return ms > 0 ? ms + MONITOR_BACKSTOP_MS : 0
}

// The task a TaskStop call stopped.
export const stoppedTaskOf = (input: Record<string, unknown>, ran: unknown): string | undefined => {
  const id = recordOf(ran).task_id ?? input.task_id ?? input.shell_id

  return typeof id === 'string' && id !== '' ? id : undefined
}

// A task-notification message: `<task-notification><task-id>..</task-id><status>completed</status>
// <summary>..</summary></task-notification>`. A notification without a status
// (say a Monitor event line) is not an end.
const RUNNING_WORDS = ['running', 'working', 'pending', 'progress', 'in_progress']
export const parseTaskEnd = (text: string): { id: string; status: string; summary: string; isEnded: boolean } | undefined => {
  const tag = (name: string): string | undefined =>
    new RegExp(`<${name}>\\s*([\\s\\S]*?)\\s*</${name}>`, 'i').exec(text)?.[1]?.trim() || undefined
  const id = tag('task-id') ?? tag('task_id') ?? tag('taskId') ?? /task[ _-]?id["':=\s]+([A-Za-z0-9_-]+)/i.exec(text)?.[1]
  if (!id) return undefined
  const status = (tag('status') ?? '').toLowerCase()

  return { id, status, summary: squash(tag('summary')), isEnded: status !== '' && !RUNNING_WORDS.includes(status) }
}

// A transcript row of a task notification (`ui.render` UserMessage) names the task and how it
// ended; undefined for any other row or a status that is not an end.
export const endedTaskOfRow = (row: unknown): { id: string; status: string } | undefined => {
  const r = row as { origin?: { kind?: string }; task?: { id?: string; status?: string } } | undefined
  const id = r?.task?.id
  const status = (r?.task?.status ?? '').toLowerCase()

  return r?.origin?.kind === 'task-notification' && id && status !== '' && !RUNNING_WORDS.includes(status) ? { id, status } : undefined
}

// Task nodes that still run in a stored view but that this process never saw start:
// they ended while nobody listened, so they are closed. `isKnown` says which ids were
// seen live.
export type TaskNode = { taskId?: string; running: number; startSum?: number; isBackground: boolean }
export const isStaleTask = (n: TaskNode, isKnown: (id: string) => boolean): boolean =>
  !!n.taskId && n.running > 0 && !isKnown(n.taskId)
export const closeStaleTasks = <T extends TaskNode>(nodes: T[], isKnown: (id: string) => boolean): T[] =>
  nodes.map(n => (isStaleTask(n, isKnown) ? { ...n, running: 0, startSum: 0, isBackground: false } : n))

// What is true about background work, from the real sources: `$.agent.list()` (subagents,
// readable any time) and the Stop event's `background_tasks` (one row per shell, monitor,
// subagent or workflow; the only place the engine lists shells and monitors, so that part
// of the truth is as old as the last Stop). The cache of started work is only a guess; a
// cached item that is absent from the truth in TASK_MISSES reconciles in a row is closed.
// A row with an ended status closes it at once. A freshly started item is not judged for
// TASK_GRACE_MS, and a Stop list older than the item's start says nothing about it.
export type TaskTruth = {
  agents?: readonly TaskRow[] // `$.agent.list()`; undefined when it could not be read
  stop?: { at: number; rows: readonly TaskRow[] } // the last Stop's `background_tasks`
}
export type TaskVerdict = { close: string[]; misses: Map<string, number>; reasons: Map<string, CloseReason> }

// `live`: id -> when it was seen starting; `agentIds`: which of them are subagents.
export const reconcileTasks = (
  live: ReadonlyMap<string, number>,
  misses: ReadonlyMap<string, number>,
  agentIds: ReadonlySet<string>,
  truth: TaskTruth,
  now: number,
): TaskVerdict => {
  const close: string[] = []
  const reasons = new Map<string, CloseReason>()
  const next = new Map<string, number>()
  for (const [id, startedAt] of live) {
    const isAgent = agentIds.has(id)
    const rows = isAgent ? truth.agents : truth.stop && truth.stop.at > startedAt ? truth.stop.rows : undefined
    const kept = misses.get(id) ?? 0
    const row = rows?.find(r => r.id === id)
    if (row && TASK_ENDED.includes((row.status ?? '').toLowerCase())) {
      close.push(id)
      reasons.set(id, 'ended-status')
    } else if (rows === undefined || now - startedAt < TASK_GRACE_MS) {
      next.set(id, kept) // no usable truth yet: neither a miss nor a reset
    } else if (row) {
      next.set(id, 0)
    } else if (kept + 1 >= TASK_MISSES) {
      close.push(id)
      reasons.set(id, 'missed-reconciles')
    } else {
      next.set(id, kept + 1)
    }
  }

  return { close, misses: next, reasons }
}
// </tasks>

// ================================================================ maths of usage and the limit

export const weigh = (u: Usage | undefined): number =>
  u
    ? (u.input_tokens ?? 0) * WEIGHT.input +
      (u.output_tokens ?? 0) * WEIGHT.output +
      (u.cache_read_input_tokens ?? 0) * WEIGHT.cacheRead +
      (u.cache_creation_input_tokens ?? 0) * WEIGHT.cacheWrite
    : 0

export const freshTokens = (u: Usage | undefined): number =>
  u ? (u.input_tokens ?? 0) + (u.output_tokens ?? 0) + (u.cache_creation_input_tokens ?? 0) : 0

export const tokensOf = (result: unknown): number => {
  try {
    return (JSON.stringify(result) ?? '').length / CHARS_PER_TOKEN
  } catch {
    return 0
  }
}

// Tokens per second of a turn that moved `tokens` in `ms`; undefined when the
// time is too short to mean anything.
const MIN_TURN_MS = 500
export const paceOf = (tokens: number, ms: number): number | undefined =>
  ms >= MIN_TURN_MS && tokens >= 0 ? tokens / (ms / 1000) : undefined

// Learn k (percent of the limit per weighted token) from how far the limit has
// moved since the base against what the turns since then weighed. The limit is
// the whole account's, so other sessions inflate k a little; it is an estimate.
export const calibrate = (v: FlowView): FlowView => {
  const grown = v.limitPct - v.basePct
  return v.limitPct >= 0 && v.basePct >= 0 && grown > 0 && v.wTotal > 0 ? { ...v, k: grown / v.wTotal } : v
}

// Fold a fresh five_hour reading into the view; a new window restarts the base.
export const applyLimit = (v: FlowView, win: LimitWindow | undefined): FlowView => {
  if (!win) return v
  const pct = win.percentUsed
  const reset = win.resetsAt ?? ''
  const isNewBase = v.basePct < 0 || v.baseReset !== reset || pct < v.basePct
  const next: FlowView = isNewBase
    ? { ...v, limitPct: pct, basePct: pct, baseReset: reset, wTotal: 0, k: 0, nodes: v.nodes.map(n => ({ ...n, w: 0 })) }
    : { ...v, limitPct: pct }

  return calibrate(next)
}

// ================================================================ which node an event lights

export type Target = { key: string; label: string; kind: NodeKind }

export const sideTarget: Target = { key: 'side:fork', label: 'Side', kind: 'side' }

export const agentTarget = (type: string): Target => ({ key: `agent:${type}`, label: type, kind: 'agent' })

// A fork that no Agent tool call started (empty tool_use_id) is one a command
// started: /btw, /subtask or /fork. The engine does not say which, so all three
// share one "side" kind.
export const isSideFork = (e: { fork?: boolean; tool_use_id?: string }): boolean => e.fork === true && !e.tool_use_id

// What a spawned agent is. A background agent's tool call returns at once, so the spawn keeps it
// running; the spawn event says outright whether it is one (a teammate is not).
export const spawnKind = (e: { fork?: boolean; toolUseId?: string; background?: boolean; isTeammate?: boolean }): { isSide: boolean; isBackground: boolean } => {
  const isSide = isSideFork({ fork: e.fork, tool_use_id: e.toolUseId })

  return { isSide, isBackground: !isSide && e.background === true && !e.isTeammate }
}

// tool name (+ call arguments) -> which node the call lights up.
export const classify = (tool: string, args: Record<string, unknown>): Target => {
  if (tool === 'Agent' || tool === 'Task') {
    return agentTarget(typeof args.subagent_type === 'string' ? args.subagent_type : 'general-purpose')
  }
  if (tool === 'Skill') {
    const skill = typeof args.skill === 'string' ? args.skill : 'Skill'
    return { key: `skill:${skill}`, label: skill, kind: 'skill' }
  }
  if (tool.startsWith('mcp__ccd_')) {
    const app = (tool.split('__')[1] ?? 'app').replace(/^ccd_/, '')
    return { key: `app:${app}`, label: app, kind: 'app' }
  }
  if (tool.startsWith('mcp__')) {
    const server = tool.split('__')[1] ?? 'mcp'
    return { key: `mcp:${server}`, label: server, kind: 'mcp' }
  }
  return { key: `tool:${tool}`, label: tool, kind: 'tool' }
}

// Light up (or add) a node; keeps at most MAX_NODES, dropping the idlest.
export const touch = (nodes: FlowNode[], c: Target, now: number, patch: (n: FlowNode) => FlowNode): FlowNode[] => {
  const found = nodes.some(n => n.key === c.key)
  let next = found ? nodes : [...nodes, { ...c, at: now, running: 0, isBackground: false, errorAt: 0, w: 0 } as FlowNode]
  next = next.map(n => (n.key === c.key ? patch(n) : n))
  while (next.length > MAX_NODES) {
    const idle = next.filter(n => n.running === 0 && n.key !== c.key).sort((a, b) => a.at - b.at)[0]
    if (!idle) break
    next = next.filter(n => n.key !== idle.key)
  }
  return next
}

// ================================================================ what the view may ask about status

export const anyRunning = (nodes: FlowNode[], subs: SubTree[]): boolean =>
  nodes.some(n => n.running > 0) || subs.some(s => anyRunning(s.nodes, s.subs))

// A session with nothing running anywhere in it.
export const isSessionIdle = (sub: SubTree): boolean => !sub.mainRunning && !anyRunning(sub.nodes, sub.subs)

// A background task (/tasks, dark blue) is drawn only while it runs; an idle one is hidden.
export const isShownNode = (nd: FlowNode): boolean => !nd.taskId || nd.running > 0

// How a block looks right now.
export const statusOf = (
  nd: FlowNode,
  mainRunning: boolean,
  now: number,
): { noUsage: boolean; isRunning: boolean; ring: Ring | undefined; isActive: boolean; led: boolean } => {
  const noUsage = nd.hasUsage === false
  const isRunning = nd.running > 0
  const ring: Ring | undefined = now - nd.errorAt < ERROR_MS ? 'error' : isRunning && nd.isBackground ? 'background' : undefined

  return {
    noUsage,
    isRunning,
    ring,
    // A background task has its own lifetime: once it ended, a running main turn must not light it again.
    isActive: isRunning || (mainRunning && !nd.taskId),
    led: noUsage && isRunning,
  }
}

// The tree of one session as it is drawn and shared with the session that started it.
export const treeOf = (v: FlowView, selfId: string): SubTree => ({
  id: selfId,
  title: v.title,
  nodes: v.nodes,
  subs: v.subs,
  mainRunning: v.mainRunning,
  isWaiting: v.isWaiting,
  wTotal: v.wTotal,
  k: v.k,
  tps: v.mainTps,
  // dollars the session spent since its last prompt, and its dollars per weighted token
  usd: v.lastUsd === undefined ? undefined : Math.max(0, v.lastUsd - (v.promptUsd ?? v.lastUsd)),
  perW: (v.allW ?? 0) > 0 ? Math.max(0, (v.lastUsd ?? 0) - (v.baseUsd ?? 0)) / (v.allW ?? 1) : 0,
})

// Nothing worth saving yet: a saved view is never overwritten by such a view.
export const isEmpty = (v: FlowView): boolean => v.nodes.length === 0 && v.subs.length === 0 && v.wTotal === 0 && v.limitPct < 0

// After a restart the pane would start empty: the last saved view comes back, with nothing
// running (what ran is judged again by the reconcile) and the sub-sessions rebuilt from the store.
export const restoredView = (old: FlowView | undefined): FlowView | undefined =>
  old && Array.isArray(old.nodes) && Array.isArray(old.subs) && typeof old.k === 'number'
    ? {
        ...old,
        subs: [],
        nodes: old.nodes.map(n => ({ ...n, running: 0, isBackground: false })),
        mainRunning: false,
        isWaiting: false,
        flushAt: 0,
      }
    : undefined
