# PNVA Root Evidence Chronology Ledger

Author: Gustavo de Aguiar Martins
Project: PNVA-Core
Edition: Open Research / Production Evidence Edition

## Purpose

The PNVA root evidence chronology ledger proves that root evidence reports have a coherent sealed-core, post-seal and publication chronology.

The goal is to make the order explicit:

```text
sealed core -> release verifier -> post-seal ledgers -> publication and growth checks
```

## Tool

```text
tools/pnva_root_evidence_chronology_ledger.py
```

## Report

```text
reports/pnva-root-evidence-chronology-ledger-2026-05-05.json
```

## Classification

```text
PNVA_ROOT_EVIDENCE_CHRONOLOGY_LEDGER_READY
```

## Current Result

```text
chronology_score: 100.0
check_count: 9
failure_count: 0
report_count: 25
claim_scanned_file_count: 88
manifest_file_count: 252
checksum_count: 251
mesh_event_count: 589
mesh_suppressed_count: 285
mesh_entity_count: 13
mesh_rule_count: 9
path_leak_count: 0
unbounded_high_risk_occurrence_count: 0
root_release_hash: sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc
```

## Checks

The chronology ledger requires:

```text
source_reports_ready
generated_at_present
sealed_core_order_valid
release_verifier_after_seal
post_seal_reports_are_after_verifier
causal_mesh_after_growth_and_claim
efficiency_after_mesh_growth_and_claim
public_counts_current
root_hash_chronology_aligned
```

## Phase Model

The chronology is divided into three phases:

```text
sealed_core
post_seal_root_ledgers
publication_and_growth
```

The sealed core produces the stable root release hash. Post-seal reports cite that hash without rewriting it. Publication and growth reports verify public boundaries, checksum closure, growth budget and cross-report mesh consistency.

## Production Interpretation

This layer prevents a common audit weakness: a set of valid reports without a declared order. The chronology ledger shows that the root package has a stable sealed base and that later reports extend the public evidence package without changing the sealed root hash.

## Boundary

This ledger audits public report chronology only. It does not execute actions, change live gates, alter mining workloads or publish private tuning.

## Command

```bash
python3 tools/pnva_root_evidence_chronology_ledger.py \
  --write reports/pnva-root-evidence-chronology-ledger-2026-05-05.json
```
