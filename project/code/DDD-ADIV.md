# DDD-ADIV for Code Projects

## Summary

DDD-ADIV is the recommended design default for code projects using SocratexPipeline.

DDD-ADIV means Domain-Driven, Architecture-Decisive, Invariant-Visible development.

## Known-Solutions Alignment

Use known solutions as domain-clarifying tools, not as abstract ceremony.

Before custom design:

- check known solutions, proven practices, standard tools, and business/software archetypes,
- compare the problem against architecture archetypes such as layered architecture, hexagonal architecture, CQRS, state machines, queues, adapters, repositories, and domain services,
- prefer build-vs-borrow discipline when a framework feature, library, workflow, or pattern is cheaper and clearer,
- check future fit before executing requested work, and recommend a better prerequisite or design when the requested route would create avoidable retrofit cost,
- align the selected solution with domain language, ownership, invariants, and boundaries.

Reject a known solution only when it conflicts with the domain, creates worse coupling, weakens invariants, or hides the source of truth.

## Domain-Driven

Use project language as the primary naming source.

Prefer:

- business-meaningful names over mechanism names,
- explicit domain state over incidental data shape,
- commands and policies that describe intent,
- domain services only when behavior does not naturally belong to one entity or value object.

Avoid:

- generic managers that own unrelated behavior,
- anemic data objects plus scattered rules,
- framework vocabulary leaking into core domain logic,
- hidden domain meaning encoded only in comments or UI labels.

## Architecture-Decisive

Make durable ownership and dependency decisions explicit.

Prefer:

- small boundaries with clear responsibilities,
- ports and adapters for external systems,
- dependency direction that points inward toward stable domain logic,
- explicit source-of-truth ownership,
- decision records for choices that future work must preserve.

Avoid:

- circular ownership,
- duplicated sources of truth,
- convenience coupling across unrelated modules,
- broad shared utility layers that hide domain meaning.

## Invariant-Visible

Make important rules mechanically findable and checkable.

Prefer:

- validation at boundaries,
- explicit constructors or factories for valid states,
- assertions or guards for impossible states,
- schema checks for external data,
- tests for high-risk invariants,
- named policies for conditional rules.

Avoid:

- relying on call order when a state machine or explicit phase would be clearer,
- implicit defaults that silently create invalid states,
- scattered checks that implement one invariant differently in multiple places.

## Verification-Attached

Attach verification to risky work.

Verification can be:

- unit tests,
- integration tests,
- contract tests,
- typechecks,
- linters,
- build checks,
- smoke tests,
- manual reproduction steps.

If verification is not practical, record the residual risk.
