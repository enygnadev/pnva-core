# PNVA Root Event Identity Ledger

Author: Gustavo de Aguiar Martins
Project: PNVA-Core
Edition: Open Research / Production Evidence Edition

## Purpose

The PNVA root event identity ledger proves that the public root event streams have stable event identity, proof identity, entity binding, heuristic-rule binding and R3 precheck/commit shape.

The goal is to make every event answer:

```text
which event?
which proof hash?
which entity?
which heuristic rules?
which decision?
which causal chain?
```

## Tool

```text
tools/pnva_root_event_identity_ledger.py
```

## Report

```text
reports/pnva-root-event-identity-ledger-2026-05-05.json
```

## Classification

```text
PNVA_ROOT_EVENT_IDENTITY_LEDGER_READY
```

## Current Result

```text
event_identity_score: 100.0
check_count: 10
failure_count: 0
event_count: 589
event_id_count: 589
unique_event_id_count: 589
proof_hash_count: 589
unique_proof_hash_count: 589
entity_binding_count: 13
rule_count: 9
rule_event_edge_count: 1350
r3_chain_count: 35
r3_pair_failure_count: 0
native_count: 77
projected_event_count: 0
path_leak_count: 0
unbounded_high_risk_occurrence_count: 0
root_release_hash: sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc
```

## Checks

The event identity ledger requires:

```text
source_reports_ready
event_streams_parse_and_count
event_and_proof_identity_unique
entity_binding_complete
heuristic_rule_identity_bound
decision_and_tension_contract
proof_policy_clean
r3_chain_shape_clean
public_surface_current
root_hash_aligned
```

## Production Interpretation

This layer protects no-tick evidence at the log level. It proves that the public event streams are not relying on duplicated event IDs, duplicated proof hashes, orphaned entities, unknown rules, missing core fields, projected evidence or malformed R3 chains.

## Boundary

This ledger audits public event identity only. It does not execute actions, change live gates, alter mining workloads or publish private tuning.

## Command

```bash
python3 tools/pnva_root_event_identity_ledger.py \
  --write reports/pnva-root-event-identity-ledger-2026-05-05.json
```
