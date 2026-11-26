// Shared vocabulary of the mod: constants, plain data types and the empty view.
// No logic and no imports from the other mod files; every layer may import this one.
import type { Figure, FlowView } from '../types'

// ------------------------------------------------------------------ tunables
export const RECONCILE_MS = 30000 // how often the real sources (session store, agent list) are read again
export const RECONCILE_DEBOUNCE_MS = 2000 // an event-triggered reconcile runs at most this often
export const FLUSH_MS = 2000 // state writes are batched into one redraw per this long
export const LIVE_REFRESH_MS = 60000 // a running time gets fresh labels this often
export const MAX_NODES = 12 // blocks per session level; the idlest finished one is dropped first
export const ERROR_MS = 6000 // how long a failed block keeps its red ring
export const MONITOR_BACKSTOP_MS = 5000 // a finite Monitor is closed this long after its deadline

// Relative price of a token, the stand-in for how much of the limit it eats.
// A guess from API list prices; the learned factor `k` absorbs the scale.
export const WEIGHT = { input: 1, output: 5, cacheRead: 0.1, cacheWrite: 1.25 }
// A tool result enters the context once (cache write) and is re-read on later
// turns: charged as a write plus about one cheap re-read per ten turns' worth.
export const RESULT_WEIGHT = 1.35
export const CHARS_PER_TOKEN = 4

// ------------------------------------------------------------------ plain data
export type Usage = {
  input_tokens?: number
  output_tokens?: number
  cache_read_input_tokens?: number
  cache_creation_input_tokens?: number
}

export type Ring = 'waiting' | 'error' | 'background'

export const FIGURES = ['cost', 'time', 'tokens'] as const satisfies readonly Figure[]

export const INITIAL: FlowView = {
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

// One row of the engine's background work lists (`$.agent.list()`, the Stop event's `background_tasks`).
export type TaskRow = { id: string; status?: string }

// One file of the desktop app's session store, reduced to what the tree needs.
export type Stored = {
  local: string // the app's own id (`local_<uuid>`), the file name; what `spawnedFrom.sessionId` names
  cli: string // the id a mod sees as its session id; empty until the session first runs
  prior: string[] // earlier ids of the same session (after a clear or compaction)
  lastCli: string
  from: string // the local id of the session that started it
  isFork: boolean // a side chat the person forked, not work we started
  isArchived: boolean
  title: string
  created: number
  mtime: number
}
export type StoredNode = { entry: Stored; kids: StoredNode[] }

// ------------------------------------------------------------------ the state
// Why a followed task or agent was closed (the table that explains each is CLOSE_RULES in rules.ts).
export type CloseReason =
  | 'task-stop'
  | 'monitor-deadline'
  | 'notification'
  | 'transcript-row'
  | 'ended-status'
  | 'missed-reconciles'
  | 'unseen-after-restart'

// A background task (Bash, Monitor) or a background agent this process saw starting.
// Life cycle: running -> closed(reason). A closed entry is never reopened.
export type WorkEntry = {
  id: string
  kind: 'task' | 'agent'
  key: string // the node key of an agent (its branch); empty for a task
  startedAt: number
  misses: number // reconciles in a row in which the real source did not list it
  phase: 'running' | 'closed'
  reason?: CloseReason // set once closed
}

// Everything the mod knows: the picture's data and the cache of work it follows.
export type FlowState = {
  selfId: string // the engine id of this session ('' until learned)
  localId: string // the desktop app's id of this session ('' until learned)
  view: FlowView // what is drawn and saved
  work: ReadonlyMap<string, WorkEntry> // tasks and agents by id
  turns: ReadonlyMap<string, number> // when each running turn began, by agent id ('' = the main loop)
  forks: ReadonlyMap<string, number> // when a command's fork (/btw ...) started, by agent id
  lastStop?: { at: number; rows: readonly TaskRow[] } // the last Stop event's `background_tasks`
}

export const INITIAL_STATE: FlowState = {
  selfId: '',
  localId: '',
  view: INITIAL,
  work: new Map(),
  turns: new Map(),
  forks: new Map(),
}
