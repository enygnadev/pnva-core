# PNVA Canonical Event Bridge

Author: Gustavo de Aguiar Martins  
Project: PNVA-Core / Enygnalab / EnyOS  
Edition: Open Research / Production Evidence Edition, 2026

## Purpose

The PNVA Canonical Event Bridge converts legacy PNVA laboratory logs into the public `pnva.event.v1` envelope.

It does not change runtime behavior, thresholds, gates or proof status. It is a read-only transformation layer.

## Why This Matters

Research logs naturally evolve. Early PNVA logs use different shapes:

```text
event
kind
payload
seal
decision
pnva_decision
runtime_decision_action
```

That is acceptable in a live lab, but a sovereign architecture needs a canonical contract.

The bridge creates that contract:

```text
legacy JSONL -> sanitized pnva.event.v1 -> entity catalog -> audit-ready report
```

## Public Files

Generated public artifacts:

```text
reports/pnva-canonical-events-sample-2026-05-05.jsonl
reports/pnva-entity-catalog-2026-05-05.json
reports/pnva-canonical-bridge-summary-2026-05-05.json
```

Tool:

```text
tools/pnva_canonical_bridge.py
```

Schema:

```text
schemas/pnva-event.schema.json
schemas/pnva-entity.schema.json
```

## Sanitization Rules

The bridge follows public safety rules:

```text
raw paths are not published
raw job/session IDs are not published
private logs remain private
only file names are shown
IDs are hashed or normalized
canonical proof hashes are derived from sanitized canonical content
```

Allowed public examples:

```text
pnva_decisions.jsonl
zano-entity-00
entity_9ad2a10c30be
chain_021c088f7853
```

Not allowed:

```text
absolute local paths
pool secrets
wallets
tokens
raw session IDs
raw job IDs
```

## Canonical Event Shape

Every converted event has:

```text
schema_version
event_id
timestamp
causal_chain_id
entity_id
entity_type
event_type
field
tension
decision
heuristics
proof
source
```

Guard events may also include:

```text
relations.target_entity_id
relations.relation = guards
```

## Current Bridge Summary

Current sanitized sample:

```text
event_count: 512
entity_count: 6
top decision kind: collapse
dominant action: RESIZE_BATCH
dominant risk flags: RESIZE_BATCH_PRESSURE, THERMAL_PRESSURE, VEONIC_TRACE
```

Interpretation:

The PNVA lab is not randomly executing. It is repeatedly observing pressure, resizing work and preserving conservative no-tick behavior under thermal and veonic heuristic traces.

## Engineering Meaning

The bridge makes it possible to compare old and new PNVA runtimes with the same envelope.

This enables:

```text
cross-version replay
gate regression analysis
entity health analysis
heuristic drift detection
public sanitized proof samples
AI/search-readable evidence
```

## Command

Local lab mode:

```bash
python3 tools/pnva_canonical_bridge.py --limit 512 --limit-per-input 128
```

Public CI/demo mode:

```bash
python3 tools/pnva_canonical_bridge.py --demo \
  --output /tmp/pnva-events.jsonl \
  --entity-catalog /tmp/pnva-entities.json \
  --summary /tmp/pnva-bridge-summary.json
```

## Sovereign Rule

The bridge must never rewrite a legacy event to make it look better. It may normalize structure and sanitize identity, but it must preserve the decision kind, action, event type, risk flags and proof relationship.
