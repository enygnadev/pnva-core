# PNVA Root Traceability Matrix

Author: Gustavo de Aguiar Martins
Project: PNVA-Core
Edition: Open Research / Production Evidence Edition

## Purpose

The PNVA root traceability matrix turns runtime no-tick evidence into an auditable laboratory table.

Each R3 runtime slot must connect:

```text
slot -> precheck no-tick event -> collapse commit event -> entity -> heuristic rules -> proof refs -> proof hashes -> downstream validators
```

This makes the root package easier to review because a reader does not need to infer traceability from multiple reports.

## Tool

```text
tools/pnva_root_traceability_matrix.py
```

## Report

```text
reports/pnva-root-traceability-matrix-2026-05-05.json
```

## Classification

```text
PNVA_ROOT_TRACEABILITY_MATRIX_READY
```

## Current Result

```text
root_traceability_score: 100.0
check_count: 8
failure_count: 0
event_count: 70
slot_count: 35
valid_slot_count: 35
invalid_slot_count: 0
precheck_count: 35
commit_count: 35
entity_count: 1
heuristic_rule_count: 4
risk_flag_count: 1
proof_hash_unique_count: 70
proof_ref_unique_count: 70
no_tick_suppression_ratio: 0.5
runtime_guard_negative_controls: 63/63
root_traceability_hash: sha256:f6bd17b7e2103e6a3f224b3be267cbd835ad548cfa5b5aa04245817ef91feb7d
```

## Checks

The matrix verifies:

```text
runtime event stream is closed
all slot rows are valid
entity binding is closed
heuristic authority is H2 and legacy-free in runtime scope
no-tick efficiency matches the runtime no-tick report
runtime evidence guard is aligned
proof-chain seal is aligned
proof identity is native, non-projected and unique
```

## Production Interpretation

This layer strengthens the PNVA/no-tick claim by making every suppression and collapse traceable.

It does not replace the root sovereignty guard. It feeds it. The root guard now consumes this matrix as an explicit root input, so a traceability failure becomes a root blocker.

## Boundary

This validates the public deterministic R3 runtime sample only. It does not claim private deployment coverage or universal performance behavior.

## Command

```bash
python3 tools/pnva_root_traceability_matrix.py \
  --write reports/pnva-root-traceability-matrix-2026-05-05.json
```
