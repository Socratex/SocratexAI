import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Figure, FlowNode, FlowView, NodeKind, SubTree } from '../types'

const PANE = 'flow-panel'

// Tunables
const FONT = 20 // label size in CSS px (the SVG is drawn 1:1)
// The box takes the drawing's own width up to the pane and a wider drawing is
// shrunk to it, so FIT must stay 1 (3 made everything three times smaller). A drawing declared FIT
// times larger than its viewBox is stretched to the pane width (scaled up or down).
const FIT = 1
const MIN_W = 300
const STALE_MS = 3 * 60 * 1000 // an idle session file this old is dropped (the app tells the mod nothing about archiving)
const SYNC_MS = 3000 // how often the shared session files are looked at
const ATTACH_WINDOW_MS = 120000 // a new session file this soon after start_session is its child
const RADIUS = 10
const MAX_NODES = 12
const ERROR_MS = 6000
const LABEL_CHARS = 8
const FLUSH_MS = 2000 // state writes are batched into one redraw per this long

// Relative price of a token, the stand-in for how much of the limit it eats.
// A guess from API list prices; the learned factor `k` absorbs the scale.
const WEIGHT = { input: 1, output: 5, cacheRead: 0.1, cacheWrite: 1.25 }
// A tool result enters the context once (cache write) and is re-read on later
// turns: charged as a write plus about one cheap re-read per ten turns' worth.
const RESULT_WEIGHT = 1.35
const CHARS_PER_TOKEN = 4

// Component colours (fill) and state colours (ring).
// `light` is the border of a component that is working right now.
const KIND = {
  you: { fill: '#3b82f6', light: '#8ab4fa', text: '#ffffff' }, // blue
  claude: { fill: '#e8803a', light: '#f4a76b', text: '#1b1b1b' }, // orange
  agent: { fill: '#26c6da', light: '#7ee3ef', text: '#102027' }, // cyan
  tool: { fill: '#8e1b3a', light: '#c2476a', text: '#ffffff' }, // burgundy
  mcp: { fill: '#8e44ad', light: '#be7fd6', text: '#ffffff' }, // purple
  skill: { fill: '#f2c94c', light: '#f8e08e', text: '#1b1b1b' }, // yellow
  session: { fill: '#26c6da', light: '#7ee3ef', text: '#102027' }, // cyan, like a sub-agent
  app: { fill: '#e8803a', light: '#f4a76b', text: '#1b1b1b' }, // orange: the desktop app's own tools (ccd_*)
  side: { fill: '#ec4899', light: '#f59ac4', text: '#ffffff' }, // pink: a side fork a command started (/btw, /subtask)
  task: { fill: '#1e3a8a', light: '#4f6fc4', text: '#ffffff' }, // dark blue: a background command or monitor (/tasks)
}
const STATE = {
  waiting: '#ff9800', // waiting for the user
  error: '#e53935',
  background: '#9e9e9e', // background work (grey)
}

type Kind = keyof typeof KIND

// Every session gets its own small shift of the whole palette, so its tree reads
// as a family of its own: the hue moves a few degrees and the lightness a little
// up or down. The shift covers fills, active borders, glow, lines and dots (they
// all come from `palette`); state rings and text colours stay as they are,
// because they carry meaning. The root tree (this session) is never shifted.
const SHADES = [
  { hue: 0, light: 0 },
  { hue: 14, light: 0.05 },
  { hue: -14, light: -0.05 },
  { hue: 26, light: -0.04 },
  { hue: -26, light: 0.06 },
  { hue: 8, light: -0.08 },
  { hue: -8, light: 0.09 },
]

const hexToHsl = (hex: string): [number, number, number] => {
  const r = parseInt(hex.slice(1, 3), 16) / 255
  const g = parseInt(hex.slice(3, 5), 16) / 255
  const b = parseInt(hex.slice(5, 7), 16) / 255
  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  const l = (max + min) / 2
  const d = max - min
  if (d === 0) return [0, 0, l]
  const sat = d / (1 - Math.abs(2 * l - 1))
  const h = max === r ? ((g - b) / d) % 6 : max === g ? (b - r) / d + 2 : (r - g) / d + 4

  return [(h * 60 + 360) % 360, sat, l]
}

const hslToHex = (h: number, s: number, l: number): string => {
  const c = (1 - Math.abs(2 * l - 1)) * s
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1))
  const m = l - c / 2
  const [r, g, b] = h < 60 ? [c, x, 0] : h < 120 ? [x, c, 0] : h < 180 ? [0, c, x] : h < 240 ? [0, x, c] : h < 300 ? [x, 0, c] : [c, 0, x]
  const hex = (v: number): string => Math.round((v + m) * 255).toString(16).padStart(2, '0')

  return `#${hex(r)}${hex(g)}${hex(b)}`
}

const shiftHex = (hex: string, shade: number): string => {
  const sh = SHADES[shade <= 0 ? 0 : 1 + ((shade - 1) % (SHADES.length - 1))]!
  if (sh.hue === 0 && sh.light === 0) return hex
  const [h, s, l] = hexToHsl(hex)

  return hslToHex((h + sh.hue + 360) % 360, s, Math.min(0.9, Math.max(0.1, l + sh.light)))
}

// The colours of a kind in a session's shade (0 = the root tree, unshifted).
const palette = (kind: Kind, shade = 0): { fill: string; light: string; text: string } => {
  const k = KIND[kind]

  return { fill: shiftHex(k.fill, shade), light: shiftHex(k.light, shade), text: k.text }
}
type Box = {
  label: string
  full?: string // the whole name, shown as a tooltip when label is cut
  kind: Kind
  cx: number
  cy: number
  w: number
  h: number
  ring?: keyof typeof STATE
  isActive?: boolean // working now: a lighter border of its own colour
  shade?: number // the session's colour shift (index into SHADES)
  led?: boolean // a small blinking grey status LED in the top-right corner (work with no usage data to show as dots)
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
  shape: 'flow-9',
})

// What the figure on every line shows. Kept apart from the view: it is a
// display choice of this person, not shared with the sessions above or below.
// The toggle: one icon per measure; the chosen one is lit, the others dim.
const FIGURE_ICON: Record<Figure, string> = { cost: '$', time: '◷', tokens: '❐' }

const figureAtom = atom({ plugin: 'flow-panel', key: 'figure' } as const, 'cost' as Figure, {
  shape: 'figure-1',
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

// ---------------------------------------------------------------- intensity
// <tiers>
// How hard a line works is the pace of tokens through it, in tokens per second
// (tps): input + output + cache-write tokens of a turn over the turn's wall time
// (cache reads are cheap and would drown everything else). Every second one
// batch of dots leaves; the batch size (1-8) is the tier of the line's tps.
//
// Thresholds come from the owner's own data, not a guess: 25k assistant turns
// in ~/.claude/projects transcripts (measured 2026-11-18, turns of 1-600 s),
// tps of the turns at percentiles p10/p25/p40/p55/p70/p85/p95 was
// 219/375/559/816/1254/2322/5465. Those seven cut points make eight tiers; they
// grow about 1.5x to 2.4x per step (roughly logarithmic), so the middle tiers
// separate everyday work and the top two only light up on really heavy turns
// instead of filling the screen. Rounded for readability. Typical model
// generation speeds: no source, derived from local data (the output-only median
// there is about 220 tok/s, inflated by streamed entries, so it is not a model
// speed claim). Change the pace of the animation by editing this table only.
const TIERS = [
  { name: 'almost nothing', minTps: 0, dots: 1 },
  { name: 'little', minTps: 220, dots: 2 }, // p10
  { name: 'not so little', minTps: 375, dots: 3 }, // p25
  { name: 'medium', minTps: 560, dots: 4 }, // p40
  { name: 'a bit above medium', minTps: 800, dots: 5 }, // p55
  { name: 'quite a lot', minTps: 1250, dots: 6 }, // p70
  { name: 'a lot', minTps: 2300, dots: 7 }, // p85
  { name: 'tons', minTps: 5500, dots: 8 }, // p95
]

// The tier (0-based index into TIERS) of a pace; unknown, zero or negative pace
// is the lowest tier, so an active line always shows at least one dot.
const tierOf = (tps: number | undefined): number => {
  if (tps === undefined || !(tps > 0)) return 0
  let tier = 0
  for (let i = 0; i < TIERS.length; i += 1) if (tps >= TIERS[i]!.minTps) tier = i

  return tier
}

// Tokens per second of a turn that moved `tokens` in `ms`; undefined when the
// time is too short to mean anything.
const MIN_TURN_MS = 500
const paceOf = (tokens: number, ms: number): number | undefined =>
  ms >= MIN_TURN_MS && tokens >= 0 ? tokens / (ms / 1000) : undefined

// Paint order of lines: SVG has no z-index, a later element lies on top. Idle
// lines go first, then active ones by rising tier, so the busiest line is on
// top. The sort is stable: equal intensity keeps the layout order.
const byIntensity = <T extends { rank: number }>(items: T[]): T[] =>
  items
    .map((item, i) => ({ item, i }))
    .sort((a, b) => a.item.rank - b.item.rank || a.i - b.i)
    .map(x => x.item)

// A fork that no Agent tool call started (empty tool_use_id) is one a command
// started: /btw, /subtask or /fork. The engine does not say which, so all three
// share one "side" kind.
const isSideFork = (e: { fork?: boolean; tool_use_id?: string }): boolean => e.fork === true && !e.tool_use_id

// The figure on a line is one of three measures; a button cycles through them.
const FIGURES = ['cost', 'time', 'tokens'] as const
const nextFigure = (f: string | undefined): (typeof FIGURES)[number] =>
  FIGURES[(Math.max(0, FIGURES.indexOf(f as (typeof FIGURES)[number])) + 1) % FIGURES.length]!

// Tokens in K, then in M, always one decimal: 743 -> 0.7K, 34500 -> 34.5K, 1.5M.
const fmtTokens = (n: number): string => {
  const v = Math.max(0, Number.isFinite(n) ? n : 0)
  if (v === 0) return '0'
  const k = Math.round(v / 100) / 10 // thousands, one decimal
  if (k < 1000) return `${k.toFixed(1)}K`

  return `${(Math.round(v / 1e5) / 10).toFixed(1)}M`
}

// Wall time in seconds and minutes only: 0.4s, 12s, 3m05s, 62m00s.
const fmtTime = (ms: number): string => {
  const v = Math.max(0, Number.isFinite(ms) ? ms : 0)
  if (v < 10000) return `${(Math.round(v / 100) / 10).toString()}s`
  const s = Math.round(v / 1000)
  if (s < 60) return `${s}s`

  return `${Math.floor(s / 60)}m${String(s % 60).padStart(2, '0')}s`
}

// Live time. A path that is running now has `running` calls, which started at
// `startSum` in total, so the time it has spent grows by `running` seconds each
// second: elapsed(T) = ms + running * T - startSum. The picture pre-draws one
// label per second ahead and a SMIL animation shows them one after another.
const liveElapsed = (ms: number, running: number, startSum: number, nowMs: number): number =>
  Math.max(0, ms + running * nowMs - startSum)

const liveLabels = (ms: number, running: number, startSum: number, nowMs: number, count: number): string[] =>
  Array.from({ length: Math.max(1, count) }, (_, k) =>
    fmtTime(Math.floor(liveElapsed(ms, running, startSum, nowMs + k * 1000) / 1000) * 1000),
  )
// You -> Claude: how far the account's 5-hour limit has grown since the base.
// Short percent: 1 or more keeps one decimal, below 1 keeps one significant
// digit (0.054 -> 0.05, 0.245 -> 0.2); trailing zeros are dropped (18.0 -> 18).
const pct = (n: number): string => {
  if (n <= 0) return '0'
  const decimals = n >= 1 ? 1 : Math.min(20, Math.ceil(-Math.log10(n)))
  const s = n.toFixed(decimals)

  return s.includes('.') ? s.replace(/\.?0+$/, '') : s
}

// Money: cents (rounded like the percent figures) below one dollar, then dollars
// with one decimal: 0.4 -> 40¢, 1.234 -> $1.2. Cents that would round up to 100
// already show as dollars.
const fmtMoney = (usd: number): string => {
  const cents = Math.max(0, Number.isFinite(usd) ? usd : 0) * 100
  if (cents >= 99.95) return `$${(Math.round(cents / 10) / 10).toFixed(1)}`

  return `${pct(cents)}¢`
}
// </tiers>

// ------------------------------------------------------------- merged blocks
// <merge>
const esc = (s: string) => s.replace(/[<>&"]/g, '')

// Claude -> a path: what it cost, as the engine's cost ledger prices it (see `fmtMoney`).
const usdText = (usd: number | undefined): string => (usd === undefined ? '...' : fmtMoney(usd))

// The text on a line for the chosen measure. A path with no usage data at all
// (a background command) has no cost and no tokens, only time.
const figureText = (
  f: 'cost' | 'time' | 'tokens',
  r: { usd: number | undefined; tok: number; ms: number; noUsage?: boolean },
): string =>
  r.noUsage && f !== 'time' ? '-' : f === 'tokens' ? fmtTokens(r.tok) : f === 'time' ? fmtTime(r.ms) : usdText(r.usd)

// Leaf blocks (no children) that cost less than this merge into one block per
// category when a category has two or more of them. The threshold is always by
// cost, whatever the toggle shows, so blocks do not jump when the unit changes.
const CHEAP_USD = 0.01
const MERGE_LABELS: Record<string, string> = { tool: 'Tools', mcp: 'MCP', skill: 'Skills', app: 'Apps' }

type MergeRow = {
  label: string
  full?: string
  kind: string
  ring?: string
  usd: number | undefined
  tok: number
  ms: number
  liveN: number
  liveSum: number
  text: string
  isActive: boolean
  tps?: number
  tpsIn?: number
  noUsage?: boolean
  led?: boolean
  calls?: number
  kids: unknown[]
}

// A block with an unknown cost ('...') or no usage data (a task) is never merged.
const isCheapLeaf = (r: MergeRow): boolean =>
  r.kind in MERGE_LABELS && r.kids.length === 0 && !r.noUsage && r.usd !== undefined && r.usd < CHEAP_USD

const mergedRow = <T extends MergeRow>(group: T[], unit: 'cost' | 'time' | 'tokens', nowMs: number): T => {
  const sum = (pick: (r: T) => number): number => group.reduce((a, r) => a + pick(r), 0)
  const live = (r: { ms: number; liveN: number; liveSum: number }): number =>
    r.ms + (r.liveN > 0 ? liveElapsed(0, r.liveN, r.liveSum, nowMs) : 0)
  const total = {
    usd: sum(r => r.usd ?? 0),
    tok: sum(r => r.tok),
    ms: sum(r => r.ms),
    liveN: sum(r => r.liveN),
    liveSum: sum(r => r.liveSum),
  }
  // The tooltip: one member a line in the chosen unit; the same name twice counts calls.
  const byName = new Map<string, { calls: number; usd: number; tok: number; ms: number; liveN: number; liveSum: number }>()
  for (const r of group) {
    const name = r.full ?? r.label // the whole name: the label is cut and two names may share a prefix
    const m = byName.get(name) ?? { calls: 0, usd: 0, tok: 0, ms: 0, liveN: 0, liveSum: 0 }
    byName.set(name, {
      calls: m.calls + (r.calls ?? 1),
      usd: m.usd + (r.usd ?? 0),
      tok: m.tok + r.tok,
      ms: m.ms + r.ms,
      liveN: m.liveN + r.liveN,
      liveSum: m.liveSum + r.liveSum,
    })
  }
  const lines = [...byName.entries()].map(
    ([name, m]) => `${name}${m.calls > 1 ? ` (x${m.calls})` : ''} ${figureText(unit, { usd: m.usd, tok: m.tok, ms: live(m) })}`,
  )
  const ring = group.some(r => r.ring === 'error') ? 'error' : group.some(r => r.ring === 'background') ? 'background' : undefined

  return {
    ...group[0]!,
    label: MERGE_LABELS[group[0]!.kind]!,
    full: esc(lines.join('\n')),
    ring,
    ...total,
    text: figureText(unit, { usd: total.usd, tok: total.tok, ms: live(total) }),
    isActive: group.some(r => r.isActive),
    led: group.some(r => r.led),
    calls: sum(r => r.calls ?? 1),
    tps: group.reduce<number | undefined>((a, r) => (r.tps === undefined ? a : Math.max(a ?? 0, r.tps)), undefined),
    tpsIn: group.reduce<number | undefined>((a, r) => (r.tpsIn === undefined ? a : Math.max(a ?? 0, r.tpsIn)), undefined),
  }
}

// Per category, the cheap leaf blocks become one block (at the place of the
// first of them) when there are two or more; a single cheap block stays as is.
const mergeCheap = <T extends MergeRow>(rows: T[], unit: 'cost' | 'time' | 'tokens', nowMs: number): T[] => {
  const groups = new Map<string, T[]>()
  for (const r of rows) if (isCheapLeaf(r)) groups.set(r.kind, [...(groups.get(r.kind) ?? []), r])
  const out: T[] = []
  const placed = new Set<string>()
  for (const r of rows) {
    const group = isCheapLeaf(r) ? groups.get(r.kind) : undefined
    if (!group || group.length < 2) out.push(r)
    else if (!placed.has(r.kind)) {
      placed.add(r.kind)
      out.push(mergedRow(group, unit, nowMs))
    }
  }

  return out
}
// </merge>

// ------------------------------------------------------- background tasks
// <tasks>
// A background command (Bash run_in_background, Ctrl+B, a timeout that moved it to
// the background) or a Monitor shows as a block of its own for as long as it runs.
// It has no token or cost data, so it is drawn without dots.
const TASK_NAME_CHARS = 200
const squash = (v: unknown): string => (typeof v === 'string' ? v.replace(/\s+/g, ' ').trim() : '')

// The name /tasks lists: Bash its description, else its command; Monitor its description.
const taskNameOf = (tool: string, input: Record<string, unknown>): string =>
  (squash(input.description) || squash(input.command)).slice(0, TASK_NAME_CHARS) || tool

// The tool call's own record: from `tool.call` it is `{ result }`, a bare record also works.
const recordOf = (ran: unknown): Record<string, unknown> => {
  const r = (ran as { result?: unknown } | undefined)?.result ?? ran

  return r && typeof r === 'object' ? (r as Record<string, unknown>) : {}
}

// The id of the task a finished tool call started: Bash returns `backgroundTaskId`
// only when the command went to the background, Monitor always returns `taskId`.
const taskIdOf = (tool: string, ran: unknown): string | undefined => {
  const r = recordOf(ran)
  const id = tool === 'Bash' ? r.backgroundTaskId : tool === 'Monitor' ? r.taskId : undefined

  return typeof id === 'string' && id !== '' ? id : undefined
}

// How long a finite Monitor may run (0 = no limit); the engine reports the expiry
// itself, this is only a backstop.
const monitorTimeoutMs = (ran: unknown): number => {
  const r = recordOf(ran)

  return r.persistent === true || typeof r.timeoutMs !== 'number' || !(r.timeoutMs > 0) ? 0 : r.timeoutMs
}

// The task a TaskStop call stopped.
const stoppedTaskOf = (input: Record<string, unknown>, ran: unknown): string | undefined => {
  const id = recordOf(ran).task_id ?? input.task_id ?? input.shell_id

  return typeof id === 'string' && id !== '' ? id : undefined
}

// A task-notification message: `<task-notification><task-id>..</task-id><status>completed</status>
// <summary>..</summary></task-notification>`. A notification without a status
// (say a Monitor event line) is not an end.
const RUNNING_WORDS = ['running', 'working', 'pending', 'progress', 'in_progress']
const parseTaskEnd = (text: string): { id: string; status: string; summary: string; isEnded: boolean } | undefined => {
  const tag = (name: string): string | undefined =>
    new RegExp(`<${name}>\\s*([\\s\\S]*?)\\s*</${name}>`, 'i').exec(text)?.[1]?.trim() || undefined
  const id = tag('task-id') ?? tag('task_id') ?? tag('taskId') ?? /task[ _-]?id["':=\s]+([A-Za-z0-9_-]+)/i.exec(text)?.[1]
  if (!id) return undefined
  const status = (tag('status') ?? '').toLowerCase()

  return { id, status, summary: squash(tag('summary')), isEnded: status !== '' && !RUNNING_WORDS.includes(status) }
}

// A transcript row of a task notification (`ui.render` UserMessage) names the task and how it
// ended; undefined for any other row or a status that is not an end.
const endedTaskOfRow = (row: unknown): { id: string; status: string } | undefined => {
  const r = row as { origin?: { kind?: string }; task?: { id?: string; status?: string } } | undefined
  const id = r?.task?.id
  const status = (r?.task?.status ?? '').toLowerCase()

  return r?.origin?.kind === 'task-notification' && id && status !== '' && !RUNNING_WORDS.includes(status) ? { id, status } : undefined
}

// A background agent is done when the agent list says it ended, or has dropped it
// (the engine drops a finished agent's row a little later). A freshly started
// agent may not be listed yet, hence the grace.
const AGENT_GRACE_MS = 10000
const AGENT_ENDED = ['completed', 'failed', 'killed']
const isAgentDone = (status: string | undefined, ageMs: number): boolean =>
  status === undefined ? ageMs > AGENT_GRACE_MS : AGENT_ENDED.includes(status)

// Task nodes that still run in a stored view but that this process never saw start:
// they ended while nobody listened, so they are closed. `isKnown` says which ids were
// seen live.
type TaskNode = { taskId?: string; running: number; startSum?: number; isBackground: boolean }
const isStaleTask = (n: TaskNode, isKnown: (id: string) => boolean): boolean =>
  !!n.taskId && n.running > 0 && !isKnown(n.taskId)
const closeStaleTasks = <T extends TaskNode>(nodes: T[], isKnown: (id: string) => boolean): T[] =>
  nodes.map(n => (isStaleTask(n, isKnown) ? { ...n, running: 0, startSum: 0, isBackground: false } : n))

// The engine's own list of in-flight background work (what /tasks shows) is handed to the
// mod only with the Stop event (`background_tasks`, one row per shell, monitor, subagent
// or workflow). A task this process saw start that is absent from a Stop's list, or
// listed with an ended status, is over. A freshly started task gets a grace period.
const TASK_GRACE_MS = 10000
const TASK_ENDED = ['completed', 'failed', 'killed', 'stopped', 'cancelled', 'canceled', 'error']
type TaskRow = { id: string; status?: string }
const isTaskGone = (row: TaskRow | undefined, ageMs: number): boolean =>
  row === undefined ? ageMs > TASK_GRACE_MS : TASK_ENDED.includes((row.status ?? '').toLowerCase())
// Ids of the live tasks (id -> start time) that the list says are over. An undefined list
// (an engine that sends none) closes nothing.
const goneTasks = (live: ReadonlyMap<string, number>, rows: readonly TaskRow[] | undefined, now: number): string[] =>
  rows === undefined ? [] : [...live].filter(([id, at]) => isTaskGone(rows.find(r => r.id === id), now - at)).map(([id]) => id)
// </tasks>

// ----------------------------------------------- background task re-check
// <recheck>
// While the only live things are background tasks (nothing else runs), the mod asks the
// engine's GetTask tool about each of them (once right away, then every minute) and closes only the ones it
// lists as finished (an explicit ended status). Best effort: whether GetTask accepts the ids of a background Bash or a
// Monitor is not proven, so every doubt leaves the task running (a longer glow, never a
// false close). The Stop event's own list (above) still reconciles while other work runs.
const RECHECK_MS = 60000
const RECHECK_MAX_FAILS = 3 // consecutive useless answers after which the tool is given up
const RECHECK_ENDED: Record<string, 'completed' | 'failed' | 'killed'> = {
  completed: 'completed',
  failed: 'failed',
  error: 'failed',
  killed: 'killed',
  stopped: 'killed',
  cancelled: 'killed',
  canceled: 'killed',
}
const RECHECK_RUNNING = ['working', 'running', 'pending', 'in_progress', 'progress']

type RecheckState = {
  isEnabled: boolean // FLOW_TASK_RECHECK is not 0
  failures: number // consecutive probes that told nothing usable
  mainRunning: boolean
  liveAgents: number // background agents this process follows
  nodes: Array<{ taskId?: string; running: number }>
}

// True when something still runs that is a background task and nothing else does.
const shouldRecheck = (s: RecheckState): boolean =>
  s.isEnabled &&
  s.failures < RECHECK_MAX_FAILS &&
  !s.mainRunning &&
  s.liveAgents === 0 &&
  s.nodes.some(n => n.running > 0 && !!n.taskId) &&
  s.nodes.every(n => n.running === 0 || !!n.taskId)

type TaskProbe =
  | { kind: 'ended'; status: 'completed' | 'failed' | 'killed' }
  | { kind: 'running' }
  | { kind: 'unknown' } // an answer of a shape or status not understood
  | { kind: 'error' } // the call threw, was denied or reported an error

// What GetTask answered: `{ result: { status, ... } }` (or the bare record), `{ deny }`,
// or `{ isError, text }`.
const probeOfResult = (ran: unknown): TaskProbe => {
  const top = (ran && typeof ran === 'object' ? ran : {}) as Record<string, unknown>
  if (typeof top.deny === 'string') return { kind: 'error' }
  if (top.isError === true) return { kind: 'error' } // includes "task not found": that never closes a task
  const status = recordOf(ran).status
  if (typeof status !== 'string') return { kind: 'unknown' }
  const word = status.trim().toLowerCase()
  if (word in RECHECK_ENDED) return { kind: 'ended', status: RECHECK_ENDED[word] }

  return RECHECK_RUNNING.includes(word) ? { kind: 'running' } : { kind: 'unknown' }
}

// A thrown error is a failure whatever its text (an unknown task included).
const probeOfError = (_err: unknown): TaskProbe => ({ kind: 'error' })

type ProbeBook = { failures: number }
// What one probe changes: whether to close the task (with which end status) and the
// book-keeping. Only an explicit ended status closes; every other answer (running, not
// found, error, unknown shape) leaves the task running, and all but "running" count as
// a useless answer toward the give-up limit.
const decideProbe = (p: TaskProbe, b: ProbeBook): { close?: 'completed' | 'failed' | 'killed'; book: ProbeBook } => {
  if (p.kind === 'running') return { book: { failures: 0 } }
  if (p.kind === 'ended') return { close: p.status, book: { failures: 0 } }

  return { book: { failures: b.failures + 1 } }
}
const isRecheckOff = (failures: number): boolean => failures >= RECHECK_MAX_FAILS

// One check runs right away when the timer condition begins to hold (not a minute later);
// while the timer already runs, only its ticks check.
const isInitialCheckDue = (want: boolean, isTimerRunning: boolean): boolean => want && !isTimerRunning

// Ids to probe now: tasks the panel shows as running that this process saw start, past
// the same start grace as the Stop-list check.
const tasksToProbe = (
  nodes: ReadonlyArray<{ taskId?: string; running: number }>,
  live: ReadonlyMap<string, number>,
  now: number,
): string[] => {
  const ids = nodes.filter(n => n.running > 0 && !!n.taskId && live.has(n.taskId)).map(n => n.taskId as string)

  return [...new Set(ids)].filter(id => now - (live.get(id) ?? now) > TASK_GRACE_MS)
}
// </recheck>

// ---------------------------------------------------------------- drawing

const M = 5 // left/top margin, px (always 5px from the left edge)
const TRUNK = M + 24 // x of the vertical trunk
const ELBOW = 14 // radius of the rounded corners
const ROW = 64 // vertical distance between branches

// The same pill with a time that ticks on its own: one <text> per second, each
// shown for its second by a SMIL <set>; the last one stays.
const livePill = (x: number, y: number, labels: string[], pw: number): string => {
  const at = (k: number, last: boolean): string =>
    `<text class="t" x="${x}" y="${y}"${k === 0 ? '' : ' visibility="hidden"'}>${labels[k]}` +
    (k === 0
      ? `<set attributeName="visibility" to="hidden" begin="1s" fill="freeze"/>`
      : `<set attributeName="visibility" to="visible" begin="${k}s"${last ? ' fill="freeze"' : ' dur="1s"'}/>`) +
    `</text>`
  let texts = ''
  for (let k = 0; k < labels.length; k += 1) texts += at(k, k === labels.length - 1)

  return `<rect x="${x - pw / 2}" y="${y - 15}" width="${pw}" height="30" rx="8" ry="8" fill="#1e1e1e"/>` + texts
}

const pill = (x: number, y: number, text: string, pw: number) => {
  return (
    `<rect x="${x - pw / 2}" y="${y - 15}" width="${pw}" height="30" rx="8" ry="8" fill="#1e1e1e"/>` +
    `<text x="${x}" y="${y}" fill="#cfd8dc" font-size="${FONT}" font-family="sans-serif" text-anchor="middle" dominant-baseline="central">${text}</text>`
  )
}

// A line, plus travelling dots (coloured like the component it leads to) while
// that component is active. A new batch of dots (1-8, by the line's tps tier)
// leaves the start every EMIT_S seconds, the dots in a row DOT_GAP apart, and
// every dot moves at DOT_SPEED px/s, so a long line simply holds more dots.
// All timing is pinned to the wall clock (`nowS`), so a redraw carries on where
// the dots were instead of restarting them. An active line also pulses once per
// emitted dot.
const DOT_SPEED = 120 // px per second, the same on every line
const EMIT_S = 1 // a new batch of dots every this many seconds
const DOT_BODY = 15 // length of a dot's solid body, px
const DOT_GAP = 1 // free space between neighbouring dots of a batch, px

// Seconds since a wall-clock-aligned cycle of `period` began, as a negative SMIL begin.
const clockBegin = (nowS: number, period: number, offset = 0): string =>
  (-(((nowS - offset) % period) + period) % period).toFixed(3)

// The same path walked the other way. Paths here are only M, V, H and Q with
// absolute coordinates, so reversing is a matter of reading the points back.
const reversePath = (d: string): string => {
  const toks = d.match(/[MVHQ]|-?\d+(?:\.\d+)?/g) ?? []
  const segs: Array<{ c: string; n: number[] }> = []
  for (const t of toks) {
    if (/[MVHQ]/.test(t)) segs.push({ c: t, n: [] })
    else segs[segs.length - 1]!.n.push(Number(t))
  }
  let [x, y] = segs[0]!.n as [number, number]
  const pts: Array<{ c: string; n: number[]; from: [number, number] }> = []
  for (const sg of segs.slice(1)) {
    pts.push({ ...sg, from: [x, y] })
    if (sg.c === 'V') y = sg.n[0]!
    else if (sg.c === 'H') x = sg.n[0]!
    else if (sg.c === 'Q') [x, y] = [sg.n[2]!, sg.n[3]!]
  }
  let out = `M${x},${y}`
  for (const sg of pts.reverse()) {
    if (sg.c === 'V') out += ` V${sg.from[1]}`
    else if (sg.c === 'H') out += ` H${sg.from[0]}`
    else if (sg.c === 'Q') out += ` Q${sg.n[0]},${sg.n[1]} ${sg.from[0]},${sg.from[1]}`
  }

  return out
}

const LANE = 6 // px between the centre of a line and the centre of each lane

// One active line carries two lanes of dots: the request goes down (parent to
// child) on one side of the line, the result comes back up on the other. Each
// lane has its own batch size (the tier of its own pace). A dot is offset
// sideways by its `cy`, which `rotate="auto"` turns perpendicular to the path,
// so the lane keeps the same side of its direction of travel round the corners:
// down it rides on the west/south side, up on the east/north side.
let isCalm = false // set by `draw`: no moving dots, no ticking times (see `fitted`)

const line = (
  d: string,
  length: number,
  colour: string,
  isActive: boolean,
  nowS: number,
  light = colour,
  tpsUp?: number,
  tpsDown?: number,
  hasNoDots = false, // no usage data to show: the line only pulses (see Row.noUsage)
) => {
  if (!isActive) return `<path d="${d}" fill="none" stroke="${colour}" stroke-opacity="0.3" stroke-width="2"/>`
  // A drawing near the size cap loses its moving dots, not the whole picture.
  if (isCalm) return `<path d="${d}" fill="none" stroke="${light}" stroke-opacity="0.8" stroke-width="3"/>`

  // A dot needs `travel` seconds for the line. A batch of `count` dots, each
  // trailing the one before by `lag` seconds, leaves every EMIT_S, so `n` batches
  // are on the line at once; each dot runs, then waits unseen for its next turn.
  const lag = (DOT_BODY + DOT_GAP) / DOT_SPEED
  const travel = Math.max(0.2, length / DOT_SPEED)
  const lane = (path: string, count: number, tint: string, offset: number): string => {
    const n = Math.max(1, Math.ceil((travel + (count - 1) * lag) / EMIT_S))
    const cycle = n * EMIT_S
    const run = (travel / cycle).toFixed(4)
    let dots = ''
    for (let j = 0; j < n; j += 1) {
      for (let i = 0; i < count; i += 1) {
        const begin = clockBegin(nowS, cycle, j * EMIT_S + i * lag + offset)
        const motion =
          `<animateMotion begin="${begin}s" dur="${cycle}s" repeatCount="indefinite" rotate="auto" path="${path}" ` +
          `calcMode="linear" keyPoints="0;1;1" keyTimes="0;${run};1"/>` +
          `<animate attributeName="visibility" values="visible;hidden;hidden" keyTimes="0;${run};1" calcMode="discrete" dur="${cycle}s" begin="${begin}s" repeatCount="indefinite"/>`
        // glow, solid body in the lighter colour, and a white-hot centre
        dots +=
          `<ellipse cy="${LANE}" rx="${DOT_BODY / 2 + 4.5}" ry="7" fill="${tint}" opacity="0.95" filter="url(#dotglow)">${motion}</ellipse>` +
          `<ellipse cy="${LANE}" rx="${DOT_BODY / 2}" ry="3.6" fill="${tint}">${motion}</ellipse>` +
          `<ellipse cy="${LANE}" rx="3.5" ry="1.4" fill="#fff" opacity="0.9">${motion}</ellipse>`
      }
    }

    return dots
  }
  // The returning lane starts half a beat later, so the two lanes do not pulse in step.
  const dots = hasNoDots
    ? ''
    : lane(d, TIERS[tierOf(tpsDown)]!.dots, light, 0) +
      lane(reversePath(d), TIERS[tierOf(tpsUp)]!.dots, light, EMIT_S / 2)
  // The pulse: a blurred halo and the line itself brighten as each dot leaves.
  const beat = clockBegin(nowS, EMIT_S)
  const halo =
    `<path d="${d}" fill="none" stroke="${light}" stroke-width="8" stroke-linecap="round" filter="url(#lineglow)">` +
    `<animate attributeName="stroke-opacity" values="0.7;0.15;0.7" dur="${EMIT_S}s" begin="${beat}s" repeatCount="indefinite"/></path>`
  const body =
    `<path d="${d}" fill="none" stroke="${light}" stroke-width="3">` +
    `<animate attributeName="stroke-opacity" values="1;0.5;1" dur="${EMIT_S}s" begin="${beat}s" repeatCount="indefinite"/></path>`

  return `${halo}${body}${dots}`
}

const node = (b: Box) => {
  const k = palette(b.kind, b.shade)
  const ring = b.ring ? STATE[b.ring] : b.isActive ? k.light : 'none'
  const ringW = b.ring || b.isActive ? 3.5 : 0
  const tip = b.full ? `<title>${b.full}</title>` : ''
  const x = b.cx - b.w / 2
  const y = b.cy - b.h / 2
  // A working node glows, its border pulses and a blinking dot sits on its corner.
  const glow = b.isActive
    ? `<rect x="${x - 2}" y="${y - 2}" width="${b.w + 4}" height="${b.h + 4}" rx="${RADIUS + 2}" ry="${RADIUS + 2}" fill="${k.light}" filter="url(#glow)"><animate attributeName="opacity" values="0.25;0.7;0.25" dur="1.4s" repeatCount="indefinite"/></rect>`
    : ''
  const pulse = b.isActive
    ? `<animate attributeName="stroke-opacity" values="1;0.35;1" dur="1.4s" repeatCount="indefinite"/>`
    : ''
  const dot = b.led
    ? `<circle cx="${x + b.w}" cy="${y}" r="5" fill="${STATE.background}" stroke="#000" stroke-opacity="0.4" stroke-width="1"><animate attributeName="opacity" values="1;0.2;1" dur="1s" repeatCount="indefinite"/></circle>`
    : b.isActive
    ? `<circle cx="${x + b.w}" cy="${y}" r="5" fill="${k.light}" stroke="#000" stroke-opacity="0.4" stroke-width="1"><animate attributeName="opacity" values="1;0.2;1" dur="1s" repeatCount="indefinite"/></circle>`
    : ''
  return (
    `<g>${tip}${glow}` +
    `<rect x="${x}" y="${y}" width="${b.w}" height="${b.h}" rx="${RADIUS}" ry="${RADIUS}" fill="${k.fill}" stroke="${ring}" stroke-width="${ringW}">${pulse}</rect>` +
    `<text x="${b.cx}" y="${b.cy}" fill="${k.text}" font-size="${FONT}" font-family="sans-serif" text-anchor="middle" dominant-baseline="central">${b.label}</text>${dot}</g>`
  )
}

// A path's dollars: an agent's own (exact) plus its tool results, priced at the
// session's average dollars per weighted token. Unknown until that average is.
const nodeUsd = (n: FlowNode, perW: number | undefined): number | undefined =>
  n.usd === undefined && n.w > 0 && !perW ? undefined : (n.usd ?? 0) + n.w * (perW ?? 0)

// One branch of the tree: a box, the figure on its line and what hangs below it.
type Row = {
  label: string
  full?: string
  kind: Kind
  w: number
  ring?: Box['ring']
  usd: number | undefined // the figure on its line; undefined = not known yet
  tok: number // fresh tokens of the path (a session: the sum of its branches)
  ms: number // execution time of the path (a session: the sum of its branches)
  liveN: number // calls running now (a session: the sum over its branches); its time ticks while > 0
  liveSum: number // their start times, summed (see liveElapsed)
  text: string
  isActive: boolean
  tps?: number // token pace of the result coming back up: sets the dots of the up lane
  tpsIn?: number // token pace of the request going down: sets the dots of the down lane
  shade: number // the session's colour shift: the same for a session tile and everything below it
  isIdle?: boolean // a session with nothing running anywhere in it
  noUsage?: boolean // no token or cost data exists (a background command): no dots, a status LED instead
  led?: boolean // a status LED on the block (any merged member has one)
  calls?: number // calls the path had; shown in the tooltip of a merged block
  kids: Row[]
}

// The sum of the known figures of some rows; '...' (undefined) when there are
// rows but none of them is known yet. No rows at all sum to zero. Rows with no
// usage data at all (background commands) are not part of any sum.
const sumUsd = (rows: Row[]): number | undefined => {
  const counted = rows.filter(r => !r.noUsage)
  const known = counted.map(r => r.usd).filter((u): u is number => u !== undefined)

  return counted.length > 0 && known.length === 0 ? undefined : known.reduce((a, b) => a + b, 0)
}

type Src = Pick<SubTree, 'nodes' | 'subs' | 'mainRunning' | 'perW' | 'usd' | 'tps'>

// The measure the figures show while a picture is drawn (set by `draw`).
let shownFigure: Figure = 'cost'
// The clock the drawing was made at, and how many live timers it may still carry.
const nowMsOf = (now: number): number => now
const LIVE_SECONDS = 70 // labels drawn ahead of a ticking time; a redraw is forced before they run out
const LIVE_MAX = 6 // ticking times per drawing (the SVG source is capped at 131072 characters)
const LIVE_REFRESH_MS = 60000
let liveLeft = LIVE_MAX

// The session this copy of the mod runs in: the root of every tree it draws.
let selfId = ''

// A session's branches: its own paths first, then the sessions it started,
// each of those holding the same again. `count` numbers the sessions.
const MAX_DEPTH = 4 // a guard: never draw sessions nested deeper than this
let depthLimit = MAX_DEPTH // lowered by `fitted` when the drawing is still too big
let isFolding = false // set by `fitted`: idle sessions fold into one tile even when few
const IDLE_FOLD_AT = 10 // this many idle sessions on one level fold into one tile
// Idle sessions sink to the bottom of their level and show no children. From
// IDLE_FOLD_AT of them (or near the size cap) they become a single tile,
// "12 sessions", whose tooltip lists their names one per line (nested ones indented).
const sessionNames = (r: Row, indent: string): string[] => [
  `${indent}${r.label}${r.full && r.full !== r.label ? ` - ${r.full}` : ''}`,
  ...r.kids.filter(k => k.kind === 'session').flatMap(k => sessionNames(k, `${indent}  `)),
]
const groupIdle = (rows: Row[]): Row[] => {
  const idle = rows.filter(r => r.kind === 'session' && r.isIdle)
  if (idle.length === 0) return rows
  const rest = rows.filter(r => !idle.includes(r))
  if (!isFolding && idle.length < IDLE_FOLD_AT) return [...rest, ...idle.map(r => ({ ...r, kids: [] }))]
  const usd = sumUsd(idle)
  const tok = idle.reduce((a, r) => a + r.tok, 0)
  const ms = idle.reduce((a, r) => a + r.ms, 0)
  const label = `${idle.length} session${idle.length === 1 ? '' : 's'}`
  const group: Row = {
    label,
    full: esc(idle.flatMap(r => sessionNames(r, '')).join('\n')),
    kind: 'session',
    w: 120,
    usd,
    tok,
    ms,
    liveN: 0,
    liveSum: 0,
    text: figureText(shownFigure, { usd, tok, ms }),
    isActive: false,
    shade: idle[0]!.shade,
    kids: [],
  }

  return [...rest, group]
}

const rowsOf = (s: Src, now: number, count: { n: number }, depth = 0, path: string[] = [selfId], shade = 0): Row[] =>
  groupIdle([
  // A background task (/tasks, dark blue) is drawn only while it runs; an idle one is hidden.
  ...mergeCheap(s.nodes.filter(nd => !nd.taskId || nd.running > 0).map((nd): Row => {
    const noUsage = nd.hasUsage === false
    const usd = noUsage ? undefined : nodeUsd(nd, s.perW)
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
      kind: (nd.taskId ? 'task' : nd.kind) as Kind,
      w: 96,
      ring,
      usd,
      tok: nd.tok ?? 0,
      ms: nd.ms ?? 0,
      liveN: isRunning ? nd.running : 0,
      liveSum: isRunning ? (nd.startSum ?? 0) : 0,
      text: figureText(shownFigure, { usd, tok: nd.tok ?? 0, ms: (nd.ms ?? 0) + (isRunning ? liveElapsed(0, nd.running, nd.startSum ?? 0, nowMsOf(now)) : 0), noUsage }),
      // A background task has its own lifetime: once it ended, a running main turn must not light it again.
      isActive: isRunning || (s.mainRunning && !nd.taskId),
      tps: nd.tps ?? s.tps,
      tpsIn: nd.tpsIn,
      shade,
      noUsage,
      led: noUsage && isRunning,
      calls: nd.calls,
      kids: [],
    }
  }), shownFigure, nowMsOf(now)),
  // A session already on the path above is the same session again: skip it.
  ...(depth >= depthLimit ? [] : s.subs.filter(sub => !path.includes(sub.id))).map((sub): Row => {
    count.n += 1
    const label = `Session ${count.n}`
    const subShade = count.n // the n-th session of the drawing; 0 stays the root's own
    const kids = rowsOf(sub, now, count, depth + 1, [...path, sub.id], subShade)
    // While a session works, its own ledger figure only moves at the end of a
    // turn, so it shows the sum of its branches, which grows as they finish.
    // Once it is idle, it shows what it really spent (its own model tokens too).
    const usd = sub.mainRunning ? sumUsd(kids) : sub.usd
    const tok = kids.reduce((a, k) => a + k.tok, 0)
    // A background task keeps its time on its own line; it is not part of a session's time.
    const timed = kids.filter(k => !k.noUsage)
    const ms = timed.reduce((a, k) => a + k.ms, 0)
    const liveN = timed.reduce((a, k) => a + k.liveN, 0)
    const liveSum = timed.reduce((a, k) => a + k.liveSum, 0)
    const isIdle = !sub.mainRunning && !anyRunning(sub.nodes, sub.subs)
    const figure = figureText(shownFigure, { usd, tok, ms: ms + (liveN > 0 ? liveElapsed(0, liveN, liveSum, nowMsOf(now)) : 0) })

    return {
      label,
      full: esc(sub.title || label),
      kind: 'session' as Kind,
      w: 120,
      ring: undefined,
      usd,
      tok,
      ms,
      liveN,
      liveSum,
      text: figure,
      isActive: sub.mainRunning,
      tps: sub.tps,
      shade: subShade,
      isIdle,
      kids,
    }
  }),
])

type Out = { lines: Array<{ rank: number; svg: string }>; boxes: string[]; right: number; bottom: number }

// Lays rows out down a trunk: a rounded elbow to each box, and a row's own
// branches start below it, a step to the right. Returns the next free row.
const layout = (
  rows: Row[],
  trunkX: number,
  topY: number,
  y0: number,
  out: Out,
  nowS: number,
): number => {
  let y = y0
  for (const r of rows) {
    const left = trunkX + ELBOW + 6
    const d = `M${trunkX},${topY} V${y - ELBOW} Q${trunkX},${y} ${trunkX + ELBOW},${y} H${left}`
    // straight down, a rounded quarter (about 1.16 x its radius), then across
    const length = Math.max(0, y - ELBOW - topY) + ELBOW * 1.16 + (left - trunkX - ELBOW)
    const isLive = shownFigure === 'time' && r.liveN > 0 && liveLeft > 0
    const labels = isLive ? liveLabels(r.ms, r.liveN, r.liveSum, nowS * 1000, LIVE_SECONDS) : []
    if (isLive) liveLeft -= 1
    const pw = (isLive ? labels[labels.length - 1]!.length : r.text.length) * 12 + 12
    // The figure sits right of the box, so deeper levels cost little width.
    out.lines.push({
      rank: r.isActive ? Math.max(tierOf(r.tps), tierOf(r.tpsIn)) : -1, // idle lines lie below every active one
      svg: line(d, length, palette(r.kind, r.shade).fill, r.isActive, nowS, palette(r.kind, r.shade).light, r.tps, r.tpsIn, r.noUsage) + (isLive ? livePill(left + r.w + 6 + pw / 2, y, labels, pw) : pill(left + r.w + 6 + pw / 2, y, r.text, pw)),
    })
    out.boxes.push(node({ label: r.label, full: r.full, kind: r.kind, cx: left + r.w / 2, cy: y, w: r.w, h: 40, ring: r.ring, isActive: r.isActive, shade: r.shade, led: r.led }))
    out.right = Math.max(out.right, left + r.w + 6 + pw)
    out.bottom = Math.max(out.bottom, y + 20)
    y = r.kids.length ? layout(r.kids, left + 12, y + 20, y + ROW, out, nowS) : y + ROW
  }

  return y
}

const draw = (v: FlowView, now: number, figure: Figure = 'cost'): string => {
  shownFigure = figure
  liveLeft = isCalm ? 0 : LIVE_MAX
  const you: Box = {
    label: 'User',
    kind: 'you',
    cx: M + 48,
    cy: M + 20,
    w: 96,
    h: 40,
  }
  const claude: Box = { label: 'Claude', kind: 'claude', cx: M + 65, cy: M + 100, w: 130, h: 46, isActive: v.mainRunning }
  const trunkTop = you.cy + you.h / 2
  const trunkEnd = claude.cy - claude.h / 2
  const branchTop = claude.cy + claude.h / 2

  const out: Out = { lines: [], boxes: [], right: M + 130, bottom: branchTop }
  const nowS = now / 1000
  const rows = rowsOf(treeOf(v), now, { n: 0 })
  layout(rows, TRUNK, branchTop, branchTop + 50, out, nowS)

  // User -> Claude: the sum of the branches below, as their lines show them.
  const timed = rows.filter(r => !r.noUsage) // tasks keep their time on their own line
  const totalMs = timed.reduce((a, r) => a + r.ms, 0)
  const liveN = timed.reduce((a, r) => a + r.liveN, 0)
  const liveSum = timed.reduce((a, r) => a + r.liveSum, 0)
  const growth = figureText(figure, {
    usd: sumUsd(rows),
    tok: rows.reduce((a, r) => a + r.tok, 0),
    ms: totalMs + (liveN > 0 ? liveElapsed(0, liveN, liveSum, now) : 0),
  })
  const trunkLabels =
    figure === 'time' && liveN > 0 && liveLeft > 0 ? liveLabels(totalMs, liveN, liveSum, now, LIVE_SECONDS) : undefined
  const gw = (trunkLabels ? trunkLabels[trunkLabels.length - 1]!.length : growth.length) * 12 + 12
  const width = Math.max(MIN_W, out.right + M)
  const height = out.bottom + M

  return (
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width * FIT}" height="${height * FIT}" preserveAspectRatio="xMinYMin meet">` +
    `<defs><style>.t{fill:#cfd8dc;font:${FONT}px sans-serif;text-anchor:middle;dominant-baseline:central}</style><filter id="glow" x="-30%" y="-60%" width="160%" height="220%"><feGaussianBlur stdDeviation="4"/></filter><filter id="dotglow" x="-100%" y="-200%" width="300%" height="500%"><feGaussianBlur stdDeviation="3"/></filter><filter id="lineglow" filterUnits="userSpaceOnUse" x="-20" y="-20" width="${width + 40}" height="${height + 40}"><feGaussianBlur stdDeviation="3"/></filter></defs>` +
    line(`M${TRUNK},${trunkTop} V${trunkEnd}`, trunkEnd - trunkTop, KIND.claude.fill, v.mainRunning, nowS, KIND.claude.light, v.mainTps) +
    (trunkLabels
      ? livePill(TRUNK + 14 + gw / 2, (trunkTop + trunkEnd) / 2, trunkLabels, gw)
      : pill(TRUNK + 14 + gw / 2, (trunkTop + trunkEnd) / 2, growth, gw)) +
    byIntensity(out.lines).map(l => l.svg).join('') +
    node(you) +
    node(claude) +
    out.boxes.join('') +
    // Grey edges at the bottom and right of the drawing: they show where the
    // drawing ends, so it is visible what limits its size in the pane.
    `<line x1="0" y1="${height - 1}" x2="${width}" y2="${height - 1}" stroke="#000" stroke-opacity="0.1" stroke-width="2"/>` +
    `<line x1="${width - 1}" y1="0" x2="${width - 1}" y2="${height}" stroke="#000" stroke-opacity="0.1" stroke-width="2"/>` +
    `</svg>`
  )
}

// The pane refuses an Svg whose source is over 131072 characters, and then shows
// "nothing to show yet" instead of the whole panel. Active lines (two lanes of
// dots each) are the bulk of a big tree. Idle sessions sink to the bottom without
// children (10+ of them fold into one tile); if that is too big, all idle ones
// fold; then no moving dots and ticking times anywhere; last, fewer nested levels.
const SVG_LIMIT = 126000 // a margin under the pane's 131072
const fitted = (v: FlowView, now: number, figure: Figure): string => {
  try {
    isCalm = false
    isFolding = false
    depthLimit = MAX_DEPTH
    let source = draw(v, now, figure)
    if (source.length <= SVG_LIMIT) return source
    isFolding = true
    source = draw(v, now, figure)
    if (source.length <= SVG_LIMIT) return source
    isCalm = true
    for (let depth = MAX_DEPTH; depth >= 0; depth -= 1) {
      depthLimit = depth
      source = draw(v, now, figure)
      if (source.length <= SVG_LIMIT) break
    }

    return source
  } finally {
    isCalm = false
    isFolding = false
    depthLimit = MAX_DEPTH
  }
}

// ----------------------------------------------------------------- events

type Target = { key: string; label: string; kind: NodeKind }

const sideTarget: Target = { key: 'side:fork', label: 'Side', kind: 'side' }

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


// When each running turn began, by agent id ('' = the main loop), for its pace.
const turnStartedAt = new Map<string, number>()
// When a command's fork (/btw ...) started, by agent id: its run is one timed span.
const spawnedAt = new Map<string, number>()
// Background agents still working, by agent id. They survive a new prompt: the
// prompt wipes the view, but not these. The periodic poll reads the engine's agent
// list (`$.agent.list()`) and ends the ones it reports finished (see `syncAgents`).
const liveAgents = new Map<string, { key: string; spawnAt: number }>()
// Background tasks seen starting in this process. The view outlives a reload, this does
// not: a task node that is running in the view but is not here ended while nobody listened.
const liveTasks = new Map<string, number>() // task id -> when it was seen starting
// Whether the log already holds a sample of a task notification (one line each, once).
let hasLoggedEnd = false
let hasLoggedOther = false
// Re-check of background tasks (see the <recheck> block): the timer exists only while
// nothing but background tasks runs.
let recheckTimer: { cancel: () => void } | undefined
let recheckBook: ProbeBook = { failures: 0 }
let isRechecking = false
let isRecheckEnabled: boolean | undefined
const loggedProbes = new Set<string>() // outcome kinds already written to the debug log

const freshTokens = (u: Usage | undefined): number =>
  u ? (u.input_tokens ?? 0) + (u.output_tokens ?? 0) + (u.cache_creation_input_tokens ?? 0) : 0

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

let startedAt = 0
let lastPublished = ''
const HEAD_CHARS = 400 // how much of its first prompt a session shares
const SNIPPET_CHARS = 60 // how much of a brief identifies the session it started
type Spawn = { at: number; snippet: string }
const norm = (s: string) => s.replace(/\s+/g, ' ').trim()

const treeOf = (v: FlowView): SubTree => ({
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

async function folderOf($: EngineInterface): Promise<string> {
  const home = await $.env.get('SOCRATEX_HOME')
  if (!selfId) selfId = await $.session.id()
  if (!startedAt) startedAt = await $.clock.now()

  return home ? `${home.replace(/\\/g, '/')}/local/flow` : ''
}

async function publish($: EngineInterface, v: FlowView, ended = false): Promise<void> {
  const dir = await folderOf($)
  if (!dir || (isEmpty(v) && !ended)) return // never overwrite a saved view with an empty one
  try {
    // Only a real change rewrites the file: its updatedAt must mean "this session
    // did something", or no session would ever look stale (the poll flushes often).
    const body = JSON.stringify({ tree: treeOf(v), view: v, ended })
    if (body === lastPublished) return
    lastPublished = body
    const at = await $.clock.now()
    const text = JSON.stringify({ id: selfId, startedAt, updatedAt: at, tree: treeOf(v), view: v, ended })
    await $.fs.write(`${dir}/${selfId}.json`, text)
  } catch {
    // the shared folder is optional: without it there are simply no session tiles
  }
}

type Shared = { id: string; startedAt: number; updatedAt: number; tree: SubTree; view?: FlowView; ended?: boolean }

async function loadShared($: EngineInterface, dir: string, id: string): Promise<Shared | undefined> {
  try {
    return JSON.parse(String(await $.fs.read(`${dir}/${id}.json`))) as Shared
  } catch {
    return undefined
  }
}

// After a restart the pane would start empty: take the last saved view instead
// (this session's own file when it was resumed, else the newest of any session).
// Not tied to session.start, which a resumed session may never raise: it runs
// when the pane draws or a write is about to happen, whichever comes first.
let saved: FlowView | null | undefined

const isEmpty = (v: FlowView): boolean =>
  v.nodes.length === 0 && v.subs.length === 0 && v.wTotal === 0 && v.limitPct < 0

async function restoredFor($: EngineInterface, v: FlowView): Promise<FlowView> {
  if (!isEmpty(v)) return v
  if (saved === undefined) {
    saved = null
    const dir = await folderOf($)
    if (dir) {
      const f = await loadShared($, dir, selfId)
      const old = f?.view
      if (old && Array.isArray(old.nodes) && Array.isArray(old.subs) && typeof old.k === 'number') {
        saved = {
          ...old,
          subs: [], // rebuilt from the sessions' own files by the next poll
          nodes: old.nodes.map(n => ({ ...n, running: 0, isBackground: false })),
          mainRunning: false,
          isWaiting: false,
          flushAt: 0,
        }
      }
    }
  }

  return saved ?? v
}

// ------------------------------------------- the desktop app's own session store
// The Claude desktop app keeps one small file per session (title, who started it,
// archived or not). Where it exists it tells exactly which sessions are ours, so
// nothing has to be guessed; elsewhere the brief matching below is the fallback.
type Entry = { name: string; kind: string; mtimeMs: number }
type Stored = {
  local: string
  cli: string // the id a mod sees as its session id
  from: string // the session that started it
  isFork: boolean // a side chat the person forked, not work we started
  isArchived: boolean
  title: string
  created: number
  mtime: number
}

const STORE_SCAN_MS = 10000
const STORE_AGE_MS = 3 * 24 * 3600 * 1000 // older session files are not looked at
const stored = new Map<string, Stored>()
let storeDirs: string[] | undefined
let lastStoreAt = 0

async function entriesOf($: EngineInterface, path: string): Promise<Entry[]> {
  try {
    return (await $.fs.list(path)) as Entry[]
  } catch {
    return []
  }
}

async function findStoreDirs($: EngineInterface): Promise<string[]> {
  const slash = (v: unknown) => String(v ?? '').replace(/\\/g, '/')
  const home =
    slash(await $.env.get('HOME')) ||
    slash(await $.env.get('USERPROFILE')) ||
    slash(await $.env.get('SOCRATEX_HOME')).replace(/\/[^/]+$/, '')
  const local = slash(await $.env.get('LOCALAPPDATA')) || `${home}/AppData/Local`
  const roaming = slash(await $.env.get('APPDATA')) || `${home}/AppData/Roaming`
  const roots = [
    ...(await entriesOf($, `${local}/Claude-Data`))
      .filter(d => d.kind === 'dir')
      .map(d => `${local}/Claude-Data/${d.name}/claude-code-sessions`),
    `${roaming}/Claude/claude-code-sessions`,
    `${home}/Library/Application Support/Claude/claude-code-sessions`,
    `${home}/.config/Claude/claude-code-sessions`,
  ]
  const dirs: string[] = []
  for (const root of roots) {
    for (const account of (await entriesOf($, root)).filter(d => d.kind === 'dir')) {
      for (const org of (await entriesOf($, `${root}/${account.name}`)).filter(d => d.kind === 'dir')) {
        dirs.push(`${root}/${account.name}/${org.name}`)
      }
    }
  }

  return dirs
}

// Reads new session files once; a file of ours or one we started is read again when it changes.
async function scanStore($: EngineInterface): Promise<void> {
  const now = await $.clock.now()
  if (now - lastStoreAt < STORE_SCAN_MS) return
  lastStoreAt = now
  try {
    if (!storeDirs) storeDirs = await findStoreDirs($)
    const mine = [...stored.values()].find(s => s.cli === selfId)?.local
    for (const dir of storeDirs) {
      for (const e of await entriesOf($, dir)) {
        if (e.kind !== 'file' || !/^local_.*\.json$/.test(e.name) || now - e.mtimeMs > STORE_AGE_MS) continue
        const path = `${dir}/${e.name}`
        const old = stored.get(path)
        const isWatched = !!old && (old.cli === selfId || !old.cli || (!!mine && old.from === mine))
        if (old && !(isWatched && old.mtime !== e.mtimeMs)) continue
        try {
          const j = JSON.parse(String(await $.fs.read(path))) as Record<string, any>
          stored.set(path, {
            local: e.name.replace(/\.json$/, ''),
            cli: String(j.cliSessionId ?? ''),
            from: String(j.spawnedFrom?.sessionId ?? ''),
            isFork: j.spawnedFrom?.userFork === true,
            isArchived: j.isArchived === true,
            title: String(j.title ?? ''),
            created: Number(j.createdAt ?? 0),
            mtime: e.mtimeMs,
          })
        } catch {
          // half-written or unreadable: tried again on the next change
        }
      }
    }
  } catch {
    storeDirs = []
  }
}

let lastTitleAt = 0

// The title the sidebar shows is kept in the session's transcript as the last
// "customTitle" (or "aiTitle") line; read at most once a minute.
async function refreshTitle($: EngineInterface): Promise<void> {
  const now = await $.clock.now()
  if (now - lastTitleAt < 60000) return
  lastTitleAt = now
  try {
    const { transcriptPath } = await $.session.info()
    if (!transcriptPath) return
    const text = String(await $.fs.read(transcriptPath))
    const hits = [...text.matchAll(/"(?:customTitle|aiTitle)":("(?:[^"\\]|\\.)*")/g)]
    const last = hits[hits.length - 1]
    if (!last) return
    const title = String(JSON.parse(last[1] as string)).slice(0, 80)
    change($, v => (v.title === title ? v : { ...v, title }))
  } catch {
    // no readable transcript: the tooltip just shows "Session N"
  }
}

// Debugging aid: logs (only when it changes) whether the app store knows this session
// and which children it lists, to find why children vanish from the tree.
let lastTrace = ''

async function traceStore($: EngineInterface, mine: Stored | undefined): Promise<void> {
  const kids = mine ? [...stored.values()].filter(s => s.from === mine.local) : []
  const line =
    `store self=${selfId.slice(0, 8)} found=${!!mine} entries=${stored.size} ` +
    `kids=[${kids.map(k => `${k.local.slice(6, 14)}:cli=${k.cli.slice(0, 8)}:arch=${k.isArchived}:fork=${k.isFork}`).join(',')}] ` +
    `cliOfSelfCandidates=[${[...stored.values()].filter(s => s.local === mine?.local || s.cli === selfId).map(s => s.cli.slice(0, 8)).join(',')}]`
  if (line === lastTrace) return
  lastTrace = line
  await dbg($, line)
}

async function poll($: EngineInterface): Promise<void> {
  await syncAgents($)
  await dropStaleTasks($)
  const dir = await folderOf($)
  if (!dir) return
  await scanStore($)
  void armLiveRefresh($)
  const mine = [...stored.values()].find(s => s.cli === selfId)
  await traceStore($, mine)
  if (!mine) await refreshTitle($)
  const cur = held ?? (await read($, view))
  const spawns = cur.spawns ?? []
  const now = await $.clock.now()

  if (mine) {
    // The app says exactly which sessions we started: draw those, nothing else.
    const kids = [...stored.values()]
      .filter(s => s.from === mine.local && !s.isFork && !s.isArchived && s.cli !== '' && s.cli !== selfId)
      .sort((a, b) => a.created - b.created)
    const subs: SubTree[] = []
    for (const k of kids) {
      const f = await loadShared($, dir, k.cli)
      const tree: SubTree = f?.tree ?? {
        id: k.cli,
        nodes: [],
        subs: [],
        mainRunning: false,
        isWaiting: false,
        wTotal: 0,
        k: 0,
      }
      subs.push({ ...tree, id: k.cli, title: k.title || tree.title })
    }
    change($, v => ({ ...v, title: mine.title || v.title, sessionIds: kids.map(k => k.cli), subs }))

    return
  }

  // Ours only when its first prompt is the brief of one of our start_session calls.
  const isOurs = (f: Shared | undefined): boolean => {
    const head = f?.view?.head
    return !!head && spawns.some(s => s.snippet !== '' && head.includes(s.snippet))
  }
  const ids: string[] = []
  for (const id of cur.sessionIds.filter(id => id !== 'last' && id !== selfId)) {
    if (isOurs(await loadShared($, dir, id))) ids.push(id) // drops ids attached by older, looser rules
  }

  // A file born soon after one of our start_session calls, with that brief as its head.
  if (spawns.some(s => now - s.at < ATTACH_WINDOW_MS * 5)) {
    let names: Array<{ name: string }> = []
    try {
      names = await $.fs.list(dir)
    } catch {
      names = []
    }
    for (const n of names) {
      const id = n.name.replace(/\.json$/, '')
      if (!n.name.endsWith('.json') || id === 'last' || id === selfId || ids.includes(id)) continue
      const f = await loadShared($, dir, id)
      const born = f?.startedAt ?? 0
      if (f && isOurs(f) && spawns.some(s => born >= s.at - 2000 && born <= s.at + ATTACH_WINDOW_MS)) {
        ids.push(id)
      }
    }
  }

  const subs: SubTree[] = []
  const kept: string[] = []
  for (const id of ids) {
    const f = await loadShared($, dir, id)
    // Gone when it said it ended (archived, closed) or has not been heard from for long.
    if (f && !f.ended && (f.tree.mainRunning || now - f.updatedAt < STALE_MS)) {
      subs.push({ ...f.tree, id })
      kept.push(id)
    }
  }
  change($, v => ({ ...v, sessionIds: kept, subs }))
}

// Debugging aid: the last lines of what redrew the pane and why, kept in
// $SOCRATEX_HOME/state/flow-debug/<session>.log (outside git; the mod cannot delete files,
// so old logs are rotated by `python modules/tools/scripts/state.py rotate flow-debug`).
let dbgLines: string[] = []

async function dbg($: EngineInterface, msg: string): Promise<void> {
  const at = await $.clock.now()
  dbgLines = [...dbgLines, `${new Date(at).toISOString().slice(11, 23)} ${msg}`].slice(-80)
  const dir = await folderOf($)
  if (!dir) return
  try {
    await $.fs.write(`${dir.replace(/\/local\/flow$/, '')}/state/flow-debug/${selfId.slice(0, 8)}.log`, dbgLines.join('\n'))
  } catch {
    // a debugging aid only
  }
}

const firstDiff = (a: string, b: string): string => {
  let i = 0
  while (i < a.length && i < b.length && a[i] === b[i]) i += 1

  return `at ${i}: [${a.slice(Math.max(0, i - 30), i + 50)}] vs [${b.slice(Math.max(0, i - 30), i + 50)}]`
}

let lastSource = ''

// A running time ticks by itself for LIVE_SECONDS after it was drawn. While
// anything runs, one redraw per LIVE_REFRESH_MS keeps the labels coming, even
// when nothing else changes; it is the only timer the panel keeps.
const anyRunning = (nodes: FlowNode[], subs: SubTree[]): boolean =>
  nodes.some(n => n.running > 0) || subs.some(s => anyRunning(s.nodes, s.subs))
let isRefreshArmed = false

async function armLiveRefresh($: EngineInterface): Promise<void> {
  if (isRefreshArmed) return
  isRefreshArmed = true
  $.clock.after(LIVE_REFRESH_MS, async () => {
    isRefreshArmed = false
    const cur = held ?? (await read($, view))
    if (!anyRunning(cur.nodes, cur.subs)) return
    held = undefined
    await update($, view, () => ({ ...cur, tick: cur.tick + 1 }))
    await armLiveRefresh($)
  })
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
    const cur = await restoredFor($, held ?? (await read($, view)))
    const next = batch.reduce((acc, f) => f(acc), cur)
    const before = draw(cur, at)
    const after = draw(next, at)
    void syncRecheck($, next)
    if (after === before) {
      held = next
      await publish($, next)

      return
    }
    await dbg($, `flush REDRAW ${firstDiff(before, after)}`)
    held = undefined
    await update($, view, () => next)
    await publish($, next)
  })
}

// Arms the 60 s re-check while the only live things are background tasks, and drops it
// the moment other work starts, no task remains, or the tool proved useless. Reads the
// state it is given; touches no view, so it can never redraw anything by itself.
async function syncRecheck($: EngineInterface, v: FlowView): Promise<void> {
  try {
    if (isRecheckEnabled === undefined) isRecheckEnabled = (await $.env.get('FLOW_TASK_RECHECK')) !== '0'
    const want = shouldRecheck({
      isEnabled: isRecheckEnabled,
      failures: recheckBook.failures,
      mainRunning: v.mainRunning,
      liveAgents: liveAgents.size,
      nodes: v.nodes,
    })
    if (isInitialCheckDue(want, !!recheckTimer)) {
      recheckTimer = $.clock.every(RECHECK_MS, () => {
        void recheckTasks($)
      })
      // No task shown means no call: recheckTasks probes only displayed running tasks.
      void recheckTasks($, v)
    } else if (!want && recheckTimer) {
      recheckTimer.cancel()
      recheckTimer = undefined
    }
  } catch {
    // a best-effort aid
  }
}

// One tick: ask GetTask about each task, close the ones it lists as finished. Any doubt
// leaves the task as it is.
async function recheckTasks($: EngineInterface, shown?: FlowView): Promise<void> {
  if (isRechecking) return
  isRechecking = true
  try {
    const cur = shown ?? held ?? (await read($, view))
    const now = await $.clock.now()
    const ids = tasksToProbe(cur.nodes, liveTasks, now)
    for (const id of ids) {
      if (!recheckTimer) break // other work started meanwhile
      let probe: TaskProbe
      let raw = ''
      try {
        // Raised by the mod itself: this plugin's own tool.call hook does not see it.
        const ran = await $.tool.call({ tool: 'GetTask', taskId: id } as Parameters<typeof $.tool.call>[0])
        probe = probeOfResult(ran)
        raw = JSON.stringify(ran) ?? ''
      } catch (err) {
        probe = probeOfError(err)
        raw = `threw ${err instanceof Error ? err.message : String(err)}`
      }
      if (loggedProbes.size === 0) await dbg($, `recheck first call GetTask(${id}) raw ${JSON.stringify(raw.slice(0, 600))}`)
      if (!loggedProbes.has(probe.kind)) {
        loggedProbes.add(probe.kind)
        await dbg($, `recheck outcome ${probe.kind} for ${id}: ${JSON.stringify(raw.slice(0, 300))}`)
      }
      const decided = decideProbe(probe, recheckBook)
      recheckBook = decided.book
      if (decided.close) await endTask($, id, decided.close)
      if (isRecheckOff(recheckBook.failures)) {
        await dbg($, `recheck off: ${recheckBook.failures} useless GetTask answers in a row`)
        break
      }
    }
    isRechecking = false // lets a re-armed timer run its first check at once
    await syncRecheck($, cur)
  } catch {
    // a best-effort aid
  } finally {
    isRechecking = false
  }
}

// A background agent is over: its branch stops running (grey ring off) and the
// time since its start is booked.
async function endAgent($: EngineInterface, id: string): Promise<void> {
  const cur = liveAgents.get(id)
  if (!cur) return
  liveAgents.delete(id)
  const end = await $.clock.now()
  await change($, v => ({
    ...v,
    nodes: v.nodes.map(n =>
      n.key === cur.key
        ? {
            ...n,
            at: end,
            running: Math.max(0, n.running - 1),
            startSum: n.running - 1 > 0 ? (n.startSum ?? 0) - cur.spawnAt : 0,
            isBackground: n.running - 1 > 0 ? n.isBackground : false,
            ms: (n.ms ?? 0) + (end - cur.spawnAt),
          }
        : n,
    ),
  }))
}

// The poll's look at the engine's agent list: a background agent that finished (or
// that the engine has dropped) ends here. Replaces a guess from idle time.
async function syncAgents($: EngineInterface): Promise<void> {
  if (liveAgents.size === 0) return
  try {
    const list = await $.agent.list()
    const now = await $.clock.now()
    for (const [id, a] of [...liveAgents]) {
      if (isAgentDone(list.find(x => x.id === id)?.status, now - a.spawnAt)) await endAgent($, id)
    }
  } catch {
    // no agent list: the agents stay as they are until it can be read
  }
}

// A background task is over (notification, TaskStop, Monitor timeout): the block
// stops running and the time it ran is booked. Idempotent.
async function endTask($: EngineInterface, id: string, status: string): Promise<void> {
  liveTasks.delete(id)
  const end = await $.clock.now()
  await change($, v => ({
    ...v,
    nodes: v.nodes.map(n =>
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
  }))
}

// A task node still running in the stored view that this process never saw start ended
// while the mod was not listening (restart, kill): close it. Tasks seen live keep running
// without a time limit.
async function dropStaleTasks($: EngineInterface): Promise<void> {
  const cur = held ?? (await read($, view))
  const isKnown = (id: string): boolean => liveTasks.has(id)
  if (!cur.nodes.some(n => isStaleTask(n, isKnown))) return
  await change($, v => ({ ...v, nodes: closeStaleTasks(v.nodes, isKnown) }))
}

// The engine's message that a background task ended arrives as a prompt flagged
// as a task notification. The first of each kind is written to the debug log
// (once), so its real shape can be compared with what /tasks shows.
async function onTaskNotification($: EngineInterface, text: string): Promise<void> {
  const parsed = parseTaskEnd(text)
  const sample = (): string => `notification ${JSON.stringify(squash(text).slice(0, 600))}`
  if (parsed?.isEnded && !hasLoggedEnd) {
    hasLoggedEnd = true
    await dbg($, `task end ${sample()} -> id=${parsed.id} status=${parsed.status}`)
  } else if (!parsed?.isEnded && !hasLoggedOther) {
    hasLoggedOther = true
    await dbg($, `task notification without end ${sample()}`)
  }
  if (!parsed?.isEnded) return
  await endTask($, parsed.id, parsed.status)
  await endAgent($, parsed.id)
}

export const register: Register = on => {
  // Dots are pinned to the wall clock, so a redraw does not restart them; still
  // there is no steady timer: each event
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
    const { rateLimits } = await $.session.usage()
    const win = rateLimits.find(r => r.kind === 'five_hour')
    await change($, v => applyLimit(v, win))
    $.clock.every(SYNC_MS, () => poll($))

    return next(e)
  })

  // Every prompt brings the panel back if it was closed (unless switched off).
  on('prompt.submit', async ($, e, next) => {
    // A background task's notification is not the owner's prompt: it must neither
    // clear the panel nor restart the prompt's cost. It only ends the task it names.
    if (e.origin?.kind === 'task-notification') {
      await onTaskNotification($, e.text)

      return next(e)
    }
    // Open only when it is not up: a repeated open re-seats the pane.
    if ((await $.env.get('FLOW_PANEL')) !== '0') {
      const isUp = (await $.ui.panes()).some(pane => pane.id === PANE)
      if (!isUp) void $.ui.open({ id: PANE, title: 'Flow' })
    }
    // The session's first prompt (the brief, for a started session) is how its
    // parent recognises it.
    const head = e.command ? '' : norm(e.text).slice(0, HEAD_CHARS)
    // A new prompt starts a fresh view: only segments used since then show.
    const usdNow = (await $.session.usage()).cost?.usd ?? 0
    await change($, v => ({
      ...v,
      // Background agents and tasks that still work stay (their branch, running, grey).
      nodes: v.nodes.filter(n => n.running > 0 && ((!!n.taskId && liveTasks.has(n.taskId)) || [...liveAgents.values()].some(a => a.key === n.key))),
      agentNode: Object.fromEntries(Object.entries(v.agentNode).filter(([id]) => liveAgents.has(id))),
      head: v.head || head || undefined,
      promptUsd: usdNow,
      lastUsd: usdNow,
      baseUsd: v.baseUsd ?? usdNow, // the ledger before this mod saw any turn
    }))

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
    await publish($, held ?? (await read($, view)), true)

    return next(e)
  })

  // The one place the engine lists its background tasks: the Stop event carries them.
  // Close the tasks this process follows that the list no longer holds (or ends).
  on('classic.Stop', async ($, e, next) => {
    try {
      const rows = (e as { background_tasks?: TaskRow[] }).background_tasks
      const now = await $.clock.now()
      for (const id of goneTasks(liveTasks, rows, now)) await endTask($, id, 'completed')
    } catch {
      // no list: the tasks stay as they are
    }

    return next(e)
  })

  on('turn.start', async ($, e, next) => {
    const startedAt = await $.clock.now()
    turnStartedAt.set(e.agentId ?? '', startedAt)
    if (e.agentId === undefined) {
      await change($, v => ({ ...v, mainRunning: true, isWaiting: false }))
    } else {
      const live = liveAgents.get(e.agentId)
      if (live) {
        void armLiveRefresh($)
        await change($, v => ({ ...v, nodes: v.nodes.map(n => (n.key === live.key ? { ...n, at: startedAt } : n)) }))
      }
    }

    return next(e)
  })

  // A turn's exact usage: it counts toward the calibration, and a sub-agent's
  // turn is also charged to that agent's own path.
  on('turn.complete', async ($, e, next) => {
    const cost = weigh(e.usage)
    // Pace of this turn: fresh tokens (not cache reads) over its wall time.
    const began = turnStartedAt.get(e.agentId ?? '')
    turnStartedAt.delete(e.agentId ?? '')
    const tps = began === undefined ? undefined : paceOf(freshTokens(e.usage), (await $.clock.now()) - began)
    // The engine's own ledger: what this turn added is charged to its agent's path.
    const usd = (await $.session.usage()).cost?.usd ?? 0
    const endedAt = await $.clock.now()
    const side = e.agentId === undefined ? undefined : spawnedAt.get(e.agentId)
    if (e.agentId !== undefined) spawnedAt.delete(e.agentId)
    await change($, v => {
      const key = e.agentId === undefined ? undefined : v.agentNode[e.agentId]
      const delta = Math.max(0, usd - (v.lastUsd ?? usd))
      const moved: FlowView = {
        ...v,
        wTotal: v.wTotal + cost,
        allW: (v.allW ?? 0) + cost,
        lastUsd: usd,
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
      const isSide = isSideFork(e)
      if (isSide) {
        spawnedAt.set(id, now)
        void armLiveRefresh($)
      }
      const target = isSide ? sideTarget : agentTarget(e.subagentType)
      // A background agent's tool call returns at once, so the spawn keeps it running.
      // The spawn event says outright whether it is one (a teammate is not).
      const isBg = !isSide && e.background === true && !e.isTeammate
      if (isBg) {
        liveAgents.set(id, { key: target.key, spawnAt: now })
        void armLiveRefresh($)
      }
      const marks = isSide || isBg
      await change($, v => ({
        ...v,
        agentNode: { ...v.agentNode, [id]: target.key },
        // A command's fork has no tool call to mark it running, so the spawn does.
        nodes: touch(v.nodes, target, now, n => ({
          ...n,
          at: now,
          running: n.running + (marks ? 1 : 0),
          startSum: (n.startSum ?? 0) + (marks ? now : 0),
          isBackground: marks || n.isBackground,
        })),
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
    // A session we start gets a brief: remember its start, so the child can be
    // recognised by that brief later (and no other session is taken for it).
    const spawn: Spawn[] =
      /start_session|hand_off_to_session/.test(String(e.tool)) && typeof args.prompt === 'string'
        ? [{ at: now, snippet: norm(args.prompt).slice(0, SNIPPET_CHARS) }]
        : []
    void armLiveRefresh($)
    await change($, v => ({
      ...v,
      spawns: [...(v.spawns ?? []), ...spawn].slice(-20),
      nodes: touch(v.nodes, c, now, n => ({
        ...n,
        at: now,
        running: n.running + 1,
        startSum: (n.startSum ?? 0) + now,
        isBackground: isBackground || n.isBackground,
      })),
    }))

    let failed = false
    let resultTokens = 0
    let taskId: string | undefined
    let monitorMs = 0
    const requestTokens = tokensOf(args)
    try {
      const ran = await next(e)
      resultTokens = tokensOf(ran)
      // A command that went to the background, or a Monitor, stays as a running block.
      taskId = taskIdOf(String(e.tool), ran)
      monitorMs = e.tool === 'Monitor' ? monitorTimeoutMs(ran) : 0
      if (e.tool === 'TaskStop') {
        const stopped = stoppedTaskOf(args, ran)
        if (stopped) void endTask($, stopped, 'killed')
      }

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
                startSum: n.running - 1 > 0 ? (n.startSum ?? 0) - now : 0,
                isBackground: n.running - 1 > 0 ? n.isBackground : false,
                errorAt: failed ? end : n.errorAt,
                w: n.w + resultTokens * RESULT_WEIGHT,
                calls: (n.calls ?? 0) + 1,
                tok: (n.tok ?? 0) + resultTokens + requestTokens,
                ms: (n.ms ?? 0) + (end - now),
                tps: paceOf(resultTokens, end - now) ?? n.tps,
                tpsIn: paceOf(requestTokens, end - now) ?? n.tpsIn,
              }
            : n,
        ),
      }))
      if (taskId && !failed) {
        const id = taskId
        liveTasks.set(id, end)
        const task: Target = { key: `task:${id}`, label: taskNameOf(String(e.tool), args), kind: 'tool' }
        await change($, v =>
          v.nodes.some(n => n.taskId === id)
            ? v
            : {
                ...v,
                nodes: touch(v.nodes, task, end, n => ({
                  ...n,
                  at: end,
                  taskId: id,
                  taskName: task.label,
                  hasUsage: false,
                  running: 1,
                  startSum: now,
                  isBackground: true,
                  calls: 1,
                })),
              },
        )
        // A finite Monitor ends at its deadline; the engine says so too, this is a backstop.
        if (monitorMs > 0) $.clock.after(monitorMs + 5000, () => endTask($, id, 'timeout'))
      }
    }
  })

  // A notification that reaches a running turn does not always raise `prompt.submit`, and
  // the Stop event can be skipped by an earlier plugin: the transcript row is the one place
  // the end is always drawn. The row names the task and how it ended; the end is idempotent.
  on('ui.render', { component: 'UserMessage' }, async ($, e, next) => {
    try {
      const ended = endedTaskOfRow(e)
      if (ended && (liveTasks.has(ended.id) || liveAgents.has(ended.id))) {
        await endTask($, ended.id, ended.status)
        await endAgent($, ended.id)
      }
    } catch {
      // drawing the row must never fail because of this
    }

    return next(e)
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text, Svg, Button } = $.ui.resolve(e)
    await folderOf($) // makes sure the session id is known before drawing
    const v = await restoredFor($, await read($, view))
    void syncRecheck($, v) // the panel loaded with tasks still shown: check at once
    const now = await $.clock.now()
    // The picture must never depend on the toggle: if its value cannot be read, show cost.
    let figure: Figure = 'cost'
    try {
      figure = (await read($, figureAtom)) ?? 'cost'
    } catch {
      figure = 'cost'
    }
    const source = fitted(v, now, figure)
    await dbg($, `render ${source === lastSource ? 'same picture' : `new picture ${firstDiff(lastSource, source)}`}`)
    lastSource = source
    // Without an explicit size the pane seems to cap the drawing's height and
    // shrink a taller one, so state the drawing's own size.
    const size = /width="([\d.]+)" height="([\d.]+)"/.exec(source)

    return (
      <Box flexDirection="column" alignItems="flex-start" width="100%">
        {Button ? (
          // Centred over the drawing, a gap below it, no background of its own.
          <Box width="100%" justifyContent="center" marginBottom="md">
            <Box borderStyle="round" paddingX="sm" gap="md">
              {FIGURES.map(f => (
                <Button
                  key={`figure-${f}`}
                  label={FIGURE_ICON[f]}
                  // `plain` would draw both states alike, so the lit one is the primary button.
                  variant={f === figure ? 'primary' : 'secondary'}
                  dimColor={f !== figure}
                  onPress={() => {
                    void update($, figureAtom, () => f)
                  }}
                />
              ))}
            </Box>
          </Box>
        ) : null}
        {Svg ? (
          <Svg
            source={source}
            width={size ? Number(size[1]) : undefined}
            height={size ? Number(size[2]) : undefined}
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
