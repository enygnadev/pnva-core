# PNVA Root Runtime Growth Budget

Author: Gustavo de Aguiar Martins
Project: PNVA-Core
Edition: Open Research / Production Evidence Edition

## Purpose

The PNVA root runtime growth budget defines how root runtime evidence may grow without breaking the no-tick causal contract, proof hashes, entity coverage, heuristic admission, negative controls, regression boundaries or public claim limits.

It turns future growth into a controlled batch process:

```text
current proof state -> restricted growth budget -> next evidence batch
```

## Tool

```text
tools/pnva_root_runtime_growth_budget.py
```

## Report

```text
reports/pnva-root-runtime-growth-budget-2026-05-05.json
```

## Classification

```text
PNVA_ROOT_RUNTIME_GROWTH_BUDGET_READY
```

## Current Result

```text
growth_budget_score: 100.0
check_count: 10
failure_count: 0
event_count: 589
suppressed_count: 285
suppression_ratio: 0.483871
r3_chain_count: 35
entity_rule_edge_count: 38
denied_edge_count: 0
negative_control_count: 8
negative_detected_count: 8
regressed_metric_count: 0
root_release_hash: sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc
```

## Budget Policy

```text
growth_mode: SMALL_BATCH_RESTRICTED
max_new_events_per_batch: 118
max_new_r3_chains_per_batch: 7
max_new_entity_rule_edges_per_batch: 8
min_suppression_ratio: 0.45
max_suppression_ratio: 0.70
max_denied_edges: 0
max_unknown_entities: 0
max_unknown_rules: 0
max_projected_events: 0
max_r3_pair_failures: 0
max_strict_threshold_violations: 0
max_bounded_legacy_edges: 5
min_negative_controls_detected: 8
```

Allowed growth modes:

```text
restricted_native_event_ingest
restricted_r3_precheck_commit
planning_only_evolution
```

Blocked growth modes:

```text
unpaired_r3_runtime_events
projected_runtime_evidence
unknown_entity_or_rule_runtime
unsanitized_log_ingest
private_threshold_publication
hardware_energy_claim_without_counter_benchmark
```

## Checks

The budget requires:

```text
source_reports_ready
baseline_no_tick_budget_locked
runtime_pair_and_threshold_budget_clean
entity_heuristic_growth_budget_clean
admission_modes_match_growth_policy
negative_controls_preserved
governor_and_regression_budget_clean
public_boundary_budget_clean
root_hash_stable
budget_policy_complete
```

## Production Interpretation

This layer makes PNVA growth sovereign at the root level. New evidence is not accepted just because it exists. It must fit the no-tick suppression range, preserve paired R3 proof chains, keep entity-rule edges classified, keep unknown and denied edges at zero, preserve negative-control detection and remain inside public claim boundaries.

The current budget permits small restricted batches only. That makes the next evolution measurable before it becomes part of the public evidence package.

## Boundary

This budget audits public evidence only. It does not execute actions, change live gates, alter mining workloads, publish private thresholds or claim hardware-energy gains without a separate counter benchmark.

## Command

```bash
python3 tools/pnva_root_runtime_growth_budget.py \
  --write reports/pnva-root-runtime-growth-budget-2026-05-05.json
```
