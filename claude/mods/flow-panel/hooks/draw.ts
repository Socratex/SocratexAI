// DRAW: turns a FlowView into one SVG string (the pane's picture). A pure function of the view,
// the clock and the chosen figure: it decides nothing about task or session status (it asks
// `statusOf`, `isShownNode` and `isSessionIdle` in rules.ts) and changes no state.
// The module variables below are settings of one drawing pass, set by `draw` / `fitted`.
import type { Figure, FlowNode, FlowView, SubTree } from '../types'
import { byIntensity, esc, figureText, liveElapsed, liveLabels, mergeCheap, tierOf, TIERS } from './format'
import type { Ring } from './model'
import { KIND, palette, STATE, type Kind } from './palette'
import { isSessionIdle, isShownNode, statusOf, treeOf } from './rules'

// Tunables
const FONT = 20 // label size in CSS px (the SVG is drawn 1:1)
// The box takes the drawing's own width up to the pane and a wider drawing is
// shrunk to it, so FIT must stay 1 (3 made everything three times smaller). A drawing declared FIT
// times larger than its viewBox is stretched to the pane width (scaled up or down).
const FIT = 1
const MIN_W = 300
const RADIUS = 10
const LABEL_CHARS = 8

type Box = {
  label: string
  full?: string // the whole name, shown as a tooltip when label is cut
  kind: Kind
  cx: number
  cy: number
  w: number
  h: number
  ring?: Ring
  isActive?: boolean // working now: a lighter border of its own colour
  shade?: number // the session's colour shift (index into SHADES)
  led?: boolean // a small blinking grey status LED in the top-right corner (work with no usage data to show as dots)
}

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
  ring?: Ring
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
let liveLeft = LIVE_MAX

// The session this copy of the mod runs in: the root of every tree it draws (set by `draw`).
let rootId = ''

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

const rowsOf = (s: Src, now: number, count: { n: number }, depth = 0, path: string[] = [rootId], shade = 0): Row[] =>
  groupIdle([
  // A background task (/tasks, dark blue) is drawn only while it runs; an idle one is hidden.
  ...mergeCheap(s.nodes.filter(isShownNode).map((nd): Row => {
    const { noUsage, isRunning, ring, isActive, led } = statusOf(nd, s.mainRunning, now)
    const usd = noUsage ? undefined : nodeUsd(nd, s.perW)

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
      isActive,
      tps: nd.tps ?? s.tps,
      tpsIn: nd.tpsIn,
      shade,
      noUsage,
      led,
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
    const isIdle = isSessionIdle(sub)
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

export const draw = (v: FlowView, now: number, figure: Figure = 'cost', selfId = ''): string => {
  shownFigure = figure
  rootId = selfId
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
  const rows = rowsOf(treeOf(v, selfId), now, { n: 0 })
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
export const SVG_LIMIT = 126000 // a margin under the pane's 131072
export const fitted = (v: FlowView, now: number, figure: Figure, selfId = ''): string => {
  try {
    isCalm = false
    isFolding = false
    depthLimit = MAX_DEPTH
    let source = draw(v, now, figure, selfId)
    if (source.length <= SVG_LIMIT) return source
    isFolding = true
    source = draw(v, now, figure, selfId)
    if (source.length <= SVG_LIMIT) return source
    isCalm = true
    for (let depth = MAX_DEPTH; depth >= 0; depth -= 1) {
      depthLimit = depth
      source = draw(v, now, figure, selfId)
      if (source.length <= SVG_LIMIT) break
    }

    return source
  } finally {
    isCalm = false
    isFolding = false
    depthLimit = MAX_DEPTH
  }
}
