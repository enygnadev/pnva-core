# PNVA Semantic Consistency Guard

Author: Gustavo de Aguiar Martins  
Project: PNVA-Core / Enygnalab / EnyOS  
Edition: Open Research / Production Evidence Edition, 2026

## Objective

This layer checks whether the public PNVA evidence package is internally consistent.

The goal is simple:

```text
if one report says 512 events, every dependent report must agree
if the Manifest publishes an evidence hash, it must match the attestation
if maturity claims 250 suppressions, it must equal canonical + native no-tick suppression
```

This makes PNVA harder to break by documentation drift.

## Why This Exists

PNVA-Core now has multiple independent validators:

```text
replay
no-tick invariants
policy
proof chain
causal graph
schema contract validation
causal chronology guard
tension-decision calibration
decision trace index
heuristic influence map
entity no-tick matrix
suppression ledger
sovereign robustness gate
R3 migration plan
authority migration ledger
R3 authority projection
R3 cutover gate
R3 runtime capture matrix
R3 runtime evidence guard
R3 runtime instrumentation plan
R3 runtime contract validation
sovereign evolution ledger
adversarial validation
entity and heuristic maturity
evidence attestation
sovereign audit
```

Each validator proves a different property. The semantic consistency guard proves that those properties still agree after publication.

## Current Public Result

Report:

```text
reports/pnva-semantic-consistency-2026-05-05.json
```

Current classification:

```text
SEMANTIC_CONSISTENCY_READY
```

Current result:

```text
check_count: 331
error_count: 0
warning_count: 0
```

## What It Checks

The guard compares:

```text
Manifest summary vs source reports
canonical bridge vs replay/no-tick/policy/graph/proof-chain
native emitter vs native no-tick/policy/graph/proof-chain
schema contract report vs Manifest and attestation
causal chronology report vs Manifest and attestation
tension-decision calibration report vs Manifest, attestation and audit
decision trace index vs Manifest, attestation and audit
heuristic influence map vs Manifest, attestation and audit
entity no-tick matrix vs Manifest, attestation and audit
suppression ledger vs Manifest, attestation and audit
sovereign robustness gate vs Manifest, attestation, maturity and audit
R3 migration plan vs Manifest, attestation, robustness gate and audit
authority migration ledger vs Manifest, R3 plan, policy, heuristic influence, attestation and audit
R3 authority projection vs Manifest, authority migration ledger, replay, policy, no-tick, attestation and audit
R3 cutover gate vs Manifest, authority migration ledger, R3 authority projection, attestation and audit
R3 runtime capture matrix vs Manifest, authority migration ledger, R3 cutover gate, attestation and audit
R3 runtime evidence guard vs Manifest, R3 runtime capture matrix, attestation and audit
R3 runtime instrumentation plan vs Manifest, R3 runtime capture matrix, R3 runtime evidence guard, attestation and audit
R3 runtime contract validation vs Manifest, R3 runtime capture matrix, R3 runtime evidence guard, R3 runtime instrumentation plan, attestation and audit
sovereign evolution ledger vs Manifest, no-tick maturity, R3 runtime capture matrix, R3 runtime contract validation, attestation and audit
maturity aggregate math vs canonical + native reports
attestation artifact count vs artifact list
audit summary vs attestation and maturity report
Manifest file list vs files on disk
```

Examples:

```text
512 canonical events must match bridge, replay, no-tick, policy, graph and proof-chain.
7 native events must match native emitter, native no-tick, native policy, native graph and native proof-chain.
250 total suppressions must equal 246 canonical suppressions + 4 native suppressions.
519 traced events must equal canonical + native event count.
9 heuristic rules must match schema contract heuristic rule count.
250 avoided executions must equal 250 ledger suppressions.
97 robustness score must preserve 8/8 native clean signals and 0 blockers.
304 strong decisions must equal 299 canonical + 5 native.
269 hard-authority strong decisions must equal 304 - 35 legacy low-authority warnings.
R3 migration starts at R2_NATIVE_CLEAN_LEGACY_QUARANTINED, targets R3_NATIVE_CLEAN_LEGACY_FREE and preserves the 35 primary legacy debt count until the native path replaces it.
35 authority migration candidates must match R3 primary debt, policy low-authority legacy count and heuristic influence uncompensated low-authority strong count.
70 projected native R3 authority events must equal 35 prechecks + 35 commits, preserve 0 projected low-authority strong decisions and pass replay, sovereign policy and no-tick validation.
R3 cutover must keep contract_ready=true, cutover_approved=false and legacy_free_claim_allowed=false until fresh native runtime evidence replaces the projected sample.
R3 runtime capture must keep 35 pending slots explicit and require 70 fresh runtime events before the final cutover claim.
R3 runtime evidence guard must keep intake_guard_ready=true, runtime_evidence_approved=false, 46/46 negative controls detected and 6/6 fixture-only positive controls accepted until fresh runtime JSONL is supplied.
R3 runtime instrumentation must keep 35 capture slots mapped into 3 action contracts, 6 event templates, 28 mandatory event fields and 70 required runtime events without claiming runtime approval.
R3 runtime contract validation must keep 239 contract checks, 43 enforced controls, zero failures and no runtime approval claim while matrix, guard and instrumentation remain aligned.
Sovereign evolution ledger must keep no-tick/log/entity/heuristic evidence ready, 35 pending runtime slots explicit, 70 required runtime events, 239 contract checks and final R3 approval blocked until fresh native runtime JSONL exists.
```

## Attestation Boundary

This guard is intentionally kept outside the evidence attestation hash seed.

Reason:

```text
the consistency guard consumes the attestation
the attestation must not hash a report that depends on the attestation
```

This avoids circular evidence hashing.

## Command

```bash
python3 tools/pnva_semantic_consistency_guard.py \
  --write reports/pnva-semantic-consistency-2026-05-05.json
```

For CI or temporary validation:

```bash
python3 tools/pnva_semantic_consistency_guard.py \
  --write /tmp/pnva-semantic-consistency.json
python3 -m json.tool /tmp/pnva-semantic-consistency.json >/dev/null
```

## Sovereign Rule

PNVA evidence should not merely pass in isolated files.

It should agree as a system:

```text
same event counts
same suppression counts
same authority counts
same graph counts
same evidence hash
same publication metadata
```

That is the difference between many reports and one coherent evidence package.
