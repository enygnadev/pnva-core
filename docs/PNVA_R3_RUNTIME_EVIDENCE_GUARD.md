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
negative_control_detected_count: 10
negative_control_count: 10
```

## What It Adds

The R3 capture matrix is a contract. This guard is the enforcement layer.

It rejects final runtime evidence when any event has:

```text
proof.projection=true
missing schema_version
missing entity_id
missing causal_chain_id
missing proof_hash
missing proof.native=true
invalid source.format
unknown original_event_id
missing r3_runtime_slot_id
entity mismatch
commit authority below H2
commit action mismatch
missing native target rules
precheck that executes instead of suppressing
```

## Required Runtime Pair

Every R3 slot must contain:

```text
1 native no-tick precheck event
1 native collapse commit event
```

The precheck proves that PNVA can observe and suppress without waking blindly.

The commit proves that PNVA can act with hard-authority heuristics when collapse is justified.

## Negative Controls

The guard runs internal rejection controls before it claims readiness:

```text
reject_projection_true
reject_missing_entity
reject_missing_chain
reject_missing_hash
reject_low_authority_commit
reject_wrong_action
reject_precheck_execution_action
reject_missing_slot_id
reject_missing_native_proof
reject_invalid_source_format
```

Current result:

```text
10/10 detected
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
21 mandatory event fields
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
