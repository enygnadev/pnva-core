# PNVA Root Claim Boundary Guard

Author: Gustavo de Aguiar Martins
Project: PNVA-Core
Edition: Open Research / Production Evidence Edition

## Purpose

The PNVA root claim boundary guard validates the public language around PNVA-Core.

The technical package is stronger when it proves not only what passed, but also what is not being claimed.

## Tool

```text
tools/pnva_root_claim_boundary_guard.py
```

## Report

```text
reports/pnva-root-claim-boundary-guard-2026-05-05.json
```

## Classification

```text
PNVA_ROOT_CLAIM_BOUNDARY_GUARD_READY
```

## Current Result

```text
claim_boundary_score: 100.0
check_count: 7
failure_count: 0
scanned_file_count: 68
high_risk_occurrence_count: 44
unbounded_high_risk_occurrence_count: 0
root_release_hash: sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc
```

## What It Checks

The guard verifies:

```text
root seal claim boundaries are present
root verifier confirmed claim boundaries
required boundary files exist
required boundary phrases are present
high-risk claim phrases are bounded by explicit limitation language
public data policy blocks raw logs, sensitive paths and private tuning
old root release hashes are not left in public text
```

## Boundary

This guard is intentionally outside the root release seal.

The root release seal proves the evidence package. The claim boundary guard checks post-seal public language before posting, publishing or indexing.

## Command

```bash
python3 tools/pnva_root_claim_boundary_guard.py \
  --write reports/pnva-root-claim-boundary-guard-2026-05-05.json
```
