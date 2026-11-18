export type NodeKind = 'agent' | 'tool' | 'mcp' | 'skill' | 'app'

export type FlowNode = {
  key: string // unique id: tool name, MCP server, skill or agent type
  label: string
  kind: NodeKind
  at: number // last activity, ms
  running: number // calls in flight
  isBackground: boolean // a background agent is running
  errorAt: number // last failure, ms (0 = none)
  w: number // weighted tokens this path has cost (see weights in register.tsx)
}

// The tree of one session, as it is shared with the session that started it.
export type SubTree = {
  id: string // the session's id: a tree never shows a session that is already above it
  nodes: FlowNode[]
  subs: SubTree[] // sessions that session started in turn
  mainRunning: boolean
  isWaiting: boolean
  wTotal: number
  k: number
}

export type FlowView = {
  sessionIds: string[] // sessions this one started (found by their shared files)
  subs: SubTree[] // their trees, in the same order

  nodes: FlowNode[]
  mainRunning: boolean // the main loop is mid-turn
  isWaiting: boolean // Claude finished, the next move is the user's
  limitPct: number // account's 5-hour limit used, percent (-1 = unknown)
  basePct: number // limitPct when this mod first saw the window (-1 = unknown)
  baseReset: string // the window's reset time the base belongs to
  wTotal: number // weighted tokens of all turns since the base (exact usage)
  k: number // learned percent of the limit per weighted token (0 = not yet)
  flushAt: number // when the last batched redraw happened, ms (dot phase)
  agentNode: Record<string, string> // sub-agent id -> node key
  tick: number // bumped to force a redraw when something expires
}

declare module 'claude-code' {
  interface PluginState {
    'flow-panel': { view: Shaped<FlowView> }
  }
}
