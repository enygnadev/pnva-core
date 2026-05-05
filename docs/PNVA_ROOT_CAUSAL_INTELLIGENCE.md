# PNVA Root Causal Intelligence

Author: Gustavo de Aguiar Martins
Project: PNVA-Core / Enygnalab / EnyOS
Edition: Open Research / Production Evidence Edition, 2026

## Objective

Root causal intelligence turns the PNVA evidence package into a deterministic score over:

```text
no-tick efficiency
runtime slot closure
entity coverage
heuristic authority
proof integrity
publication hygiene
controlled legacy context
```

It is not a black-box AI layer and not a claim about private deployments. It is a reproducible analyzer over public reports.

## Current Public Result

Report:

```text
reports/pnva-root-causal-intelligence-2026-05-05.json
```

Expected classification:

```text
PNVA_ROOT_CAUSAL_INTELLIGENCE_READY
```

Expected result:

```text
root_causal_intelligence_score: 100.0
failure_count: 0
no_tick_event_count: 589
no_tick_suppressed_count: 285
runtime_verified_slots: 35
runtime_pending_slots: 0
```

## What It Measures

The analyzer reads canonical, native-demo and R3 runtime no-tick reports and then adds root runtime checks:

```text
512 canonical no-tick events
7 native-demo no-tick events
70 R3 runtime no-tick events
285 total proof-backed suppressions
35 R3 runtime no-tick pairs
35 R3 runtime collapse commits
0 runtime low-authority legacy decisions
0 runtime projected proofs
0 public path leaks
```

## Honest Boundary

Historical canonical warnings are not deleted. They remain controlled migration context.

The accepted R3 runtime path is measured separately:

```text
native pnva.event.v1
proof.native=true
proof.projection=false
H2 runtime authority
entity-bound
same-chain no-tick precheck + commit
```

## Command

```bash
python3 tools/pnva_root_causal_intelligence.py \
  --write reports/pnva-root-causal-intelligence-2026-05-05.json
```

## Sovereign Rule

PNVA intelligence is not magic. It is a deterministic measurement of causal execution, avoided execution, entity identity, heuristic authority and proof quality.
