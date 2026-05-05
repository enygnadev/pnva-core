# PNVA Sovereign Logs, Entities And Heuristics

Author: Gustavo de Aguiar Martins  
Project: PNVA-Core / Enygnalab / EnyOS  
Edition: Open Research / Production Evidence Edition, 2026

This document defines the next robust layer of PNVA-Core: canonical logs, explicit entities and auditable heuristics.

The goal is not to change the already validated gates. The goal is to make future PNVA/no-tick evolution harder to break, easier to audit and safer to publish.

## 1. Core Finding

The current PNVA laboratory already contains the essential runtime organs:

- adaptive threshold;
- ETEV guard;
- Memory4D;
- affinity routing;
- power orchestration;
- causal event logs;
- heuristic logs;
- proof gates;
- sanitized public evidence.

The next weakness is not lack of computation. The weakness is contract dispersion: different logs use different shapes, some events use `event`, others use `kind`, some proof summaries use `pass`, others use `overall_status`.

That is normal in a research lab, but production sovereignty requires one canonical envelope.

## 2. Canonical Event Chain

Every PNVA event should be representable as:

```text
field -> event -> tension -> gate -> collapse/block -> action -> proof
```

The canonical event schema is:

```text
schemas/pnva-event.schema.json
```

Minimum envelope:

```json
{
  "schema_version": "pnva.event.v1",
  "event_id": "evt_20260505_000001",
  "timestamp": "2026-05-05T00:00:00Z",
  "causal_chain_id": "chain_runtime_001",
  "entity_id": "zano-entity-00",
  "entity_type": "worker",
  "event_type": "ETEV_GUARD_PASS",
  "field": {
    "state_before": "observing",
    "state_after": "candidate",
    "phi": 0.42,
    "gradient": 0.10,
    "hessian": 0.02
  },
  "tension": {
    "score": 0.74,
    "threshold": 0.70,
    "margin": 0.01,
    "gate_delta": 0.03
  },
  "decision": {
    "kind": "collapse",
    "action": "EXECUTE",
    "reason": "signal_above_threshold",
    "confidence": 0.86
  },
  "heuristics": {
    "rules": ["adaptive_threshold", "etev_guard", "memory4d"],
    "risk_flags": []
  },
  "proof": {
    "proof_hash": "sha256:...",
    "proof_ref": "proofs/sanitized/prove-long-run-live-gate.json",
    "valid": true,
    "canonical": true
  }
}
```

## 3. Canonical Entity Model

Every important actor must have an entity identity:

```text
schemas/pnva-entity.schema.json
```

Entity types:

```text
field
event_source
worker
gate
guard
proof
memory
heuristic
publication
author
```

This prevents ambiguity. A worker, a gate, a proof and a publication page must not be mixed into the same conceptual bucket.

## 4. Heuristic Sovereignty

A heuristic is allowed to act only when it can explain:

```text
input signal
normalization
threshold
margin
decision
reason
confidence
proof reference
fallback mode
```

Heuristics must be classified:

| Class | Meaning | Production Rule |
| --- | --- | --- |
| H0 | observation only | never executes |
| H1 | advisory | emits recommendation |
| H2 | guarded action | requires threshold and proof |
| H3 | sovereign action | requires guard, rollback and proof |
| H4 | reclassification | requires explicit criteria and backup |

No heuristic should silently mutate production state without proof.

## 5. No-Tick Robustness Rules

PNVA/no-tick should preserve these invariants:

```text
do not wake without observable cause
do not execute without threshold
do not reclassify without criteria
do not publish raw logs without sanitization
do not hide transients
do not confuse local validation with universal proof
```

## 6. Entity Health

Each runtime entity should expose:

```text
entity_id
entity_type
state
last_seen
confidence
capabilities
risk_flags
proof_ref
```

Recommended health flags:

```text
MISSING_SCHEMA_VERSION
MISSING_ENTITY_ID
MISSING_CAUSAL_CHAIN
MISSING_PROOF_REF
THERMAL_PRESSURE_WITHOUT_SENSOR_SOURCE
FINAL_TRANSIENT_RECLASSIFIED
RAW_FAIL_CANONICAL_PASS
LOW_EVENT_DIVERSITY
HIGH_RESIZE_BATCH_RATIO
STALE_JOB_PRESSURE
```

These are not automatic failures. They are early warning signals.

## 7. Current Lab Reading

Local log inspection showed:

```text
pnva_decisions.jsonl: 17525 lines, 0 JSON parse errors
pnva-miner-events.jsonl: 9427 lines, 0 JSON parse errors
pnva_causal_events.jsonl: 12735 sealed causal records
zano_pnva_heuristics.jsonl: 1845 heuristic records with veonic fields
```

Dominant mining action:

```text
RESIZE_BATCH
```

Dominant pressure reason:

```text
cpu_host_thermal_taper
```

Engineering interpretation:

The runtime is conservative and event-aware. The next improvement is not to force aggression; it is to record thermal pressure provenance and separate thermal entity state from generic field tension.

## 8. Next Production Upgrade

Add a bridge layer:

```text
legacy log -> canonical pnva.event.v1 envelope -> sovereign audit report
```

This makes old logs useful without rewriting the validated runtime.

## 9. No-Tick Invariant Layer

After canonicalization and replay, run the no-tick invariant analyzer:

```text
canonical pnva.event.v1 -> replay validation -> no-tick invariant report
```

This layer proves that PNVA is not merely executing less. It proves that suppressed actions are also represented as auditable decisions.

Current public invariant report:

```text
reports/pnva-no-tick-invariants-2026-05-05.json
```

Current classification:

```text
SOVEREIGN_NO_TICK_READY
```

Core numbers:

```text
event_count: 512
collapse_count: 266
observe_count: 213
block_count: 33
suppressed_count: 246
no_tick_suppression_ratio: 0.4805
guard_consistency_ratio: 1.0
proof_integrity_ratio: 1.0
```

Production interpretation:

PNVA/no-tick becomes stronger when it can prove not only why it acted, but also why it refused to act.

## 10. Native Event Emission

The bridge keeps legacy logs useful. The native emitter defines the production direction:

```text
runtime -> pnva.event.v1 -> replay -> no-tick invariants -> sovereign audit
```

Native events must include:

```text
source.format = native_pnva_event_v1
proof.native = true
schema_version = pnva.event.v1
```

Current native demo:

```text
reports/pnva-native-events-demo-2026-05-05.jsonl
reports/pnva-native-entity-catalog-demo-2026-05-05.json
reports/pnva-native-emitter-summary-2026-05-05.json
```

Current classification:

```text
NATIVE_EMITTER_READY
```

Production interpretation:

New PNVA runtimes should not wait for post-processing to become auditable. They should emit canonical events at the moment of observation, collapse, block, proof or suppression.

## 11. Sovereign Policy Validation

The policy layer checks whether the decision had enough authority to act.

Strong decisions:

```text
collapse
block
prove
reclassify
```

Required policy for strong decisions:

```text
valid proof
entity in catalog
H2/H3/H4 authority
```

Legacy exception:

Old converted logs may contain strong decisions with only `legacy_observer`. These are not hidden and not silently promoted. They are preserved as warnings:

```text
SOVEREIGN_POLICY_READY_WITH_LEGACY_WARNINGS
```

Native expectation:

New events must be clean:

```text
SOVEREIGN_POLICY_READY
```

This creates a migration path: preserve old evidence honestly, but demand stronger authority from every new runtime event.

## 12. Proof-Chain Sealing

After replay, invariants and policy validation, seal the event sequence:

```text
pnva.event.v1 sequence -> proof chain -> final_chain_hash
```

The proof chain computes:

```text
event_hash = sha256(canonical_event_json)
chain_hash = sha256(index, previous_chain_hash, event_id, event_hash)
```

This makes event order externally auditable. If one event is changed, removed, inserted or reordered, the final chain hash changes.

Current canonical seal:

```text
PROOF_CHAIN_SEALED
512 events
0 bad proofs
```

Current native seal:

```text
PROOF_CHAIN_SEALED
7 events
0 bad proofs
```

Production interpretation:

PNVA evidence should not only be valid event by event. It should be sealed as a sequence.

## 13. Causal Graph Audit

Entity sovereignty requires topology.

After event validation and sequence sealing, build the causal graph:

```text
entities + relations + causal_chain_id -> causal graph
```

The graph audit checks:

```text
event entities exist in catalog
relation targets exist in catalog
observed entities are connected by chain or relation edges
graph_hash is stable
```

Current canonical graph:

```text
CAUSAL_GRAPH_READY
512 events
6 observed entities
68 relation edges
230 chain edges
```

Current native graph:

```text
CAUSAL_GRAPH_READY
7 events
6 observed entities
2 relation edges
6 chain edges
```

Production interpretation:

PNVA should expose not only decisions, but the topology of the field that made those decisions possible.

## 14. Schema Contract Validation

After graph topology, validate the structural envelope itself:

```text
pnva.event.v1 + pnva.entity.v1 -> schema contract validation
```

Current report:

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

Production interpretation:

PNVA evidence becomes stronger when every public event and entity can be checked for schema version, identity, causal chain, tension, decision, heuristic context, proof and sanitized source. The canonical legacy sample keeps its type-consolidation warnings visible. The native emitter scope has zero contract warnings.

## 15. Causal Chronology Guard

After structure validation, audit time as evidence:

```text
pnva.event.v1 timestamps + causal_chain_id -> causal chronology
```

Current report:

```text
reports/pnva-causal-chronology-2026-05-05.json
```

Current classification:

```text
CAUSAL_CHRONOLOGY_READY_WITH_LEGACY_WARNINGS
```

Current result:

```text
event_count: 519
chain_count: 15
global_backward_count: 1
error_count: 0
warning_count: 2
native_chronology_clean: true
```

Production interpretation:

PNVA/no-tick does not ignore time. It refuses to let time be the blind execution motor. Time remains a proof dimension: event order, chain order, gaps and batch compaction must be visible. The canonical legacy bridge keeps one temporal reset and timestamp compaction as warnings. The native path is monotonic and clean.

## 16. Tension Decision Calibration

After chronology, validate whether the decision agrees with the field tension:

```text
score + threshold + gate_delta + guard event -> decision calibration
```

Current report:

```text
reports/pnva-tension-decision-calibration-2026-05-05.json
```

Current classification:

```text
TENSION_DECISION_READY_WITH_LEGACY_WARNINGS
```

Current result:

```text
event_count: 519
error_count: 0
warning_count: 384
native_calibration_clean: true
legacy_calibration_warning_count: 384
```

Production interpretation:

PNVA/no-tick is stronger when every `collapse`, `block` and `observe` can be explained by the tension threshold that produced it. The canonical bridge preserves 384 legacy calibration warnings instead of hiding them. The native runtime path is calibrated clean: collapse/prove are positive decisions, block/observe are below-threshold decisions.

## 17. Sovereign Evidence Attestation

After all validators run, bind the evidence package:

```text
proofs + events + replay + invariants + policy + chains + graphs + schema contract + chronology + tension decision -> evidence_hash
```

The attestation lists each tracked artifact with:

```text
path
sha256
classification
pass flag
artifact counters
```

Current classification:

```text
PNVA_SOVEREIGN_EVIDENCE_ATTESTED
```

Current package:

```text
22 tracked artifacts
0 failures
```

Production interpretation:

PNVA evidence should be cited by a single aggregate hash, while still preserving every underlying proof file for independent review.

The sovereign audit is not included inside that aggregate hash because it consumes the attestation. This avoids circular hashing.

## 18. Adversarial Validation

A sovereign validator must prove that it rejects bad evidence, not only that it accepts clean evidence.

The adversarial validation layer runs controlled mutations against the public validators:

```text
proof hash tamper
low-authority strong decision
missing event entity
bad relation target
duplicate event id
event order tamper
malformed JSON line
```

Current report:

```text
reports/pnva-adversarial-validation-2026-05-05.json
```

Current classification:

```text
ADVERSARIAL_VALIDATION_PASS
```

Current result:

```text
7 detected mutations over 7 tests
```

Production interpretation:

PNVA evidence becomes more sovereign when validators have negative controls. A `PASS` is stronger when the same tooling can also show why corrupted proof, weak authority, invalid topology, duplicate identity, reordered sequence or malformed JSON does not pass silently.

## 19. Entity And Heuristic Maturity

After validation and adversarial controls, score the maturity of the actors and rules:

```text
entities + heuristics + authority + no-tick suppression + proof coverage -> maturity score
```

Current report:

```text
reports/pnva-entity-heuristic-maturity-2026-05-05.json
```

Current classification:

```text
ENTITY_HEURISTIC_MATURITY_READY_WITH_LEGACY_WARNINGS
```

Current aggregate:

```text
maturity_score: 94.59
total_event_count: 519
total_suppressed_count: 250
aggregate_no_tick_suppression_ratio: 0.481696
aggregate_hard_authority_ratio: 0.884868
canonical_low_authority_legacy_count: 35
native_low_authority_legacy_count: 0
error_count: 0
warning_count: 35
```

Production interpretation:

The canonical legacy bridge preserves 35 low-authority strong decisions as warnings. The native runtime path has zero low-authority legacy warnings. This creates a clean migration rule: old evidence stays honest; new PNVA runtimes must emit native events with H2/H3 authority.

## 20. Semantic Consistency Guard

After all evidence reports are generated, check whether they agree as a system:

```text
manifest + reports + audit + attestation -> semantic consistency
```

Current report:

```text
reports/pnva-semantic-consistency-2026-05-05.json
```

Current classification:

```text
SEMANTIC_CONSISTENCY_READY
```

Current result:

```text
check_count: 92
error_count: 0
warning_count: 0
```

Production interpretation:

PNVA evidence should not pass only as isolated files. The release is stronger when event counts, suppression counts, strong-decision counts, graph counts, chronology, tension-decision calibration, maturity math, Manifest metadata, audit summaries and attestation hashes all agree.

The semantic consistency report is not included in the attestation hash seed because it consumes the attestation.

## 21. Reproducibility Guard

After semantic consistency, rerun the current tools and compare stable fields against published reports:

```text
source commands -> temporary reports -> stable-field comparison -> reproducibility result
```

Current report:

```text
reports/pnva-reproducibility-2026-05-05.json
```

Current classification:

```text
REPRODUCIBILITY_READY
```

Current result:

```text
command_count: 18
comparison_count: 145
failure_count: 0
command_failure_count: 0
comparison_failure_count: 0
```

Production interpretation:

PNVA evidence becomes stronger when reports are not only internally consistent, but reproducible from the repository commands. This checks that replay, no-tick invariants, native emission, policy, proof-chain, graph, schema contract, chronology, tension-decision calibration, adversarial validation, maturity, attestation and semantic consistency can be regenerated without stable-field drift.

The reproducibility report is not included in the attestation hash seed because it consumes the attestation. This keeps the evidence graph acyclic.

## 22. Public Safety

Public repositories should expose:

```text
sanitized proof summaries
schemas
audit reports
architecture
paper
limits
publication metadata
```

Public repositories should not expose:

```text
raw local logs
private thresholds
private tuning
personal system paths
mining secrets
tokens
wallets
host-specific automation
```

## 23. Principle

PNVA becomes sovereign when every action can answer:

```text
who acted?
what field changed?
which tension crossed threshold?
which heuristic decided?
what proof sealed the decision?
what rollback exists if this was wrong?
```
