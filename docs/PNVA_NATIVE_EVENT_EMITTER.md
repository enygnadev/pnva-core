# PNVA Native Event Emitter

Author: Gustavo de Aguiar Martins  
Project: PNVA-Core / Enygnalab / EnyOS  
Edition: Open Research / Production Evidence Edition, 2026

This document defines the native PNVA event emission layer.

Previous public layers proved that legacy PNVA logs can be converted into `pnva.event.v1`, replay-validated and analyzed for no-tick invariants. The native emitter closes the next engineering gap: new runtimes should emit canonical PNVA events directly.

## Purpose

The native emitter turns this:

```text
runtime action -> ad hoc log -> bridge -> canonical event
```

into this:

```text
runtime action -> canonical pnva.event.v1 -> replay -> invariant proof
```

This is more sovereign because the event is born inside the PNVA contract instead of being normalized after the fact.

## Native Contract

The emitter produces:

```text
schema_version: pnva.event.v1
source.format: native_pnva_event_v1
proof.native: true
```

Each event includes:

```text
event_id
timestamp
causal_chain_id
entity_id
entity_type
event_type
field
tension
decision
heuristics
proof
source
```

## Tension Equation

The demo emitter uses the public PNVA operational tension equation:

```text
T = alpha * event_weight
  + beta * state_gradient
  - gamma * cost
  + mu * memory
```

Default weights:

```text
alpha = 0.4
beta  = 0.3
gamma = 0.2
mu    = 0.1
```

The gate delta is:

```text
gate_delta = T - max(0, threshold - margin)
```

## Proof Hash

The native proof hash is deterministic over:

```text
source.file_name
source.line
timestamp
entity_id
event_type
decision
tension
```

This matches the replay validator. If a field changes, the replay proof changes.

## Demo Artifacts

Current native demo artifacts:

```text
reports/pnva-native-events-demo-2026-05-05.jsonl
reports/pnva-native-entity-catalog-demo-2026-05-05.json
reports/pnva-native-emitter-summary-2026-05-05.json
reports/pnva-native-replay-validation-2026-05-05.json
reports/pnva-native-no-tick-invariants-2026-05-05.json
```

Current result:

```text
native emitter: NATIVE_EMITTER_READY
native replay: REPLAY_VALID
native no-tick invariants: SOVEREIGN_NO_TICK_READY
event_count: 7
suppressed_count: 4
no_tick_suppression_ratio: 0.5714
guard_consistency_ratio: 1.0
proof_integrity_ratio: 1.0
```

## Why This Matters

The bridge proved that old logs can be made sovereign.

The native emitter proves that new logs can be sovereign from birth.

That is the production direction for PNVA/no-tick: every future runtime event should already carry state, tension, decision, heuristic class, entity identity and proof hash when it is emitted.

## Verification

Run:

```bash
python3 tools/pnva_native_event_emitter.py
python3 tools/pnva_replay_validator.py \
  --events reports/pnva-native-events-demo-2026-05-05.jsonl \
  --entity-catalog reports/pnva-native-entity-catalog-demo-2026-05-05.json
python3 tools/pnva_no_tick_invariant_analyzer.py \
  --events reports/pnva-native-events-demo-2026-05-05.jsonl \
  --entity-catalog reports/pnva-native-entity-catalog-demo-2026-05-05.json \
  --replay-report reports/pnva-native-replay-validation-2026-05-05.json
```

Expected classifications:

```text
NATIVE_EMITTER_READY
REPLAY_VALID
SOVEREIGN_NO_TICK_READY
```
