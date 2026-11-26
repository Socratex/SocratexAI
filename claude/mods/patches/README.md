# Patches for third-party mods

## lot-map-side-stack.patch
Makes lot-map (alexeyw/lot-map, 0.14.1, commit ea9de48f) a guest of side-stack (lucas-saldanha-werneck/side-stack): its map is
drawn as a section of the Stack pane next to other mods, and its own pane is not opened when side-stack is there. Adds
`hooks/stack-guest.tsx` (copied unchanged from side-stack) and two hooks in `hooks/register.tsx`. Without side-stack it changes
nothing. `claude plugin validate` passes on the patched copy; not yet tried in a live session.

Build a local copy (do not edit the installed plugin: updates would overwrite it):

    git clone https://github.com/alexeyw/lot-map.git lot-map-stack
    cd lot-map-stack && git checkout ea9de48f
    patch -p1 -l < ../claude/mods/patches/lot-map-side-stack.patch

After a lot-map update, re-check that the patch still applies. The earlier pane-grid patch was dropped: pane-grid draws a text-only
grid in the desktop app (ledger item 140).

## Where it runs (2026-11-26)
Local marketplace `sox-local` in `~/claude-mods/sox-local` (outside git): `side-stack` (upstream 0.5.2) and `lot-map` (patched copy).
Installed as `side-stack@sox-local` and `lot-map@sox-local`; the upstream `lot-map@lot-map` is uninstalled.
