# PNVA Root Sovereign Readiness Gate

Author: Gustavo de Aguiar Martins
Project: PNVA-Core
Edition: Open Research / Production Evidence Edition

## Purpose

The PNVA root sovereign readiness gate collapses the final public proof layer into one machine-readable decision.

It checks whether the root system is coherent across:

```text
no-tick metrics
event identity
proof identity
entity bindings
heuristic rules
runtime admission
growth budget
negative controls
publication hygiene
validator registry
```

## Tool

```text
tools/pnva_root_sovereign_readiness_gate.py
```

## Report

```text
reports/pnva-root-sovereign-readiness-gate-2026-05-05.json
```

## Classification

```text
PNVA_ROOT_SOVEREIGN_READINESS_GATE_PASS
```

## Current Result

```text
readiness_score: 100.0
check_count: 9
failure_count: 0
event_count: 589
suppressed_count: 285
suppression_ratio: 0.483871
avoided_action_count: 285
avoided_action_ratio: 0.483871
efficiency_score: 100.0
collapse_count: 303
observe_count: 250
block_count: 35
prove_count: 1
entity_count: 13
rule_count: 9
rule_event_edge_count: 1350
entity_rule_edge_count: 38
r3_chain_count: 35
proof_valid_count: 589
native_count: 77
projected_event_count: 0
admission_decision: ADMIT_RESTRICTED_ROOT_RUNTIME_PLANNING
growth_mode: SMALL_BATCH_RESTRICTED
negative_detected_count: 8
path_leak_count: 0
unbounded_high_risk_occurrence_count: 0
root_release_hash: sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc
```

## Checks

The readiness gate requires:

```text
source_reports_ready
no_tick_metrics_agree
event_identity_and_proof_ready
entities_and_heuristics_ready
runtime_growth_is_controlled
efficiency_proof_is_attributed
negative_controls_and_firewall_ready
publication_and_claim_boundary_clean
root_release_hash_aligned
```

## Production Interpretation

This is the final root-level gate for public evidence readiness. It proves that the no-tick result is not isolated: the same event count, suppression count, proof count, entity count, rule count, growth policy, negative controls and public boundary rules agree across the repository.

## Boundary

This gate audits public evidence only. It does not execute actions, restart live gates, alter mining workloads, expose private tuning or claim private threshold performance.

## Command

```bash
python3 tools/pnva_root_sovereign_readiness_gate.py \
  --write reports/pnva-root-sovereign-readiness-gate-2026-05-05.json
```
