// SCHEDULE: when the sources are read. Owns the timers and nothing else: it gathers the truth
// (sources.ts), hands it to the store (state.ts), which applies the rules (rules.ts).
//
// Cadence: init (the first hook or pane render that fires arms it and reconciles once), then every
// RECONCILE_MS; an event that may have ended something asks for one more, debounced to
// RECONCILE_DEBOUNCE_MS. A resumed session may never raise session.start, hence "first that fires".
import type { EngineInterface } from 'claude-code'

import { dbg, traceStore } from './debug'
import { LIVE_REFRESH_MS, RECONCILE_DEBOUNCE_MS, RECONCILE_MS, type Stored } from './model'
import { sharedIdsOf, visibleSessions } from './rules'
import { identity, listAgents, loadTrees, scanStore, transcriptTitle } from './sources'
import { dispatch, getState, reconcileInto, refreshRunning } from './state'

let isReconciling = false
let lastReconcileAt = 0
let isReconcileScheduled = false
let reconcileTimer: { cancel: () => void } | undefined

// Reads every real source once and applies it. Events only update the state optimistically and
// may ask for this; none of them is the only way a state ends.
export async function reconcile($: EngineInterface): Promise<void> {
  if (isReconciling) return
  isReconciling = true
  try {
    const now = await $.clock.now()
    lastReconcileAt = now
    const agents = await listAgents($)
    const { dir, selfId } = await identity($)
    const entries = dir ? await scanStore($) : undefined
    const nodes = entries ? visibleSessions(entries, selfId, getState().localId).nodes : []
    const shared = entries && dir ? await loadTrees($, dir, sharedIdsOf(nodes)) : undefined
    await reconcileInto($, { agents, entries, shared }, now)
    if (entries) await afterTree($, entries)
    void armLiveRefresh($)
  } catch (err) {
    await dbg($, `reconcile failed: ${err instanceof Error ? err.message : String(err)}`)
  } finally {
    isReconciling = false
  }
}

// Debug trace of the store, and while the app has no entry for this session yet, the title from the transcript.
async function afterTree($: EngineInterface, entries: readonly Stored[]): Promise<void> {
  const { selfId, localId } = getState()
  await traceStore($, entries, selfId, localId)
  if (entries.some(e => e.local === localId)) return
  const title = await transcriptTitle($)
  if (title !== undefined) await dispatch($, { type: 'title', title })
}

// An event asks for a reconcile: at most one per RECONCILE_DEBOUNCE_MS.
export async function requestReconcile($: EngineInterface): Promise<void> {
  if (isReconcileScheduled) return
  isReconcileScheduled = true
  const wait = Math.max(0, lastReconcileAt + RECONCILE_DEBOUNCE_MS - (await $.clock.now()))
  $.clock.after(wait, async () => {
    isReconcileScheduled = false
    await reconcile($)
  })
}

// Starts the RECONCILE_MS cadence from whichever hook fires first and reconciles once right away. Idempotent.
export function armReconcile($: EngineInterface): void {
  if (reconcileTimer) return
  reconcileTimer = $.clock.every(RECONCILE_MS, () => reconcile($))
  void requestReconcile($)
}

// A running time ticks by itself for a while after it was drawn. While anything runs, one redraw
// per LIVE_REFRESH_MS keeps the labels coming, even when nothing else changes; it is the only
// timer the panel keeps besides the reconcile.
let isRefreshArmed = false

export async function armLiveRefresh($: EngineInterface): Promise<void> {
  if (isRefreshArmed) return
  isRefreshArmed = true
  $.clock.after(LIVE_REFRESH_MS, async () => {
    isRefreshArmed = false
    if (!(await refreshRunning($))) return
    await armLiveRefresh($)
  })
}
