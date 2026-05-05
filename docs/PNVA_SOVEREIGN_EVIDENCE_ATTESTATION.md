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
artifact_count: 19
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
