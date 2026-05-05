# PNVA Semantic Consistency Guard

Author: Gustavo de Aguiar Martins  
Project: PNVA-Core / Enygnalab / EnyOS  
Edition: Open Research / Production Evidence Edition, 2026

## Objective

This layer checks whether the public PNVA evidence package is internally consistent.

The goal is simple:

```text
if one report says 512 events, every dependent report must agree
if the Manifest publishes an evidence hash, it must match the attestation
if maturity claims 250 suppressions, it must equal canonical + native no-tick suppression
```

This makes PNVA harder to break by documentation drift.

## Why This Exists

PNVA-Core now has multiple independent validators:

```text
replay
no-tick invariants
policy
proof chain
causal graph
schema contract validation
causal chronology guard
adversarial validation
entity and heuristic maturity
evidence attestation
sovereign audit
```

Each validator proves a different property. The semantic consistency guard proves that those properties still agree after publication.

## Current Public Result

Report:

```text
reports/pnva-semantic-consistency-2026-05-05.json
```

Current classification:

```text
SEMANTIC_CONSISTENCY_READY
```

Current result:

```text
check_count: 83
error_count: 0
warning_count: 0
```

## What It Checks

The guard compares:

```text
Manifest summary vs source reports
canonical bridge vs replay/no-tick/policy/graph/proof-chain
native emitter vs native no-tick/policy/graph/proof-chain
schema contract report vs Manifest and attestation
causal chronology report vs Manifest and attestation
maturity aggregate math vs canonical + native reports
attestation artifact count vs artifact list
audit summary vs attestation and maturity report
Manifest file list vs files on disk
```

Examples:

```text
512 canonical events must match bridge, replay, no-tick, policy, graph and proof-chain.
7 native events must match native emitter, native no-tick, native policy, native graph and native proof-chain.
250 total suppressions must equal 246 canonical suppressions + 4 native suppressions.
304 strong decisions must equal 299 canonical + 5 native.
269 hard-authority strong decisions must equal 304 - 35 legacy low-authority warnings.
```

## Attestation Boundary

This guard is intentionally kept outside the evidence attestation hash seed.

Reason:

```text
the consistency guard consumes the attestation
the attestation must not hash a report that depends on the attestation
```

This avoids circular evidence hashing.

## Command

```bash
python3 tools/pnva_semantic_consistency_guard.py \
  --write reports/pnva-semantic-consistency-2026-05-05.json
```

For CI or temporary validation:

```bash
python3 tools/pnva_semantic_consistency_guard.py \
  --write /tmp/pnva-semantic-consistency.json
python3 -m json.tool /tmp/pnva-semantic-consistency.json >/dev/null
```

## Sovereign Rule

PNVA evidence should not merely pass in isolated files.

It should agree as a system:

```text
same event counts
same suppression counts
same authority counts
same graph counts
same evidence hash
same publication metadata
```

That is the difference between many reports and one coherent evidence package.
