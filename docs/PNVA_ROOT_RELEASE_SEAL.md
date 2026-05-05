# PNVA Root Release Seal

Author: Gustavo de Aguiar Martins
Project: PNVA-Core / Enygnalab / EnyOS
Edition: Open Research / Production Evidence Edition, 2026

## Objective

The root release seal creates one citeable hash for the final public PNVA evidence package.

It seals:

```text
root sovereignty guard
root causal intelligence
root traceability matrix
root adversarial sentry
sovereign evolution ledger
R3 cutover gate
R3 runtime evidence guard
semantic consistency
reproducibility
sovereign evidence attestation
sovereign audit
```

## Current Public Result

Report:

```text
reports/pnva-root-release-seal-2026-05-05.json
```

Expected classification:

```text
PNVA_ROOT_RELEASE_SEALED
```

Expected result:

```text
sealed_artifact_count: 11
failure_count: 0
root_score: 100.0
root_causal_intelligence_score: 100.0
root_adversarial_detection_ratio: 8/8
runtime_accepted_slots: 35
runtime_pending_slots: 0
root_release_hash: sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc
```

## Hash Policy

The seal creates:

```text
root_release_hash
```

This hash is separate from:

```text
evidence_hash
```

The evidence hash binds the core public evidence artifacts. The root release hash binds the final root readiness layer that consumes attestation, audit, semantic consistency and reproducibility.

The root release seal is intentionally outside the attestation seed to avoid circular evidence hashing.

## Boundary

This seal allows the public claim:

```text
The public PNVA-Core evidence package is root-sealed for the deterministic R3 runtime sample.
```

It does not claim:

```text
universal performance improvement
private deployment validation
hardware-level energy gain without separate counters
physical particle or physics proof
```

## Command

```bash
python3 tools/pnva_root_release_seal.py \
  --write reports/pnva-root-release-seal-2026-05-05.json
```

## Sovereign Rule

The root seal is the final citation anchor. If any root report, attestation, audit, semantic result, reproducibility result, cutover state or runtime evidence guard changes, the root release hash must change.
