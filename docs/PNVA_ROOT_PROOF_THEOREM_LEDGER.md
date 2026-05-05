# PNVA Root Proof Theorem Ledger

Author: Gustavo de Aguiar Martins
Project: PNVA-Core
Edition: Open Research / Production Evidence Edition

## Purpose

The PNVA root proof theorem ledger converts root PASS reports into explicit theorem cards.

Each theorem card contains:

```text
claim
criteria
evidence
boundary
dependencies
```

This makes the public package easier to audit: a reader can see what was proven, which report supports it, and where the claim stops.

## Tool

```text
tools/pnva_root_proof_theorem_ledger.py
```

## Report

```text
reports/pnva-root-proof-theorem-ledger-2026-05-05.json
```

## Classification

```text
PNVA_ROOT_PROOF_THEOREM_LEDGER_READY
```

## Current Result

```text
theorem_score: 100.0
check_count: 4
failure_count: 0
theorem_count: 12
proven_theorem_count: 12
failed_theorem_count: 0
root_release_hash: sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc
```

## Theorem Set

```text
T1_NO_TICK_SUPPRESSION_OBSERVED
T2_RUNTIME_R3_NATIVE_NON_PROJECTED
T3_ENTITY_CATALOG_COVERAGE
T4_HEURISTIC_VISIBILITY_CLOSED
T5_ROOT_PROOF_CHAIN_ACYCLIC
T6_PUBLIC_CLAIM_BOUNDARY_CLEAN
T7_RELEASE_HASH_VERIFIED
T8_REGRESSION_BASELINE_STABLE
T9_SEMANTIC_REPRODUCIBILITY_CLEAN
T10_ADVERSARIAL_CONTROLS_DETECT_MUTATIONS
T11_TRACEABILITY_SLOT_CLOSURE
T12_CAUSAL_INTELLIGENCE_ALIGNMENT
```

## Production Interpretation

The ledger turns validation into a readable proof layer.

The previous reports answer whether each gate passed.
The theorem ledger answers which technical statements can be cited from those gates.

This is the academic bridge between logs and claims: every strong sentence should point to a theorem ID, and every theorem ID should point to deterministic evidence.

## Boundary

This ledger is a post-seal publication layer over deterministic public evidence. It does not change the root release seal, publish raw local evidence or validate claims outside the repository evidence set.

## Command

```bash
python3 tools/pnva_root_proof_theorem_ledger.py \
  --write reports/pnva-root-proof-theorem-ledger-2026-05-05.json
```
