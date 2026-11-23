---
type: patch
title: Guard narrowing for project knowledge (decision 9)
description: Ready patch for core/safety.json and claude/hooks/guard.py so the agent can edit knowledge documents but not config files in local/projects and local/groups
updated: 2026-11-23
---

# Guard patch (apply by hand)

Why: `core/safety.json` rule `safety-config-edits` protects all of `local/projects/**`, so the agent cannot write `PROJECT.md`, `DEVIATIONS.md`, rules or tickets. Spec decision 9 narrows it to config and flow files.

Two files change, because the guard matches only exact paths or a `/**` prefix and has no `*` support today:
- `core/safety.json`: replace the one `local/projects/**` entry with config, flow and stage files of projects and groups.
- `claude/hooks/guard.py`: let a `repo_paths` pattern with `*` match through `fnmatch` (stricter, never looser), and derive the Bash text needle from the part before the first `*`.

`core/safety.json` is protected and `claude/hooks` is agent configuration: back up first (`modules/tools/scripts/backup.py`), then apply as the owner. Then run `sox install` so the installed hook copy matches.

Verified on a scratch copy of the repo: `tests/test_safety.py` 62 passed, including the new cases below (config, flow, stage and group config blocked; PROJECT.md, DEVIATIONS.md, rules, GROUP.md and tickets editable from Write, Edit and Bash).

Open decision for the owner: `local/projects/*/project.json` sets `group`, so changing it can pull in a group config that relaxes safety rules. It is left unprotected here (the spec lists only config, flow and stage files). Add `"local/projects/*/project.json"` to the same list if you want it protected too.

## Patch

```diff
--- a/core/safety.json
+++ b/core/safety.json
@@ -89,7 +89,7 @@
         {
           "kind": "protected-paths",
           "tools": ["Edit", "Write", "Bash"],
-          "repo_paths": ["core/safety.json", "core/safety.schema.json", "local/overrides/**", "local/projects/**", "defaults/config.json", "defaults/adapters/**"],
+          "repo_paths": ["core/safety.json", "core/safety.schema.json", "local/overrides/**", "local/projects/*/config.json", "local/projects/*/flow.json", "local/projects/*/review.json", "local/projects/*/planning.json", "local/groups/*/config.json", "local/groups/*/flow.json", "defaults/config.json", "defaults/adapters/**"],
           "anywhere_paths": [".socratex/config.json"],
           "override_env": "SOCRATEX_GUARD_ALLOW_SAFETY_EDIT",
           "reason": "{path} defines or relaxes safety rules; only the owner edits it by hand (owner override for one session: SOCRATEX_GUARD_ALLOW_SAFETY_EDIT=1)."
--- a/claude/hooks/guard.py
+++ b/claude/hooks/guard.py
@@ -18,6 +18,7 @@
 
 from __future__ import annotations
 
+import fnmatch
 import json
 import os
 import re
@@ -132,13 +133,17 @@
             wanted = wanted[:-3]
             if path == wanted or path.startswith(wanted + "/"):
                 return True
+        elif "*" in pattern:
+            if fnmatch.fnmatchcase(path, wanted):
+                return True
         elif path == wanted:
             return True
     return any(path == name.lower() or path.endswith("/" + name.lower()) for name in entry.get("anywhere_paths", []))
 
 
 def protected_needles(entry: dict) -> list[str]:
-    return [p.lower().removesuffix("/**") for p in entry.get("repo_paths", [])] + [p.lower() for p in entry.get("anywhere_paths", [])]
+    return [p.lower().split("*")[0].removesuffix("/").removesuffix("/**") if "*" in p else p.lower().removesuffix("/**")
+            for p in entry.get("repo_paths", [])] + [p.lower() for p in entry.get("anywhere_paths", [])]
 
 
 # ---------- Bash command analysis ----------
--- a/tests/test_safety.py
+++ b/tests/test_safety.py
@@ -172,6 +172,7 @@
 # ---------- the agent cannot edit the files that relax rules ----------
 
 PROTECTED = ["core/safety.json", "core/safety.schema.json", "local/overrides/config.json", "local/projects/p/config.json",
+             "local/projects/p/flow.json", "local/projects/p/review.json", "local/groups/g/config.json",
              "defaults/config.json", "defaults/adapters/yolo.json"]
 
 
@@ -183,6 +184,19 @@
     assert code == 2 and "defines or relaxes safety rules" in err
 
 
+@pytest.mark.parametrize("relative", ["local/projects/p/PROJECT.md", "local/projects/p/DEVIATIONS.md", "local/projects/p/rules/r.md",
+                                      "local/groups/g/GROUP.md", "local/tickets/APP/APP-1/STATE.json"])
+@pytest.mark.parametrize("name", ["Write", "Edit"])
+def test_agent_can_edit_knowledge_documents(world, relative, name):
+    root, project = world
+    assert guard(tool(name, root / relative), root, project)[0] == 0
+
+
+def test_agent_can_write_knowledge_documents_from_bash(world):
+    root, project = world
+    assert guard(bash(f"echo hi > {root.as_posix()}/local/projects/p/PROJECT.md"), root, project)[0] == 0
+
+
 def test_agent_cannot_edit_a_project_socratex_config(world):
     root, project = world
     assert guard(tool("Write", project / ".socratex" / "config.json"), root, project)[0] == 2
```
