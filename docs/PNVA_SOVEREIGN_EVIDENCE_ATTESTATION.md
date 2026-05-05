# PNVA Sovereign Evidence Attestation

Author: Gustavo de Aguiar Martins  
Project: PNVA-Core / Enygnalab / EnyOS  
Edition: Open Research / Production Evidence Edition, 2026

This document defines the sovereign evidence attestation layer of PNVA-Core.

PNVA now has many independent evidence layers:

```text
proof gates
canonical bridge
replay validation
no-tick invariants
native event emission
sovereign policy validation
proof-chain sealing
causal graph audit
schema contract validation
causal chronology guard
tension-decision calibration
decision trace index
heuristic influence map
entity no-tick matrix
suppression ledger
sovereign robustness gate
R3 migration plan
authority migration ledger
R3 authority projection
R3 cutover gate
R3 runtime capture matrix
R3 runtime evidence guard
R3 runtime instrumentation plan
adversarial validation
entity and heuristic maturity
sovereign audit
```

The attestation layer binds those artifacts into one machine-readable package.

## Purpose

The goal is to make public PNVA evidence easier to cite, reproduce and verify.

Instead of asking a reviewer to trust scattered files, the attestation lists every core artifact with:

```text
path
kind
sha256
classification
pass/fail status
artifact-specific counters
```

It also computes one aggregate:

```text
evidence_hash
```

## Current Result

Report:

```text
reports/pnva-sovereign-evidence-attestation-2026-05-05.json
```

Current result:

```text
classification: PNVA_SOVEREIGN_EVIDENCE_ATTESTED
pass: true
artifact_count: 39
failure_count: 0
```

## Evidence Hash

The `evidence_hash` changes if any tracked artifact changes its:

```text
sha256
classification
pass flag
```

This turns the public evidence package into a stable citation anchor.

The sovereign audit report is intentionally not part of the attestation hash seed. The audit consumes the attestation; including the audit inside the attestation would create a circular hash dependency.

The semantic consistency guard is also outside this hash seed for the same reason: it consumes the attestation and verifies that all public reports agree after the attestation exists.

The reproducibility guard is outside this hash seed as well. It reruns the current evidence commands, including the attestor, and compares stable fields against the published reports; hashing it into the attestation would also create a circular dependency.

## Boundary

This attestation does not claim universal proof for every PNVA deployment. It attests the integrity and consistency of this public repository evidence package.

## Verification

Run:

```bash
python3 tools/pnva_evidence_attestor.py \
  --write /tmp/pnva-sovereign-evidence-attestation.json
```

Expected classification:

```text
PNVA_SOVEREIGN_EVIDENCE_ATTESTED
```
