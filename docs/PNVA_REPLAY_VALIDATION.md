# PNVA Replay Validation

Author: Gustavo de Aguiar Martins  
Project: PNVA-Core / Enygnalab / EnyOS  
Edition: Open Research / Production Evidence Edition, 2026

## Purpose

PNVA Replay Validation proves that a canonical PNVA event sequence can be checked after the fact without trusting the original runtime blindly.

The replay validator is read-only. It does not change gates, thresholds, proofs or runtime behavior.

## Tool

```text
tools/pnva_replay_validator.py
```

Input:

```text
reports/pnva-canonical-events-sample-2026-05-05.jsonl
reports/pnva-entity-catalog-2026-05-05.json
```

Output:

```text
reports/pnva-replay-validation-2026-05-05.json
```

## What It Validates

The replay validator checks:

```text
JSONL parse integrity
required pnva.event.v1 fields
unique event_id values
deterministic proof_hash recomputation
ETEV_GUARD_PASS consistency
ETEV_GUARD_BLOCK consistency
entity relation references
causal chain count
decision distribution
risk flag distribution
timestamp disorder warnings
```

## Current Result

Current public replay report:

```text
classification: REPLAY_VALID
pass: true
event_count: 512
unique_event_ids: 512
chain_count: 14
proof_hash_ok: 512
proof_hash_bad: 0
guard_pass_ok: 35
guard_block_ok: 33
relation_count: 68
errors: 0
warnings: 2
```

The warnings are timestamp-order warnings from a sampled multi-source export. They do not invalidate replay because the sample is assembled from multiple log files, not from one globally sorted event stream.

Strict order can be required when validating a single ordered stream:

```bash
python3 tools/pnva_replay_validator.py --strict-order
```

## Why It Matters For No-Tick

No-tick systems must be auditable after execution. If the system claims it avoided unnecessary work, the proof must preserve:

```text
what event happened
which entity acted
what tension was computed
whether the gate passed or blocked
what action was selected
which proof hash seals the event
```

Replay validation makes that chain checkable.

## Interpretation

PNVA-Core now has three evidence layers:

```text
1. sanitized production proof gates
2. canonical event bridge
3. replay validation
```

This does not claim universal proof. It proves that the public sample is structurally replayable and internally consistent.

## Sovereign Rule

Future PNVA runtimes should emit `pnva.event.v1` directly. Until then, the bridge and replay validator allow legacy logs to remain useful without rewriting history.
