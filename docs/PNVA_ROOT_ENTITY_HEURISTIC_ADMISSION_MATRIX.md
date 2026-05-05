# PNVA Root Entity-Heuristic Admission Matrix

Author: Gustavo de Aguiar Martins
Project: PNVA-Core
Edition: Open Research / Production Evidence Edition

## Purpose

The PNVA root entity-heuristic admission matrix maps every observed entity-rule edge into an explicit admission class.

It answers:

```text
which entity can use which heuristic?
which edges are R3-restricted?
which edges are native-restricted?
which edges are canonical evidence only?
which edges are legacy-bounded?
which edges are denied?
```

## Tool

```text
tools/pnva_root_entity_heuristic_admission_matrix.py
```

## Report

```text
reports/pnva-root-entity-heuristic-admission-matrix-2026-05-05.json
```

## Classification

```text
PNVA_ROOT_ENTITY_HEURISTIC_ADMISSION_MATRIX_READY
```

## Current Result

```text
admission_matrix_score: 100.0
check_count: 11
failure_count: 0
event_count: 589
rule_event_edge_count: 1350
entity_rule_edge_count: 38
admitted_r3_edge_count: 4
admitted_native_edge_count: 12
controlled_canonical_edge_count: 17
bounded_legacy_edge_count: 5
denied_edge_count: 0
unknown_entity_count: 0
unknown_rule_count: 0
root_release_hash: sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc
```

## Admission Status Counts

```text
ADMIT_R3_RESTRICTED: 4
ADMIT_NATIVE_RESTRICTED: 12
CONTROLLED_CANONICAL_EVIDENCE: 17
BOUND_CANONICAL_LEGACY: 4
OBSERVE_NATIVE_LEGACY_ONLY: 1
DENY_EDGE: 0
```

## Production Interpretation

This matrix makes entity and heuristic expansion explicit. A new runtime edge cannot enter production evidence by name alone; it must land in one of the admitted or bounded classes:

```text
entity readiness + rule weight + proof coverage + topology + runtime admission -> edge admission status
```

The current matrix admits R3 and native edges only in restricted modes. Canonical edges remain evidence-only. Legacy edges remain bounded and projection-free. Unknown or unproved edges are denied.

## Boundary

This matrix audits public evidence only. It does not execute runtime actions, change live gates, alter mining workloads or publish private tuning.

## Command

```bash
python3 tools/pnva_root_entity_heuristic_admission_matrix.py \
  --write reports/pnva-root-entity-heuristic-admission-matrix-2026-05-05.json
```
