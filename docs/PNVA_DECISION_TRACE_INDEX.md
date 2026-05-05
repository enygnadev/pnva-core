# PNVA Decision Trace Index

Author: Gustavo de Aguiar Martins  
Project: PNVA-Core / Enygnalab / EnyOS  
Edition: Open Research / Production Evidence Edition, 2026

## Objective

This layer makes every public PNVA decision traceable.

It answers the reviewer-facing question:

```text
for each event, which entity acted, which heuristic rules contributed, which tension was measured and which proof sealed the decision?
```

## Current Public Result

Report:

```text
reports/pnva-decision-trace-index-2026-05-05.json
```

Current classification:

```text
DECISION_TRACE_INDEX_READY_WITH_LEGACY_WARNINGS
```

Current result:

```text
event_count: 519
traced_event_count: 519
trace_complete_count: 519
trace_coverage_ratio: 1.0
entity_coverage_ratio: 1.0
proof_coverage_ratio: 1.0
heuristic_coverage_ratio: 1.0
causal_chain_coverage_ratio: 1.0
tension_coverage_ratio: 1.0
hard_authority_event_count: 367
low_authority_trace_count: 152
hard_authority_ratio: 0.707129
error_count: 0
warning_count: 152
native_trace_clean: true
```

## Scope Reading

Canonical legacy bridge:

```text
event_count: 512
trace_coverage_ratio: 1.0
low_authority_trace_count: 152
error_count: 0
warning_count: 152
```

Native emitter:

```text
event_count: 7
trace_coverage_ratio: 1.0
low_authority_trace_count: 0
error_count: 0
warning_count: 0
native_trace_clean: true
```

## What It Validates

The index checks every event for:

```text
event_id
entity_id in catalog
causal_chain_id
decision.kind
finite tension score
finite threshold
finite gate_delta
heuristic rules
max heuristic authority
proof hash
proof reference
```

## Why This Matters

PNVA/no-tick becomes stronger when a decision can be followed from the event ID to the actor and proof:

```text
event -> entity -> heuristic rules -> authority -> tension -> decision -> proof
```

This index is not a new claim of performance. It is the map that makes existing claims auditable.

## Warning Policy

The canonical bridge preserves `152` low-authority legacy traces because old logs contain historical observer/veonic records.

The native runtime path has:

```text
0 errors
0 warnings
trace_coverage_ratio: 1.0
hard authority for every event
```

## Command

```bash
python3 tools/pnva_decision_trace_index.py \
  --write reports/pnva-decision-trace-index-2026-05-05.json
```

For CI or temporary validation:

```bash
python3 tools/pnva_decision_trace_index.py \
  --write /tmp/pnva-decision-trace-index.json
python3 -m json.tool /tmp/pnva-decision-trace-index.json >/dev/null
```

## Production Rule

Every future PNVA event should preserve:

```text
complete trace
cataloged entity
visible heuristic rules
explicit authority
finite tension fields
valid proof hash
causal chain reference
```

That is how PNVA moves from a set of logs to a sovereign decision fabric.
