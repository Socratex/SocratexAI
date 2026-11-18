import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { FlowNode, FlowView, NodeKind, SubTree } from '../types'

const PANE = 'flow-panel'

// Tunables
const FONT = 20 // label size in CSS px (the SVG is drawn 1:1)
// The box takes the drawing's own width up to the pane, so a drawing declared FIT
// times larger than its viewBox is stretched to the pane width (scaled up or down).
const FIT = 3
const MIN_W = 300
const SYNC_MS = 3000 // how often the shared session files are looked at
const ATTACH_WINDOW_MS = 120000 // a new session file this soon after start_session is its child
const RADIUS = 10
const MAX_NODES = 4
const ERROR_MS = 6000
const LABEL_CHARS = 8
const COST_DECIMALS = 3 // decimals of a path's cost in percent
const FLUSH_MS = 2000 // state writes are batched into one redraw per this long

// Relative price of a token, the stand-in for how much of the limit it eats.
// A guess from API list prices; the learned factor `k` absorbs the scale.
const WEIGHT = { input: 1, output: 5, cacheRead: 0.1, cacheWrite: 1.25 }
// A tool result enters the context once (cache write) and is re-read on later
// turns: charged as a write plus about one cheap re-read per ten turns' worth.
const RESULT_WEIGHT = 1.35
const CHARS_PER_TOKEN = 4

// Component colours (fill) and state colours (ring).
const KIND = {
  you: { fill: '#3b82f6', text: '#ffffff' }, // blue
  claude: { fill: '#e8803a', text: '#1b1b1b' }, // orange
  agent: { fill: '#26c6da', text: '#102027' }, // cyan
  tool: { fill: '#8e1b3a', text: '#ffffff' }, // burgundy
  mcp: { fill: '#8e44ad', text: '#ffffff' }, // purple
  skill: { fill: '#f2c94c', text: '#1b1b1b' }, // yellow
  session: { fill: '#78909c', text: '#102027' }, // grey-blue
  app: { fill: '#e8803a', text: '#1b1b1b' }, // orange: the desktop app's own tools (ccd_*)
}
const STATE = {
  waiting: '#ff9800', // waiting for the user
  error: '#e53935',
  background: '#43a047', // background work
}

type Kind = keyof typeof KIND
type Box = {
  label: string
  full?: string // the whole name, shown as a tooltip when label is cut
  kind: Kind
  cx: number
  cy: number
  w: number
  h: number
  ring?: keyof typeof STATE
}

const INITIAL: FlowView = {
  sessionIds: [],
  subs: [],
  nodes: [],
  mainRunning: false,
  isWaiting: false,
  limitPct: -1,
  basePct: -1,
  baseReset: '',
  wTotal: 0,
  k: 0,
  agentNode: {},
  flushAt: 0,
  tick: 0,
}
// Change the shape tag when FlowView changes: it declines what an earlier
// version stored, which outlives a reload.
const view = atom({ plugin: 'flow-panel', key: 'view' } as const, INITIAL, {
  shape: 'flow-6',
})

// ------------------------------------------------------------------ maths

type Usage = {
  input_tokens?: number
  output_tokens?: number
  cache_read_input_tokens?: number
  cache_creation_input_tokens?: number
}

const weigh = (u: Usage | undefined): number =>
  u
    ? (u.input_tokens ?? 0) * WEIGHT.input +
      (u.output_tokens ?? 0) * WEIGHT.output +
      (u.cache_read_input_tokens ?? 0) * WEIGHT.cacheRead +
      (u.cache_creation_input_tokens ?? 0) * WEIGHT.cacheWrite
    : 0

// Learn k (percent of the limit per weighted token) from how far the limit has
// moved since the base against what the turns since then weighed. The limit is
// the whole account's, so other sessions inflate k a little; it is an estimate.
const calibrate = (v: FlowView): FlowView => {
  const grown = v.limitPct - v.basePct
  return v.limitPct >= 0 && v.basePct >= 0 && grown > 0 && v.wTotal > 0
    ? { ...v, k: grown / v.wTotal }
    : v
}

// Fold a fresh five_hour reading into the view; a new window restarts the base.
const applyLimit = (
  v: FlowView,
  win: { percentUsed: number; resetsAt?: string } | undefined,
): FlowView => {
  if (!win) return v
  const pct = win.percentUsed
  const reset = win.resetsAt ?? ''
  const isNewBase = v.basePct < 0 || v.baseReset !== reset || pct < v.basePct
  const next: FlowView = isNewBase
    ? {
        ...v,
        limitPct: pct,
        basePct: pct,
        baseReset: reset,
        wTotal: 0,
        k: 0,
        nodes: v.nodes.map(n => ({ ...n, w: 0 })),
      }
    : { ...v, limitPct: pct }

  return calibrate(next)
}

// ---------------------------------------------------------------- drawing

const M = 5 // left/top margin, px (always 5px from the left edge)
const TRUNK = M + 24 // x of the vertical trunk
const ELBOW = 14 // radius of the rounded corners
const ROW = 64 // vertical distance between branches

const pill = (x: number, y: number, text: string, pw: number) => {
  return (
    `<rect x="${x - pw / 2}" y="${y - 15}" width="${pw}" height="30" rx="8" ry="8" fill="#1e1e1e"/>` +
    `<text x="${x}" y="${y}" fill="#cfd8dc" font-size="${FONT}" font-family="sans-serif" text-anchor="middle" dominant-baseline="central">${text}</text>`
  )
}

// A line, plus a travelling dot (coloured like the component it leads to)
// while that component is active. `phase` (the time of the last flush) makes
// a redrawn dot carry on instead of jumping back to the start of the line.
const line = (d: string, colour: string, i: number, isActive: boolean, phase: number) => {
  const dur = 1.5 + i * 0.3
  const begin = -(phase % dur).toFixed(2)
  return (
    `<path d="${d}" fill="none" stroke="${colour}" stroke-opacity="${isActive ? 0.8 : 0.3}" stroke-width="2"/>` +
    (isActive
      ? `<circle r="5" fill="${colour}"><animateMotion begin="${begin}s" dur="${dur}s" repeatCount="indefinite" path="${d}"/></circle>`
      : '')
  )
}

const node = (b: Box) => {
  const k = KIND[b.kind]
  const ring = b.ring ? STATE[b.ring] : 'none'
  const ringW = b.ring ? 3.5 : 0
  const tip = b.full ? `<title>${b.full}</title>` : ''
  return (
    `<g>${tip}` +
    `<rect x="${b.cx - b.w / 2}" y="${b.cy - b.h / 2}" width="${b.w}" height="${b.h}" rx="${RADIUS}" ry="${RADIUS}" fill="${k.fill}" stroke="${ring}" stroke-width="${ringW}"/>` +
    `<text x="${b.cx}" y="${b.cy}" fill="${k.text}" font-size="${FONT}" font-family="sans-serif" text-anchor="middle" dominant-baseline="central">${b.label}</text></g>`
  )
}

const esc = (s: string) => s.replace(/[<>&"]/g, '')

// You -> Claude: how far the account's 5-hour limit has grown since the base.
const growthText = (v: FlowView) =>
  v.limitPct < 0 || v.basePct < 0
    ? '...'
    : `+${Math.max(0, v.limitPct - v.basePct).toFixed(1)}%`

// Claude -> a path: the estimated share of the 5-hour limit it cost, in percent.
const costText = (k: number, w: number) =>
  k > 0 ? `~${(w * k).toFixed(COST_DECIMALS)}%` : '...'

// One branch of the tree: a box, the figure on its line and what hangs below it.
type Row = {
  label: string
  full?: string
  kind: Kind
  w: number
  ring?: Box['ring']
  text: string
  isActive: boolean
  kids: Row[]
}

type Src = Pick<FlowView, 'nodes' | 'subs' | 'mainRunning' | 'wTotal' | 'k'>

// A session's branches: its own paths first, then the sessions it started,
// each of those holding the same again. `count` numbers the sessions.
const rowsOf = (s: Src, now: number, count: { n: number }): Row[] => [
  ...s.nodes.map(nd => {
    const isRunning = nd.running > 0
    const ring: Box['ring'] =
      now - nd.errorAt < ERROR_MS
        ? 'error'
        : isRunning && nd.isBackground
          ? 'background'
          : undefined

    return {
      label: esc(nd.label.length > LABEL_CHARS ? `${nd.label.slice(0, LABEL_CHARS - 1)}…` : nd.label),
      full: nd.label.length > LABEL_CHARS ? esc(nd.label) : undefined,
      kind: nd.kind as Kind,
      w: 96,
      ring,
      text: costText(s.k, nd.w),
      isActive: isRunning || s.mainRunning,
      kids: [] as Row[],
    }
  }),
  ...s.subs.map(sub => {
    count.n += 1
    const label = `Session ${count.n}`

    return {
      label,
      kind: 'session' as Kind,
      w: 120,
      ring: sub.isWaiting ? ('waiting' as const) : undefined,
      text: costText(sub.k, sub.wTotal),
      isActive: sub.mainRunning,
      kids: rowsOf(sub, now, count),
    }
  }),
]

type Out = { lines: string[]; boxes: string[]; right: number; bottom: number }

// Lays rows out down a trunk: a rounded elbow to each box, and a row's own
// branches start below it, a step to the right. Returns the next free row.
const layout = (
  rows: Row[],
  trunkX: number,
  topY: number,
  y0: number,
  out: Out,
  idx: { i: number },
): number => {
  let y = y0
  // Room for the widest figure on this level's lines, no more: the nested
  // levels add up, and a wide picture is scaled down to the pane.
  const gap = Math.max(...rows.map(r => r.text.length * 12 + 12)) + ELBOW + 8
  for (const r of rows) {
    const left = trunkX + gap
    const d = `M${trunkX},${topY} V${y - ELBOW} Q${trunkX},${y} ${trunkX + ELBOW},${y} H${left}`
    const pw = r.text.length * 12 + 12
    idx.i += 1
    out.lines.push(
      line(d, KIND[r.kind].fill, idx.i, r.isActive, 0) + pill((trunkX + ELBOW + left) / 2, y, r.text, pw),
    )
    out.boxes.push(node({ label: r.label, full: r.full, kind: r.kind, cx: left + r.w / 2, cy: y, w: r.w, h: 40, ring: r.ring }))
    out.right = Math.max(out.right, left + r.w)
    out.bottom = Math.max(out.bottom, y + 20)
    y = r.kids.length ? layout(r.kids, left + 16, y + 20, y + ROW, out, idx) : y + ROW
  }

  return y
}

const draw = (v: FlowView, now: number): string => {
  const you: Box = {
    label: 'User',
    kind: 'you',
    cx: M + 48,
    cy: M + 20,
    w: 96,
    h: 40,
    ring: v.isWaiting ? 'waiting' : undefined,
  }
  const claude: Box = { label: 'Claude', kind: 'claude', cx: M + 65, cy: M + 100, w: 130, h: 46 }
  const trunkTop = you.cy + you.h / 2
  const trunkEnd = claude.cy - claude.h / 2
  const branchTop = claude.cy + claude.h / 2

  const out: Out = { lines: [], boxes: [], right: M + 130, bottom: branchTop }
  layout(rowsOf(v, now, { n: 0 }), TRUNK, branchTop, branchTop + 50, out, { i: 0 })

  const growth = growthText(v)
  const gw = growth.length * 12 + 12
  const width = Math.max(MIN_W, out.right + M)
  const height = out.bottom + M

  return (
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width * FIT}" height="${height * FIT}" preserveAspectRatio="xMinYMin meet">` +
    line(`M${TRUNK},${trunkTop} V${trunkEnd}`, KIND.claude.fill, 0, v.mainRunning, 0) +
    pill(TRUNK + 14 + gw / 2, (trunkTop + trunkEnd) / 2, growth, gw) +
    out.lines.join('') +
    node(you) +
    node(claude) +
    out.boxes.join('') +
    `</svg>`
  )
}

// ----------------------------------------------------------------- events

type Target = { key: string; label: string; kind: NodeKind }

const agentTarget = (type: string): Target => ({
  key: `agent:${type}`,
  label: type,
  kind: 'agent',
})

// tool name (+ call arguments) -> which node the call lights up.
const classify = (tool: string, args: Record<string, unknown>): Target => {
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
const touch = (
  nodes: FlowNode[],
  c: Target,
  now: number,
  patch: (n: FlowNode) => FlowNode,
): FlowNode[] => {
  const found = nodes.some(n => n.key === c.key)
  let next = found
    ? nodes
    : [
        ...nodes,
        { ...c, at: now, running: 0, isBackground: false, errorAt: 0, w: 0 } as FlowNode,
      ]
  next = next.map(n => (n.key === c.key ? patch(n) : n))
  while (next.length > MAX_NODES) {
    const idle = next
      .filter(n => n.running === 0 && n.key !== c.key)
      .sort((a, b) => a.at - b.at)[0]
    if (!idle) break
    next = next.filter(n => n.key !== idle.key)
  }
  return next
}


const tokensOf = (result: unknown): number => {
  try {
    return (JSON.stringify(result) ?? '').length / CHARS_PER_TOKEN
  } catch {
    return 0
  }
}

// Every state write redraws the pane, and a redraw makes the SVG frame blink.
// So writes are queued and applied together, at most once per FLUSH_MS.
let queued: Array<(v: FlowView) => FlowView> = []
let isFlushPending = false

// State that changed but would draw the same picture is held here instead of
// being written: a write redraws the pane, and every redraw makes it blink.
let held: FlowView | undefined

// ------------------------------------------------- sessions started from here
// Every session with the mod writes its tree to a file of its own in a shared
// folder; a session that starts others finds their files and draws them as
// "Session N" tiles. Nothing here costs model tokens.

let selfId = ''
let startedAt = 0
let lastSpawnAt = 0 // when this session last called start_session

const treeOf = (v: FlowView): SubTree => ({
  nodes: v.nodes,
  subs: v.subs,
  mainRunning: v.mainRunning,
  isWaiting: v.isWaiting,
  wTotal: v.wTotal,
  k: v.k,
})

async function folderOf($: EngineInterface): Promise<string> {
  const home = await $.env.get('SOCRATEX_HOME')
  if (!selfId) selfId = await $.session.id()
  if (!startedAt) startedAt = await $.clock.now()

  return home ? `${home.replace(/\\/g, '/')}/local/flow` : ''
}

async function publish($: EngineInterface, v: FlowView): Promise<void> {
  const dir = await folderOf($)
  if (!dir) return
  try {
    const at = await $.clock.now()
    const text = JSON.stringify({ id: selfId, startedAt, updatedAt: at, tree: treeOf(v), view: v })
    await $.fs.write(`${dir}/${selfId}.json`, text)
    await $.fs.write(`${dir}/last.json`, text) // what a fresh session starts from
  } catch {
    // the shared folder is optional: without it there are simply no session tiles
  }
}

type Shared = { id: string; startedAt: number; updatedAt: number; tree: SubTree; view?: FlowView }

async function loadShared($: EngineInterface, dir: string, id: string): Promise<Shared | undefined> {
  try {
    return JSON.parse(String(await $.fs.read(`${dir}/${id}.json`))) as Shared
  } catch {
    return undefined
  }
}

// After a restart the pane would start empty: take the last saved view instead
// (this session's own file when it was resumed, else the newest of any session).
async function restore($: EngineInterface): Promise<void> {
  const dir = await folderOf($)
  if (!dir) return
  const f = (await loadShared($, dir, selfId)) ?? (await loadShared($, dir, 'last'))
  const old = f?.view
  if (!old || !Array.isArray(old.nodes) || !Array.isArray(old.subs) || typeof old.k !== 'number') return
  await change($, v =>
    v.nodes.length > 0 || v.subs.length > 0 || v.wTotal > 0
      ? v
      : {
          ...old,
          nodes: old.nodes.map(n => ({ ...n, running: 0, isBackground: false })),
          mainRunning: false,
          isWaiting: false,
          flushAt: 0,
        },
  )
}

async function poll($: EngineInterface): Promise<void> {
  const dir = await folderOf($)
  if (!dir) return
  const cur = held ?? (await read($, view))
  const ids = [...cur.sessionIds]

  // A file born soon after our start_session call is the session we started.
  if (lastSpawnAt > 0) {
    let names: Array<{ name: string }> = []
    try {
      names = await $.fs.list(dir)
    } catch {
      names = []
    }
    for (const n of names) {
      const id = n.name.replace(/\.json$/, '')
      if (!n.name.endsWith('.json') || id === selfId || ids.includes(id)) continue
      const f = await loadShared($, dir, id)
      if (f && f.startedAt >= lastSpawnAt - 2000 && f.startedAt <= lastSpawnAt + ATTACH_WINDOW_MS) {
        ids.push(id)
      }
    }
  }

  const subs: SubTree[] = []
  const kept: string[] = []
  for (const id of ids) {
    const f = await loadShared($, dir, id)
    if (f) {
      subs.push(f.tree)
      kept.push(id)
    }
  }
  change($, v => ({ ...v, sessionIds: kept, subs }))
}

function change($: EngineInterface, fn: (v: FlowView) => FlowView): void {
  queued.push(fn)
  if (isFlushPending) return
  isFlushPending = true
  $.clock.after(FLUSH_MS, async () => {
    const batch = queued
    queued = []
    isFlushPending = false
    const at = await $.clock.now()
    const cur = held ?? (await read($, view))
    const next = batch.reduce((acc, f) => f(acc), cur)
    if (draw(next, at) === draw(cur, at)) {
      held = next
      await publish($, next)

      return
    }
    held = undefined
    await update($, view, () => next)
    await publish($, next)
  })
}

export const register: Register = on => {
  // A redraw restarts the dots, so there is no steady timer: each event
  // schedules one redraw for when a lit node or an error expires.
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'flow-panel',
      description: 'Open the animated flow pane',
    })
    // FLOW_PANEL=0 in the env block of a settings file turns the panel off:
    // ~/.claude/settings.json for everywhere, a project's .claude/settings.json
    // (or settings.local.json) for one project; the project value wins.
    if ((await $.env.get('FLOW_PANEL')) !== '0') {
      void $.ui.open({ id: PANE, title: 'Flow' })
    }
    await restore($)
    const { rateLimits } = await $.session.usage()
    const win = rateLimits.find(r => r.kind === 'five_hour')
    await change($, v => applyLimit(v, win))
    $.clock.every(SYNC_MS, () => poll($))

    return next(e)
  })

  // Every prompt brings the panel back if it was closed (unless switched off).
  on('prompt.submit', async ($, e, next) => {
    // Open only when it is not up: a repeated open re-seats the pane.
    if ((await $.env.get('FLOW_PANEL')) !== '0') {
      const isUp = (await $.ui.panes()).some(pane => pane.id === PANE)
      if (!isUp) void $.ui.open({ id: PANE, title: 'Flow' })
    }
    // A new prompt starts a fresh view: only segments used since then show.
    await change($, v => ({ ...v, nodes: [], agentNode: {} }))

    return next(e)
  })

  // The command opens it by hand even where the panel is switched off.
  on('command.run', { command: 'flow-panel' }, async $ => {
    await $.ui.open({ id: PANE, title: 'Flow' })

    return { text: 'Flow pane opened.' }
  })

  on('turn.start', async ($, e, next) => {
    if (e.agentId === undefined) {
      await change($, v => ({ ...v, mainRunning: true, isWaiting: false }))
    }

    return next(e)
  })

  // A turn's exact usage: it counts toward the calibration, and a sub-agent's
  // turn is also charged to that agent's own path.
  on('turn.complete', async ($, e, next) => {
    const cost = weigh(e.usage)
    await change($, v => {
      const key = e.agentId === undefined ? undefined : v.agentNode[e.agentId]
      const moved: FlowView = {
        ...v,
        wTotal: v.wTotal + cost,
        nodes: key ? v.nodes.map(n => (n.key === key ? { ...n, w: n.w + cost } : n)) : v.nodes,
        ...(e.agentId === undefined ? { mainRunning: false, isWaiting: true } : {}),
      }

      return calibrate(moved)
    })

    return next(e)
  })

  // The sub-agent's id, so its own turns can be charged to its node.
  on('agent.spawn', async ($, e, next) => {
    const started = await next(e)
    const id = 'agentId' in started ? started.agentId : undefined
    if (id) {
      const now = await $.clock.now()
      const target = agentTarget(e.subagentType)
      await change($, v => ({
        ...v,
        agentNode: { ...v.agentNode, [id]: target.key },
        nodes: touch(v.nodes, target, now, n => ({ ...n, at: now })),
      }))
    }

    return started
  })

  // Pushed when the engine measures the session: after each main turn and
  // whenever a rate-limit window moves a whole point.
  on('session.measure', async ($, e, next) => {
    const { rateLimits } = await $.session.usage()
    const win = rateLimits.find(r => r.kind === 'five_hour')
    await change($, v => applyLimit(v, win))

    return next(e)
  })

  on('tool.call', async ($, e, next) => {
    const now = await $.clock.now()
    const args = e as unknown as Record<string, unknown>
    const c = classify(String(e.tool), args)
    const isBackground = args.run_in_background === true
    if (/start_session|hand_off_to_session/.test(String(e.tool))) lastSpawnAt = now
    await change($, v => ({
      ...v,
      nodes: touch(v.nodes, c, now, n => ({
        ...n,
        at: now,
        running: n.running + 1,
        isBackground: isBackground || n.isBackground,
      })),
    }))

    let failed = false
    let resultTokens = 0
    try {
      const ran = await next(e)
      resultTokens = tokensOf(ran)

      return ran
    } catch (err) {
      failed = true
      throw err
    } finally {
      const end = await $.clock.now()
      await change($, v => ({
        ...v,
        nodes: v.nodes.map(n =>
          n.key === c.key
            ? {
                ...n,
                at: end,
                running: Math.max(0, n.running - 1),
                isBackground: n.running - 1 > 0 ? n.isBackground : false,
                errorAt: failed ? end : n.errorAt,
                w: n.w + resultTokens * RESULT_WEIGHT,
              }
            : n,
        ),
      }))
    }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text, Svg } = $.ui.resolve(e)
    const v = await read($, view)
    const now = await $.clock.now()

    return (
      <Box flexDirection="column" alignItems="flex-start">
        {Svg ? (
          <Svg
            source={draw(v, now)}
            alt="Live graph: you, Claude and the sub-agents, tools, MCP servers and skills it uses, with the limit cost on each line"
            isInteractive
          />
        ) : (
          <Text dimColor>This surface has no Svg element.</Text>
        )}
      </Box>
    )
  })
}
