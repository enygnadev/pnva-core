# PNVA Sovereign Robustness Gate

Author: Gustavo de Aguiar Martins  
Project: PNVA-Core / Enygnalab / EnyOS  
Edition: Open Research / Production Evidence Edition, 2026

## Objective

The sovereign robustness gate collapses the main PNVA evidence layers into one production-readiness decision.

It checks:

```text
no-tick suppression
decision trace coverage
heuristic influence
entity attribution
proof coverage
native cleanliness
causal integrity
legacy debt containment
adversarial detection
```

## Current Public Result

Report:

```text
reports/pnva-sovereign-robustness-gate-2026-05-05.json
```

Current classification:

```text
SOVEREIGN_ROBUSTNESS_GATE_READY_WITH_LEGACY_WARNINGS
```

Current result:

```text
readiness_level: R2_NATIVE_CLEAN_LEGACY_QUARANTINED
robustness_score: 97 / 100
event_count: 519
suppressed_count: 250
no_tick_suppression_ratio: 0.481696
native_clean_signal_count: 8
native_clean_signal_total: 8
legacy_debt_count: 35
blocker_count: 0
warning_count: 1
hard_authority_ratio: 0.884868
```

## Meaning

This gate makes the production posture explicit:

```text
native path: clean
legacy path: tolerated only as historical migration evidence
new production events: must follow native pnva.event.v1 policy
```

The result is not "legacy-free". It is stronger and more honest:

```text
ready with legacy warnings, because native signals are clean and legacy debt is bounded.
```

## Criteria

The score is composed from:

```text
complete_decision_and_proof_coverage: 15
no_tick_suppression_stability: 15
native_runtime_cleanliness: 20
causal_integrity: 15
authority_governance: 15
legacy_debt_containment: 7 / 10
adversarial_detection: 10
```

The current score is 97 because the native path is clean, but the canonical bridge still preserves legacy warning debt.

## Native Clean Signals

The gate requires all native signals to remain clean:

```text
native_policy_clean
native_trace_clean
native_influence_clean
native_matrix_clean
native_suppression_clean
native_calibration_clean
native_chronology_clean
native_proof_chain_clean
```

Current result:

```text
8 / 8 clean
```

## Migration Targets

The gate turns remaining weaknesses into an explicit backlog:

```text
legacy_observer_h0_strong_decisions: 35
low_authority_strong_influence_edges: 164
above_threshold_suppression_events: 176
legacy_schema_contract_warnings: 341
```

These are not hidden failures. They are the next hardening targets.

## Command

```bash
python3 tools/pnva_sovereign_robustness_gate.py \
  --write reports/pnva-sovereign-robustness-gate-2026-05-05.json
```

For CI or temporary validation:

```bash
python3 tools/pnva_sovereign_robustness_gate.py \
  --write /tmp/pnva-sovereign-robustness-gate.json
python3 -m json.tool /tmp/pnva-sovereign-robustness-gate.json >/dev/null
```

## Production Rule

Future PNVA runtime evidence should keep:

```text
blocker_count = 0
native clean signals = all clean
proof coverage = 1.0
heuristic coverage = 1.0
entity coverage = 1.0
suppression ledger proof coverage = 1.0
```

The next milestone is:

```text
R3_NATIVE_CLEAN_LEGACY_FREE
```

That requires migrating the remaining 35 canonical low-authority strong decisions out of legacy observer authority.
