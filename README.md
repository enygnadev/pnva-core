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

The R3 cutover gate separates native contract readiness from final runtime approval. The current package is `R3_CUTOVER_GATE_READY_RUNTIME_REQUIRED` with `contract_ready=true`, `cutover_approved=false`, `legacy_free_claim_allowed=false`, `35` remaining runtime replacements, `3` runtime blockers and contract score `100`; this prevents projected evidence from being mislabeled as final R3 runtime evidence.

The R3 runtime capture matrix converts those `35` remaining replacements into entity/action/no-tick capture slots. The current package is `R3_RUNTIME_CAPTURE_MATRIX_READY_PENDING_RUNTIME` with `35` capture slots, `35` pending runtime slots, `70` required fresh runtime events, projection-pair coverage `1.0`, `1` target entity, `3` target actions and `4` target rules; this makes the next runtime step explicit without claiming R3 completion early.

The R3 runtime evidence guard protects the intake boundary for those future runtime logs. The current package is `R3_RUNTIME_EVIDENCE_GUARD_READY_AWAITING_CAPTURE` with `35` slots, `70` required runtime events, `0` accepted runtime slots, `35` pending slots, `57/57` negative controls detected and `6/6` fixture-only positive controls accepted; this rejects projected proofs, invalid timestamps, equal or reversed no-tick pair timestamps, duplicated event/proof identifiers, duplicated source locations, causal-chain reuse across different slots, unsafe source filenames that expose local paths, regressed source lines, malformed, repeated or content-unbound proof hashes, invalid proof refs, wrong event types, extra runtime events, missing field state, missing or inconsistent gate deltas, non-finite tension values, precheck/commit reason, state-transition, JSONL/source-line order or gate-sign violations, missing or mismatched entity IDs/types, mismatched slot/original event identity, broken no-tick causal pairs, missing source location, unsanitized or invalid native source format, weak authority, unknown/duplicate heuristic rules, malformed/unknown/duplicate risk flags, missing target heuristic rules, missing precheck/commit target risk flags and non-no-tick prechecks before cutover.

The R3 runtime instrumentation plan converts the `35` pending capture slots into concrete native emitter contracts. The current package is `R3_RUNTIME_INSTRUMENTATION_PLAN_READY` with `3` action contracts, `6` event templates, `70` required runtime events, `28` mandatory event fields, `57` negative controls, `6` positive controls, `1` target entity, required R3 slot identity, required native proof/source-location, public-basename source filenames, decision-reason and field-state markers, unique causal chains per slot, unique source locations, strict timestamp order, monotonic JSONL/source-line order per source file, required heuristic risk flags on prechecks and commits, required same-chain no-tick pair policy and no final runtime approval claim.

The R3 runtime contract validator checks that the capture matrix, evidence guard and instrumentation plan agree before final capture. The current package is `R3_RUNTIME_CONTRACT_VALIDATED_READY` with `295` contract checks, `0` failures, `35` slots, `3` action contracts, `70` required runtime events, `28` mandatory fields, `54` enforced controls and no final runtime approval claim.

The sovereign evolution ledger collapses no-tick evidence, log integrity, heuristic authority, entity coverage, controlled legacy warnings and R3 runtime readiness into one release dashboard. The current package is `PNVA_SOVEREIGN_EVOLUTION_LEDGER_READY_R3_RUNTIME_REQUIRED` with score `88.37`, R3 preparation ready, `35` pending runtime slots, `70` required runtime events, `291` R3 contract checks and no final R3 approval claim.

The adversarial validator runs negative controls against the public validators. The current package is `ADVERSARIAL_VALIDATION_PASS` with `7` detections over `7` controlled mutations.

The entity and heuristic maturity auditor scores actor/rule readiness across entity coverage, proof coverage, no-tick suppression, authority and causal relations. The current package is `ENTITY_HEURISTIC_MATURITY_READY_WITH_LEGACY_WARNINGS` with score `94.59`, `0` errors and `35` preserved legacy warnings.

The semantic consistency guard checks cross-report agreement across Manifest, replay, no-tick, policy, proof-chain, graph, schema contract, causal chronology, tension-decision calibration, decision trace index, heuristic influence map, entity no-tick matrix, suppression ledger, robustness gate, R3 migration plan, authority migration ledger, R3 authority projection, R3 cutover gate, R3 runtime capture matrix, R3 runtime evidence guard, R3 runtime instrumentation plan, R3 runtime contract validation, sovereign evolution ledger, maturity, adversarial validation, attestation and audit. The current package is `SEMANTIC_CONSISTENCY_READY` with `331` checks, `0` errors and `0` warnings.

The reproducibility guard reruns the current evidence commands and compares stable fields against the published reports. The current package is `REPRODUCIBILITY_READY` with `35` commands, `406` stable-field comparisons and `0` failures.

The sovereign evidence attestor binds the public evidence base into one machine-readable attestation. The current package is `PNVA_SOVEREIGN_EVIDENCE_ATTESTED` with `41` tracked artifacts and `0` failures; the sovereign audit consumes this attestation without being included in its hash seed.

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
