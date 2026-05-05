# PNVA Root Runtime Admission Controller

Author: Gustavo de Aguiar Martins
Project: PNVA-Core
Edition: Open Research / Production Evidence Edition

## Purpose

The PNVA root runtime admission controller turns the current proof state into an explicit decision about what can enter the root runtime evidence path.

It does not start, stop or alter services. It audits public evidence and emits a machine-readable admission decision.

## Tool

```text
tools/pnva_root_runtime_admission_controller.py
```

## Report

```text
reports/pnva-root-runtime-admission-controller-2026-05-05.json
```

## Classification

```text
PNVA_ROOT_RUNTIME_ADMISSION_READY
```

## Current Result

```text
runtime_admission_score: 100.0
check_count: 10
failure_count: 0
admission_decision: ADMIT_RESTRICTED_ROOT_RUNTIME_PLANNING
event_count: 589
suppressed_count: 285
suppression_ratio: 0.483871
strict_threshold_violation_count: 0
r3_chain_count: 35
r3_pair_failure_count: 0
entity_row_count: 13
blocked_entity_count: 0
rule_count: 9
blocked_rule_count: 0
entity_rule_edge_count: 38
blocked_edge_count: 0
controlled_debt_count: 5
safe_to_plan_count: 8
regressed_metric_count: 0
path_leak_count: 0
unbounded_high_risk_occurrence_count: 0
root_release_hash: sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc
```

## Allowed Modes

```text
audit_only
observe
simulate
restricted_native_event_ingest
restricted_r3_precheck_commit
planning_only_evolution
```

## Denied Modes

```text
unbounded_public_claims
unsanitized_log_ingest
private_threshold_publication
unpaired_r3_runtime_events
projected_runtime_evidence
unknown_entity_or_rule_runtime
hardware_energy_claim_without_counter_benchmark
```

## Production Interpretation

The controller makes PNVA more sovereign because future expansion is no longer informal. A new runtime event, entity or heuristic must pass through explicit gates:

```text
no-tick contract
field topology
entity capability
heuristic weight
locked invariants
regression sentinel
claim boundary
publication hygiene
root hash stability
```

The current decision admits only restricted root runtime planning and evidence ingestion. That is the correct production posture: expand by proof, not by assumption.

## Boundary

This controller audits public evidence only. It does not execute actions, start services, stop services, change mining workloads, alter live gates or claim external deployment behavior.

## Command

```bash
python3 tools/pnva_root_runtime_admission_controller.py \
  --write reports/pnva-root-runtime-admission-controller-2026-05-05.json
```
