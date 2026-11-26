// FORMAT: how numbers become text and how cheap blocks merge. Pure functions of their arguments
// (the clock is always passed in), shared by the drawing and its tests.
import type { Figure } from '../types'
import { FIGURES } from './model'

// ---------------------------------------------------------------- intensity
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
export const TIERS = [
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
export const tierOf = (tps: number | undefined): number => {
  if (tps === undefined || !(tps > 0)) return 0
  let tier = 0
  for (let i = 0; i < TIERS.length; i += 1) if (tps >= TIERS[i]!.minTps) tier = i

  return tier
}


// Paint order of lines: SVG has no z-index, a later element lies on top. Idle
// lines go first, then active ones by rising tier, so the busiest line is on
// top. The sort is stable: equal intensity keeps the layout order.
export const byIntensity = <T extends { rank: number }>(items: T[]): T[] =>
  items
    .map((item, i) => ({ item, i }))
    .sort((a, b) => a.item.rank - b.item.rank || a.i - b.i)
    .map(x => x.item)


// The figure on a line is one of three measures; a button cycles through them.
export const nextFigure = (f: string | undefined): (typeof FIGURES)[number] =>
  FIGURES[(Math.max(0, FIGURES.indexOf(f as (typeof FIGURES)[number])) + 1) % FIGURES.length]!

// Tokens in K, then in M, always one decimal: 743 -> 0.7K, 34500 -> 34.5K, 1.5M.
export const fmtTokens = (n: number): string => {
  const v = Math.max(0, Number.isFinite(n) ? n : 0)
  if (v === 0) return '0'
  const k = Math.round(v / 100) / 10 // thousands, one decimal
  if (k < 1000) return `${k.toFixed(1)}K`

  return `${(Math.round(v / 1e5) / 10).toFixed(1)}M`
}

// Wall time in seconds and minutes only: 0.4s, 12s, 3m05s, 62m00s.
export const fmtTime = (ms: number): string => {
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
export const liveElapsed = (ms: number, running: number, startSum: number, nowMs: number): number =>
  Math.max(0, ms + running * nowMs - startSum)

export const liveLabels = (ms: number, running: number, startSum: number, nowMs: number, count: number): string[] =>
  Array.from({ length: Math.max(1, count) }, (_, k) =>
    fmtTime(Math.floor(liveElapsed(ms, running, startSum, nowMs + k * 1000) / 1000) * 1000),
  )
// You -> Claude: how far the account's 5-hour limit has grown since the base.
// Short percent: 1 or more keeps one decimal, below 1 keeps one significant
// digit (0.054 -> 0.05, 0.245 -> 0.2); trailing zeros are dropped (18.0 -> 18).
export const pct = (n: number): string => {
  if (n <= 0) return '0'
  const decimals = n >= 1 ? 1 : Math.min(20, Math.ceil(-Math.log10(n)))
  const s = n.toFixed(decimals)

  return s.includes('.') ? s.replace(/\.?0+$/, '') : s
}

// Money: cents (rounded like the percent figures) below one dollar, then dollars
// with one decimal: 0.4 -> 40¢, 1.234 -> $1.2. Cents that would round up to 100
// already show as dollars.
export const fmtMoney = (usd: number): string => {
  const cents = Math.max(0, Number.isFinite(usd) ? usd : 0) * 100
  if (cents >= 99.95) return `$${(Math.round(cents / 10) / 10).toFixed(1)}`

  return `${pct(cents)}¢`
}

// ------------------------------------------------------------- merged blocks
export const esc = (s: string) => s.replace(/[<>&"]/g, '')

// Claude -> a path: what it cost, as the engine's cost ledger prices it (see `fmtMoney`).
export const usdText = (usd: number | undefined): string => (usd === undefined ? '...' : fmtMoney(usd))

// The text on a line for the chosen measure. A path with no usage data at all
// (a background command) has no cost and no tokens, only time.
export const figureText = (
  f: 'cost' | 'time' | 'tokens',
  r: { usd: number | undefined; tok: number; ms: number; noUsage?: boolean },
): string =>
  r.noUsage && f !== 'time' ? '-' : f === 'tokens' ? fmtTokens(r.tok) : f === 'time' ? fmtTime(r.ms) : usdText(r.usd)

// Leaf blocks (no children) that cost less than this merge into one block per
// category when a category has two or more of them. The threshold is always by
// cost, whatever the toggle shows, so blocks do not jump when the unit changes.
export const CHEAP_USD = 0.01
export const MERGE_LABELS: Record<string, string> = { tool: 'Tools', mcp: 'MCP', skill: 'Skills', app: 'Apps' }

export type MergeRow = {
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
export const isCheapLeaf = (r: MergeRow): boolean =>
  r.kind in MERGE_LABELS && r.kids.length === 0 && !r.noUsage && r.usd !== undefined && r.usd < CHEAP_USD

export const mergedRow = <T extends MergeRow>(group: T[], unit: 'cost' | 'time' | 'tokens', nowMs: number): T => {
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
export const mergeCheap = <T extends MergeRow>(rows: T[], unit: 'cost' | 'time' | 'tokens', nowMs: number): T[] => {
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
