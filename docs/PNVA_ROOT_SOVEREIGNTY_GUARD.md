# PNVA Root Sovereignty Guard

Author: Gustavo de Aguiar Martins
Project: PNVA-Core / Enygnalab / EnyOS
Edition: Open Research / Production Evidence Edition, 2026

## Objective

The root sovereignty guard is the final repository-level cross-check for the public PNVA evidence package.

It does not replace replay, policy, no-tick, proof-chain, cutover, attestation, semantic consistency, reproducibility or audit. It reads them together and verifies that the root claim is coherent:

```text
runtime events + entities + no-tick pairs + heuristic authority + proof chain + cutover + ledger + attestation + audit -> root readiness
```

## Current Public Result

Report:

```text
reports/pnva-root-sovereignty-guard-2026-05-05.json
```

Expected classification:

```text
PNVA_ROOT_SOVEREIGNTY_GUARD_READY
```

Expected result:

```text
root_score: 100.0
failure_count: 0
event_count: 70
slot_count: 35
entity_count: 1
```

## What It Proves

The guard checks that:

```text
R3 runtime capture has 35 verified slots and zero pending slots
the runtime JSONL has 70 native events
each slot has exactly one no-tick precheck and one collapse commit
precheck and commit share the same causal chain
commit state_before equals precheck state_after
timestamps, JSONL order and source lines move forward
every event is bound to the entity catalog
every proof is native, valid, non-projected and sha256-bound
source filenames are sanitized public basenames
heuristic rules and risk flags are known and non-legacy
strong runtime decisions are H2+ by policy
replay, policy, no-tick, proof-chain, cutover, ledger, attestation, semantic consistency, reproducibility and audit all pass
```

## Boundary

This guard validates the public repository evidence package and deterministic R3 runtime sample.

It does not claim universal proof for private deployments, external miners or environments not represented by the published artifacts.

It is intentionally kept outside the evidence attestation hash seed because it consumes the attestation, audit and reproducibility reports.

## Command

```bash
python3 tools/pnva_root_sovereignty_guard.py \
  --write reports/pnva-root-sovereignty-guard-2026-05-05.json
```

## Sovereign Rule

PNVA root readiness is not a single isolated PASS.

It is a cross-report invariant: no-tick causality, entity identity, heuristic authority, proof integrity, sanitized publication, accepted cutover and reproducible evidence must all agree.
