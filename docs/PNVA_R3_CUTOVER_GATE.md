# PNVA R3 Cutover Gate

Author: Gustavo de Aguiar Martins
Project: PNVA-Core / Enygnalab / EnyOS
Edition: Open Research / Production Evidence Edition, 2026

## Objective

The R3 cutover gate separates two claims that must not be confused:

```text
contract ready + accepted runtime evidence = cutover approved
```

The R3 authority projection proves that the mapped H0 authority debt has a native replacement contract.

The cutover gate decides whether that contract can be promoted into a real legacy-free runtime claim.

## Current Public Result

Report:

```text
reports/pnva-r3-cutover-gate-2026-05-05.json
```

Current classification:

```text
R3_CUTOVER_APPROVED
```

Current result:

```text
contract_ready: true
cutover_approved: true
legacy_free_claim_allowed: true
fresh_runtime_evidence_present: true
authority_candidate_count: 35
projected_event_count: 70
projected_precheck_count: 35
projected_commit_count: 35
projected_low_authority_strong_count: 0
remaining_runtime_replacement_count: 0
runtime_blocker_count: 0
contract_score: 100
```

## Why This Matters

Without this gate, a project could accidentally treat projected evidence as final runtime evidence.

PNVA avoids that mistake.

The gate says:

```text
the native replacement contract is valid
the public R3 runtime sample was accepted
the legacy-free claim is allowed for the slot-bound runtime replacement sample
```

## Runtime Requirements

The approved public runtime package includes:

```text
70 native runtime events for the mapped authority debt
35 no-tick prechecks
35 hard-authority commits
replay, policy, no-tick and proof-chain validation over the sample
semantic consistency and reproducibility over the final package
```

The final runtime sample must not depend on:

```text
proof.projection=true
historical H0 strong authority
bridge-normalized schema warnings
unmapped entity/action debt
```

## Boundary

This gate does not erase historical evidence.

It preserves the existing R2 package honestly while defining the final condition for the next R3 production claim.

## Command

```bash
python3 tools/pnva_r3_cutover_gate.py \
  --write reports/pnva-r3-cutover-gate-2026-05-05.json
```

Expected classification:

```text
R3_CUTOVER_APPROVED
```

## Sovereign Rule

PNVA becomes stronger when it refuses premature victory.

The correct sequence is:

```text
map legacy debt
project native contract
gate the cutover
capture fresh runtime evidence
then claim legacy-free R3
```
