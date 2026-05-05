# PNVA R3 Migration Plan

Author: Gustavo de Aguiar Martins
Project: PNVA-Core / Enygnalab / EnyOS
Edition: Open Research / Production Evidence Edition, 2026

## Objective

The R3 migration plan turns PNVA legacy debt into an explicit engineering backlog.

The current public package is already robust:

```text
R2_NATIVE_CLEAN_LEGACY_QUARANTINED
```

The next target is:

```text
R3_NATIVE_CLEAN_LEGACY_FREE
```

## Current Public Result

Report:

```text
reports/pnva-r3-migration-plan-2026-05-05.json
```

Current classification:

```text
R3_MIGRATION_PLAN_READY
```

Current result:

```text
current_readiness_level: R2_NATIVE_CLEAN_LEGACY_QUARANTINED
target_readiness_level: R3_NATIVE_CLEAN_LEGACY_FREE
current_robustness_score: 97
target_robustness_score: 100
source_event_count: 519
native_clean_signal_count: 8 / 8
primary_blocking_debt_count: 35
migration_action_count: 6
raw_migration_signal_count: 903
estimated_r3_candidate: false
```

## Required R3 Actions

The plan defines four required R3 migration actions:

```text
R3-A1 Replace H0 strong legacy decisions with native H2/H3 authority
R3-A2 Migrate low-authority strong heuristic influence edges
R3-A3 Re-emit above-threshold suppressions through native calibrated thresholds
R3-A4 Emit pnva.event.v1 directly instead of relying on bridge normalization
```

Current required counts:

```text
legacy_observer_h0_strong_decisions: 35
low_authority_strong_influence_edges: 164
above_threshold_suppression_events: 176
legacy_schema_contract_warnings: 341
```

These counts are overlapping migration signals, not a de-duplicated event count.

## Supporting Actions

The plan also tracks two supporting actions:

```text
R3-A5 Reduce low-authority trace debt in public decision index
R3-A6 Keep entity no-tick migration debt bounded by actor
```

These keep the transition auditable while the native path remains clean.

## Command

```bash
python3 tools/pnva_r3_migration_planner.py \
  --write reports/pnva-r3-migration-plan-2026-05-05.json
```

For CI or temporary validation:

```bash
python3 tools/pnva_r3_migration_planner.py \
  --write /tmp/pnva-r3-migration-plan.json
python3 -m json.tool /tmp/pnva-r3-migration-plan.json >/dev/null
```

## Production Rule

The package can claim `R3_NATIVE_CLEAN_LEGACY_FREE` only when:

```text
primary_blocking_debt_count = 0
primary_required_remaining_count = 0
native_clean_signal_count = native_clean_signal_total
current_robustness_score = 100
estimated_r3_candidate = true
```

Until then, the honest status remains:

```text
R2_NATIVE_CLEAN_LEGACY_QUARANTINED
```
