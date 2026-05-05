# PNVA Suppression Ledger

Author: Gustavo de Aguiar Martins  
Project: PNVA-Core / Enygnalab / EnyOS  
Edition: Open Research / Production Evidence Edition, 2026

## Objective

This layer makes PNVA no-tick suppression auditable.

It answers a direct question:

```text
when PNVA did not execute, which entity, heuristic, authority, tension and proof justified the suppression?
```

## Current Public Result

Report:

```text
reports/pnva-suppression-ledger-2026-05-05.json
```

Current classification:

```text
SUPPRESSION_LEDGER_READY_WITH_LEGACY_WARNINGS
```

Current result:

```text
event_count: 519
suppressed_count: 250
estimated_avoided_execution_count: 250
proof_valid_count: 250
proof_coverage_ratio: 1.0
aggregate_no_tick_suppression_ratio: 0.481696
above_threshold_suppression_count: 176
below_threshold_suppression_count: 74
error_count: 0
warning_count: 176
native_suppression_clean: true
```

## Scope Reading

Canonical legacy bridge:

```text
suppressed_count: 246
observe_count: 213
block_count: 33
proof_coverage_ratio: 1.0
above_threshold_suppression_count: 176
warning_count: 176
```

Native emitter:

```text
suppressed_count: 4
observe_count: 2
block_count: 2
proof_coverage_ratio: 1.0
above_threshold_suppression_count: 0
warning_count: 0
native_suppression_clean: true
```

## What It Validates

The ledger checks every suppressed decision:

```text
entity_id exists in catalog
decision is observe or block
proof hash is valid
heuristic rules are visible
authority level is recorded
gate_delta is present
below-threshold suppression is clean
above-threshold legacy suppression is explicit warning
native suppression has zero warning drift
```

## Why This Matters

No-tick should not look like absence.

In PNVA, non-execution is a decision:

```text
event -> tension -> threshold -> suppression -> proof
```

This is the proof surface for avoided work. The current ledger records `250` proof-backed suppressions, which are the public sample's estimated avoided executions.

## Warning Policy

The canonical bridge preserves `176` above-threshold suppression warnings because old logs were converted from legacy formats.

This is not hidden as clean native behavior.

The native runtime scope has:

```text
0 errors
0 warnings
0 above-threshold suppressions
proof_coverage_ratio: 1.0
```

## Command

```bash
python3 tools/pnva_suppression_ledger.py \
  --write reports/pnva-suppression-ledger-2026-05-05.json
```

For CI or temporary validation:

```bash
python3 tools/pnva_suppression_ledger.py \
  --write /tmp/pnva-suppression-ledger.json
python3 -m json.tool /tmp/pnva-suppression-ledger.json >/dev/null
```

## Production Rule

Native no-tick suppression should remain:

```text
proof-backed
entity-attributed
heuristic-visible
authority-recorded
below threshold
reproducible
```

That is how PNVA turns doing less into a defensible engineering claim.
