# PNVA Proof Chain Sealing

Author: Gustavo de Aguiar Martins  
Project: PNVA-Core / Enygnalab / EnyOS  
Edition: Open Research / Production Evidence Edition, 2026

This document defines the proof-chain sealing layer of PNVA-Core.

PNVA already publishes proof hashes per event. The proof-chain layer seals the sequence itself, so event content, event order and proof mutations become externally detectable.

## Why This Layer Exists

Individual event hashes prove local integrity.

A chain hash proves sequence integrity.

For no-tick research, order matters because the claim is causal:

```text
field -> event -> tension -> decision -> proof
```

If the order can be silently changed, the causal claim is weaker. The proof chain makes the order auditable.

## Method

For each event:

```text
event_hash = sha256(canonical_event_json)
chain_hash_i = sha256(index, previous_chain_hash, event_id, event_hash)
```

The first previous hash is:

```text
sha256("pnva.proof_chain.v1")
```

The final chain hash is the public sequence anchor.

## Current Canonical Seal

Report:

```text
reports/pnva-proof-chain-2026-05-05.json
```

Result:

```text
classification: PROOF_CHAIN_SEALED
event_count: 512
unique_event_ids: 512
proof_bad: 0
checkpoints: 9
```

## Current Native Seal

Report:

```text
reports/pnva-native-proof-chain-2026-05-05.json
```

Result:

```text
classification: PROOF_CHAIN_SEALED
event_count: 7
unique_event_ids: 7
proof_bad: 0
checkpoints: 2
```

## Interpretation

This layer does not rewrite any historical proof. It adds an external seal over the published event sequence.

That means:

```text
legacy bridge evidence remains preserved
native evidence remains clean
sequence order becomes auditable
tampering changes final_chain_hash
```

## Verification

Run:

```bash
python3 tools/pnva_proof_chain_sealer.py \
  --events reports/pnva-canonical-events-sample-2026-05-05.jsonl

python3 tools/pnva_proof_chain_sealer.py \
  --events reports/pnva-native-events-demo-2026-05-05.jsonl
```

Expected classification:

```text
PROOF_CHAIN_SEALED
```
