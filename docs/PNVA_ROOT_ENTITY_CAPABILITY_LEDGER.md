# PNVA Root Entity Capability Ledger

Author: Gustavo de Aguiar Martins
Project: PNVA-Core
Edition: Open Research / Production Evidence Edition

## Purpose

The PNVA root entity capability ledger exposes entity readiness across canonical, native and R3 runtime evidence.

It links each entity to:

```text
catalog scope
capabilities
state
event coverage
proof coverage
native/projection status
no-tick suppression behavior
heuristic rules
risk flags
governance status
```

## Tool

```text
tools/pnva_root_entity_capability_ledger.py
```

## Report

```text
reports/pnva-root-entity-capability-ledger-2026-05-05.json
```

## Classification

```text
PNVA_ROOT_ENTITY_CAPABILITY_LEDGER_READY
```

## Current Result

```text
entity_capability_score: 100.0
check_count: 12
failure_count: 0
entity_row_count: 13
scope_count: 3
profile_event_count: 589
capability_edge_count: 25
r3_runtime_ready_count: 1
native_ready_count: 6
controlled_canonical_count: 6
blocked_entity_count: 0
proof_complete: true
projection_clean: true
root_release_hash: sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc
```

## Governance Status

```text
R3_RUNTIME_READY
NATIVE_READY
CONTROLLED_CANONICAL
BLOCKED_FOR_RUNTIME_USE
```

Current status:

```text
R3_RUNTIME_READY: 1
NATIVE_READY: 6
CONTROLLED_CANONICAL: 6
BLOCKED_FOR_RUNTIME_USE: 0
```

## Production Interpretation

The ledger makes entities governable. A PNVA entity is no longer only an identifier in a log; it has capabilities, state, proof coverage, no-tick behavior, heuristic links and a governance status.

This is the safe path for expanding the runtime field: add entities only when they can be cataloged, linked to proof events and kept projection-free.

## Boundary

This ledger is an audit layer. It does not execute system actions, change live gates or expand claims beyond public evidence.

## Command

```bash
python3 tools/pnva_root_entity_capability_ledger.py \
  --write reports/pnva-root-entity-capability-ledger-2026-05-05.json
```
