import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { FlowNode, FlowView, NodeKind } from '../types'

const PANE = 'flow-panel'

// Tunables
const FONT = 20 // label size in CSS px (the SVG is drawn 1:1)
const W = 440
const H = 300
const RADIUS = 10
const MAX_NODES = 4
const ACTIVE_MS = 3000 // a node stays "lit" this long after its last call
const ERROR_MS = 6000
const LABEL_CHARS = 8
const COST_DECIMALS = 3 // decimals of a path's cost in percent
const FLUSH_MS = 1000 // state writes are batched into one redraw per this long

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
}
const STATE = {
  waiting: '#ff9800', // waiting for the user
  error: '#e53935',
  background: '#43a047', // background work
}

type Kind = keyof typeof KIND
type Box = {
  label: string
  kind: Kind
  cx: number
  cy: number
  w: number
  h: number
  ring?: keyof typeof STATE
}

const INITIAL: FlowView = {
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
  shape: 'flow-5',
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

const curve = (a: Box, b: Box) => {
  const x1 = a.cx
  const y1 = a.cy + a.h / 2
  const x2 = b.cx
  const y2 = b.cy - b.h / 2
  const mid = (y1 + y2) / 2
  return `M${x1},${y1} C${x1},${mid} ${x2},${mid} ${x2},${y2}`
}

// Where a label sits on the curve: the middle of a vertical line, but for a
// slanted one a point near the child end, where neighbours are far enough apart.
const labelPoint = (a: Box, b: Box) => {
  const x1 = a.cx
  const y1 = a.cy + a.h / 2
  const x2 = b.cx
  const y2 = b.cy - b.h / 2
  if (Math.abs(x2 - x1) < 20) return { x: (x1 + x2) / 2, y: (y1 + y2) / 2 }
  const mid = (y1 + y2) / 2
  const t = 0.75
  const b0 = (1 - t) ** 3
  const b1 = 3 * (1 - t) ** 2 * t
  const b2 = 3 * (1 - t) * t ** 2
  const b3 = t ** 3

  return { x: x1 * (b0 + b1) + x2 * (b2 + b3), y: y1 * b0 + mid * (b1 + b2) + y2 * b3 }
}

const pill = (x: number, y: number, text: string) => {
  const pw = text.length * 12 + 12
  return (
    `<rect x="${x - pw / 2}" y="${y - 15}" width="${pw}" height="30" rx="8" ry="8" fill="#1e1e1e"/>` +
    `<text x="${x}" y="${y}" fill="#cfd8dc" font-size="${FONT}" font-family="sans-serif" text-anchor="middle" dominant-baseline="central">${text}</text>`
  )
}

// A line, plus a travelling dot (coloured like the component it leads to)
// while that component is active, plus its label.
// `phase` (the time of the last flush) makes a redrawn dot carry on from where
// it was instead of jumping back to the start of the line.
const edge = (a: Box, b: Box, i: number, isActive: boolean, label: string, phase: number) => {
  const d = curve(a, b)
  const colour = KIND[b.kind].fill
  const p = labelPoint(a, b)
  const dur = 1.5 + i * 0.3
  const begin = -(((phase / 1000) % dur)).toFixed(2)
  return (
    `<path d="${d}" fill="none" stroke="${colour}" stroke-opacity="${isActive ? 0.8 : 0.3}" stroke-width="2"/>` +
    (isActive
      ? `<circle r="5" fill="${colour}"><animateMotion begin="${begin}s" dur="${dur}s" repeatCount="indefinite" path="${d}"/></circle>`
      : '') +
    pill(p.x, p.y, label)
  )
}

const node = (b: Box) => {
  const k = KIND[b.kind]
  const ring = b.ring ? STATE[b.ring] : 'none'
  const ringW = b.ring ? 3.5 : 0
  return (
    `<rect x="${b.cx - b.w / 2}" y="${b.cy - b.h / 2}" width="${b.w}" height="${b.h}" rx="${RADIUS}" ry="${RADIUS}" fill="${k.fill}" stroke="${ring}" stroke-width="${ringW}"/>` +
    `<text x="${b.cx}" y="${b.cy}" fill="${k.text}" font-size="${FONT}" font-family="sans-serif" text-anchor="middle" dominant-baseline="central">${b.label}</text>`
  )
}

const esc = (s: string) => s.replace(/[<>&"]/g, '')

// You -> Claude: how far the account's 5-hour limit has grown since the base.
const growthText = (v: FlowView) =>
  v.limitPct < 0 || v.basePct < 0
    ? '–%'
    : `+${Math.max(0, v.limitPct - v.basePct).toFixed(1)}%`

// Claude -> a path: the estimated share of the 5-hour limit it cost, in percent.
const costText = (v: FlowView, n: FlowNode) =>
  v.k > 0 ? `~${(n.w * v.k).toFixed(COST_DECIMALS)}%` : '~?%'

const draw = (v: FlowView, now: number): string => {
  const you: Box = {
    label: 'Ty',
    kind: 'you',
    cx: 220,
    cy: 32,
    w: 96,
    h: 40,
    ring: v.isWaiting ? 'waiting' : undefined,
  }
  const claude: Box = { label: 'Claude', kind: 'claude', cx: 220, cy: 130, w: 130, h: 46 }

  const n = v.nodes.length
  const kids = v.nodes.map((nd, i) => {
    const isRunning = nd.running > 0
    const ring: Box['ring'] =
      now - nd.errorAt < ERROR_MS
        ? 'error'
        : isRunning && nd.isBackground
          ? 'background'
          : undefined
    const box: Box = {
      label: esc(nd.label.slice(0, LABEL_CHARS)),
      kind: nd.kind,
      cx: 220 + (i - (n - 1) / 2) * 110,
      cy: 238,
      w: 96,
      h: 40,
      ring,
    }
    return { nd, box, isActive: isRunning || now - nd.at < ACTIVE_MS }
  })

  return (
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}">` +
    edge(you, claude, 0, v.mainRunning, growthText(v), v.flushAt) +
    kids
      .map((k, i) => edge(claude, k.box, i + 1, k.isActive, costText(v, k.nd), v.flushAt))
      .join('') +
    node(you) +
    node(claude) +
    kids.map(k => node(k.box)).join('') +
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

const bump = (v: FlowView): FlowView => ({ ...v, tick: v.tick + 1 })

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

function change($: EngineInterface, fn: (v: FlowView) => FlowView): void {
  queued.push(fn)
  if (isFlushPending) return
  isFlushPending = true
  $.clock.after(FLUSH_MS, async () => {
    const batch = queued
    queued = []
    isFlushPending = false
    const at = await $.clock.now()
    await update($, view, v => ({ ...batch.reduce((acc, f) => f(acc), v), flushAt: at }))
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
    const { rateLimits } = await $.session.usage()
    const win = rateLimits.find(r => r.kind === 'five_hour')
    await change($, v => applyLimit(v, win))

    return next(e)
  })

  // Every prompt brings the panel back if it was closed (unless switched off).
  on('prompt.submit', async ($, e, next) => {
    // Open only when it is not up: a repeated open re-seats the pane.
    if ((await $.env.get('FLOW_PANEL')) !== '0') {
      const isUp = (await $.ui.panes()).some(pane => pane.id === PANE)
      if (!isUp) void $.ui.open({ id: PANE, title: 'Flow' })
    }

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
      $.clock.after(ACTIVE_MS + 200, () => change($, bump))
      if (failed) $.clock.after(ERROR_MS + 200, () => change($, bump))
    }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text, Svg } = $.ui.resolve(e)
    const v = await read($, view)
    const now = await $.clock.now()

    return (
      <Box flexDirection="column">
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
