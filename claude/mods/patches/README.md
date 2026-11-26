# Patches for third-party mods

## lot-map-pane-grid.patch
Makes lot-map (alexeyw/lot-map, 0.14.1, commit ea9de48f) grid-ready for pane-grid: a grid render hook, a `state.set` hook that
closes its own pane while placed, and `hooks/pane-grid.ts` (copied unchanged from hwanyong/pane-grid). Without pane-grid it
changes nothing. `claude plugin validate` passes on the patched copy; not yet tried in a live session.

Build a local copy (do not edit the installed plugin: updates would overwrite it):

    git clone https://github.com/alexeyw/lot-map.git lot-map-grid
    cd lot-map-grid && git checkout ea9de48f
    patch -p1 -l < ../claude/mods/patches/lot-map-pane-grid.patch

Load that folder with `claude --plugin-dir <folder>` for a test, and disable the installed `lot-map@lot-map` so the two do not draw twice.
After a lot-map update, re-check that the patch still applies.
