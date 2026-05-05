# PNVA Adversarial Validation

Author: Gustavo de Aguiar Martins  
Project: PNVA-Core / Enygnalab / EnyOS  
Edition: Open Research / Production Evidence Edition, 2026

## Objective

This layer adds negative controls to PNVA-Core.

The goal is not to create new runtime claims. The goal is to prove that the existing validators reject or expose controlled evidence mutations.

In practical terms:

```text
green path validation proves valid evidence is accepted
adversarial validation proves bad evidence is detected
```

Both are required for a sovereign proof system.

## What Is Tested

The adversarial validator creates temporary mutated event files and runs the public PNVA validators against them.

No mutated file is published as evidence.

Current negative controls:

| Test | Mutation | Expected detection |
| --- | --- | --- |
| replay_proof_hash_tamper | changes one proof hash | PROOF_HASH_MISMATCH |
| native_low_authority_strong_decision | downgrades a native strong action to legacy authority | LOW_AUTHORITY_STRONG_DECISION |
| graph_missing_entity | uses an entity absent from the catalog | EVENT_ENTITY_NOT_IN_CATALOG |
| graph_bad_relation_target | uses a relation target absent from the catalog | RELATION_TARGET_NOT_IN_CATALOG |
| proof_chain_duplicate_event_id | appends a duplicate event id | DUPLICATE_EVENT_IDS |
| proof_chain_order_tamper | swaps two events without changing their content | CHAIN_HASH_DRIFT |
| json_parse_error | appends malformed JSON | JSON_PARSE_ERROR |

## Current Public Result

Report:

```text
reports/pnva-adversarial-validation-2026-05-05.json
```

Current classification:

```text
ADVERSARIAL_VALIDATION_PASS
```

Current result:

```text
test_count: 7
detected_count: 7
failure_count: 0
```

## Why This Matters

PNVA claims should not depend on validators that only approve the ideal case.

A robust PNVA validator must fail when:

```text
proof hash is corrupted
strong decision has weak authority
event entity is unknown
relation target is unknown
event id is duplicated
event order is changed
JSON evidence is malformed
```

The order-tamper test is intentionally different. It may still be a structurally valid sequence, but the final proof-chain hash must change. That is the point of sequence sealing: order tampering becomes externally visible even when each event still looks valid alone.

## Boundary

This is adversarial validation over the public PNVA evidence package.

It is not a universal security proof for all possible deployments. It proves that the published validators detect the defined negative controls in the current evidence release.

## Command

```bash
python3 tools/pnva_adversarial_validator.py --write reports/pnva-adversarial-validation-2026-05-05.json
```

For CI or temporary validation:

```bash
python3 tools/pnva_adversarial_validator.py --write /tmp/pnva-adversarial-validation.json
python3 -m json.tool /tmp/pnva-adversarial-validation.json >/dev/null
```

## Sovereign Rule

PNVA evidence is stronger when it can answer two questions:

```text
why did this valid event pass?
why did this invalid mutation fail?
```

That is the difference between a status report and an auditable proof system.
