# PNVA Entity And Heuristic Maturity

Author: Gustavo de Aguiar Martins  
Project: PNVA-Core / Enygnalab / EnyOS  
Edition: Open Research / Production Evidence Edition, 2026

## Objective

This layer measures how mature the PNVA evidence is across:

```text
entities
heuristic rules
authority levels
no-tick suppression
proof coverage
causal chains
relations
```

The goal is to make PNVA more sovereign without changing the validated PASS chain.

## Why This Exists

Replay validation proves event consistency.  
No-tick invariants prove causal suppression.  
Policy validation proves authority rules.  
Causal graph audit proves topology.

The maturity layer asks a different question:

```text
which entity and which heuristic carried the decision?
```

That matters because a no-tick system is only production-grade when both execution and non-execution can be attributed to an actor, a rule, a threshold and a proof.

## Current Public Result

Report:

```text
reports/pnva-entity-heuristic-maturity-2026-05-05.json
```

Current classification:

```text
ENTITY_HEURISTIC_MATURITY_READY_WITH_LEGACY_WARNINGS
```

Current aggregate result:

```text
maturity_score: 94.59
total_event_count: 519
total_suppressed_count: 250
aggregate_no_tick_suppression_ratio: 0.481696
total_strong_decision_count: 304
total_strong_with_hard_authority: 269
aggregate_hard_authority_ratio: 0.884868
canonical_low_authority_legacy_count: 35
native_low_authority_legacy_count: 0
error_count: 0
warning_count: 35
```

## Scope Reading

Canonical legacy bridge:

```text
classification: ENTITY_HEURISTIC_MATURITY_READY_WITH_LEGACY_WARNINGS
event_count: 512
maturity_score: 94.17
legacy warnings: 35
errors: 0
```

Native runtime demo:

```text
classification: ENTITY_HEURISTIC_MATURITY_READY
event_count: 7
maturity_score: 95.0
legacy warnings: 0
errors: 0
```

## Interpretation

The result is intentionally honest.

The canonical sample preserves old evidence from legacy logs. It contains 35 low-authority strong decisions, already documented by the sovereign policy validator. They remain warnings, not hidden failures, because they came from historical sanitized evidence.

The native sample is the production direction: direct `pnva.event.v1` emission with H2/H3 authority and zero legacy warnings.

## What The Auditor Measures

For each entity:

```text
catalog presence
entity type
capabilities
event count
strong decision count
suppressed count
proof coverage
causal chain coverage
relation in/out count
maximum authority observed
decision mix
heuristic rules
risk flags
maturity score
```

For each heuristic:

```text
authority level
event count
entity coverage
native vs legacy use
strong decision count
suppressed count
proof coverage
average tension
average gate delta
decision mix
risk flags
maturity score
```

## No-Tick Meaning

In PNVA, suppression is not absence.

Suppression means:

```text
the field was observed
the heuristic evaluated the event
the threshold was not satisfied or a guard blocked it
the system did not execute
the non-execution was recorded as proof
```

This makes no-tick auditable. The system can explain why it acted and why it refused to act.

## Command

```bash
python3 tools/pnva_entity_heuristic_maturity.py \
  --write reports/pnva-entity-heuristic-maturity-2026-05-05.json
```

For CI or temporary validation:

```bash
python3 tools/pnva_entity_heuristic_maturity.py \
  --write /tmp/pnva-entity-heuristic-maturity.json
python3 -m json.tool /tmp/pnva-entity-heuristic-maturity.json >/dev/null
```

## Sovereign Rule

PNVA becomes stronger when every runtime decision can answer:

```text
which entity acted?
which heuristic ruled?
which authority level allowed it?
which no-tick suppression was intentional?
which proof validates the decision?
```

This is the engineering path from event logs to a sovereign causal runtime.
