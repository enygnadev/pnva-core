# PNVA R3 Cutover Gate

Author: Gustavo de Aguiar Martins
Project: PNVA-Core / Enygnalab / EnyOS
Edition: Open Research / Production Evidence Edition, 2026

## Objective

The R3 cutover gate separates two claims that must not be confused:

```text
contract ready != runtime cutover approved
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
R3_CUTOVER_GATE_READY_RUNTIME_REQUIRED
```

Current result:

```text
contract_ready: true
cutover_approved: false
legacy_free_claim_allowed: false
fresh_runtime_evidence_present: false
authority_candidate_count: 35
projected_event_count: 70
projected_precheck_count: 35
projected_commit_count: 35
projected_low_authority_strong_count: 0
remaining_runtime_replacement_count: 35
runtime_blocker_count: 3
contract_score: 100
```

## Why This Matters

Without this gate, a project could accidentally treat projected evidence as final runtime evidence.

PNVA avoids that mistake.

The gate says:

```text
the native replacement contract is valid
the final R3 claim is still blocked
fresh runtime evidence is required
```

## Runtime Requirements

Before `R3_NATIVE_CLEAN_LEGACY_FREE` can be claimed, PNVA must publish:

```text
fresh native runtime events for the mapped authority debt
replay validation over the fresh sample
sovereign policy validation over the fresh sample
no-tick invariant validation over the fresh sample
new robustness, maturity, semantic and reproducibility reports
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
R3_CUTOVER_GATE_READY_RUNTIME_REQUIRED
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
