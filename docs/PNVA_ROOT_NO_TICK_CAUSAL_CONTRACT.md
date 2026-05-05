# PNVA Root No-Tick Causal Contract

Author: Gustavo de Aguiar Martins
Project: PNVA-Core
Edition: Open Research / Production Evidence Edition

## Purpose

The PNVA root no-tick causal contract binds event logs, proof hashes, entities, heuristic rules, suppression behavior and threshold decisions into one root-level audit.

It verifies:

```text
event identity
schema and public source safety
proof integrity
entity and rule closure
no-tick suppression consistency
native and R3 threshold discipline
R3 precheck/commit pairing
guard pass/block behavior
bounded canonical legacy exceptions
public boundary cleanliness
```

## Tool

```text
tools/pnva_root_no_tick_causal_contract.py
```

## Report

```text
reports/pnva-root-no-tick-causal-contract-2026-05-05.json
```

## Classification

```text
PNVA_ROOT_NO_TICK_CAUSAL_CONTRACT_READY
```

## Current Result

```text
causal_contract_score: 100.0
check_count: 15
failure_count: 0
event_count: 589
canonical_events: 512
native_events: 7
runtime_r3_events: 70
collapse_count: 303
observe_count: 250
block_count: 35
prove_count: 1
suppressed_count: 285
suppression_ratio: 0.483871
proof_valid_count: 589
projection_event_count: 0
strict_native_r3_event_count: 77
strict_threshold_violation_count: 0
canonical_legacy_threshold_exception_count: 294
r3_chain_count: 35
r3_pair_failure_count: 0
guard_contract_failure_count: 0
unknown_entity_count: 0
unknown_rule_count: 0
root_release_hash: sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc
```

## Contract Rule

Native and R3 runtime evidence must obey the strict threshold contract:

```text
observe or block -> gate_delta <= 0
collapse or prove -> gate_delta > 0
```

Canonical legacy evidence is not forced into that strict rule retroactively. It is accepted only as bounded canonical history when proof coverage is complete, topology has no blocked edges and no native/R3 threshold violation exists.

## Production Interpretation

This contract is stronger than a simple log count. It proves that the no-tick package is not only present, but causally closed:

```text
event -> proof -> entity -> rule -> decision -> suppression/collapse -> boundary
```

The current R3 runtime sample has `35` causal chains, each with one precheck suppression and one commit collapse. That is the clean no-tick pattern for future production: observe without waking unnecessary execution, then collapse only when the runtime cause is committed.

## Boundary

This report audits public evidence only. It does not execute system actions, alter live gates, restart services, change mining workloads or claim universal deployment behavior.

## Command

```bash
python3 tools/pnva_root_no_tick_causal_contract.py \
  --write reports/pnva-root-no-tick-causal-contract-2026-05-05.json
```
