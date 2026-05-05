# PNVA Root Field Topology Ledger

Author: Gustavo de Aguiar Martins
Project: PNVA-Core
Edition: Open Research / Production Evidence Edition

## Purpose

The PNVA root field topology ledger exposes the audit graph that connects entities, heuristic rules and no-tick decisions.

It answers:

```text
which entities are present?
which rules govern them?
which decisions were produced?
which edges are R3-ready, native-ready, controlled canonical or controlled legacy?
which edges must be blocked before runtime use?
```

## Tool

```text
tools/pnva_root_field_topology_ledger.py
```

## Report

```text
reports/pnva-root-field-topology-ledger-2026-05-05.json
```

## Classification

```text
PNVA_ROOT_FIELD_TOPOLOGY_LEDGER_READY
```

## Current Result

```text
field_topology_score: 100.0
check_count: 13
failure_count: 0
entity_node_count: 13
rule_node_count: 9
event_count: 589
rule_event_edge_count: 1350
entity_rule_edge_count: 38
entity_decision_edge_count: 17
rule_decision_edge_count: 20
topology_density: 0.324786
r3_edge_count: 4
legacy_edge_count: 5
blocked_edge_count: 0
orphan_entity_count: 0
orphan_rule_count: 0
unruled_event_count: 0
unknown_entity_event_count: 0
root_release_hash: sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc
```

## Edge Status

```text
R3_READY_EDGE: runtime R3 entity linked to public-ready rules with proof coverage
NATIVE_READY_EDGE: native evidence linked to public-ready or bounded legacy rules
CONTROLLED_CANONICAL_EDGE: canonical evidence linked to controlled public rules
CONTROLLED_LEGACY_EDGE: legacy rule relation kept bounded and projection-free
BLOCKED: edge with projection leakage, missing proof coverage or unsafe status
```

Current edge status counts:

```text
R3_READY_EDGE: 4
NATIVE_READY_EDGE: 13
CONTROLLED_CANONICAL_EDGE: 17
CONTROLLED_LEGACY_EDGE: 4
BLOCKED: 0
```

## Production Interpretation

The topology ledger makes the PNVA field governable as a graph. Entities, heuristic rules and decisions are no longer isolated reports; they become linked evidence.

This strengthens no-tick production because every runtime expansion can be checked against visible topology:

```text
entity -> rule -> decision -> proof -> boundary
```

The current graph has no orphan entities, no orphan rules, no unruled events, no unknown entity events and no blocked edges. Legacy context exists only as bounded evidence and has no R3 runtime leak.

## Boundary

This ledger is an audit graph over public evidence. It does not execute system actions, alter live gates, restart services, change mining workloads or claim external deployment behavior.

## Command

```bash
python3 tools/pnva_root_field_topology_ledger.py \
  --write reports/pnva-root-field-topology-ledger-2026-05-05.json
```
