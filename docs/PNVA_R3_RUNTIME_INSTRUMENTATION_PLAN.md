# PNVA R3 Runtime Instrumentation Plan

Author: Gustavo de Aguiar Martins
Project: PNVA-Core / Enygnalab / EnyOS
Edition: Open Research / Production Evidence Edition, 2026

## Objective

The R3 runtime instrumentation plan converts pending R3 runtime slots into concrete emitter contracts.

The capture matrix says what must be captured.

The evidence guard says what must be rejected.

The instrumentation plan says how the runtime should emit the final evidence.

```text
capture slots -> action contracts -> event templates -> mandatory fields -> validation commands
```

## Current Public Result

Report:

```text
reports/pnva-r3-runtime-instrumentation-plan-2026-05-05.json
```

Current classification:

```text
R3_RUNTIME_INSTRUMENTATION_PLAN_READY
```

Current result:

```text
instrumentation_plan_ready: true
runtime_evidence_present: false
runtime_evidence_approved: false
capture_slot_count: 35
entity_target_count: 1
action_contract_count: 3
required_runtime_event_count: 70
required_no_tick_precheck_count: 35
required_collapse_commit_count: 35
event_template_count: 6
mandatory_field_count: 28
negative_control_detected_count: 48
positive_control_passed_count: 6
```

## Action Contracts

Current action contracts:

```text
RESIZE_BATCH: 32 slots, 64 runtime events
COOLDOWN_GPU: 2 slots, 4 runtime events
EXECUTE: 1 slot, 2 runtime events
```

Every action contract requires:

```text
1 native no-tick precheck per slot
1 native commit per slot
proof.projection=false
proof.native=true
source.format=native_pnva_event_v1
source.sanitized=true
commit authority >= H2
entity_id present
causal_chain_id present
same causal_chain_id across precheck and commit
commit timestamp >= precheck timestamp
exactly one precheck and one commit per slot
runtime event count equals required_runtime_event_count
precheck event_type equals slot event_type + _authority_precheck
commit event_type equals slot event_type
unique event_id values
proof_hash present
proof_hash bound to event identity
proof_ref in runtime:<slot-id>:<role> form
gate_delta equals score - threshold
precheck gate_delta <= 0
commit gate_delta >= 0
tension.components.original_event_id present
tension.components.r3_runtime_slot_id present
```

## Mandatory Event Fields

The final runtime JSONL must include:

```text
schema_version
event_id
timestamp
entity_id
entity_type
causal_chain_id
event_type
field.state_before
field.state_after
decision.kind
decision.action
decision.reason
heuristics.rules
heuristics.risk_flags
tension.score
tension.threshold
tension.gate_delta
tension.components.original_event_id
tension.components.r3_runtime_slot_id
proof.valid
proof.projection
proof.native
proof.proof_hash
proof.proof_ref
source.format
source.sanitized
```

## Runtime Phases

```text
1. instrument_native_emitters
2. capture_fresh_runtime_jsonl
3. run_runtime_evidence_guard
4. run_runtime_validators
5. request_cutover
```

The cutover phase must not run before the runtime evidence guard accepts the fresh sample.

## Contract Validation

The instrumentation plan is validated by:

```text
docs/PNVA_R3_RUNTIME_CONTRACT_VALIDATION.md
reports/pnva-r3-runtime-contract-validation-2026-05-05.json
```

Current result:

```text
R3_RUNTIME_CONTRACT_VALIDATED_READY
253 contract checks
0 failures
```

This proves the matrix, evidence guard and instrumentation templates agree before final runtime capture begins.

## Validation Commands

```bash
python3 tools/pnva_r3_runtime_evidence_guard.py \
  --runtime-events <fresh-runtime-events.jsonl> \
  --write /tmp/pnva-r3-runtime-evidence-guard.json

python3 tools/pnva_replay_validator.py \
  --events <fresh-runtime-events.jsonl> \
  --entity-catalog <fresh-runtime-entities.json> \
  --write /tmp/pnva-r3-runtime-replay.json

python3 tools/pnva_sovereign_policy_validator.py \
  --events <fresh-runtime-events.jsonl> \
  --entity-catalog <fresh-runtime-entities.json> \
  --write /tmp/pnva-r3-runtime-policy.json

python3 tools/pnva_no_tick_invariant_analyzer.py \
  --events <fresh-runtime-events.jsonl> \
  --entity-catalog <fresh-runtime-entities.json> \
  --replay-report /tmp/pnva-r3-runtime-replay.json \
  --write /tmp/pnva-r3-runtime-no-tick.json

python3 tools/pnva_proof_chain_sealer.py \
  --events <fresh-runtime-events.jsonl> \
  --write /tmp/pnva-r3-runtime-proof-chain.json
```

## Boundary

This plan does not claim final R3 runtime completion.

It deliberately keeps:

```text
runtime_evidence_present: false
runtime_evidence_approved: false
```

The value of this layer is operational clarity: the next runtime capture now has exact emitter contracts and cannot depend on informal interpretation.
