<p align="center">
  <img src="assets/pnva-core-mark.svg" width="180" alt="PNVA-Core mark">
</p>

<h1 align="center">PNVA-Core</h1>

<p align="center">
  <strong>A post-temporal causal architecture for state/event-oriented computation.</strong>
</p>

<p align="center">
  <a href="LICENSE"><img alt="Code License: MIT" src="https://img.shields.io/badge/code-MIT-0b1020?style=for-the-badge"></a>
  <a href="LICENSE-DOCS"><img alt="Docs License: CC BY 4.0" src="https://img.shields.io/badge/docs-CC_BY_4.0-1d4ed8?style=for-the-badge"></a>
  <a href="https://doi.org/10.5281/zenodo.20044503"><img alt="DOI: 10.5281/zenodo.20044503" src="https://zenodo.org/badge/DOI/10.5281/zenodo.20044503.svg"></a>
  <img alt="Production Candidate" src="https://img.shields.io/badge/production--candidate-PASS-c9a227?style=for-the-badge">
  <img alt="Research Edition" src="https://img.shields.io/badge/open--research-2026-6d28d9?style=for-the-badge">
</p>

## What PNVA Is

PNVA-Core is a causal runtime architecture proposed by **Gustavo de Aguiar Martins / Enygnalab**.

It replaces execution by temporal habit with execution by observable cause:

```text
state -> event -> tension -> collapse -> execution -> proof
```

The central shift is simple:

```text
from: "is it time to check again?"
to:   "did the field change enough to justify action?"
```

PNVA is not presented here as a universal physical theory or a miracle optimization. It is a technical architecture for event-aware, proof-driven computation.

## DOI

Canonical Zenodo record:

```text
Gustavo de Aguiar Martins. PNVA-Core: A Post-Temporal Causal Architecture for State/Event-Oriented Computation. Open Research / Production Evidence Edition, 2026. DOI: 10.5281/zenodo.20044503
```

Record URL: https://zenodo.org/records/20044503

DOI URL: https://doi.org/10.5281/zenodo.20044503

## Production Evidence

This repository publishes the sanitized evidence layer of a local live-field validation.

```text
15m live gate          PASS
8h live gate           PASS
12h live gate          PASS
24h live gate          PASS canonical
G1 stable opportunity  PASS
long-run-live-gate     PASS
guard rails            PASS
distribution-gate      PASS
production-candidate   PASS
```

The 24h result is intentionally documented as **canonical PASS**, not hidden as a pure raw PASS. The raw artifact captured a final `WARMUP`/selective-recompose transient after a stable long-run window. That distinction is preserved in the evidence.

## Architecture

```mermaid
flowchart LR
    A[Live Field Phi_t] --> B[Observable Event]
    B --> C[Tension Score]
    C --> D{Collapse?}
    D -->|No| E[Ignore + Proof]
    D -->|Yes| F[Execute Restricted Action]
    F --> G[Proof Log]
    E --> G
    G --> H[Validation Gates]
```

Core layers:

```text
pnva-field        observes state
pnva-eventd       normalizes events
pnva-tension      estimates causal pressure
pnva-collapse     authorizes action
pnva-memory       preserves causal history
pnva-proof        emits auditable logs
pnva-fieldcomms   reflects state without owning policy
pnva-gates        validates production readiness
```

## Veonic Layer

PNVA introduces a computational concept called the **Veonic unit**:

```text
Veon = minimal logical unit of causal influence activated by threshold.
```

Formal sketch:

```text
S_t = { i | G_i(Phi_t) > theta_t }

nu_i,t = 1[G_i(Phi_t) > theta_t] * G_tilde_i(Phi_t)

D_i,t = alpha * grad(I_i) + beta * K_i(M_i) - gamma * A_i * u_i

V_i,t = nu_i,t * D_i,t

Phi_t+1 = Phi_t
        + eta_t * ( sum_{j in S_t} G_tilde_j(Phi_t)
        + delta * sum_{i in S_t} V_i,t )
        + mu_t * (Phi_t - Phi_t-1)
```

The Veon is a computational unit, not a claim of physical particle discovery.

## Repository Map

```text
docs/
  PNVA_ARCHITECTURE.md
  VALIDATION_PROTOCOL.md
  PROOF_MATRIX.md
  PNVA_SOVEREIGN_LOGS_ENTITIES_HEURISTICS.md
  PNVA_CANONICAL_EVENT_BRIDGE.md
  PNVA_REPLAY_VALIDATION.md
  PNVA_NO_TICK_INVARIANTS.md
  PNVA_NATIVE_EVENT_EMITTER.md
  PNVA_SOVEREIGN_POLICY_VALIDATION.md
  PNVA_PROOF_CHAIN_SEALING.md
  PNVA_CAUSAL_GRAPH_AUDIT.md
  PNVA_SCHEMA_CONTRACT_VALIDATION.md
  PNVA_CAUSAL_CHRONOLOGY_GUARD.md
  PNVA_TENSION_DECISION_CALIBRATION.md
  PNVA_DECISION_TRACE_INDEX.md
  PNVA_HEURISTIC_INFLUENCE_MAP.md
  PNVA_ENTITY_NO_TICK_MATRIX.md
  PNVA_SUPPRESSION_LEDGER.md
  PNVA_SOVEREIGN_ROBUSTNESS_GATE.md
  PNVA_R3_MIGRATION_PLAN.md
  PNVA_AUTHORITY_MIGRATION_LEDGER.md
  PNVA_R3_AUTHORITY_PROJECTION.md
  PNVA_R3_CUTOVER_GATE.md
  PNVA_R3_RUNTIME_CAPTURE_MATRIX.md
  PNVA_R3_RUNTIME_EVIDENCE_GUARD.md
  PNVA_R3_RUNTIME_INSTRUMENTATION_PLAN.md
  PNVA_R3_RUNTIME_CONTRACT_VALIDATION.md
  PNVA_SOVEREIGN_EVOLUTION_LEDGER.md
  PNVA_SOVEREIGN_EVIDENCE_ATTESTATION.md
  PNVA_ADVERSARIAL_VALIDATION.md
  PNVA_ENTITY_HEURISTIC_MATURITY.md
  PNVA_SEMANTIC_CONSISTENCY_GUARD.md
  PNVA_REPRODUCIBILITY_GUARD.md
  PNVA_ROBUSTNESS_EVOLUTION_REPORT_2026-05-05.md
  VEON_MODEL_VALIDATION.md
  PNVA_POST_TEMPORAL_CIVILIZATION.md
  PNVA_SOVEREIGNTY_PUBLICATION_SCALE.md
  PUBLIC_POSITIONING.md
  REPOSITORY_PUBLISHING_CHECKLIST.md
  LIMITATIONS.md
  ONLINE_PUBLICATION.md
  PNVA_ROOT_SOVEREIGNTY_GUARD.md
  PNVA_ROOT_CAUSAL_INTELLIGENCE.md
  PNVA_ROOT_TRACEABILITY_MATRIX.md
  PNVA_ROOT_ADVERSARIAL_SENTRY.md
  PNVA_ROOT_RELEASE_SEAL.md
  PNVA_ROOT_RELEASE_VERIFIER.md
  PNVA_ROOT_CLAIM_BOUNDARY_GUARD.md
  PNVA_ROOT_PUBLICATION_GATE.md
  PNVA_ROOT_DEPENDENCY_GRAPH.md
  PNVA_ROOT_OBSERVABILITY_INDEX.md
  PNVA_ROOT_INVARIANT_FIREWALL.md
  PNVA_ROOT_REGRESSION_SENTINEL.md
  PNVA_ROOT_PROOF_THEOREM_LEDGER.md
  PNVA_ROOT_EVOLUTION_GOVERNOR.md
  PNVA_ROOT_HEURISTIC_WEIGHT_LEDGER.md
  PNVA_ROOT_ENTITY_CAPABILITY_LEDGER.md
  PNVA_ROOT_FIELD_TOPOLOGY_LEDGER.md
  PNVA_ROOT_NO_TICK_CAUSAL_CONTRACT.md
  PNVA_ROOT_RUNTIME_ADMISSION_CONTROLLER.md
  PNVA_ROOT_ENTITY_HEURISTIC_ADMISSION_MATRIX.md
  PNVA_ROOT_ADMISSION_NEGATIVE_CONTROLS.md
  PNVA_ROOT_EVENT_IDENTITY_LEDGER.md
  PNVA_ROOT_RUNTIME_GROWTH_BUDGET.md
  PNVA_ROOT_CAUSAL_MESH_LEDGER.md
  PNVA_ROOT_EFFICIENCY_PROOF_LEDGER.md
  PNVA_ROOT_EQUATION_CONSISTENCY_LEDGER.md
  PNVA_ROOT_LEGACY_QUARANTINE_LEDGER.md
  PNVA_ROOT_EVIDENCE_CHRONOLOGY_LEDGER.md
  PNVA_ROOT_SOVEREIGN_READINESS_GATE.md
  PNVA_ROOT_VALIDATOR_REGISTRY.md

paper/
  PNVA_CORE_OPEN_RESEARCH_PAPER.md

proofs/sanitized/
  JSON proof summaries suitable for public review

schemas/
  pnva-event.schema.json
  pnva-entity.schema.json

reports/
  pnva-sovereign-audit-2026-05-05.json
  pnva-canonical-events-sample-2026-05-05.jsonl
  pnva-entity-catalog-2026-05-05.json
  pnva-canonical-bridge-summary-2026-05-05.json
  pnva-replay-validation-2026-05-05.json
  pnva-no-tick-invariants-2026-05-05.json
  pnva-native-events-demo-2026-05-05.jsonl
  pnva-native-entity-catalog-demo-2026-05-05.json
  pnva-native-emitter-summary-2026-05-05.json
  pnva-native-replay-validation-2026-05-05.json
  pnva-native-no-tick-invariants-2026-05-05.json
  pnva-sovereign-policy-2026-05-05.json
  pnva-native-sovereign-policy-2026-05-05.json
  pnva-proof-chain-2026-05-05.json
  pnva-native-proof-chain-2026-05-05.json
  pnva-causal-graph-2026-05-05.json
  pnva-native-causal-graph-2026-05-05.json
  pnva-schema-contract-validation-2026-05-05.json
  pnva-causal-chronology-2026-05-05.json
  pnva-tension-decision-calibration-2026-05-05.json
  pnva-decision-trace-index-2026-05-05.json
  pnva-heuristic-influence-map-2026-05-05.json
  pnva-entity-no-tick-matrix-2026-05-05.json
  pnva-suppression-ledger-2026-05-05.json
  pnva-sovereign-robustness-gate-2026-05-05.json
  pnva-r3-migration-plan-2026-05-05.json
  pnva-authority-migration-ledger-2026-05-05.json
  pnva-r3-authority-projection-summary-2026-05-05.json
  pnva-r3-authority-projection-events-2026-05-05.jsonl
  pnva-r3-authority-projection-entities-2026-05-05.json
  pnva-r3-authority-projection-replay-2026-05-05.json
  pnva-r3-authority-projection-policy-2026-05-05.json
  pnva-r3-authority-projection-no-tick-2026-05-05.json
  pnva-r3-cutover-gate-2026-05-05.json
  pnva-r3-runtime-capture-matrix-2026-05-05.json
  pnva-r3-runtime-evidence-guard-2026-05-05.json
  pnva-r3-runtime-instrumentation-plan-2026-05-05.json
  pnva-r3-runtime-contract-validation-2026-05-05.json
  pnva-sovereign-evolution-ledger-2026-05-05.json
  pnva-sovereign-evidence-attestation-2026-05-05.json
  pnva-adversarial-validation-2026-05-05.json
  pnva-entity-heuristic-maturity-2026-05-05.json
  pnva-semantic-consistency-2026-05-05.json
  pnva-reproducibility-2026-05-05.json
  pnva-root-sovereignty-guard-2026-05-05.json
  pnva-root-causal-intelligence-2026-05-05.json
  pnva-root-traceability-matrix-2026-05-05.json
  pnva-root-adversarial-sentry-2026-05-05.json
  pnva-root-release-seal-2026-05-05.json
  pnva-root-release-verifier-2026-05-05.json
  pnva-root-claim-boundary-guard-2026-05-05.json
  pnva-root-publication-gate-2026-05-05.json
  pnva-root-dependency-graph-2026-05-05.json
  pnva-root-observability-index-2026-05-05.json
  pnva-root-invariant-firewall-2026-05-05.json
  pnva-root-regression-sentinel-2026-05-05.json

release/
  final production closure note
  professional public announcement draft

tools/
  sanitize_proofs.py
  pnva_sovereign_audit.py
  pnva_canonical_bridge.py
  pnva_replay_validator.py
  pnva_no_tick_invariant_analyzer.py
  pnva_native_event_emitter.py
  pnva_sovereign_policy_validator.py
  pnva_proof_chain_sealer.py
  pnva_causal_graph_auditor.py
  pnva_schema_contract_validator.py
  pnva_causal_chronology_guard.py
  pnva_tension_decision_calibrator.py
  pnva_decision_trace_index.py
  pnva_heuristic_influence_map.py
  pnva_entity_no_tick_matrix.py
  pnva_suppression_ledger.py
  pnva_sovereign_robustness_gate.py
  pnva_r3_migration_planner.py
  pnva_authority_migration_ledger.py
  pnva_r3_authority_projection.py
  pnva_r3_cutover_gate.py
  pnva_r3_runtime_capture_matrix.py
  pnva_r3_runtime_evidence_guard.py
  pnva_r3_runtime_instrumentation_plan.py
  pnva_r3_runtime_contract_validator.py
  pnva_sovereign_evolution_ledger.py
  pnva_evidence_attestor.py
  pnva_adversarial_validator.py
  pnva_entity_heuristic_maturity.py
  pnva_semantic_consistency_guard.py
  pnva_reproducibility_guard.py
  pnva_root_sovereignty_guard.py
  pnva_root_causal_intelligence.py
  pnva_root_traceability_matrix.py
  pnva_root_adversarial_sentry.py
  pnva_root_release_seal.py
  pnva_root_release_verifier.py
  pnva_root_claim_boundary_guard.py
  pnva_root_publication_gate.py
  pnva_root_dependency_graph.py
  pnva_root_observability_index.py
  pnva_root_invariant_firewall.py
  pnva_root_regression_sentinel.py
```

## Public Launch

For the first public announcement, use:

```text
release/POST_01_PROFISSIONAL_AUTORAL.md
```

For repository setup and publication order, use:

```text
docs/REPOSITORY_PUBLISHING_CHECKLIST.md
docs/PUBLIC_POSITIONING.md
```

## AI And Search Discovery

This repository includes a crawler-friendly public layer:

```text
index.html
author.html
pnva-core.html
proofs.html
veonic-model.html
robots.txt
sitemap.xml
llms.txt
```

GitHub Pages URL:

```text
https://enygnadev.github.io/pnva-core/
```

The `robots.txt` file allows OAI-SearchBot, GPTBot, ChatGPT-User, Googlebot, Bingbot and other crawlers so public AI/search systems can discover the canonical PNVA-Core pages.

## Public Claim

Use this claim:

```text
PNVA/no-tick was locally validated in a live field with 15m, 8h, 12h, 24h, G1, guard rails, distribution-gate and production-candidate PASS, using auditable JSON proof logs and documented canonical reclassification criteria.
```

Do not overclaim:

```text
Not a universal proof.
Not a full Linux kernel tick replacement claim.
Not a medical, legal or physical theory.
Not evidence that a Veon is a physical particle.
```

## Verify The Release Package

```bash
sha256sum -c SHA256SUMS.txt
python3 -m json.tool MANIFEST.json >/dev/null
for f in proofs/sanitized/*.json; do python3 -m json.tool "$f" >/dev/null; done
python3 tools/pnva_sovereign_audit.py --repo . --strict-public --min-score 80 >/tmp/pnva-sovereign-audit.json
python3 tools/pnva_canonical_bridge.py --demo --output /tmp/pnva-events.jsonl --entity-catalog /tmp/pnva-entities.json --summary /tmp/pnva-bridge.json
python3 tools/pnva_replay_validator.py --events reports/pnva-canonical-events-sample-2026-05-05.jsonl --entity-catalog reports/pnva-entity-catalog-2026-05-05.json >/tmp/pnva-replay.json
python3 tools/pnva_no_tick_invariant_analyzer.py --events reports/pnva-canonical-events-sample-2026-05-05.jsonl --entity-catalog reports/pnva-entity-catalog-2026-05-05.json --replay-report reports/pnva-replay-validation-2026-05-05.json >/tmp/pnva-no-tick-invariants.json
python3 tools/pnva_native_event_emitter.py --events /tmp/pnva-native-events.jsonl --entity-catalog /tmp/pnva-native-entities.json --summary /tmp/pnva-native-summary.json
python3 tools/pnva_sovereign_policy_validator.py --events reports/pnva-canonical-events-sample-2026-05-05.jsonl --entity-catalog reports/pnva-entity-catalog-2026-05-05.json >/tmp/pnva-sovereign-policy.json
python3 tools/pnva_proof_chain_sealer.py --events reports/pnva-canonical-events-sample-2026-05-05.jsonl >/tmp/pnva-proof-chain.json
python3 tools/pnva_causal_graph_auditor.py --events reports/pnva-canonical-events-sample-2026-05-05.jsonl --entity-catalog reports/pnva-entity-catalog-2026-05-05.json >/tmp/pnva-causal-graph.json
python3 tools/pnva_adversarial_validator.py --write /tmp/pnva-adversarial-validation.json
python3 tools/pnva_entity_heuristic_maturity.py --write /tmp/pnva-entity-heuristic-maturity.json
python3 tools/pnva_schema_contract_validator.py --write /tmp/pnva-schema-contract-validation.json
python3 tools/pnva_causal_chronology_guard.py --write /tmp/pnva-causal-chronology.json
python3 tools/pnva_tension_decision_calibrator.py --write /tmp/pnva-tension-decision-calibration.json
python3 tools/pnva_decision_trace_index.py --write /tmp/pnva-decision-trace-index.json
python3 tools/pnva_heuristic_influence_map.py --write /tmp/pnva-heuristic-influence-map.json
python3 tools/pnva_entity_no_tick_matrix.py --write /tmp/pnva-entity-no-tick-matrix.json
python3 tools/pnva_suppression_ledger.py --write /tmp/pnva-suppression-ledger.json
python3 tools/pnva_r3_runtime_instrumentation_plan.py --write /tmp/pnva-r3-runtime-instrumentation-plan.json
python3 tools/pnva_r3_runtime_contract_validator.py --write /tmp/pnva-r3-runtime-contract-validation.json
python3 tools/pnva_sovereign_evolution_ledger.py --write /tmp/pnva-sovereign-evolution-ledger.json
python3 tools/pnva_evidence_attestor.py --write /tmp/pnva-evidence-attestation.json
python3 tools/pnva_semantic_consistency_guard.py --write /tmp/pnva-semantic-consistency.json
python3 tools/pnva_reproducibility_guard.py --write /tmp/pnva-reproducibility.json
python3 tools/pnva_root_traceability_matrix.py --write /tmp/pnva-root-traceability-matrix.json
python3 tools/pnva_root_sovereignty_guard.py --write /tmp/pnva-root-sovereignty-guard.json
python3 tools/pnva_root_causal_intelligence.py --write /tmp/pnva-root-causal-intelligence.json
python3 tools/pnva_root_adversarial_sentry.py --write /tmp/pnva-root-adversarial-sentry.json
python3 tools/pnva_root_release_seal.py --write /tmp/pnva-root-release-seal.json
python3 tools/pnva_root_release_verifier.py --write /tmp/pnva-root-release-verifier.json
python3 tools/pnva_root_claim_boundary_guard.py --write /tmp/pnva-root-claim-boundary-guard.json
python3 tools/pnva_root_publication_gate.py --write /tmp/pnva-root-publication-gate.json
python3 tools/pnva_root_dependency_graph.py --write /tmp/pnva-root-dependency-graph.json
python3 tools/pnva_root_observability_index.py --write /tmp/pnva-root-observability-index.json
python3 tools/pnva_root_invariant_firewall.py --write /tmp/pnva-root-invariant-firewall.json
python3 tools/pnva_root_regression_sentinel.py --write /tmp/pnva-root-regression-sentinel.json
```

## Sovereign Robustness Layer

PNVA-Core now includes a canonical event/entity contract and an audit tool:

```text
schemas/pnva-event.schema.json
schemas/pnva-entity.schema.json
tools/pnva_sovereign_audit.py
```

The audit checks proof integrity, AI/search discovery, log contract readiness, publication hygiene and local log health when run inside the PNVA lab.

The canonical bridge converts legacy PNVA JSONL logs into `pnva.event.v1` envelopes, producing sanitized event samples and entity catalogs without exposing raw local logs.

The replay validator checks that the canonical event sequence is internally consistent, proof-hash stable and guard-aware.

The no-tick invariant analyzer proves the stronger PNVA claim: execution and non-execution are both causal, entity-aware, heuristic-visible and proof-backed. The current public report classifies the sample as `SOVEREIGN_NO_TICK_READY` with `246` causal suppressions over `512` events.

The native event emitter shows the production direction: new PNVA runtimes can emit `pnva.event.v1` directly, before any legacy bridge is needed. The current native demo is `NATIVE_EMITTER_READY`, replay-valid and no-tick-invariant-valid.

The sovereign policy validator checks heuristic authority. The canonical sample is `SOVEREIGN_POLICY_READY_WITH_LEGACY_WARNINGS`, preserving 35 low-authority legacy strong decisions as explicit warnings. The native sample is `SOVEREIGN_POLICY_READY` with zero warnings.

The proof-chain sealer adds sequence-level tamper evidence. It seals canonical and native event order with final chain hashes, so content or ordering changes alter the public chain anchor.

The causal graph auditor exposes entity topology: observed entities, guard relations, causal-chain edges and graph hashes. Both canonical and native graphs are `CAUSAL_GRAPH_READY`.

The schema contract validator checks public `pnva.event.v1` logs and `pnva.entity.v1` catalogs for required fields, finite tension values, decision shape, heuristic context, proof hashes, relation targets and sanitization. The current package is `SCHEMA_CONTRACT_READY_WITH_LEGACY_WARNINGS` with `519` events, `12` entities, `0` errors and `341` explicit legacy warnings; the native scope has `0` warnings.

The causal chronology guard checks timestamp order and time-gap evidence. The current package is `CAUSAL_CHRONOLOGY_READY_WITH_LEGACY_WARNINGS` with `519` events, `15` chains, `0` errors and `2` explicit legacy chronology warnings; the native scope is monotonic and clean.

The tension-decision calibrator checks whether `score`, `threshold`, `gate_delta`, guard events and `decision.kind` agree. The current package is `TENSION_DECISION_READY_WITH_LEGACY_WARNINGS` with `519` events, `0` errors and `384` explicit legacy warnings; the native scope is calibrated and clean.

The decision trace index maps every public event to entity, heuristic rules, authority, tension and proof. The current package is `DECISION_TRACE_INDEX_READY_WITH_LEGACY_WARNINGS` with `519` traced events, trace coverage `1.0`, proof coverage `1.0`, `0` errors and `152` preserved legacy low-authority trace warnings; the native trace path is clean.

The heuristic influence map quantifies rule influence by decision, authority, entity reach and proof coverage. The current package is `HEURISTIC_INFLUENCE_MAP_READY_WITH_LEGACY_WARNINGS` with `1136` influence edges, heuristic coverage `1.0`, proof-event coverage `1.0`, `0` errors and `70` preserved legacy warnings; native influence is clean.

The entity no-tick matrix attributes execution and suppression by entity, heuristic rule, authority and proof. The current package is `ENTITY_NO_TICK_MATRIX_READY_WITH_LEGACY_WARNINGS` with `519` events, `12` entity rows, `250` suppressions, `0` errors and `35` preserved legacy warnings; the native matrix is clean.

The suppression ledger treats non-execution as proof-backed work avoidance. The current package is `SUPPRESSION_LEDGER_READY_WITH_LEGACY_WARNINGS` with `250` suppressions, `250` estimated avoided executions, proof coverage `1.0`, `0` errors and `176` preserved legacy threshold warnings; native suppression is clean.

The sovereign robustness gate collapses no-tick, trace coverage, heuristic influence, entity attribution, suppression ledger, causal integrity, adversarial validation and legacy debt into one readiness decision. The current package is `SOVEREIGN_ROBUSTNESS_GATE_READY_WITH_LEGACY_WARNINGS` with score `97/100`, `519` events, `250` suppressions, `8/8` native clean signals, `0` blockers and `35` quarantined legacy low-authority strong decisions.

The R3 migration plan turns the remaining legacy debt into a measurable engineering backlog. The current package is `R3_MIGRATION_PLAN_READY`, moving from `R2_NATIVE_CLEAN_LEGACY_QUARANTINED` toward `R3_NATIVE_CLEAN_LEGACY_FREE`, with `6` migration actions, `35` primary blocking legacy decisions, `903` overlapping migration signals and `0` blockers in the planner.

The authority migration ledger maps the primary R3 authority debt to concrete entity/action targets. The current package is `AUTHORITY_MIGRATION_LEDGER_READY_WITH_LEGACY_WARNINGS` with `35` H0 strong candidates, `1` affected entity, `3` affected actions, native low-authority strong debt `0`, migration coverage `1.0` and proof coverage `1.0`.

The R3 authority projection converts those `35` mapped candidates into a native hard-authority candidate sample before runtime replacement. The current package is `R3_AUTHORITY_PROJECTION_READY` with `70` projected native events, `35` no-tick prechecks, `35` collapse commits, `0` projected low-authority strong decisions, replay `REPLAY_VALID`, policy `SOVEREIGN_POLICY_READY` and no-tick `SOVEREIGN_NO_TICK_READY`.

The R3 cutover gate separates native contract readiness from final runtime approval. The current package is `R3_CUTOVER_APPROVED` with `contract_ready=true`, `cutover_approved=true`, `legacy_free_claim_allowed=true`, `0` remaining runtime replacements, `0` runtime blockers and contract score `100`; this keeps projected evidence separate while approving the slot-bound native runtime replacement sample.

The R3 runtime capture matrix converts those mapped replacements into entity/action/no-tick capture slots. The current package is `R3_RUNTIME_CAPTURE_MATRIX_COMPLETE` with `35` capture slots, `35` verified runtime slots, `0` pending runtime slots, `70` required runtime events, projection-pair coverage `1.0`, `1` target entity, `3` target actions and `4` target rules.

The R3 runtime evidence guard protects the intake boundary for runtime logs. The current package is `R3_RUNTIME_EVIDENCE_ACCEPTED` with `35` slots, `70` required runtime events, `35` accepted runtime slots, `0` pending slots, `0` rejected events, `35/35` no-tick pairs intact, `63/63` negative controls detected and `6/6` fixture-only positive controls accepted; this rejects projected proofs, invalid timestamps, equal or reversed no-tick pair timestamps, duplicated event/proof identifiers, duplicated source locations, causal-chain reuse across different slots, unsafe source filenames that expose local paths, mismatched source files inside a no-tick pair, broken precheck-to-commit state continuity, regressed source lines, malformed, repeated or content-unbound proof hashes, invalid proof refs, wrong event types, extra runtime events, missing field state, missing or inconsistent gate deltas, non-finite tension values, precheck/commit reason, state-transition, JSONL/source-line order or gate-sign violations, missing or mismatched entity IDs/types, mismatched slot/original event identity, broken no-tick causal pairs, missing source location, unsanitized or invalid native source format, weak authority, legacy, unknown or duplicate heuristic rules, malformed/unknown/duplicate risk flags, missing precheck/commit target heuristic rules and missing precheck/commit target risk flags.

The R3 runtime instrumentation plan converts the capture slots into concrete native emitter contracts. The current package is `R3_RUNTIME_INSTRUMENTATION_PLAN_READY` with `3` action contracts, `6` event templates, `70` required runtime events, `28` mandatory event fields, `63` negative controls, `6` positive controls, `1` target entity, required R3 slot identity, required native proof/source-location, public-basename source filenames, decision-reason and field-state markers, unique causal chains per slot, unique source locations, strict timestamp order, same-source no-tick pairs, explicit field-state continuity, monotonic JSONL/source-line order per source file and required target heuristic rules/risk flags on prechecks and commits.

The R3 runtime contract validator checks that the capture matrix, evidence guard and instrumentation plan agree. The current package is `R3_RUNTIME_CONTRACT_VALIDATED_READY` with `315` contract checks, `0` failures, `35` slots, `3` action contracts, `70` required runtime events, `28` mandatory fields, `59` enforced controls and accepted runtime approval.

The sovereign evolution ledger collapses no-tick evidence, log integrity, heuristic authority, entity coverage, controlled legacy warnings and R3 runtime readiness into one release dashboard. The current package is `PNVA_SOVEREIGN_EVOLUTION_LEDGER_R3_READY` with score `98.37`, R3 preparation ready, `0` pending runtime slots, `70` required runtime events, `315` R3 contract checks and accepted slot-bound R3 runtime approval.

The adversarial validator runs negative controls against the public validators. The current package is `ADVERSARIAL_VALIDATION_PASS` with `7` detections over `7` controlled mutations.

The entity and heuristic maturity auditor scores actor/rule readiness across entity coverage, proof coverage, no-tick suppression, authority and causal relations. The current package is `ENTITY_HEURISTIC_MATURITY_READY_WITH_LEGACY_WARNINGS` with score `94.59`, `0` errors and `35` preserved legacy warnings.

The semantic consistency guard checks cross-report agreement across Manifest, replay, no-tick, policy, proof-chain, graph, schema contract, causal chronology, tension-decision calibration, decision trace index, heuristic influence map, entity no-tick matrix, suppression ledger, robustness gate, R3 migration plan, authority migration ledger, R3 authority projection, R3 cutover gate, R3 runtime capture matrix, R3 runtime evidence guard, R3 runtime instrumentation plan, R3 runtime contract validation, sovereign evolution ledger, maturity, adversarial validation, attestation and audit. The current package is `SEMANTIC_CONSISTENCY_READY` with `331` checks, `0` errors and `0` warnings.

The reproducibility guard reruns the current evidence commands and compares stable fields against the published reports. The current package is `REPRODUCIBILITY_READY` with `40` commands, `445` stable-field comparisons and `0` failures.

The root sovereignty guard collapses runtime events, entities, no-tick pairs, heuristic authority, proof integrity, traceability matrix, cutover, ledger, attestation, semantic consistency, reproducibility and audit into one final repository-level check. The current package is `PNVA_ROOT_SOVEREIGNTY_GUARD_READY` with root score `100.0`, `27` checks, `0` failures, `70` runtime events, `35` verified slots and `1` runtime entity.

The root causal intelligence analyzer turns no-tick logs, heuristic authority, entity coverage and proof integrity into one deterministic root score. The current package is `PNVA_ROOT_CAUSAL_INTELLIGENCE_READY` with score `100.0`, `589` aggregate no-tick events, `285` proof-backed suppressions, suppression ratio `0.483871`, `35` verified runtime slots, `0` pending runtime slots and `0` runtime projected proofs.

The root traceability matrix maps every R3 runtime slot to its no-tick precheck, collapse commit, entity, heuristic rules, proof refs, proof hashes and downstream validator alignment. The current package is `PNVA_ROOT_TRACEABILITY_MATRIX_READY` with score `100.0`, `35` valid slots, `0` invalid slots, `70` unique proof hashes and no-tick suppression ratio `0.5`.

The root adversarial sentry mutates temporary copies of runtime evidence and requires the root validators to fail. The current package is `PNVA_ROOT_ADVERSARIAL_SENTRY_PASS` with clean control PASS, `8` controlled mutations, `8` detections and `0` undetected failures across projection, entity identity, no-tick continuity, authority, source path, event identity, gate delta and legacy heuristic injection.

The root release seal binds the final root reports into one public citation hash. The current package is `PNVA_ROOT_RELEASE_SEALED` with `11` sealed artifacts, `0` failures, root score `100.0`, causal intelligence score `100.0`, adversarial detection `8/8`, `35` accepted runtime slots and root release hash `sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc`.

The root release verifier independently recomputes that citation hash and checks sealed artifact classifications, stable hashes, checksum coverage, release-vector closure and explicit claim boundaries. The current package is `PNVA_ROOT_RELEASE_VERIFIED` with `9` verifications, `0` failures, `11` sealed artifacts and `0` checksum, stable-hash or classification mismatches.

The root claim boundary guard scans public language after the seal and verifier. The current package is `PNVA_ROOT_CLAIM_BOUNDARY_GUARD_READY` with score `100.0`, `7` checks, `0` failures, `90` scanned public text files, `48` bounded high-risk claim occurrences and `0` unbounded high-risk claims.

The root publication gate validates final public readiness for repository publication and AI/search discovery. The current package is `PNVA_ROOT_PUBLICATION_GATE_READY` with score `100.0`, `9` checks, `0` failures, `258` Manifest files, `257` checksum entries, valid discovery metadata and `0` local path leaks.

The root dependency graph maps public contract, sanitized proof gates, canonical/native event validators, heuristic/entity ledgers, R3 runtime proof, root guards, release seal, verifier, claim boundary and publication gate into one acyclic proof graph. The current package is `PNVA_ROOT_DEPENDENCY_GRAPH_READY` with score `100.0`, `49` nodes, `104` edges, `11` phases, `0` missing artifacts, `0` readiness failures, `0` cycles and `0` unreachable nodes.

The root observability index consolidates no-tick logs, proof hashes, entity catalogs, heuristic influence, runtime slots and root gates into one laboratory view. The current package is `PNVA_ROOT_OBSERVABILITY_INDEX_READY` with score `100.0`, `589` aggregate events, `285` proof-backed suppressions, suppression ratio `0.483871`, `13` entity catalog rows, `9` heuristic rules, `35` accepted runtime slots and `0` rejected runtime events.

The root invariant firewall blocks regressions across logs, entities, heuristics, runtime R3, dependency graph, publication hygiene and claim boundaries. The current package is `PNVA_ROOT_INVARIANT_FIREWALL_READY` with score `100.0`, `12` checks, `0` failures, `3` event streams, `3` entity catalogs, `35` accepted runtime slots, `0` no-tick pair failures, `0` dependency cycles, `0` path leaks and `0` unbounded high-risk claims.

The root regression sentinel watches future metric drift after the firewall passes. The current package is `PNVA_ROOT_REGRESSION_SENTINEL_READY` with score `100.0`, `5` checks, `0` failures, `36` monitored metrics, `36` stable metrics, `0` regressed metrics, no-tick suppression ratio range `0.45..0.70` and the root release hash stable.

The root proof theorem ledger converts PASS reports into explicit theorem cards with claim, criteria, evidence, boundary and dependencies. The current package is `PNVA_ROOT_PROOF_THEOREM_LEDGER_READY` with score `100.0`, `4` checks, `0` failures, `12` theorem cards, `12` proven theorem cards and `0` failed theorem cards.

The root evolution governor defines safe future improvement paths after root proof passes. The current package is `PNVA_ROOT_EVOLUTION_GOVERNOR_READY` with score `100.0`, `6` checks, `0` failures, `22` locked invariants, `0` invariant failures, `5` controlled debts, `8` safe evolution cards and `0` blocked cards.

The root heuristic weight ledger exposes public audit weights for PNVA heuristic rules. The current package is `PNVA_ROOT_HEURISTIC_WEIGHT_LEDGER_READY` with score `100.0`, `9` checks, `0` failures, `9` rules, `8` public-weight-ready rules, `1` controlled legacy rule, `0` blocked rules, `1350` rule-event edges, complete proof coverage and clean projection status.

The root entity capability ledger exposes entity readiness across canonical, native and R3 runtime evidence. The current package is `PNVA_ROOT_ENTITY_CAPABILITY_LEDGER_READY` with score `100.0`, `12` checks, `0` failures, `13` entity rows, `3` scopes, `589` profiled events, `25` capability edges, `1` R3 runtime-ready entity, `6` native-ready entities, `6` controlled canonical entities and `0` blocked entities.

The root field topology ledger exposes the entity-rule-decision no-tick topology as an audit graph. The current package is `PNVA_ROOT_FIELD_TOPOLOGY_LEDGER_READY` with score `100.0`, `13` checks, `0` failures, `13` entity nodes, `9` rule nodes, `589` events, `1350` rule-event edges, `38` entity-rule edges, `17` entity-decision edges, `20` rule-decision edges, `4` R3-ready edges, `5` legacy edges, `0` blocked edges, `0` orphan nodes, `0` unruled events and `0` unknown entity events.

The root no-tick causal contract binds logs, proof hashes, entities, rules, suppression and threshold behavior into one root audit. The current package is `PNVA_ROOT_NO_TICK_CAUSAL_CONTRACT_READY` with score `100.0`, `15` checks, `0` failures, `589` events, `285` suppressed decisions, suppression ratio `0.483871`, `589` valid proof hashes, `77` strict native/R3 threshold events, `0` strict threshold violations, `35` R3 precheck/commit pairs, `0` pair failures, `0` guard contract failures, `0` unknown entities and `0` unknown rules.

The root runtime admission controller turns the current proof state into an explicit admission decision for future runtime evidence. The current package is `PNVA_ROOT_RUNTIME_ADMISSION_READY` with score `100.0`, `10` checks, `0` failures and decision `ADMIT_RESTRICTED_ROOT_RUNTIME_PLANNING`. It allows audit, observe, simulate, restricted native event ingest, restricted R3 precheck/commit and planning-only evolution; it denies unbounded public claims, unsanitized logs, private threshold publication, unpaired R3 events, projected runtime evidence, unknown entities/rules and hardware-energy claims without a separate counter benchmark.

The root entity-heuristic admission matrix maps every observed entity-rule edge into an explicit admission class. The current package is `PNVA_ROOT_ENTITY_HEURISTIC_ADMISSION_MATRIX_READY` with score `100.0`, `11` checks, `0` failures, `589` events, `1350` rule-event edges, `38` entity-rule edges, `4` R3-restricted edges, `12` native-restricted edges, `17` controlled canonical evidence edges, `5` bounded legacy edges, `0` denied edges, `0` unknown entities and `0` unknown rules.

The root admission negative controls prove that corrupted no-tick, entity and heuristic evidence is rejected. The current package is `PNVA_ROOT_ADMISSION_NEGATIVE_CONTROLS_PASS` with clean control PASS, `8` controlled mutations, `8` detections, `0` undetected mutations and `0` failures across R3 gate inversion, unpaired R3 chain, unknown entity, projected proof, unknown rule, duplicate event ID, invalid proof hash and native source path leak.

The root event identity ledger proves public event identity at the log level. The current package is `PNVA_ROOT_EVENT_IDENTITY_LEDGER_READY` with score `100.0`, `10` checks, `0` failures, `589` events, `589` unique event IDs, `589` unique proof hashes, `13` entity bindings, `9` rules, `1350` rule-event edges, `35` R3 chains, `0` R3 pair failures, `77` native events and `0` projected events.

The root runtime growth budget defines how runtime evidence may grow without breaking no-tick, proof, entity or heuristic guarantees. The current package is `PNVA_ROOT_RUNTIME_GROWTH_BUDGET_READY` with score `100.0`, `10` checks, `0` failures, growth mode `SMALL_BATCH_RESTRICTED`, max `118` new events, `7` new R3 chains, `8` new entity-rule edges per batch, `0` denied, unknown or projected events, suppression range `0.45..0.70` and negative controls preserved at `8/8`.

The root causal mesh ledger proves that the root PASS reports agree with each other instead of standing alone. The current package is `PNVA_ROOT_CAUSAL_MESH_LEDGER_READY` with score `100.0`, `10` checks, `0` failures, `589` events, `285` suppressions, `13` entities, `9` rules, `1350` rule-event edges, `38` entity-rule edges, `35` R3 chains, `589` valid proofs, `0` denied edges, `0` unknown entities/rules, `0` projected events and `0` public path leaks.

The root efficiency proof ledger quantifies PNVA/no-tick gain as proof-backed causal non-execution against a public event baseline. The current package is `PNVA_ROOT_EFFICIENCY_PROOF_LEDGER_READY` with score `100.0`, `9` checks, `0` failures, `589` baseline event actions, `285` avoided actions, avoided-action ratio `0.483871`, `304` observed required actions, `13` entity rows, `9` heuristic rule rows, `1350` rule-event edges, `0` projected events and `0` suppressed proof failures.

The root equation consistency ledger proves that public tension logs preserve `gate_delta = score - max(0, threshold - margin)` and that native/R3 decisions obey strict threshold semantics. The current package is `PNVA_ROOT_EQUATION_CONSISTENCY_LEDGER_READY` with score `100.0`, `9` checks, `0` failures, `589` events, `285` suppressions, avoided-action ratio `0.483871`, `0` formula mismatches, `0` missing equation fields, `0` strict native/R3 violations, `384` bounded canonical legacy warnings, `13` entity bindings and `9` heuristic rules.

The root legacy quarantine ledger proves that canonical legacy threshold warnings remain visible, attributed and bounded instead of being promoted into clean native/R3 runtime evidence. The current package is `PNVA_ROOT_LEGACY_QUARANTINE_LEDGER_READY` with score `100.0`, `9` checks, `0` failures, `384` canonical legacy warnings, `0` native/R3 legacy warnings, `5` bounded legacy edges, `1` controlled legacy rule, `0` denied edges, `0` unknown entities/rules and `0` strict native/R3 threshold violations.

The root evidence chronology ledger proves the report order across sealed core, post-seal ledgers and publication/growth checks. The current package is `PNVA_ROOT_EVIDENCE_CHRONOLOGY_LEDGER_READY` with score `100.0`, `11` checks, `0` failures, `27` root reports ordered, `90` scanned public text files, `258` Manifest files, `257` checksum entries, stable root release hash and `0` public path leaks.

The root sovereign readiness gate collapses no-tick metrics, event identity, proof identity, entity/rule mesh, efficiency proof, equation consistency, legacy quarantine, runtime admission, growth budget, negative controls and publication hygiene into one final root decision. The current package is `PNVA_ROOT_SOVEREIGN_READINESS_GATE_PASS` with score `100.0`, `11` checks, `0` failures, `589` events, `285` suppressions, avoided-action ratio `0.483871`, equation consistency score `100.0`, legacy quarantine score `100.0`, `0` native/R3 legacy warnings, `13` entities, `9` rules, `35` R3 chains, `589` valid proofs, `77` native events, `0` projected events and restricted runtime admission.

The root validator registry proves every root validator is discoverable across tool, report, document, Manifest, checksum, CI, README, llms.txt and the sovereign documentation. The current package is `PNVA_ROOT_VALIDATOR_REGISTRY_READY` with score `100.0`, `8` checks, `0` failures, `30` validators, `30` CI registrations, `30` public documentation registrations and `30` PASS reports.

The sovereign evidence attestor binds the public evidence base into one machine-readable attestation. The current package is `PNVA_SOVEREIGN_EVIDENCE_ATTESTED` with `48` tracked artifacts and `0` failures; the sovereign audit consumes this attestation without being included in its hash seed.

## Citation

If this repository supports your research, cite:

```text
Gustavo de Aguiar Martins. PNVA-Core: A Post-Temporal Causal Architecture for State/Event-Oriented Computation. Open Research / Production Evidence Edition, 2026.
```

## Licenses

- Code and scripts: MIT.
- Documentation, paper and diagrams: CC BY 4.0.

## Author

**Gustavo de Aguiar Martins**  
Enygnalab / EnyOS / PNVA-Core  
GitHub: https://github.com/enygnadev
