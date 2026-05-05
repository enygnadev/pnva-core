# PNVA Root Causal Mesh Ledger

Author: Gustavo de Aguiar Martins
Project: PNVA-Core
Edition: Open Research / Production Evidence Edition

## Purpose

The PNVA root causal mesh ledger proves that the root no-tick logs, entities, heuristics, admission, observability, growth budget and public boundary reports agree as one causal evidence mesh.

The goal is simple:

```text
PASS reports must cross-count each other
```

## Tool

```text
tools/pnva_root_causal_mesh_ledger.py
```

## Report

```text
reports/pnva-root-causal-mesh-ledger-2026-05-05.json
```

## Classification

```text
PNVA_ROOT_CAUSAL_MESH_LEDGER_READY
```

## Current Result

```text
causal_mesh_score: 100.0
check_count: 10
failure_count: 0
event_count: 589
suppressed_count: 285
suppression_ratio: 0.483871
entity_count: 13
rule_count: 9
rule_event_edge_count: 1350
entity_rule_edge_count: 38
r3_chain_count: 35
proof_valid_count: 589
denied_edge_count: 0
unknown_entity_count: 0
unknown_rule_count: 0
manifest_file_count: 252
checksum_count: 251
path_leak_count: 0
unbounded_high_risk_occurrence_count: 0
root_release_hash: sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc
```

## Checks

The mesh requires:

```text
source_reports_ready
no_tick_counts_mesh_agree
entity_counts_mesh_agree
heuristic_counts_mesh_agree
entity_rule_admission_mesh_agree
runtime_r3_mesh_agree
proof_projection_and_negative_controls_clean
public_boundary_mesh_closed
growth_budget_mesh_applied
root_release_hash_mesh_aligned
```

## Mesh Meaning

The ledger verifies that:

```text
589 events match across no-tick, topology, admission, observability, intelligence and growth reports
285 suppressions match across root no-tick reports
13 entities match across topology, capability, admission and observability
9 heuristic rules match across topology, weight ledger, admission and observability
1350 rule-event edges match across topology, weight ledger and admission matrix
38 entity-rule edges match across topology, admission matrix, runtime admission and growth budget
35 R3 chains match across no-tick, runtime admission, observability and growth budget
589 proof hashes are valid
0 denied edges, 0 unknown entities, 0 unknown rules, 0 projected events and 0 public path leaks remain
```

## Production Interpretation

This layer makes the PNVA root more robust because it no longer treats each PASS in isolation. A report can only strengthen the architecture when its counts agree with the other reports that describe the same field.

That gives the system a stronger publication posture: no-tick efficiency, entity governance, heuristic authority, R3 runtime integrity, growth control and public boundary safety are checked as one mesh.

## Boundary

This ledger audits public evidence only. It does not execute actions, change live gates, alter mining workloads or publish private tuning.

## Command

```bash
python3 tools/pnva_root_causal_mesh_ledger.py \
  --write reports/pnva-root-causal-mesh-ledger-2026-05-05.json
```
