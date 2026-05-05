# PNVA Tension Decision Calibration

Author: Gustavo de Aguiar Martins  
Project: PNVA-Core / Enygnalab / EnyOS  
Edition: Open Research / Production Evidence Edition, 2026

## Objective

This layer validates whether PNVA decisions agree with the tension field that produced them.

It answers a direct no-tick question:

```text
when PNVA collapses, blocks or observes, does the decision match score, threshold and gate_delta?
```

## Current Public Result

Report:

```text
reports/pnva-tension-decision-calibration-2026-05-05.json
```

Current classification:

```text
TENSION_DECISION_READY_WITH_LEGACY_WARNINGS
```

Current result:

```text
event_count: 519
error_count: 0
warning_count: 384
native_calibration_clean: true
legacy_calibration_warning_count: 384
```

## Scope Reading

Canonical legacy bridge:

```text
event_count: 512
error_count: 0
warning_count: 384
LEGACY_COLLAPSE_BELOW_THRESHOLD: 208
LEGACY_OBSERVE_ABOVE_THRESHOLD: 176
```

Native emitter:

```text
event_count: 7
error_count: 0
warning_count: 0
native_calibration_clean: true
```

## Warning Policy

The canonical warnings are preserved as legacy migration evidence.

Meaning:

```text
old converted logs contain decisions whose labels do not always match the reconstructed gate_delta sign
```

This is not hidden and not promoted as a clean native property.

The native path is clean:

```text
collapse -> positive gate_delta
block -> negative gate_delta
observe -> negative gate_delta
prove -> positive proof event
```

## What Is Validated

The calibrator checks:

```text
score
threshold
margin
gate_delta formula
decision.kind
decision.action
decision.reason
collapse vs positive tension
block vs negative tension
observe vs below-threshold tension
ETEV_GUARD_PASS consistency
ETEV_GUARD_BLOCK consistency
native calibration cleanliness
legacy warning counts
```

## Why This Matters

The PNVA claim depends on causal decision, not only event formatting.

Schema validation proves the event has shape.

Tension-decision calibration proves the decision is explainable by the field.

Together:

```text
field -> tension -> threshold -> decision -> proof
```

## Command

```bash
python3 tools/pnva_tension_decision_calibrator.py \
  --write reports/pnva-tension-decision-calibration-2026-05-05.json
```

For CI or temporary validation:

```bash
python3 tools/pnva_tension_decision_calibrator.py \
  --write /tmp/pnva-tension-decision-calibration.json
python3 -m json.tool /tmp/pnva-tension-decision-calibration.json >/dev/null
```

## Production Rule

Native PNVA runtime events must be calibrated.

The following are release-blocking for native evidence:

```text
collapse below threshold
block above threshold
observe above threshold
ETEV guard pass without collapse
ETEV guard block without block
gate_delta formula mismatch
```

Legacy calibration warnings may remain only when they are explicit, counted and not used as clean native claims.
