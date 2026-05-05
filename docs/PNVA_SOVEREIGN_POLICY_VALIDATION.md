# PNVA Sovereign Policy Validation

Author: Gustavo de Aguiar Martins  
Project: PNVA-Core / Enygnalab / EnyOS  
Edition: Open Research / Production Evidence Edition, 2026

This document defines the sovereign policy layer of PNVA-Core.

The purpose is to validate not only whether an event is well-formed, replayable and proof-backed, but whether the decision had enough heuristic authority to act.

## Why This Layer Exists

A no-tick runtime is dangerous if every weak signal can collapse into action.

PNVA must distinguish:

```text
observation
advisory signal
guarded action
sovereign guard
reclassification
```

This is how PNVA stays auditable instead of becoming a black box.

## Authority Classes

| Class | Meaning | Example |
| --- | --- | --- |
| H0 | Observation only | `legacy_observer` |
| H1 | Advisory signal or memory | `veonic_layer`, `memory4d` |
| H2 | Guarded runtime authority | `native_event_emitter`, `adaptive_threshold`, `field_scheduler`, `affinity_router`, `power_orchestrator` |
| H3 | Sovereign guard authority | `etev_guard` |
| H4 | Reclassification authority | reserved for future explicit reclassification criteria |

## Strong Decisions

The validator treats these as strong decisions:

```text
collapse
block
prove
reclassify
```

Every strong decision must have:

```text
valid proof_hash
proof_ref
entity_id in entity catalog
H2/H3/H4 authority, or legacy warning when legacy_tolerant is enabled
```

Every `ETEV_GUARD_PASS` and `ETEV_GUARD_BLOCK` event must include `etev_guard`.

## Current Canonical Result

Report:

```text
reports/pnva-sovereign-policy-2026-05-05.json
```

Result:

```text
classification: SOVEREIGN_POLICY_READY_WITH_LEGACY_WARNINGS
pass: true
event_count: 512
strong_decision_count: 299
low_authority_legacy_count: 35
errors: 0
warnings: 35
```

Interpretation:

The canonical sample is policy-valid, but it preserves a legacy weakness honestly: 35 strong decisions came from low-authority legacy observer records. They are tolerated because this is historical evidence converted through the bridge, not native runtime emission.

## Current Native Result

Report:

```text
reports/pnva-native-sovereign-policy-2026-05-05.json
```

Result:

```text
classification: SOVEREIGN_POLICY_READY
pass: true
event_count: 7
strong_decision_count: 5
low_authority_legacy_count: 0
errors: 0
warnings: 0
```

Interpretation:

The native emitter is clean: strong decisions carry sufficient H2/H3 authority from birth.

## Engineering Meaning

The bridge proves that legacy evidence can be preserved.

The native emitter proves that future evidence can be born clean.

The sovereign policy validator proves which events are production-grade and which ones remain legacy-tolerated.

## Verification

Run:

```bash
python3 tools/pnva_sovereign_policy_validator.py \
  --events reports/pnva-canonical-events-sample-2026-05-05.jsonl \
  --entity-catalog reports/pnva-entity-catalog-2026-05-05.json

python3 tools/pnva_sovereign_policy_validator.py \
  --events reports/pnva-native-events-demo-2026-05-05.jsonl \
  --entity-catalog reports/pnva-native-entity-catalog-demo-2026-05-05.json
```

Expected classifications:

```text
SOVEREIGN_POLICY_READY_WITH_LEGACY_WARNINGS
SOVEREIGN_POLICY_READY
```
