// SOURCES: where the mod reads the truth from (and the one file it writes for others).
// Nothing here decides anything and nothing here changes the state: each function returns
// plain data. The few module variables are read caches (file mtimes, the saved view).
import type { EngineInterface } from 'claude-code'

import type { FlowView, SubTree } from '../types'
import type { Stored, TaskRow } from './model'

// ------------------------------------------------------------------ who we are and where files live

export type Identity = { dir: string; selfId: string; startedAt: number }

let selfId = ''
let startedAt = 0

// The engine id of this session, when it started (as far as this process knows) and the folder of the
// shared views (`$SOCRATEX_HOME/local/flow`; '' when the variable is not set: no shared files then).
export async function identity($: EngineInterface): Promise<Identity> {
  const home = await $.env.get('SOCRATEX_HOME')
  if (!selfId) selfId = await $.session.id()
  if (!startedAt) startedAt = await $.clock.now()

  return { dir: home ? `${home.replace(/\\/g, '/')}/local/flow` : '', selfId, startedAt }
}

// ------------------------------------------------------------------ the engine's agent list

// `$.agent.list()`; undefined when it could not be read (agents then stay as they are).
export async function listAgents($: EngineInterface): Promise<readonly TaskRow[] | undefined> {
  try {
    return await $.agent.list()
  } catch {
    return undefined
  }
}

// ------------------------------------------------------------------ shared files (local/flow/<id>.json)

export type Shared = { id: string; startedAt: number; updatedAt: number; tree: SubTree; view?: FlowView; ended?: boolean }

export async function loadShared($: EngineInterface, dir: string, id: string): Promise<Shared | undefined> {
  try {
    return JSON.parse(String(await $.fs.read(`${dir}/${id}.json`))) as Shared
  } catch {
    return undefined
  }
}

// The shared trees of the sessions with these engine ids.
export async function loadTrees($: EngineInterface, dir: string, ids: readonly string[]): Promise<Map<string, SubTree | undefined>> {
  const files = await Promise.all(ids.map(id => loadShared($, dir, id)))

  return new Map(ids.map((id, i): [string, SubTree | undefined] => [id, files[i]?.tree]))
}

let lastPublished = ''

// Writes this session's tree and view for the session that started it (and for a restart).
// Only a real change rewrites the file: its updatedAt must mean "this session did something",
// or no session would ever look stale.
export async function publish($: EngineInterface, tree: (selfId: string) => SubTree, view: FlowView, ended: boolean): Promise<void> {
  const { dir, selfId: id, startedAt: began } = await identity($)
  if (!dir) return
  try {
    const body = JSON.stringify({ tree: tree(id), view, ended })
    if (body === lastPublished) return
    lastPublished = body
    const at = await $.clock.now()
    const text = JSON.stringify({ id, startedAt: began, updatedAt: at, tree: tree(id), view, ended })
    await $.fs.write(`${dir}/${id}.json`, text)
  } catch {
    // the shared folder is optional: without it there are simply no session tiles
  }
}

// The view this session saved in an earlier run (undefined = none).
export async function savedView($: EngineInterface): Promise<FlowView | undefined> {
  const { dir, selfId: id } = await identity($)

  return dir ? (await loadShared($, dir, id))?.view : undefined
}

// ------------------------------------------------------------------ the desktop app's own session store
// The Claude desktop app keeps one small file per session (title, who started it, archived or not).
// It is the truth of which sessions are ours.

type Entry = { name: string; kind: string; mtimeMs: number }
const parsed = new Map<string, Stored>() // path -> parsed file, re-read only when its mtime changes
let storeDirs: string[] | undefined

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

const parseStored = (name: string, mtime: number, j: Record<string, any>): Stored => ({
  local: name.replace(/\.json$/, ''),
  cli: String(j.cliSessionId ?? ''),
  prior: Array.isArray(j.priorCliSessionIds) ? j.priorCliSessionIds.map(String) : [],
  lastCli: String(j.lastAssistantCliSessionId ?? ''),
  from: String(j.spawnedFrom?.sessionId ?? ''),
  isFork: j.spawnedFrom?.userFork === true,
  isArchived: j.isArchived === true,
  title: String(j.title ?? ''),
  created: Number(j.createdAt ?? 0),
  mtime,
})

// One scan per reconcile: lists every store folder once and reads only the files that are new
// or changed since the last scan. A file that is gone leaves the result.
export async function scanStore($: EngineInterface): Promise<Stored[]> {
  try {
    if (!storeDirs?.length) storeDirs = await findStoreDirs($)
    const seen = new Set<string>()
    for (const dir of storeDirs) {
      for (const e of await entriesOf($, dir)) {
        if (e.kind !== 'file' || !/^local_.*\.json$/.test(e.name)) continue
        const path = `${dir}/${e.name}`
        seen.add(path)
        if (parsed.get(path)?.mtime === e.mtimeMs) continue
        try {
          parsed.set(path, parseStored(e.name, e.mtimeMs, JSON.parse(String(await $.fs.read(path))) as Record<string, any>))
        } catch {
          // half-written or unreadable: tried again on the next change
        }
      }
    }
    for (const path of [...parsed.keys()]) if (!seen.has(path)) parsed.delete(path)
  } catch {
    storeDirs = []
  }

  return [...parsed.values()]
}

// ------------------------------------------------------------------ the transcript

let lastTitleAt = 0

// The title the sidebar shows is kept in the session's transcript as the last "customTitle"
// (or "aiTitle") line; read at most once a minute. undefined = not due, or nothing readable.
export async function transcriptTitle($: EngineInterface): Promise<string | undefined> {
  const now = await $.clock.now()
  if (now - lastTitleAt < 60000) return undefined
  lastTitleAt = now
  try {
    const { transcriptPath } = await $.session.info()
    if (!transcriptPath) return undefined
    const text = String(await $.fs.read(transcriptPath))
    const hits = [...text.matchAll(/"(?:customTitle|aiTitle)":("(?:[^"\\]|\\.)*")/g)]
    const last = hits[hits.length - 1]
    if (!last) return undefined

    return String(JSON.parse(last[1] as string)).slice(0, 80)
  } catch {
    return undefined // no readable transcript: the tooltip just shows "Session N"
  }
}
