// DEBUG: the last lines of what redrew the pane and why, kept in
// $SOCRATEX_HOME/state/flow-debug/<session>.log (outside git; the mod cannot delete files,
// so old logs are rotated by `python modules/tools/scripts/state.py rotate flow-debug`).
// A debugging aid only: nothing reads it back.
import type { EngineInterface } from 'claude-code'

import type { Stored } from './model'
import { identity } from './sources'

let lines: string[] = []

export async function dbg($: EngineInterface, msg: string): Promise<void> {
  const at = await $.clock.now()
  lines = [...lines, `${new Date(at).toISOString().slice(11, 23)} ${msg}`].slice(-80)
  const { dir, selfId } = await identity($)
  if (!dir) return
  try {
    await $.fs.write(`${dir.replace(/\/local\/flow$/, '')}/state/flow-debug/${selfId.slice(0, 8)}.log`, lines.join('\n'))
  } catch {
    // a debugging aid only
  }
}

export const firstDiff = (a: string, b: string): string => {
  let i = 0
  while (i < a.length && i < b.length && a[i] === b[i]) i += 1

  return `at ${i}: [${a.slice(Math.max(0, i - 30), i + 50)}] vs [${b.slice(Math.max(0, i - 30), i + 50)}]`
}

let lastTrace = ''

// Logs (only when it changes) whether the app store knows this session and which children it
// lists, to find why children vanish from the tree.
export async function traceStore($: EngineInterface, entries: readonly Stored[], selfId: string, localId: string): Promise<void> {
  const kids = localId ? entries.filter(s => s.from === localId) : []
  const line =
    `store self=${selfId.slice(0, 8)} local=${localId.slice(6, 14)} entries=${entries.length} ` +
    `kids=[${kids.map(k => `${k.local.slice(6, 14)}:cli=${k.cli.slice(0, 8)}:arch=${k.isArchived}:fork=${k.isFork}`).join(',')}]`
  if (line === lastTrace) return
  lastTrace = line
  await dbg($, line)
}

let lastSource = ''

// What the pane drew: the same picture as before, or where it first differs.
export async function noteRender($: EngineInterface, source: string): Promise<void> {
  await dbg($, `render ${source === lastSource ? 'same picture' : `new picture ${firstDiff(lastSource, source)}`}`)
  lastSource = source
}

const logged = new Set<string>()

// The first of each kind of sample is written once (a task notification, to compare with /tasks).
export async function dbgOnce($: EngineInterface, kind: string, msg: string): Promise<void> {
  if (logged.has(kind)) return
  logged.add(kind)
  await dbg($, msg)
}
