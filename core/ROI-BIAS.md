# ROI Bias

## Purpose

Use ROI bias to rank improvements by what pays off now for this project profile.

Do not optimize for what looks elegant in abstraction when another option better improves the project's current correctness, speed, diagnosability, or verifiability.

## Value Axes

`Quality`: improves correctness, reduces bugs, protects behavior, or prevents regressions.

`Speed`: improves development velocity, iteration time, setup speed, or delivery flow.

`Diagnosability`: makes failures easier to understand, localize, reproduce, or explain.

`Truthfulness`: makes claims about the system easier to verify through tests, assertions, schemas, logs, monitoring, reproducible scripts, or explicit contracts.

Use value marks:

- `++`: large impact,
- `+`: noticeable impact,
- `~`: marginal impact.

## Cost Axes

`Effort`: estimated implementation cost.

- `S`: small,
- `M`: medium,
- `L`: large,
- `XL`: very large.

`Risk`: chance of regression, data loss, workflow breakage, or architectural churn.

- `L`: low,
- `M`: medium,
- `H`: high.

`Reversibility`: how easy it is to undo or isolate the change.

- `H`: easy to reverse,
- `M`: moderately reversible,
- `L`: hard to reverse.

## ROI Rule

A recommendation is worth doing now when:

`(impact_on_value_axes * profile_weight) / (effort * risk * inverse_reversibility)` is high.

This is a judgment heuristic, not a numeric obligation.

## Profile Weight

Legacy, low-test, custom-framework projects weight `Diagnosability` and `Truthfulness` higher.

Greenfield and early projects weight `Quality` and `Speed` higher, while still preserving verification.

Mature projects weight `Quality`, `Risk`, and team coordination cost higher.

Sunset projects weight low-risk maintenance and migration leverage higher than broad redesign.

## ROI Picks

Analysis, review, planning, and finish reports should end with `ROI Picks` when they contain recommendations or next steps.

List one to three improvements worth doing now:

```text
## <emoji> ROI Picks
1. <improvement> - value: Truthfulness++, Diagnosability+ | cost: Effort=S, Risk=L, Reversibility=H | why now: <one line>
```

If no follow-up is worth doing now, say that explicitly.

## Anti-Pattern

Flag recommendations that are abstract-pretty but low ROI for the current profile.

Prefer the improvement that pays off for the user's actual pain, constraints, and verification reality.

