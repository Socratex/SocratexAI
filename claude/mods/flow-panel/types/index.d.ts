export type NodeKind = 'agent' | 'tool' | 'mcp' | 'skill' | 'app' | 'side'

export type FlowNode = {
  key: string // unique id: tool name, MCP server, skill or agent type
  label: string
  kind: NodeKind
  at: number // last activity, ms
  running: number // calls in flight
  isBackground: boolean // a background agent is running
  errorAt: number // last failure, ms (0 = none)
  w: number // weighted tokens of this path's tool results (see weights in register.tsx)
  usd?: number // dollars the engine's ledger charged to this agent's own turns
  tps?: number // tokens per second of its last turn or the result of its last call (dots of the up lane)
  tok?: number // fresh tokens this path moved (agent turns: input + output + cache write; tools: request + result)
  startSum?: number // sum of the start times (ms) of the calls running now: the live time is ms + running * now - startSum
  ms?: number // wall time this path spent executing (agent turns, tool calls), summed
  tpsIn?: number // tokens per second of the request of its last call (dots of the down lane)
  taskId?: string // a background task (Bash, Monitor): the engine's task id; the node is that task, not a tool
  taskName?: string // the task's name as /tasks lists it (Bash: description, else command; Monitor: description)
  calls?: number // how many calls this path has had (shown as "(x2)" in the tooltip of a merged block)
  hasUsage?: boolean // false = no token or cost data exists for it (a background command): drawn without dots, with a status LED
}

// The tree of one session, as it is shared with the session that started it.
export type SubTree = {
  id: string // the session's id: a tree never shows a session that is already above it
  title?: string // first prompt of the session, shown in its tooltip
  nodes: FlowNode[]
  subs: SubTree[] // sessions that session started in turn
  mainRunning: boolean
  isWaiting: boolean
  wTotal: number
  k: number
  usd?: number // dollars spent since the session's last prompt (undefined = unknown)
  tps?: number // tokens per second of the session's last main turn
  perW?: number // the session's dollars per weighted token (0 = not yet known)
}

export type FlowView = {
  mainTps?: number // tokens per second of the main loop's last turn
  allW?: number // weighted tokens of every turn this session (never reset)
  lastUsd?: number // the engine's cost ledger at the last turn, dollars
  promptUsd?: number // the ledger when the last prompt started
  baseUsd?: number // the ledger before this mod saw any turn (a resumed session has spent before)
  head?: string // this session's first prompt: how its parent recognises it
  spawns?: Array<{ at: number; snippet: string }> // start_session calls made here: when, and the start of the brief
  title?: string // first prompt of this session (its name in the parent's tooltip)
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

export type Figure = 'cost' | 'time' | 'tokens' // what the figure on each line shows

declare module 'claude-code' {
  interface PluginState {
    'flow-panel': { view: Shaped<FlowView>; figure: Shaped<Figure> }
  }
}
