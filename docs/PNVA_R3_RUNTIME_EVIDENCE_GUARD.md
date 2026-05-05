# PNVA R3 Runtime Evidence Guard

Author: Gustavo de Aguiar Martins
Project: PNVA-Core / Enygnalab / EnyOS
Edition: Open Research / Production Evidence Edition, 2026

## Objective

The R3 runtime evidence guard protects the intake boundary for the next PNVA runtime capture.

The runtime capture matrix defines what must be captured.

The runtime evidence guard defines what must be rejected.

```text
fresh runtime JSONL -> slot mapping -> no-tick pair check -> authority check -> proof check -> accept or reject
```

## Current Public Result

Report:

```text
reports/pnva-r3-runtime-evidence-guard-2026-05-05.json
```

Current classification:

```text
R3_RUNTIME_EVIDENCE_GUARD_READY_AWAITING_CAPTURE
```

Current result:

```text
intake_guard_ready: true
runtime_evidence_present: false
runtime_evidence_approved: false
runtime_acceptance_complete: false
capture_slot_count: 35
required_runtime_event_count: 70
required_no_tick_precheck_count: 35
required_collapse_commit_count: 35
accepted_slot_count: 0
pending_slot_count: 35
rejected_event_count: 0
duplicate_event_rejection_count: 0
duplicate_proof_hash_rejection_count: 0
duplicate_proof_ref_rejection_count: 0
no_tick_pair_integrity_count: 0
no_tick_pair_failure_count: 0
negative_control_detected_count: 43
negative_control_count: 43
positive_control_passed_count: 6
positive_control_count: 6
positive_controls_fixture_only: true
```

## What It Adds

The R3 capture matrix is a contract. This guard is the enforcement layer.

It rejects final runtime evidence when any event has:

```text
proof.projection=true
missing schema_version
missing timestamp
invalid timestamp
duplicate event_id
missing entity_id
missing entity_type
entity_type mismatch
missing causal_chain_id
missing field.state_before or field.state_after
missing proof_hash
invalid proof_hash format
duplicate proof_hash
duplicate proof_ref
missing proof.native=true
invalid source.format
missing or invalid tension.score
missing or invalid tension.threshold
missing or invalid tension.gate_delta
non-finite tension.score or tension.threshold
unknown original_event_id
missing r3_runtime_slot_id
original event mismatch
R3 runtime slot mismatch
entity mismatch
precheck and commit without shared causal_chain_id
commit timestamp before precheck timestamp
commit authority below H2
commit action mismatch
missing native target rules
unknown heuristic rule
duplicate heuristic rule
precheck that executes instead of suppressing
```

## Required Runtime Pair

Every R3 slot must contain:

```text
1 native no-tick precheck event
1 native collapse commit event
same causal_chain_id
commit timestamp >= precheck timestamp
unique event_id values
unique proof_hash values
unique proof_ref values
known and unique heuristic rules
proof_ref in runtime:<slot-id>:<role> form
proof_hash bound to the event identity payload
source.sanitized=true
gate_delta equal to score - threshold
precheck gate_delta <= 0
commit gate_delta >= 0
event_type matching the slot contract
exactly one precheck and one commit per slot
runtime event count equal to the declared requirement
```

The precheck proves that PNVA can observe and suppress without waking blindly.

The commit proves that PNVA can act with hard-authority heuristics when collapse is justified.

## Negative Controls

The guard runs internal rejection controls before it claims readiness:

```text
reject_projection_true
reject_missing_timestamp
reject_invalid_timestamp
reject_missing_field_state
reject_missing_gate_delta
reject_gate_delta_inconsistent
reject_nonfinite_tension_score
reject_nonfinite_tension_threshold
reject_missing_entity
reject_entity_mismatch
reject_missing_entity_type
reject_entity_type_mismatch
reject_missing_chain
reject_missing_hash
reject_invalid_proof_hash_format
reject_proof_hash_binding_tamper
reject_proof_ref_role_mismatch
reject_low_authority_commit
reject_missing_target_rules
reject_unknown_heuristic_rule
reject_duplicate_heuristic_rule
reject_wrong_action
reject_precheck_event_type_mismatch
reject_commit_event_type_mismatch
reject_precheck_execution_action
reject_precheck_positive_gate_delta
reject_commit_negative_gate_delta
reject_missing_slot_id
reject_slot_id_mismatch
reject_original_event_mismatch
reject_missing_native_proof
reject_invalid_source_format
reject_unsanitized_source
reject_duplicate_event_id
reject_duplicate_proof_hash
reject_duplicate_proof_ref
reject_no_tick_pair_chain_mismatch
reject_commit_before_precheck
reject_invalid_risk_flags
reject_duplicate_risk_flag
reject_unknown_risk_flag
reject_missing_target_risk_flags
reject_precheck_missing_target_risk_flags
```

Current result:

```text
43/43 detected
```

## Positive Controls

The guard also runs fixture-only acceptance controls before it claims intake readiness:

```text
accept_cooldown_gpu_precheck
accept_cooldown_gpu_commit
accept_execute_precheck
accept_execute_commit
accept_resize_batch_precheck
accept_resize_batch_commit
```

Current result:

```text
6/6 accepted
fixture_only: true
runtime_evidence: false
```

## Instrumentation Plan Link

The next layer turns these guard rules into concrete emitter contracts:

```text
docs/PNVA_R3_RUNTIME_INSTRUMENTATION_PLAN.md
reports/pnva-r3-runtime-instrumentation-plan-2026-05-05.json
```

Current result:

```text
R3_RUNTIME_INSTRUMENTATION_PLAN_READY
35 capture slots
3 action contracts
6 event templates
70 required runtime events
26 mandatory event fields
43 negative controls
6 positive controls
```

This keeps the workflow explicit:

```text
capture matrix -> evidence guard -> instrumentation plan -> fresh runtime JSONL -> final guard acceptance
```

## Command

Guard contract only:

```bash
python3 tools/pnva_r3_runtime_evidence_guard.py \
  --write reports/pnva-r3-runtime-evidence-guard-2026-05-05.json
```

Guard fresh runtime evidence:

```bash
python3 tools/pnva_r3_runtime_evidence_guard.py \
  --runtime-events path/to/fresh-runtime-events.jsonl \
  --write /tmp/pnva-r3-runtime-evidence-guard.json
```

## Boundary

This guard does not claim R3 completion without fresh runtime evidence.

It deliberately keeps:

```text
runtime_evidence_present: false
runtime_evidence_approved: false
runtime_acceptance_complete: false
```

That makes PNVA more robust because a future runtime sample must pass a strict intake boundary before the cutover gate can change state.

## Sovereign Rule

Projected evidence can guide engineering, but it cannot become final runtime evidence.

The final R3 runtime package must be native, entity-bound, no-tick paired, H2+ authorized and proof-clean.
