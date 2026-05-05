# PNVA No-Tick Invariants

Author: Gustavo de Aguiar Martins  
Project: PNVA-Core / Enygnalab / EnyOS  
Edition: Open Research / Production Evidence Edition, 2026

This document defines the no-tick invariant layer of PNVA-Core. It does not replace the already published 15m, 8h, 12h, 24h, G1, distribution and production-candidate proofs. It adds a stricter reading over the canonical event sample: what must remain true for a PNVA runtime to be considered event-aware, auditable and sovereign.

## Purpose

The no-tick claim is not just that fewer actions happened. The stronger claim is that non-actions were also recorded with cause.

In PNVA, an ignored event is not silence. It is a decision:

```text
field observed -> tension measured -> threshold not satisfied -> action suppressed -> proof recorded
```

That is the difference between a naive idle state and a causal no-tick state.

## Invariants

The current public analyzer checks these invariants:

| Invariant | Meaning |
| --- | --- |
| `CANONICAL_SCHEMA_REPLAYED` | The event sequence can be parsed and replay-validated. |
| `PROOF_HASH_STABLE` | Proof hashes match the deterministic replay contract. |
| `NO_TICK_SUPPRESSION_OBSERVED` | Observe/block decisions exist and represent causal suppression. |
| `GUARD_COLLAPSE_BLOCK_CONSISTENT` | ETEV pass/block decisions match their gate deltas. |
| `ENTITY_CATALOG_COVERS_EVENTS` | Every observed event entity is represented in the entity catalog. |
| `HEURISTIC_VISIBILITY_PRESENT` | Heuristic rules and risk flags are visible in the evidence. |
| `PUBLIC_SAFE_EVENT_REFERENCES` | Published event references do not expose raw local paths. |

## Current Public Result

The current public report is:

```text
reports/pnva-no-tick-invariants-2026-05-05.json
```

Current result:

```text
classification: SOVEREIGN_NO_TICK_READY
event_count: 512
collapse_count: 266
observe_count: 213
block_count: 33
suppressed_count: 246
no_tick_suppression_ratio: 0.4805
guard_consistency_ratio: 1.0
proof_integrity_ratio: 1.0
```

Interpretation:

The canonical sample contains both executions and non-executions. The non-executions are not treated as missing work; they are treated as audited causal suppression. This is the operational core of PNVA/no-tick.

## Heuristic Authority Classes

PNVA heuristics are classified by authority level:

| Class | Meaning | Example |
| --- | --- | --- |
| H0 | Observation only | `legacy_observer` |
| H1 | Advisory signal or memory | `veonic_layer`, `memory4d` |
| H2 | Guarded threshold/action | `adaptive_threshold`, `field_scheduler`, `affinity_router`, `power_orchestrator` |
| H3 | Sovereign guard | `etev_guard` |

This prevents heuristic intelligence from becoming opaque authority. A heuristic may suggest, route, block or execute only according to its class and proof context.

## Entity Health

The analyzer derives entity health from canonical events:

```text
entity_id
entity_type
event_count
decision_mix
top_actions
top_rules
risk_flags
block_ratio
risk_flag_density
status
attention
```

Entity health is evidence, not decoration. It shows which actors are active, guarded, pressured or missing catalog coverage.

## Boundary

This layer does not claim universal kernel replacement. It proves a narrower and stronger engineering point:

```text
PNVA can publish a no-tick evidence chain where execution and suppression are both causal, replayable, entity-aware and proof-backed.
```

## Verification

Run:

```bash
python3 tools/pnva_no_tick_invariant_analyzer.py \
  --events reports/pnva-canonical-events-sample-2026-05-05.jsonl \
  --entity-catalog reports/pnva-entity-catalog-2026-05-05.json \
  --replay-report reports/pnva-replay-validation-2026-05-05.json \
  --write /tmp/pnva-no-tick-invariants.json
```

Expected classification:

```text
SOVEREIGN_NO_TICK_READY
```
