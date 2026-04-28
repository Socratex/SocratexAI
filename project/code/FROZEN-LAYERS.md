# Frozen Layers for Code Projects

## Summary

Frozen layers are working code or architecture areas that should not be changed casually.

## Default Contract

Use `context-docs/FROZEN_LAYERS.yaml` to list freeze candidates.

Before changing a frozen or semi-frozen layer:

1. State that the change touches a frozen layer.
2. Explain why the change is necessary.
3. Prefer asking for confirmation when the reason is not an obvious local fix.
4. Keep the diff bounded.
5. Run the relevant regression check.
6. Update the frozen-layer note if the ownership or invariant changed.

## Freeze Candidate Examples

- stable public API contracts,
- persistence schema,
- build or release tooling,
- migration framework,
- authentication or authorization boundaries,
- generated ID contracts,
- cross-module orchestration,
- core domain invariants.

## Non-Local Changes

If a new feature wants to change a frozen layer indirectly, first check whether an adapter, compatibility layer, or explicit extension point can avoid destabilizing the existing contract.
