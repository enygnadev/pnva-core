# PNVA Root Release Verifier

Author: Gustavo de Aguiar Martins
Project: PNVA-Core
Edition: Open Research / Production Evidence Edition

## Purpose

The PNVA root release verifier independently recomputes the public root release seal.

The seal creates a citation hash over the final root evidence package. The verifier checks that this citation hash can still be derived from the current public artifacts and that the surrounding release boundary remains honest, complete and reproducible.

## Tool

```text
tools/pnva_root_release_verifier.py
```

## Report

```text
reports/pnva-root-release-verifier-2026-05-05.json
```

## Classification

```text
PNVA_ROOT_RELEASE_VERIFIED
```

## Verification Scope

The verifier checks:

```text
seal report is ready
root release hash recomputes
sealed artifact count matches
sealed artifacts still pass
stable artifact hashes match the seal
artifact classifications match the seal
SHA256SUMS covers sealed artifacts and the seal report
release vector is closed
claim boundaries are present
```

## Current Result

```text
verification_count: 9
failure_count: 0
sealed_artifact_count: 11
checksum_missing_count: 0
checksum_mismatch_count: 0
stable_hash_mismatch_count: 0
classification_mismatch_count: 0
root_release_hash: sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc
```

## Why It Matters

The verifier turns the final release from "a generated seal exists" into "the seal can be recomputed and challenged."

This is the difference between a static claim and a release proof. If a root report, root classification, checksum, runtime slot count, adversarial result, causal score or public claim boundary drifts, the verifier fails.

## Boundary

The verifier consumes the seal and is intentionally outside the seal hash. Including the verifier inside the seal would make the verifier part of the thing it verifies.

The verifier does not claim universal performance improvement, private deployment validation, hardware-level energy gain without separate counters, or any physical particle proof.

## Command

```bash
python3 tools/pnva_root_release_verifier.py \
  --write reports/pnva-root-release-verifier-2026-05-05.json
```
