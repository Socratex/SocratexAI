// STATE: the one store. The only place the state is replaced (`state = nextState(...)`), the only
// place the saved picture (the pane's atom) and the shared file are written.
//
// Two things live here:
//   - the FlowState (view data + the work cache), replaced at once by every event;
//   - its persistence: the pane draws from an atom, and every write to it redraws (and blinks) the
//     pane, so writes are batched to one per FLUSH_MS and skipped when the picture would not change.
import { atom, read, update } from 'claude-code'
import type { EngineInterface } from 'claude-code'

import type { Figure, FlowView } from '../types'
import { dbg, firstDiff } from './debug'
import { FLUSH_MS, INITIAL, INITIAL_STATE, type FlowState } from './model'
import { anyRunning, isEmpty, nextState, reconcile, restoredView, treeOf, type FlowEvent, type Truth } from './rules'
import { identity, publish, savedView } from './sources'

// The persisted view. Change the shape tag when FlowView changes: it declines what an earlier
// version stored, which outlives a reload.
const viewAtom = atom({ plugin: 'flow-panel', key: 'view' } as const, INITIAL, { shape: 'flow-9' })

// What the figure on every line shows. Kept apart from the view: it is a display choice of this
// person, not shared with the sessions above or below.
const figureAtom = atom({ plugin: 'flow-panel', key: 'figure' } as const, 'cost' as Figure, { shape: 'figure-1' })

let state: FlowState = INITIAL_STATE
let loading: Promise<void> | undefined

// State that changed but would draw the same picture is held here instead of being written.
let held: FlowView | undefined
let isFlushPending = false

// How the drawing is made (set once by the hooks module; the store must not import the view).
let picture: (v: FlowView, now: number, selfId: string) => string = () => ''
export const bindPicture = (fn: typeof picture): void => {
  picture = fn
}

export const getState = (): FlowState => state

// ------------------------------------------------------------------ changing the state

// Applies one engine event.
export async function dispatch($: EngineInterface, event: FlowEvent): Promise<void> {
  await ready($)
  state = nextState(state, event)
  scheduleFlush($)
}

// Applies what the real sources say (see `reconcile` in rules.ts).
export async function reconcileInto($: EngineInterface, truth: Truth, now: number): Promise<void> {
  await ready($)
  state = reconcile(state, truth, now)
  scheduleFlush($)
}

// Forces a redraw while something runs, so its ticking time gets fresh labels. False = nothing runs.
export async function refreshRunning($: EngineInterface): Promise<boolean> {
  await ready($)
  const cur = held ?? (await read($, viewAtom))
  if (!anyRunning(cur.nodes, cur.subs)) return false
  held = undefined
  state = nextState(state, { type: 'tick' })
  await update($, viewAtom, () => ({ ...cur, tick: cur.tick + 1 }))

  return true
}

// ------------------------------------------------------------------ first load

// The identity and the picture of an earlier run are loaded once, before the first event is applied.
function ready($: EngineInterface): Promise<void> {
  loading ??= load($).catch(err => {
    loading = undefined
    throw err
  })

  return loading
}

async function load($: EngineInterface): Promise<void> {
  const { selfId } = await identity($)
  const view = await restoredFor($, held ?? (await read($, viewAtom)))
  state = { ...state, selfId, view }
}

// After a restart the pane would start empty: take the last saved view instead (this session's own
// file when it was resumed). Not tied to session.start, which a resumed session may never raise.
let saved: FlowView | null | undefined

async function restoredFor($: EngineInterface, v: FlowView): Promise<FlowView> {
  if (!isEmpty(v)) return v
  if (saved === undefined) {
    saved = null
    saved = restoredView(await savedView($)) ?? null
  }

  return saved ?? v
}

// ------------------------------------------------------------------ writing it out

// Every state write redraws the pane, and a redraw makes the SVG frame blink: the changes are
// applied together, at most once per FLUSH_MS, and not at all when the picture stays the same.
function scheduleFlush($: EngineInterface): void {
  if (isFlushPending) return
  isFlushPending = true
  $.clock.after(FLUSH_MS, async () => {
    isFlushPending = false
    const at = await $.clock.now()
    const cur = await restoredFor($, held ?? (await read($, viewAtom)))
    const next = state.view
    const before = picture(cur, at, state.selfId)
    const after = picture(next, at, state.selfId)
    if (after === before) {
      held = next
      await persist($, next)

      return
    }
    await dbg($, `flush REDRAW ${firstDiff(before, after)}`)
    held = undefined
    await update($, viewAtom, () => next)
    await persist($, next)
  })
}

// Never overwrites a saved view with an empty one (unless the session ended).
async function persist($: EngineInterface, v: FlowView, ended = false): Promise<void> {
  if (isEmpty(v) && !ended) return
  await publish($, selfId => treeOf(v, selfId), v, ended)
}

// A closing or archived session marks its file, so the session that started it stops drawing it.
export async function markEnded($: EngineInterface): Promise<void> {
  await persist($, held ?? (await read($, viewAtom)), true)
}

// ------------------------------------------------------------------ what the pane reads

// The view the pane draws (the saved one while this session has nothing of its own yet) and the
// engine id of the session, the root of the tree.
export async function paneView($: EngineInterface): Promise<{ view: FlowView; selfId: string }> {
  const { selfId } = await identity($) // makes sure the session id is known before drawing

  return { view: await restoredFor($, await read($, viewAtom)), selfId }
}

// The picture must never depend on the toggle: if its value cannot be read, show cost.
export async function pickedFigure($: EngineInterface): Promise<Figure> {
  try {
    return (await read($, figureAtom)) ?? 'cost'
  } catch {
    return 'cost'
  }
}

export async function pickFigure($: EngineInterface, figure: Figure): Promise<void> {
  await update($, figureAtom, () => figure)
}
