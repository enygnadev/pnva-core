# PNVA Causal Graph Audit

Author: Gustavo de Aguiar Martins  
Project: PNVA-Core / Enygnalab / EnyOS  
Edition: Open Research / Production Evidence Edition, 2026

This document defines the causal graph audit layer of PNVA-Core.

After event replay, no-tick invariants, sovereign policy and proof-chain sealing, the next question is structural:

```text
Which entities are connected, and how does causality move through them?
```

## Purpose

PNVA entities should not be isolated labels. A robust no-tick system needs a graph of:

```text
entities
causal chains
guard relations
sequence edges
decision pressure
risk flags
```

The causal graph auditor builds that graph from public event logs and entity catalogs.

## Validation Rules

The auditor checks:

```text
every event entity exists in the catalog
every relation target exists in the catalog
observed entities are connected through relation or chain edges
causal chains have measurable length
graph hash is deterministic
```

## Current Canonical Graph

Report:

```text
reports/pnva-causal-graph-2026-05-05.json
```

Result:

```text
classification: CAUSAL_GRAPH_READY
event_count: 512
catalog_entity_count: 6
observed_entity_count: 6
chain_count: 14
relation_edge_count: 68
chain_edge_count: 230
errors: 0
warnings: 0
```

## Current Native Graph

Report:

```text
reports/pnva-native-causal-graph-2026-05-05.json
```

Result:

```text
classification: CAUSAL_GRAPH_READY
event_count: 7
catalog_entity_count: 6
observed_entity_count: 6
chain_count: 1
relation_edge_count: 2
chain_edge_count: 6
errors: 0
warnings: 0
```

## Graph Hash

Each graph report includes:

```text
graph_hash
```

The graph hash is a stable digest over nodes and edges. It does not replace proof-chain sealing. It complements it:

```text
proof chain = sequence integrity
causal graph = entity/relation topology integrity
```

## Engineering Meaning

This layer makes PNVA more explainable. A reviewer can inspect not only whether events are valid, but how entities participate in causal flow.

## Verification

Run:

```bash
python3 tools/pnva_causal_graph_auditor.py \
  --events reports/pnva-canonical-events-sample-2026-05-05.jsonl \
  --entity-catalog reports/pnva-entity-catalog-2026-05-05.json

python3 tools/pnva_causal_graph_auditor.py \
  --events reports/pnva-native-events-demo-2026-05-05.jsonl \
  --entity-catalog reports/pnva-native-entity-catalog-demo-2026-05-05.json
```

Expected classification:

```text
CAUSAL_GRAPH_READY
```
