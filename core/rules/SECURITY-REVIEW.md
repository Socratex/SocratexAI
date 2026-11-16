---
type: rules
title: Security review
description: Short security checklist for business and client projects; run only when a change touches auth, secrets, payments, user input or external endpoints. Not for game projects.
updated: 2026-11-16
---

# 🔐 Security review

Business and client projects only. Game projects get one security check on their roadmap before multiplayer or release, not per change.

Run only when the change touches auth, secrets, payments, user input or an external endpoint. Otherwise skip it.

- No secrets, keys or tokens in code, logs, tests or commits; they come from the environment or a vault.
- Every input from outside (forms, query, headers, files, webhooks) is validated at the boundary; queries are parameterized.
- Auth and permission checks happen on the server for every protected action, not only in the UI.
- Payments: amounts and ids are checked server-side; webhooks are verified by signature; retries are idempotent.
- Errors and logs do not leak internals, personal data or secrets.
- New dependencies: known, maintained, pinned; no install scripts from unknown sources.
- Output that carries user data is escaped for its context (HTML, SQL, shell).
- Client NDA: no client code or data sent to a service the contract does not allow.

Report findings as: what is exposed, how it could be abused, smallest fix. Do not pad with generic advice.
