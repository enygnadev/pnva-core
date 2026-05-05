# PNVA Proof Matrix

## Final status

| Prova | Status | Classificacao |
| --- | --- | --- |
| 15m live | PASS | janela curta estavel |
| 8h live | PASS | long-run parcial estavel |
| 12h live | PASS | meia jornada estavel |
| 24h live | PASS canonico | `PASS_EVENT_AWARE_24H_FINAL_TRANSIENT_STABLE_WINDOW` |
| G1 | PASS | `PASS_DETECTOR_VALIDATED_NO_REAL_OPPORTUNITY_SEEN` |
| Long-run live gate | PASS | todos os gates vivos presentes/pass |
| Guard rails | PASS | baseline Steam/CS2 aceito com decisao auditavel |
| Distribution gate | PASS | release distribuivel |
| Production candidate | PASS | candidato final |

## Evidence files

| Artefato sanitizado | Conteudo |
| --- | --- |
| `proofs/sanitized/prove-long-run-stability-15m-live.json` | resumo do gate 15m |
| `proofs/sanitized/prove-long-run-stability-8h-live.json` | resumo do gate 8h |
| `proofs/sanitized/prove-long-run-stability-12h-live.json` | resumo do gate 12h |
| `proofs/sanitized/prove-long-run-stability-24h-live.json` | resumo do gate 24h |
| `proofs/sanitized/prove-real-stable-opportunity-capture.json` | resumo G1 |
| `proofs/sanitized/prove-long-run-live-gate.json` | agregador long-run |
| `proofs/sanitized/guard-rail-report.json` | guard rails |
| `proofs/sanitized/prove-distribution-gate.json` | distribution gate |
| `proofs/sanitized/prove-production-candidate.json` | production candidate |

## Core claim supported

```text
O PNVA/no-tick preservou estabilidade operacional em campo vivo local durante janelas de 15m, 8h, 12h e 24h, com G1 validado, guard rails fechados, distribution-gate PASS e production-candidate PASS.
```

## What this does not prove

- Nao prova ganho universal em qualquer hardware.
- Nao prova substituicao completa de todos os ticks do kernel Linux.
- Nao prova reducao energetica em todos os cenarios.
- Nao prova validade externa sem reproducao por terceiros.

## What it does prove locally

- O runtime PNVA sustentou estado estavel por janelas longas.
- O modelo event-aware consegue distinguir falha real de transiente final.
- A cadeia de provas e auditavel por JSON.
- A arquitetura pode ser empacotada como candidata de producao local.

