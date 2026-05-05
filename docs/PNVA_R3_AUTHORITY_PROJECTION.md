# PNVA R3 Authority Projection

Author: Gustavo de Aguiar Martins
Project: PNVA-Core / Enygnalab / EnyOS
Edition: Open Research / Production Evidence Edition, 2026

## Objective

The R3 authority projection turns the mapped H0 authority debt into a native hard-authority candidate sample.

The previous layers established:

```text
R3 migration plan -> 35 primary H0 strong decisions
authority migration ledger -> one entity/action target with full proof coverage
```

This layer answers the next engineering question:

```text
what should the future native runtime emit before we claim R3?
```

## Current Public Result

Summary report:

```text
reports/pnva-r3-authority-projection-summary-2026-05-05.json
```

Projected evidence:

```text
reports/pnva-r3-authority-projection-events-2026-05-05.jsonl
reports/pnva-r3-authority-projection-entities-2026-05-05.json
reports/pnva-r3-authority-projection-replay-2026-05-05.json
reports/pnva-r3-authority-projection-policy-2026-05-05.json
reports/pnva-r3-authority-projection-no-tick-2026-05-05.json
```

Current classification:

```text
R3_AUTHORITY_PROJECTION_READY
```

Current result:

```text
source_candidate_count: 35
projected_event_count: 70
projected_precheck_count: 35
projected_commit_count: 35
projected_strong_decision_count: 35
projected_low_authority_strong_count: 0
projected_no_tick_suppression_count: 35
projected_no_tick_suppression_ratio: 0.5
proof_coverage_ratio: 1.0
entity_count: 1
```

Validator result:

```text
replay: REPLAY_VALID
policy: SOVEREIGN_POLICY_READY
no_tick: SOVEREIGN_NO_TICK_READY
```

## Projection Model

Each legacy H0 strong candidate becomes two native events:

```text
native observe precheck -> native collapse commit
```

The precheck preserves no-tick discipline:

```text
decision.kind: observe
decision.action: NO_ACTION
reason: native_authority_precheck_no_tick
```

The commit preserves the operational intent with hard authority:

```text
decision.kind: collapse
decision.action: RESIZE_BATCH | COOLDOWN_GPU | EXECUTE
reason: native_authority_projection_authorized
```

Native rules:

```text
native_event_emitter
adaptive_threshold
field_scheduler
power_orchestrator for cooldown cases
```

## Boundary

This projection does not rewrite history.

It does not claim the old H0 evidence was already native H2 evidence.

It proves a reproducible implementation contract for the next runtime:

```text
old evidence remains preserved
projected native evidence is replay-valid
projected native policy has zero low-authority strong decisions
projected native no-tick has explicit suppression before collapse
```

## Command

```bash
python3 tools/pnva_r3_authority_projection.py \
  --events reports/pnva-r3-authority-projection-events-2026-05-05.jsonl \
  --entity-catalog reports/pnva-r3-authority-projection-entities-2026-05-05.json \
  --summary reports/pnva-r3-authority-projection-summary-2026-05-05.json
```

Validation:

```bash
python3 tools/pnva_replay_validator.py \
  --events reports/pnva-r3-authority-projection-events-2026-05-05.jsonl \
  --entity-catalog reports/pnva-r3-authority-projection-entities-2026-05-05.json \
  --write reports/pnva-r3-authority-projection-replay-2026-05-05.json

python3 tools/pnva_sovereign_policy_validator.py \
  --events reports/pnva-r3-authority-projection-events-2026-05-05.jsonl \
  --entity-catalog reports/pnva-r3-authority-projection-entities-2026-05-05.json \
  --write reports/pnva-r3-authority-projection-policy-2026-05-05.json

python3 tools/pnva_no_tick_invariant_analyzer.py \
  --events reports/pnva-r3-authority-projection-events-2026-05-05.jsonl \
  --entity-catalog reports/pnva-r3-authority-projection-entities-2026-05-05.json \
  --replay-report reports/pnva-r3-authority-projection-replay-2026-05-05.json \
  --write reports/pnva-r3-authority-projection-no-tick-2026-05-05.json
```

## Production Rule

R3 should not be claimed from a projection alone.

The projection is the implementation contract. The runtime must later emit fresh native events with the same authority shape before the package can move from:

```text
R2_NATIVE_CLEAN_LEGACY_QUARANTINED
```

to:

```text
R3_NATIVE_CLEAN_LEGACY_FREE
```
