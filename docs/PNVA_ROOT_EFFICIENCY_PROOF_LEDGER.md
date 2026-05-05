# PNVA Root Efficiency Proof Ledger

Author: Gustavo de Aguiar Martins
Project: PNVA-Core
Edition: Open Research / Production Evidence Edition

## Purpose

The PNVA root efficiency proof ledger quantifies no-tick efficiency as proof-backed causal non-execution.

It uses a public event baseline:

```text
baseline event actions = all public events
PNVA avoided actions = observe + block decisions with valid proof
PNVA required actions = collapse + proof-only decisions
```

This is an engineering metric. It does not claim universal speedup, hardware counters or private deployment performance.

## Tool

```text
tools/pnva_root_efficiency_proof_ledger.py
```

## Report

```text
reports/pnva-root-efficiency-proof-ledger-2026-05-05.json
```

## Classification

```text
PNVA_ROOT_EFFICIENCY_PROOF_LEDGER_READY
```

## Current Result

```text
efficiency_score: 100.0
check_count: 9
failure_count: 0
event_count: 589
baseline_event_action_count: 589
collapse_count: 303
suppressed_count: 285
prove_count: 1
observed_required_action_count: 304
avoided_action_count: 285
avoided_action_ratio: 0.483871
causal_execution_ratio: 0.514431
entity_row_count: 13
rule_row_count: 9
rule_event_edge_count: 1350
native_count: 77
projected_event_count: 0
strict_threshold_violation_count: 0
suppressed_proof_failure_count: 0
path_leak_count: 0
unbounded_high_risk_occurrence_count: 0
root_release_hash: sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc
```

## Checks

The efficiency proof ledger requires:

```text
source_reports_ready
event_streams_parse_and_match_root
suppression_gain_matches_no_tick
suppressed_actions_are_proof_backed
strict_native_r3_threshold_gain_clean
entity_efficiency_attribution_complete
heuristic_efficiency_attribution_complete
growth_and_negative_controls_preserve_efficiency
public_boundaries_and_root_hash_stable
```

## Production Interpretation

This ledger makes the efficiency claim defendable. The gain is not asserted by narrative; it is derived from public event logs and then attributed to entities and heuristic rules.

The current public result means:

```text
589 public events were analyzed
285 actions were causally suppressed
285 suppressions have proof
13 entity rows carry the attribution
9 heuristic rules carry the attribution
0 projected events entered the proof
0 public path leaks remain
```

## Boundary

This ledger audits public proof logs only. It does not execute actions, restart live gates, alter mining workloads, expose private tuning or claim hardware-level measurements.

## Command

```bash
python3 tools/pnva_root_efficiency_proof_ledger.py \
  --write reports/pnva-root-efficiency-proof-ledger-2026-05-05.json
```
