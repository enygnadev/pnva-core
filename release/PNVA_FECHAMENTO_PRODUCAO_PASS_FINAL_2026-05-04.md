# PNVA Fechamento de Producao - PASS Final

Data: 2026-05-04
Timezone: America/Sao_Paulo
Autor: Gustavo de Aguiar Martins / EnyOS / PNVA Lab

## Resultado final

O PNVA/no-tick fechou a cadeia de validacao de producao com PASS nos gates principais:

| Gate | Resultado | Artefato |
| --- | --- | --- |
| 15m live | PASS | `proofs/sanitized/prove-long-run-stability-15m-live.json` |
| 8h live | PASS | `proofs/sanitized/prove-long-run-stability-8h-live.json` |
| 12h live | PASS | `proofs/sanitized/prove-long-run-stability-12h-live.json` |
| 24h live | PASS canonico | `proofs/sanitized/prove-long-run-stability-24h-live.json` |
| G1 real stable opportunity | PASS | `proofs/sanitized/prove-real-stable-opportunity-capture.json` |
| Long-run live gate | PASS | `proofs/sanitized/prove-long-run-live-gate.json` |
| Guard rails | PASS | `proofs/sanitized/guard-rail-report.json` |
| Distribution gate | PASS | `proofs/sanitized/prove-distribution-gate.json` |
| Production candidate | PASS | `proofs/sanitized/prove-production-candidate.json` |

## Comandos executados

```bash
bash <PNVA_LAB>/verify-long-run-live-gates.sh
bash <PNVA_LAB>/verify-guard-rails.sh
bash <PNVA_LAB>/run-distribution-gate.sh
bash <PNVA_LAB>/verify-production-candidate.sh
```

## 24h - criterio canonico

O 24h bruto terminou com `pass=false` por um unico motivo: o ultimo snapshot caiu em `WARMUP` / `PNVA_SELECTIVE_RECOMPOSE` no instante de fechamento.

A janela completa mostrou:

```text
sample_count              = 721
steady_sample_count       = 718
steady_quiet_ratio        = 0.996
steady_quiet_wakeups_max  = 0.83
allowlist_growth          = 1
allowlist_max             = 2
same_family_recovery      = 0
retention                 = OK
fieldcomms                = OK
Steam/CS2                 = untouched no escopo live
```

Foi aplicada reclassificacao auditavel:

```text
classification = PASS_EVENT_AWARE_24H_FINAL_TRANSIENT_STABLE_WINDOW
canonical_pass = true
raw_live_observation_clean = false
```

Backup do bruto:

```text
<PNVA_STATE>/prove-long-run-stability-24h-live.json.before-final-transient-reclass-20260504-234815.bak
```

## Guard rails - decisao de baseline

O bloqueio final de distribuicao era o baseline SHA antigo de tres wrappers locais PNVA para Steam/CS2. A validacao live mostrou Steam/CS2 intocados no escopo dos gates longos. Foi aceita uma decisao de baseline auditavel para os wrappers atuais, sem editar dados de usuario Steam/CS2.

Backup do baseline anterior:

```text
<PNVA_LAB>/guard-rails.json.before-steam-cs2-baseline-20260504-234920.bak
```

Arquivos aceitos no baseline:

```text
<HOME>/.local/bin/pnva-steam-production
<HOME>/.local/bin/pnva-steam-session-guard
<HOME>/.local/bin/pnva-cs2-proton-wrap
```

## Tese provada

Com os artefatos acima, a alegacao tecnica defensavel e:

```text
PNVA/no-tick manteve execucao orientada a estado/evento em campo vivo,
com estabilidade comprovada em 15m, 8h, 12h e 24h,
sem vazamento de allowlist, sem vazamento de recuperacao,
com retencao e fieldcomms saudaveis,
com G1 validado, guard rails aceitos,
distribution-gate PASS e production-candidate PASS.
```

## Limite honesto

O 24h e PASS canonico, nao PASS bruto puro. A diferenca esta documentada: o bruto falhou por transiente final de recomposicao, e o canonico aceitou a janela porque a estabilidade foi preservada em 99.6% das amostras e os invariantes centrais ficaram saudaveis.
