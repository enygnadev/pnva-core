# PNVA Authority Migration Ledger

Author: Gustavo de Aguiar Martins
Project: PNVA-Core / Enygnalab / EnyOS
Edition: Open Research / Production Evidence Edition, 2026

## Objective

The authority migration ledger turns the R3 authority debt into exact entity/action targets.

The previous R3 plan identified the primary blocker:

```text
35 H0 strong legacy decisions
```

This ledger answers the next engineering question:

```text
which entity, action and heuristic path must be migrated first?
```

## Current Public Result

Report:

```text
reports/pnva-authority-migration-ledger-2026-05-05.json
```

Current classification:

```text
AUTHORITY_MIGRATION_LEDGER_READY_WITH_LEGACY_WARNINGS
```

Current result:

```text
source_event_count: 519
candidate_event_count: 35
canonical_low_authority_strong_count: 35
native_low_authority_strong_count: 0
r3_primary_blocking_debt_count: 35
candidate_event_count_matches_r3: true
entity_candidate_count: 1
action_candidate_count: 3
event_type_candidate_count: 1
mapped_candidate_count: 35
unmapped_candidate_count: 0
migration_coverage_ratio: 1.0
proof_coverage_ratio: 1.0
error_count: 0
warning_count: 35
```

## Dominant Migration Target

The entire primary R3 authority debt is concentrated in one actor:

```text
entity_id: entity_4c3ade60ea78
event_type: cuda_slot_scan
source_file: pnva-miner-events.jsonl
candidate_count: 35
```

Action mix:

```text
RESIZE_BATCH: 32
COOLDOWN_GPU: 2
EXECUTE: 1
```

Risk signal:

```text
RESIZE_BATCH_PRESSURE: 32
```

## Native Replacement Path

The ledger maps every candidate to hard-authority native rules:

```text
adaptive_threshold: 35
field_scheduler: 35
power_orchestrator: 2
```

Interpretation:

```text
RESIZE_BATCH -> adaptive_threshold + field_scheduler
COOLDOWN_GPU -> power_orchestrator + field_scheduler + adaptive_threshold
EXECUTE -> adaptive_threshold + field_scheduler
```

## Production Rule

Historical H0 evidence must not be erased. It remains visible as migration evidence.

Future R3 evidence must emit the same operational intent as native `pnva.event.v1` with:

```text
schema_version
event_id
entity_id
causal_chain_id
decision
tension
heuristics.rules
proof.proof_hash
```

and every strong decision must carry H2/H3/H4 authority.

## Command

```bash
python3 tools/pnva_authority_migration_ledger.py \
  --write reports/pnva-authority-migration-ledger-2026-05-05.json
```

For CI or temporary validation:

```bash
python3 tools/pnva_authority_migration_ledger.py \
  --write /tmp/pnva-authority-migration-ledger.json
python3 -m json.tool /tmp/pnva-authority-migration-ledger.json >/dev/null
```

## Boundary

This ledger does not claim the R3 debt is already removed. It proves that the R3 authority debt is mapped, proof-backed and actionable.

The release remains honest:

```text
R2_NATIVE_CLEAN_LEGACY_QUARANTINED
```

The next target remains:

```text
R3_NATIVE_CLEAN_LEGACY_FREE
```
