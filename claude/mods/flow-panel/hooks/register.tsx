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
const MAX_NODES = 4
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
}
const STATE = {
  waiting: '#ff9800', // waiting for the user
  error: '#e53935',
  background: '#43a047', // background work
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
  shape: 'flow-8',
})

// What the figure on every line shows. Kept apart from the view: it is a
// display choice of this person, not shared with the sessions above or below.
// The toggle: one icon per measure; the chosen one is lit, the others dim.
const FIGURE_ICON: Record<Figure, string> = { cost: '$', time: '◷', tokens: '❐' }
const FIGURE_ON = { fill: '#3b82f6', text: '#ffffff' } // the blue of the "you" box

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

// Tokens as 950, 1.2k, 34k, 1.5M (three digits at most, no trailing zero).
const fmtTokens = (n: number): string => {
  const v = Math.max(0, Number.isFinite(n) ? n : 0)
  if (v < 1000) return String(Math.round(v))
  const [d, unit] = v < 1e6 ? [v / 1e3, 'k'] : [v / 1e6, 'M']
  const s = d < 10 ? d.toFixed(1) : String(Math.round(d))

  return `${s.replace(/\.0$/, '')}${unit}`
}

// Wall time as 0.4s, 12s, 3m05s, 1h02m.
const fmtTime = (ms: number): string => {
  const v = Math.max(0, Number.isFinite(ms) ? ms : 0)
  if (v < 10000) return `${(Math.round(v / 100) / 10).toString()}s`
  const s = Math.round(v / 1000)
  if (s < 60) return `${s}s`
  if (s < 3600) return `${Math.floor(s / 60)}m${String(s % 60).padStart(2, '0')}s`

  return `${Math.floor(s / 3600)}h${String(Math.floor((s % 3600) / 60)).padStart(2, '0')}m`
}
// </tiers>

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
const line = (
  d: string,
  length: number,
  colour: string,
  isActive: boolean,
  nowS: number,
  light = colour,
  tpsUp?: number,
  tpsDown?: number,
) => {
  if (!isActive) return `<path d="${d}" fill="none" stroke="${colour}" stroke-opacity="0.3" stroke-width="2"/>`

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
  const dots =
    lane(d, TIERS[tierOf(tpsDown)]!.dots, light, 0) +
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
  const dot = b.isActive
    ? `<circle cx="${x + b.w}" cy="${y}" r="5" fill="${k.light}" stroke="#000" stroke-opacity="0.4" stroke-width="1"><animate attributeName="opacity" values="1;0.2;1" dur="1s" repeatCount="indefinite"/></circle>`
    : ''
  return (
    `<g>${tip}${glow}` +
    `<rect x="${x}" y="${y}" width="${b.w}" height="${b.h}" rx="${RADIUS}" ry="${RADIUS}" fill="${k.fill}" stroke="${ring}" stroke-width="${ringW}">${pulse}</rect>` +
    `<text x="${b.cx}" y="${b.cy}" fill="${k.text}" font-size="${FONT}" font-family="sans-serif" text-anchor="middle" dominant-baseline="central">${b.label}</text>${dot}</g>`
  )
}

const esc = (s: string) => s.replace(/[<>&"]/g, '')

// You -> Claude: how far the account's 5-hour limit has grown since the base.
// Short percent: 1 or more keeps one decimal, below 1 keeps one significant
// digit (0.054 -> 0.05, 0.245 -> 0.2); trailing zeros are dropped (18.0 -> 18).
const pct = (n: number): string => {
  if (n <= 0) return '0'
  const decimals = n >= 1 ? 1 : Math.min(20, Math.ceil(-Math.log10(n)))
  const s = n.toFixed(decimals)

  return s.includes('.') ? s.replace(/\.?0+$/, '') : s
}

// Claude -> a path: what it cost in US cents, as the engine's cost ledger prices
// it, rounded like the percent figures (see `pct`).
const usdText = (usd: number | undefined): string =>
  usd === undefined ? '...' : `${pct(usd * 100)}¢`

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
  text: string
  isActive: boolean
  tps?: number // token pace of the result coming back up: sets the dots of the up lane
  tpsIn?: number // token pace of the request going down: sets the dots of the down lane
  shade: number // the session's colour shift: the same for a session tile and everything below it
  kids: Row[]
}

// The sum of the known figures of some rows; '...' (undefined) when there are
// rows but none of them is known yet. No rows at all sum to zero.
// The text on a line for the chosen measure.
const figureText = (f: Figure, r: { usd: number | undefined; tok: number; ms: number }): string =>
  f === 'tokens' ? fmtTokens(r.tok) : f === 'time' ? fmtTime(r.ms) : usdText(r.usd)

const sumUsd = (rows: Row[]): number | undefined => {
  const known = rows.map(r => r.usd).filter((u): u is number => u !== undefined)

  return rows.length > 0 && known.length === 0 ? undefined : known.reduce((a, b) => a + b, 0)
}

type Src = Pick<SubTree, 'nodes' | 'subs' | 'mainRunning' | 'perW' | 'usd' | 'tps'>

// The measure the figures show while a picture is drawn (set by `draw`).
let shownFigure: Figure = 'cost'

// The session this copy of the mod runs in: the root of every tree it draws.
let selfId = ''

// A session's branches: its own paths first, then the sessions it started,
// each of those holding the same again. `count` numbers the sessions.
const MAX_DEPTH = 4 // a guard: never draw sessions nested deeper than this

const rowsOf = (s: Src, now: number, count: { n: number }, depth = 0, path: string[] = [selfId], shade = 0): Row[] => [
  ...s.nodes.map((nd): Row => {
    const usd = nodeUsd(nd, s.perW)
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
      usd,
      tok: nd.tok ?? 0,
      ms: nd.ms ?? 0,
      text: figureText(shownFigure, { usd, tok: nd.tok ?? 0, ms: nd.ms ?? 0 }),
      isActive: isRunning || s.mainRunning,
      tps: nd.tps ?? s.tps,
      tpsIn: nd.tpsIn,
      shade,
      kids: [],
    }
  }),
  // A session already on the path above is the same session again: skip it.
  ...(depth >= MAX_DEPTH ? [] : s.subs.filter(sub => !path.includes(sub.id))).map((sub): Row => {
    count.n += 1
    const label = `Session ${count.n}`
    const subShade = count.n // the n-th session of the drawing; 0 stays the root's own
    const kids = rowsOf(sub, now, count, depth + 1, [...path, sub.id], subShade)
    // While a session works, its own ledger figure only moves at the end of a
    // turn, so it shows the sum of its branches, which grows as they finish.
    // Once it is idle, it shows what it really spent (its own model tokens too).
    const usd = sub.mainRunning ? sumUsd(kids) : sub.usd
    const tok = kids.reduce((a, k) => a + k.tok, 0)
    const ms = kids.reduce((a, k) => a + k.ms, 0)

    return {
      label,
      full: esc(sub.title || label),
      kind: 'session' as Kind,
      w: 120,
      ring: undefined,
      usd,
      tok,
      ms,
      text: figureText(shownFigure, { usd, tok, ms }),
      isActive: sub.mainRunning,
      tps: sub.tps,
      shade: subShade,
      kids,
    }
  }),
]

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
    const pw = r.text.length * 12 + 12
    // The figure sits right of the box, so deeper levels cost little width.
    out.lines.push({
      rank: r.isActive ? Math.max(tierOf(r.tps), tierOf(r.tpsIn)) : -1, // idle lines lie below every active one
      svg: line(d, length, palette(r.kind, r.shade).fill, r.isActive, nowS, palette(r.kind, r.shade).light, r.tps, r.tpsIn) + pill(left + r.w + 6 + pw / 2, y, r.text, pw),
    })
    out.boxes.push(node({ label: r.label, full: r.full, kind: r.kind, cx: left + r.w / 2, cy: y, w: r.w, h: 40, ring: r.ring, isActive: r.isActive, shade: r.shade }))
    out.right = Math.max(out.right, left + r.w + 6 + pw)
    out.bottom = Math.max(out.bottom, y + 20)
    y = r.kids.length ? layout(r.kids, left + 12, y + 20, y + ROW, out, nowS) : y + ROW
  }

  return y
}

const draw = (v: FlowView, now: number, figure: Figure = 'cost'): string => {
  shownFigure = figure
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
  const growth = figureText(figure, {
    usd: sumUsd(rows),
    tok: rows.reduce((a, r) => a + r.tok, 0),
    ms: rows.reduce((a, r) => a + r.ms, 0),
  })
  const gw = growth.length * 12 + 12
  const width = Math.max(MIN_W, out.right + M)
  const height = out.bottom + M

  return (
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width * FIT}" height="${height * FIT}" preserveAspectRatio="xMinYMin meet">` +
    `<defs><filter id="glow" x="-30%" y="-60%" width="160%" height="220%"><feGaussianBlur stdDeviation="4"/></filter><filter id="dotglow" x="-100%" y="-200%" width="300%" height="500%"><feGaussianBlur stdDeviation="3"/></filter><filter id="lineglow" filterUnits="userSpaceOnUse" x="-20" y="-20" width="${width + 40}" height="${height + 40}"><feGaussianBlur stdDeviation="3"/></filter></defs>` +
    line(`M${TRUNK},${trunkTop} V${trunkEnd}`, trunkEnd - trunkTop, KIND.claude.fill, v.mainRunning, nowS, KIND.claude.light, v.mainTps) +
    pill(TRUNK + 14 + gw / 2, (trunkTop + trunkEnd) / 2, growth, gw) +
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
        const isWatched = !!old && (old.cli === selfId || (!!mine && old.from === mine))
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

async function poll($: EngineInterface): Promise<void> {
  const dir = await folderOf($)
  if (!dir) return
  await scanStore($)
  const mine = [...stored.values()].find(s => s.cli === selfId)
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
// $SOCRATEX_HOME/local/flow-debug-<session>.log (outside the shared folder).
let dbgLines: string[] = []

async function dbg($: EngineInterface, msg: string): Promise<void> {
  const at = await $.clock.now()
  dbgLines = [...dbgLines, `${new Date(at).toISOString().slice(11, 23)} ${msg}`].slice(-80)
  const dir = await folderOf($)
  if (!dir) return
  try {
    await $.fs.write(`${dir.replace(/\/flow$/, '')}/flow-debug-${selfId.slice(0, 8)}.log`, dbgLines.join('\n'))
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
      nodes: [],
      agentNode: {},
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

  on('turn.start', async ($, e, next) => {
    turnStartedAt.set(e.agentId ?? '', await $.clock.now())
    if (e.agentId === undefined) {
      await change($, v => ({ ...v, mainRunning: true, isWaiting: false }))
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
                    ms: (n.ms ?? 0) + (began === undefined ? 0 : endedAt - began),
                    ...(key === sideTarget.key ? { running: Math.max(0, n.running - 1), isBackground: n.running > 1, at: endedAt } : {}),
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
      const target = isSide ? sideTarget : agentTarget(e.subagentType)
      await change($, v => ({
        ...v,
        agentNode: { ...v.agentNode, [id]: target.key },
        // A command's fork has no tool call to mark it running, so the spawn does.
        nodes: touch(v.nodes, target, now, n => ({ ...n, at: now, running: n.running + (isSide ? 1 : 0), isBackground: isSide || n.isBackground })),
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
    await change($, v => ({
      ...v,
      spawns: [...(v.spawns ?? []), ...spawn].slice(-20),
      nodes: touch(v.nodes, c, now, n => ({
        ...n,
        at: now,
        running: n.running + 1,
        isBackground: isBackground || n.isBackground,
      })),
    }))

    let failed = false
    let resultTokens = 0
    const requestTokens = tokensOf(args)
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
                tok: (n.tok ?? 0) + resultTokens + requestTokens,
                ms: (n.ms ?? 0) + (end - now),
                tps: paceOf(resultTokens, end - now) ?? n.tps,
                tpsIn: paceOf(requestTokens, end - now) ?? n.tpsIn,
              }
            : n,
        ),
      }))
    }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text, Svg, Button } = $.ui.resolve(e)
    await folderOf($) // makes sure the session id is known before drawing
    const v = await restoredFor($, await read($, view))
    const now = await $.clock.now()
    // The picture must never depend on the toggle: if its value cannot be read, show cost.
    let figure: Figure = 'cost'
    try {
      figure = (await read($, figureAtom)) ?? 'cost'
    } catch {
      figure = 'cost'
    }
    const source = draw(v, now, figure)
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
                  plain
                  label={FIGURE_ICON[f]}
                  onPress={() => {
                    void update($, figureAtom, () => f)
                  }}
                >
                  {f === figure ? (
                    <Text color={FIGURE_ON.text} backgroundColor={FIGURE_ON.fill} weight="bold">{` ${FIGURE_ICON[f]} `}</Text>
                  ) : (
                    <Text dimColor>{` ${FIGURE_ICON[f]} `}</Text>
                  )}
                </Button>
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
