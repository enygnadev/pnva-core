# PNVA Validation Protocol

## Objetivo

Validar se PNVA/no-tick permanece estavel em campo vivo e se a cadeia de producao pode ser marcada como candidata.

## Gates

| Gate | Objetivo | Resultado |
| --- | --- | --- |
| `15m` | estabilidade curta e entrada em STEADY | PASS |
| `8h` | jornada longa parcial | PASS |
| `12h` | meia jornada estavel | PASS |
| `24h` | ciclo completo de um dia | PASS canonico |
| `G1` | captura/validacao de oportunidade estavel | PASS |
| `long-run-live-gate` | agregacao dos gates longos | PASS |
| `guard rails` | protecao de limites sensiveis | PASS |
| `distribution-gate` | pronto para empacotar | PASS |
| `production-candidate` | candidato final | PASS |

## Criterios centrais

Um gate vivo deve preservar:

- runtime em janela majoritariamente `STEADY`;
- baixo `steady_quiet_wakeups_max`;
- allowlist sem vazamento;
- recuperacao same-family sem crescimento indevido;
- retencao de eventos e logs dentro do limite;
- fieldcomms ativo e coerente;
- monotonicidade de prova;
- guard rails intactos ou rebaseline explicitamente documentada.

## Regra de reclassificacao canonica

Reclassificacao so e permitida quando:

1. O artefato bruto e preservado em backup.
2. O novo resultado registra `raw_pass_before_reclassification`.
3. A classificacao canonica explica a causa.
4. Os invariantes centrais passaram.
5. A decisao e documentada.

## 24h final transient rule

O 24h pode ser PASS canonico se:

```text
steady_quiet_ratio >= 0.94
steady_sample_count >= sample_count - 3
steady_quiet_wakeups_max <= 3.2
allowlist_max <= 3
allowlist_growth <= 2
same_family_recovery_growth <= 1
previous_sample.runtime_phase == STEADY
final_sample.runtime_phase == WARMUP
previous_sample.dirty_area_pct <= 1.0
retention == OK
fieldcomms == OK
guard scope == untouched
```

Essa regra cobre transiente de recomposicao no fechamento, sem aceitar drift real prolongado.

## G1 rule

O G1 passa em dois casos:

```text
oportunidade real capturada -> PASS_REAL_STABLE_OPPORTUNITY_CAPTURED
sem oportunidade real + detector sintetico PASS -> PASS_DETECTOR_VALIDATED_NO_REAL_OPPORTUNITY_SEEN
```

O G1 falha se uma oportunidade fica pendente/candidata e o detector nao prova captura nem ausencia legitima.

## Comandos finais

```bash
bash <PNVA_LAB>/verify-long-run-live-gates.sh
bash <PNVA_LAB>/verify-guard-rails.sh
bash <PNVA_LAB>/run-distribution-gate.sh
bash <PNVA_LAB>/verify-production-candidate.sh
```

## Artefatos publicos recomendados

Use `proofs/sanitized/` para publicacao. Revise `proofs/raw/` antes de publicar, pois pode conter caminhos locais ou trechos de logs.
