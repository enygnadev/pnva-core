# PNVA Causal Chronology Guard

Author: Gustavo de Aguiar Martins  
Project: PNVA-Core / Enygnalab / EnyOS  
Edition: Open Research / Production Evidence Edition, 2026

## Objective

This layer validates the chronology of public PNVA event evidence.

It answers a direct no-tick question:

```text
if PNVA does not execute by blind time, does it still preserve time as auditable evidence?
```

The answer must be yes. PNVA uses state, event, tension and proof as the execution reason, while timestamp order remains part of the audit trail.

## Current Public Result

Report:

```text
reports/pnva-causal-chronology-2026-05-05.json
```

Current classification:

```text
CAUSAL_CHRONOLOGY_READY_WITH_LEGACY_WARNINGS
```

Current result:

```text
event_count: 519
chain_count: 15
global_backward_count: 1
error_count: 0
warning_count: 2
native_chronology_clean: true
```

## Scope Reading

Canonical legacy bridge:

```text
event_count: 512
chain_count: 14
global_backward_count: 1
global_zero_gap_count: 316
error_count: 0
warning_count: 2
```

Native emitter:

```text
event_count: 7
chain_count: 1
global_backward_count: 0
global_zero_gap_count: 0
error_count: 0
warning_count: 0
```

## Warning Policy

The canonical warnings are preserved as legacy migration evidence:

```text
LEGACY_BACKWARD_TIME
LEGACY_BATCH_TIMESTAMP_COMPACTION
```

Meaning:

```text
the converted legacy sample includes one temporal reset and many same-timestamp batch records
```

This is not promoted as a clean native property. It is documented as a legacy bridge artifact.

The native path is clean and monotonic.

## What Is Validated

The guard checks:

```text
timestamp parseability
global event order
causal-chain event order
backward time count
zero-gap count
gap statistics
dominant fixed interval ratio
decision distribution over time
chain span and chain density
native monotonicity
```

## Why This Matters

PNVA/no-tick does not mean "ignore time".

It means:

```text
time measures
state causes
event triggers
tension decides
proof preserves
```

This guard makes that distinction auditable.

## Command

```bash
python3 tools/pnva_causal_chronology_guard.py \
  --write reports/pnva-causal-chronology-2026-05-05.json
```

For CI or temporary validation:

```bash
python3 tools/pnva_causal_chronology_guard.py \
  --write /tmp/pnva-causal-chronology.json
python3 -m json.tool /tmp/pnva-causal-chronology.json >/dev/null
```

## Production Rule

Native PNVA runtime events must be monotonic and warning-light.

Legacy chronology warnings may be preserved only when:

```text
they are explicit
they are counted
they do not create parse errors
they do not affect native runtime cleanliness
```
