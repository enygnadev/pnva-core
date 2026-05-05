# PNVA Root Observability Index

Author: Gustavo de Aguiar Martins
Project: PNVA-Core
Edition: Open Research / Production Evidence Edition

## Purpose

The PNVA root observability index creates one laboratory view over:

```text
no-tick metrics
event logs
proof hashes
entity catalogs
heuristic influence
runtime R3 slots
root gates
publication boundaries
```

It exists because root PASS is stronger when the reviewer can see the observable metrics behind it.

## Tool

```text
tools/pnva_root_observability_index.py
```

## Report

```text
reports/pnva-root-observability-index-2026-05-05.json
```

## Classification

```text
PNVA_ROOT_OBSERVABILITY_INDEX_READY
```

## Current Result

```text
observability_score: 100.0
check_count: 8
failure_count: 0
aggregate_event_count: 589
aggregate_suppressed_count: 285
aggregate_suppression_ratio: 0.483871
entity_catalog_rows: 13
runtime_accepted_slots: 35
runtime_pending_slots: 0
runtime_rejected_events: 0
runtime_no_tick_pair_failures: 0
heuristic_rule_count: 9
influence_edge_count: 1136
root_release_hash: sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc
```

## Checks

The index verifies:

```text
required observability reports are ready
event streams parse and match no-tick reports
aggregate no-tick metrics match root causal intelligence
proof and guard coverage are closed
native and runtime scopes are clean
runtime slots, contract and guard are closed
root scores are all 100
claim and publication boundaries are clean
```

## Production Interpretation

This is the root laboratory dashboard for PNVA/no-tick.

It shows that the current public package contains:

```text
512 canonical events
7 native demo events
70 R3 runtime events
285 proof-backed suppressions
70 unique R3 runtime proof hashes
13 entity catalog rows
9 heuristic rules
35 accepted runtime slots
0 runtime rejected events
0 public path leaks
0 unbounded high-risk claims
```

## Boundary

This index is a public observability layer over existing reports. It does not change the root release seal and does not claim private deployment validation.

## Command

```bash
python3 tools/pnva_root_observability_index.py \
  --write reports/pnva-root-observability-index-2026-05-05.json
```
