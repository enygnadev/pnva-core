# PNVA R3 Runtime Contract Validation

Author: Gustavo de Aguiar Martins
Project: PNVA-Core / Enygnalab / EnyOS
Edition: Open Research / Production Evidence Edition, 2026

## Objective

The R3 runtime contract validator checks whether the capture matrix, evidence guard and instrumentation plan form one coherent runtime contract.

It answers one question:

```text
is the next R3 runtime capture contract internally valid before fresh JSONL is accepted?
```

This layer does not claim final runtime evidence. It validates the contract that future runtime evidence must obey.

## Current Public Result

Report:

```text
reports/pnva-r3-runtime-contract-validation-2026-05-05.json
```

Current classification:

```text
R3_RUNTIME_CONTRACT_VALIDATED_READY
```

Current result:

```text
contract_validation_ready: true
runtime_evidence_present: false
runtime_evidence_approved: false
capture_slot_count: 35
action_contract_count: 3
required_runtime_event_count: 70
event_template_count: 6
mandatory_field_count: 28
negative_control_detected_count: 51
positive_control_passed_count: 6
enforced_control_count: 48
contract_check_count: 271
failure_count: 0
```

## What It Validates

The validator checks:

```text
matrix classification
guard classification
instrumentation plan classification
runtime approval remains false
35 capture slots remain explicit
70 required runtime events remain paired
6 templates remain two per action contract
28 mandatory runtime fields are present
51 negative controls are detected
6 positive controls are accepted as fixture-only guard controls
guard enforced controls match the runtime contract
contract slot IDs cover the matrix
contract original event IDs cover the matrix
precheck templates are no-tick observe/NO_ACTION
commit templates match their action
precheck decision.reason is native_authority_precheck_no_tick
commit decision.reason is native_runtime_commit
precheck field.state_after is suppressed
commit field.state_after is committed
precheck event_type matches the slot precheck contract
commit event_type matches the slot commit contract
proof.projection=false
proof.native=true
source.file_name is present
source.format=native_pnva_event_v1
source.line is present
source.sanitized=true
field.state_before and field.state_after are required
tension.gate_delta is required
tension.gate_delta must equal score - threshold
precheck gate_delta must be nonpositive
commit gate_delta must be nonnegative
tension.components.r3_runtime_slot_id is required
timestamps must be parseable ISO-8601 values
duplicate event_id values are forbidden
proof_hash must be strict sha256:64-hex
proof_hash must bind to the event identity and source-location payload
proof_hash and proof_ref values must be unique in the runtime stream
proof_ref must match runtime:<slot-id>:<role>
entity_type must be present and match the capture slot
heuristic rules must be known and unique
risk_flags must be lists, known, unique and present on prechecks and commits when the slot declares target risk
precheck and commit must share causal_chain_id
commit timestamp must be at or after precheck timestamp
commit source.line must be after precheck source.line
each slot must have exactly one precheck and one commit
runtime event count must equal the declared requirement
```

## Why This Matters

The capture matrix says what must be captured.

The evidence guard says what must be rejected.

The instrumentation plan says how emitters should produce final events.

The contract validator proves those three documents agree before final runtime capture starts.

## Boundary

This validator does not approve R3 cutover.

It deliberately keeps:

```text
runtime_evidence_present: false
runtime_evidence_approved: false
```

Final R3 evidence still requires fresh native runtime JSONL accepted by the runtime evidence guard and then validated by replay, policy, no-tick and proof-chain checks.

## Command

```bash
python3 tools/pnva_r3_runtime_contract_validator.py \
  --write reports/pnva-r3-runtime-contract-validation-2026-05-05.json
```

For CI or temporary validation:

```bash
python3 tools/pnva_r3_runtime_contract_validator.py \
  --write /tmp/pnva-r3-runtime-contract-validation.json
python3 -m json.tool /tmp/pnva-r3-runtime-contract-validation.json >/dev/null
```

## Sovereign Rule

Before PNVA accepts final runtime evidence, the contract itself must be coherent.

That prevents a future runtime sample from passing because of documentation drift, missing slot identity, weak native markers or mismatched action templates.
