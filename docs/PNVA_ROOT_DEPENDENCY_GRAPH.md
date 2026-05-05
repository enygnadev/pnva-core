# PNVA Root Dependency Graph

Author: Gustavo de Aguiar Martins
Project: PNVA-Core
Edition: Open Research / Production Evidence Edition

## Purpose

The PNVA root dependency graph turns the evidence package into an explicit dependency chain.

It answers a production-review question:

```text
which proof depends on which proof, and can every layer reach the final publication gate without circular validation?
```

## Tool

```text
tools/pnva_root_dependency_graph.py
```

## Report

```text
reports/pnva-root-dependency-graph-2026-05-05.json
```

## Classification

```text
PNVA_ROOT_DEPENDENCY_GRAPH_READY
```

## Current Result

```text
dependency_score: 100.0
check_count: 8
failure_count: 0
node_count: 49
edge_count: 104
phase_count: 11
missing_artifact_count: 0
readiness_failure_count: 0
cycle_count: 0
phase_violation_count: 0
unreachable_node_count: 0
topological_order_count: 49
max_distance_to_publication: 9
root_release_hash: sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc
dependency_graph_hash: sha256:b163111434ae28702917fb66aa71a9a0d0e527092cc64a6da0b72b7d69246f2f
```

## Checks

The graph verifies:

```text
all dependency artifacts exist
all classified reports are ready
the dependency graph is acyclic
dependency phases do not point forward
all nodes reach the root publication gate
the root release seal has the expected root inputs
pre-seal nodes do not depend on post-seal nodes
topological order covers all nodes
```

## Production Interpretation

This layer improves PNVA/no-tick sovereignty because the public package is no longer only a collection of successful gates. It becomes a directed proof graph.

A reviewer can see the chain from public contract, sanitized proof gates, canonical events, native events, no-tick invariants, heuristic/entity ledgers, runtime R3 validation, root guards, release seal, verifier, claim boundary and publication gate.

## Boundary

This validates public repository evidence dependencies only. It does not extend claims beyond the published proof reports and does not validate private deployments.

## Command

```bash
python3 tools/pnva_root_dependency_graph.py \
  --write reports/pnva-root-dependency-graph-2026-05-05.json
```
