# PNVA Root Equation Consistency Ledger

Author: Gustavo de Aguiar Martins
Project: PNVA-Core
Edition: Open Research / Production Evidence Edition

## Purpose

The PNVA root equation consistency ledger proves that public no-tick logs preserve the operational tension equation:

```text
gate_delta = score - max(0, threshold - margin)
```

It also proves that native/R3 decisions obey strict threshold semantics:

```text
collapse -> gate_delta >= 0
observe/block -> gate_delta < 0
```

Canonical legacy bridge warnings are retained as bounded evidence, not hidden as clean native runtime behavior.

## Tool

```text
tools/pnva_root_equation_consistency_ledger.py
```

## Report

```text
reports/pnva-root-equation-consistency-ledger-2026-05-05.json
```

## Classification

```text
PNVA_ROOT_EQUATION_CONSISTENCY_LEDGER_READY
```

## Current Result

```text
equation_consistency_score: 100.0
check_count: 9
failure_count: 0
event_count: 589
suppressed_count: 285
collapse_count: 303
prove_count: 1
avoided_action_ratio: 0.483871
formula_mismatch_count: 0
missing_equation_field_count: 0
strict_native_r3_violation_count: 0
canonical_legacy_warning_count: 384
canonical_legacy_threshold_exception_count: 294
entity_binding_count: 13
rule_count: 9
rule_event_edge_count: 1350
path_leak_count: 0
unbounded_high_risk_occurrence_count: 0
root_release_hash: sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc
```

## Checks

The equation consistency ledger requires:

```text
source_reports_ready
event_streams_parse_and_match_root
equation_fields_complete
gate_delta_formula_consistent
native_r3_threshold_semantics_strict
canonical_legacy_exceptions_bounded
equation_supports_efficiency_proof
entity_rule_attribution_closed
public_boundaries_and_root_hash_stable
```

## Production Interpretation

This ledger makes the equation auditable. The no-tick gain is not just a count of avoided actions; it is attached to finite tension values, threshold deltas, entity IDs, heuristic rules, proof hashes and explicit legacy boundaries.

## Boundary

This ledger audits public proof logs only. It does not execute actions, restart live gates, alter mining workloads, expose private thresholds or claim hardware-level measurements.

## Command

```bash
python3 tools/pnva_root_equation_consistency_ledger.py \
  --write reports/pnva-root-equation-consistency-ledger-2026-05-05.json
```
