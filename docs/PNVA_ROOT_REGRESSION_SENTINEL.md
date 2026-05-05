# PNVA Root Regression Sentinel

Author: Gustavo de Aguiar Martins
Project: PNVA-Core
Edition: Open Research / Production Evidence Edition

## Purpose

The PNVA root regression sentinel watches for metric drift after the invariant firewall passes.

It protects the current root baseline:

```text
no-tick suppression budget
event stream counts
unique proof hashes
entity catalog coverage
heuristic coverage
runtime R3 slot acceptance
publication hygiene
claim boundaries
semantic consistency
reproducibility
root release hash stability
```

## Tool

```text
tools/pnva_root_regression_sentinel.py
```

## Report

```text
reports/pnva-root-regression-sentinel-2026-05-05.json
```

## Classification

```text
PNVA_ROOT_REGRESSION_SENTINEL_READY
```

## Current Result

```text
regression_score: 100.0
check_count: 5
failure_count: 0
monitored_metric_count: 36
stable_metric_count: 36
regressed_metric_count: 0
aggregate_event_count_min: 589
aggregate_suppressed_count_min: 285
aggregate_suppression_ratio_range: 0.45..0.70
runtime_r3_event_count_min: 70
runtime_r3_projected_count_max: 0
entity_catalog_rows_min: 13
heuristic_rule_count_min: 9
runtime_accepted_slot_count_min: 35
publication_path_leak_count_max: 0
unbounded_high_risk_occurrence_count_max: 0
root_release_hash: sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc
```

## Checks

The sentinel verifies:

```text
baseline classifications are stable
root hash is stable
regression metrics are stable
firewall remains clean
public hygiene remains clean
```

## Production Interpretation

The firewall answers whether the package is valid now.
The regression sentinel answers whether future edits degraded the root baseline.

Future PNVA changes should improve the system without reducing proof identity, no-tick budget, entity coverage, heuristic coverage or publication hygiene.

## Boundary

This sentinel tracks the public evidence package and deterministic runtime sample. It does not change the root release seal.

## Command

```bash
python3 tools/pnva_root_regression_sentinel.py \
  --write reports/pnva-root-regression-sentinel-2026-05-05.json
```
