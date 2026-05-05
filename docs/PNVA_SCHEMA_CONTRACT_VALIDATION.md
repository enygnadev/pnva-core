# PNVA Schema Contract Validation

Author: Gustavo de Aguiar Martins  
Project: PNVA-Core / Enygnalab / EnyOS  
Edition: Open Research / Production Evidence Edition, 2026

## Objective

This layer validates whether public PNVA event logs and entity catalogs obey the canonical contract.

It answers a direct release question:

```text
are public pnva.event.v1 and pnva.entity.v1 records structurally safe enough to cite?
```

## Current Public Result

Report:

```text
reports/pnva-schema-contract-validation-2026-05-05.json
```

Current classification:

```text
SCHEMA_CONTRACT_READY_WITH_LEGACY_WARNINGS
```

Current result:

```text
event_count: 519
entity_count: 12
relation_count: 70
heuristic_rule_count: 9
error_count: 0
warning_count: 341
```

## What Is Validated

The validator checks both public evidence scopes:

```text
canonical legacy bridge sample
native runtime emitter sample
```

For events, it validates:

```text
schema_version
event_id
timestamp
causal_chain_id
entity_id
entity catalog membership
field states
tension score, threshold, margin and gate_delta
decision kind, action, reason and confidence
heuristic rules and risk flags
proof hash, proof reference and validity
relations and target entity IDs
sanitized public source
forbidden public marker absence
```

For entities, it validates:

```text
schema_version
entity_id uniqueness
entity_type
sovereignty_domain
state
capabilities
evidence proof_ref
confidence range
last_seen shape
entity_count agreement
forbidden public marker absence
```

## Reading The Warnings

The current warnings are legacy warnings from the canonical bridge:

```text
EVENT_ENTITY_TYPE_DIFFERS_FROM_CATALOG
```

Meaning:

```text
some legacy-derived events expose an event-local entity_type that differs from the catalog's consolidated entity_type
```

This is not hidden and not promoted to a clean native claim. It is preserved as evidence of legacy log migration.

The native emitter scope is clean:

```text
native error_count: 0
native warning_count: 0
```

## Why This Matters

Replay proves deterministic sequence validity.

Policy proves authority.

Graph audit proves topology.

Schema contract validation proves the public evidence has a stable structural envelope.

Together:

```text
contract -> replay -> policy -> graph -> seal -> attestation
```

## Command

```bash
python3 tools/pnva_schema_contract_validator.py \
  --write reports/pnva-schema-contract-validation-2026-05-05.json
```

For CI or temporary validation:

```bash
python3 tools/pnva_schema_contract_validator.py \
  --write /tmp/pnva-schema-contract-validation.json
python3 -m json.tool /tmp/pnva-schema-contract-validation.json >/dev/null
```

## Production Rule

Any schema contract error is release-blocking.

Legacy warnings may be preserved only when:

```text
they are explicit
they are counted
they do not affect pass/fail integrity
the native path remains clean
```

The native path is the production direction for future PNVA runtimes.
