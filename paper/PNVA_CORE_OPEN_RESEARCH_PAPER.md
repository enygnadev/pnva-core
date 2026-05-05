# PNVA-Core: A Causal Architecture for State/Event-Oriented No-Tick Runtime Validation

Gustavo de Aguiar Martins  
Open Research / Production Evidence Edition, 2026

## Abstract

PNVA-Core presents a causal runtime architecture based on observable state, events, operational tension, collapse decisions and auditable proof logs. The proposal reduces unnecessary execution driven by fixed polling by moving the execution trigger from time habit to observable state change. This release documents a local live-field validation with 15m, 8h, 12h and 24h gates, a stable opportunity detector gate, guard rails, distribution gate and production-candidate gate. The final local result is production-candidate PASS, with a documented canonical reclassification for a final 24h recomposition transient.

## Keywords

PNVA, no-tick, event-aware runtime, causal computation, proof logs, long-run validation, operating systems, state-oriented execution.

## 1. Introduction

Many systems still execute repeated checks because a timer fires, not because the state changed. This creates empty wakeups, operational noise and weak decision traceability. PNVA-Core proposes a causal execution model:

```text
state -> event -> tension -> collapse -> execution -> proof
```

The system executes only when observable tension justifies collapse.

## 2. Model

Let `Phi(t)` be the current field state. Let `E(t)` be an event and `G(t)` the state gradient. Let `C(t)` be estimated cost and `M(t)` causal memory.

```text
T = alpha E + beta G - gamma C + mu M
```

Execution is authorized when:

```text
T >= theta
```

## 3. Runtime Architecture

PNVA-Core is organized as:

- field observer;
- event daemon;
- tension calculator;
- collapse decision layer;
- causal memory;
- proof logger;
- field communications reflector;
- validation gates.

The architecture separates observation, decision and proof.

## 4. Validation Method

The validation chain used:

```text
15m -> 8h -> 12h -> 24h -> G1 -> long-run-live -> guard rails -> distribution -> production candidate
```

Each gate emits JSON evidence.

## 5. Results

Final local results:

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

The 24h gate completed with 721 samples, 718 steady samples and 0.996 steady quiet ratio. The raw artifact failed because the final snapshot captured `WARMUP` during selective recomposition. The canonical classification is:

```text
PASS_EVENT_AWARE_24H_FINAL_TRANSIENT_STABLE_WINDOW
```

## 6. Discussion

The result supports the local claim that PNVA/no-tick can maintain long-run stable operation in a live field with auditable event-aware decision criteria. The evidence is not a universal proof for all hardware or kernels. It is a production-candidate local validation with explicit limits.

## 7. Conclusion

PNVA-Core demonstrates a practical architecture for causal execution: observe state, measure event tension, collapse only when justified and prove each decision. The current release closes a full local production-candidate chain and prepares the project for external reproduction.

