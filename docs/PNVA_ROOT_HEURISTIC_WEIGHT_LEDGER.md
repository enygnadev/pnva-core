# PNVA Root Heuristic Weight Ledger

Author: Gustavo de Aguiar Martins
Project: PNVA-Core
Edition: Open Research / Production Evidence Edition

## Purpose

The PNVA root heuristic weight ledger exposes a deterministic public audit layer for heuristic rules.

It converts public evidence into:

```text
rule authority
public evidence weight
proof coverage
no-tick suppression behavior
native/projection status
entity links
governance status
```

## Tool

```text
tools/pnva_root_heuristic_weight_ledger.py
```

## Report

```text
reports/pnva-root-heuristic-weight-ledger-2026-05-05.json
```

## Classification

```text
PNVA_ROOT_HEURISTIC_WEIGHT_LEDGER_READY
```

## Current Result

```text
weight_ledger_score: 100.0
check_count: 9
failure_count: 0
rule_count: 9
ready_rule_count: 8
controlled_legacy_rule_count: 1
blocked_rule_count: 0
total_rule_edge_count: 1350
proof_complete: true
projection_clean: true
root_release_hash: sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc
```

## Public Weight Model

```text
public_weight =
  0.30 * support_norm
+ 0.25 * proof_coverage
+ 0.20 * authority_norm
+ 0.15 * control_norm
+ 0.10 * suppression_balance_norm
```

This weight is not private production tuning. It is a public audit score that summarizes how visible, supported, covered and controlled each rule is in the evidence package.

## Rule Status

```text
PUBLIC_WEIGHT_READY
CONTROLLED_LEGACY
BLOCKED_FOR_RUNTIME_USE
```

Current status:

```text
PUBLIC_WEIGHT_READY: 8
CONTROLLED_LEGACY: 1
BLOCKED_FOR_RUNTIME_USE: 0
```

## Production Interpretation

The ledger makes PNVA heuristics governable. A rule is not just a name in a log; it has authority, proof coverage, public weight, no-tick behavior, entity links and an explicit boundary.

This is the next step for robust no-tick intelligence: every future rule should enter through this ledger before it becomes part of a public claim.

## Boundary

This ledger is an audit layer. It does not publish private tuning, execute system actions, change live gates or validate external deployment behavior.

## Command

```bash
python3 tools/pnva_root_heuristic_weight_ledger.py \
  --write reports/pnva-root-heuristic-weight-ledger-2026-05-05.json
```
