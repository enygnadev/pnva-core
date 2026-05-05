# PNVA Root Legacy Quarantine Ledger

Author: Gustavo de Aguiar Martins
Project: PNVA-Core
Edition: Open Research / Production Evidence Edition

## Purpose

The PNVA root legacy quarantine ledger keeps canonical legacy warnings visible, measured and separated from clean native/R3 runtime evidence.

The goal is not to hide legacy debt. The goal is to prevent it from contaminating production claims.

## Tool

```text
tools/pnva_root_legacy_quarantine_ledger.py
```

## Report

```text
reports/pnva-root-legacy-quarantine-ledger-2026-05-05.json
```

## Classification

```text
PNVA_ROOT_LEGACY_QUARANTINE_LEDGER_READY
```

## Current Result

```text
legacy_quarantine_score: 100.0
check_count: 9
failure_count: 0
event_count: 589
legacy_warning_count: 384
canonical_legacy_warning_count: 384
native_legacy_warning_count: 0
runtime_r3_legacy_warning_count: 0
canonical_legacy_threshold_exception_count: 294
legacy_decision_counts: collapse=208, observe=176
legacy_entity_count: 4
legacy_rule_count: 7
bounded_legacy_edge_count: 5
controlled_legacy_rule_count: 1
denied_edge_count: 0
unknown_entity_count: 0
unknown_rule_count: 0
strict_native_r3_violation_count: 0
projected_event_count: 0
path_leak_count: 0
unbounded_high_risk_occurrence_count: 0
root_release_hash: sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc
```

## Checks

The legacy quarantine ledger requires:

```text
source_reports_ready
event_streams_parse_clean
legacy_warnings_are_canonical_only
legacy_warning_counts_match_equation_and_calibration
legacy_decision_mix_bounded
legacy_entity_rule_attribution_visible
admission_keeps_legacy_bounded
clean_runtime_path_preserves_efficiency
public_boundaries_and_root_hash_stable
```

## Production Interpretation

This ledger makes the boundary honest:

```text
canonical bridge warnings are preserved
native/R3 runtime path remains strict
legacy entities and rules are attributed
legacy edges are bounded
production claims must use the clean native/R3 path
```

## Boundary

This ledger audits public evidence only. It does not execute actions, restart live gates, alter mining workloads, rewrite legacy logs, expose private thresholds or claim hardware-level measurements.

## Command

```bash
python3 tools/pnva_root_legacy_quarantine_ledger.py \
  --write reports/pnva-root-legacy-quarantine-ledger-2026-05-05.json
```
