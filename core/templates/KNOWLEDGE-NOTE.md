---
type: template
title: Knowledge note
description: Frontmatter and layout for any rule document, guide or knowledge note, so scripts can index it and agents can skim it.
updated: 2026-11-16
---

# 🗂️ Knowledge note template

One file is one concept (a rule set, a guide, a table, a runbook, a design). The path is its identity. Folders may carry an `index.md` or an `INDEX.json` entry for progressive disclosure; link related notes with plain relative Markdown links.

```markdown
---
type: <rules|guide|design|reference|log|runbook|template>
title: <short title>
description: <one line: what it is and when to read it>
updated: <YYYY-MM-DD>
tags: [optional, tags]
---

# <emoji> <title>

<body: free-form Markdown, the most important point first>
```

- `type`, `title` and `description` are required; `tools/build_index.py` reads them to refresh `INDEX.json` (it never removes entries by hand-written keys).
- Data that scripts consume stays in JSON; this format is for text that people and models read.
- Change history belongs in git; a long-lived knowledge folder may add a `log.md` with dated one-line entries.
