# PNVA Root Invariant Firewall

Author: Gustavo de Aguiar Martins
Project: PNVA-Core
Edition: Open Research / Production Evidence Edition

## Purpose

The PNVA root invariant firewall blocks regressions across the public PNVA/no-tick evidence package.

It protects:

```text
root classifications
root release hash agreement
no-tick budget
event stream proof identity
entity catalog identity
heuristic authority visibility
runtime R3 contract
dependency graph closure
publication boundaries
semantic consistency
reproducibility
adversarial controls
```

## Tool

```text
tools/pnva_root_invariant_firewall.py
```

## Report

```text
reports/pnva-root-invariant-firewall-2026-05-05.json
```

## Classification

```text
PNVA_ROOT_INVARIANT_FIREWALL_READY
```

## Current Result

```text
firewall_score: 100.0
check_count: 12
failure_count: 0
aggregate_event_count: 589
aggregate_suppressed_count: 285
aggregate_suppression_ratio: 0.483871
event_stream_count: 3
entity_catalog_count: 3
entity_catalog_rows: 13
heuristic_rule_count: 9
influence_edge_count: 1136
runtime_accepted_slots: 35
runtime_pending_slots: 0
runtime_rejected_events: 0
runtime_no_tick_pair_failures: 0
root_dependency_cycles: 0
publication_path_leaks: 0
unbounded_high_risk_claims: 0
root_release_hash: sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc
```

## Checks

The firewall verifies:

```text
required reports are ready
root release hashes agree
no-tick budget is locked
event stream identity is locked
entity catalog contract is locked
heuristic authority visibility is locked
runtime R3 contract is locked
dependency graph is locked
root scores are locked
publication boundary is locked
semantic and reproducibility reports are locked
adversarial controls are locked
```

## Production Interpretation

This layer turns PNVA PASS into a guarded contract. Future changes must preserve:

```text
observable log identity
unique proof hashes
entity identity
heuristic visibility
native runtime cleanliness
no-tick suppression budget
publication hygiene
claim boundaries
```

## Boundary

The firewall validates the public evidence package and deterministic runtime sample. It does not change the root release seal and does not validate external deployments.

## Command

```bash
python3 tools/pnva_root_invariant_firewall.py \
  --write reports/pnva-root-invariant-firewall-2026-05-05.json
```
