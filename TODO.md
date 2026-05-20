# TODO

## Side Backlog

- Directive hierarchy and context-bloat audit: review all persistent directives, classify them into an explicit hierarchy, and demote directive-FOMO items into backlog/reference layers instead of always-loaded context. Goal: keep the compiled DB, flows, and routed context benefits without letting low-priority future-proofing notes bloat startup context or cause random rule loss when context pressure rises. Preserve truly core directives as high-priority rules; move "do next time" ideas into lower-priority backlog or profile-gated guidance. Useful output: an AI-generated readable hierarchy list for owner approval, with ROI picks for deletions, merges, profile gates, and shorter formulations.
