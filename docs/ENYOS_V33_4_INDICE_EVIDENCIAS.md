# ENY-OS v33.4 — indice da referencia oficial de certificacao

Selado em 17/11/2026. Este arquivo diz **onde esta cada prova** e, entre as execucoes
preservadas, **qual e a autoritativa**. As tentativas superadas foram mantidas de proposito:
documentam o caminho e os erros de metodo, e permitem auditar a conclusao.

## Artefato certificado

```
release/enyos-pnva-v33.4-20261116.iso
SHA-256   ac0e7c6cb929f2a84b0405c8edc0d5fb6279b89b2bb20ce46fabd67dd67cb40d
Assinatura RSA-4096 destacada: enyos-pnva-v33.4-20261116.iso.sig
Chave publica: enyos-pnva.pubkey.pem
```
Verificar: `sha256sum -c SHA256SUMS` e
`openssl dgst -sha256 -verify enyos-pnva.pubkey.pem -signature <iso>.sig <iso>`

## Documentos

| Arquivo | Conteudo |
|---|---|
| `CERTIFICACAO_v33.4.md` | Campanha completa, Fases 1–7, veredito por gate, metodos e ressalvas |
| `RELATORIO_FINAL_v33.4.md` | Fechamento de release (19 lacunas de empacotamento/rede) |
| `release/RELEASE_NOTES.md` | Notas publicas, requisito de topologia, tabela de gates |
| `REDE_DIAGNOSTICO.md` | Diagnostico de rede (netplan, NetworkManager, elo EnySync) |
| `BUILD_AUTOSSUFICIENTE.md` | Como gerar a ISO so a partir do projeto |
| `PROJETO_AUTOSSUFICIENTE.md` | Guardas de segredo e limites do empacotamento |
| `TUTORIAL_ENYSYNC.md` | Uso do EnySync e do controle visual |

## Evidencia por gate — qual arquivo vale

| Gate | Autoritativo | Resultado |
|---|---|---|
| **P1** identidade causal | `reports/P1_P3_ftrace_CLEAN_N900_8vcpu_20261116-203545.json` | 980/980 casados pelo `ts` de 64 bits, 0 duplicados, ordem preservada |
| **P1** corroboracao no host | `reports/P1_P5_A2_20261116-085524.json` | 30 toggles, kbus +73/+73, 0 drops, rollback limpo |
| **P3** T0–T2 sem ptrace | `reports/P1_P3_ftrace_CLEAN_N900_8vcpu_20261116-203545.json` | ring→Core p50 73 µs, overhead −0,5% |
| **P3** T3–T5 sem ptrace | `reports/P3_T3T5_FINAL_v334_20261116-214553.json` | contabilidade de bytes fecha, T5≥T4 em todos, fim a fim p50 8,50 ms |
| **P3** comparacao sob ptrace | `reports/P1_P3_P5_chain_VM_20261116-134643.json` | 60/60 casados; base da comparacao 8,7×–33× |
| **P5** ordem/duplicacao/entrega | `reports/P3_T3T5_FINAL_v334_20261116-214553.json` | 901/901 lotes lidos integralmente, ordem crescente |
| **P5** recuperacao do budget | `reports/vm-fase2/budget_watch.txt` | `budget_ok` NO→YES, `drops` de ring = 0 |
| **P6** falha induzida | `reports/vm-fase2/p6_verify_{1,2,3}.txt` | 3/3 ciclos, `recovery complete`, `fs_errors=0` |
| **P0/P2/P4** regressao final | `reports/vm-fase2/final_a.txt`, `reports/vm-fase7/final_t3.txt` | boot limpo, 20/20, No-Tick 1/0/0/0 |
| **Topologia** | `reports/vm-fase2/topo_{8,4pre,4post,4final}.txt` | 8 vCPU 6/6 ativos; 4 vCPU falha 215/CPUAFFINITY |
| **Correcao v33.4** | `reports/vm-fase7/final_t3.txt` | `systemctl --failed` vazio |

## Execucoes preservadas que **nao** sao autoritativas

Mantidas porque mostram metodos descartados e erros corrigidos — util para auditoria.

| Arquivo | Por que nao vale |
|---|---|
| `P1_P3_A1_20261115-140702.json` | Estimulo invalido: `governor=performance`, 0/50 casados |
| `P1_P3_A1bis_20261116-082703.json` | Abort: `open().write()` sem flush no meu harness |
| `P1_P3_A1bis2_20261116-083005.json` | Abort: readback do sysfs antes de assentar |
| `P1_P3_A1bis3_20261116-083322.json` | Negativo definitivo do estimulo cpufreq (kbus +0) |
| `P1_P3_P5_passive_20261116-085148.json` | Casador sem tolerancia de 1 ms (0 casados) |
| `P1_P3_P5_passive_20261116-085330.json` | Corrigido, mas N=1 — serve so para o achado estrutural |
| `P1_P3_P5_chain_VM_20261116-134508.json` | Regex de linha quebrada em `type=0x0101` (0 casados) |
| `P1_P3_ftrace_min8_20261116-202720.json` | Sondagem: 430/430 — primeira prova do ID, amostra menor |
| `P1_P3_ftrace_N900_8vcpu_20261116-203129.json` | Contaminada: filtro de `cmd` solto (1870 pops espurios) |
| `P3_T3T5_byteacct_v334_20261116-214326.json` | FIFO mal identificado (10628 em vez de 901) |
| `P3_T3T5_byteacct_v334_20261116-214409.json` | FIFO ok, mas T5 negativo (stream desalinhado) |
| `P3_T3T5_FINAL_v334_20261116-214450.json` | Ancoragem insuficiente, T5 ainda negativo |

## Artefatos brutos

- `reports/vm-fase2/` (36) — capturas sob ptrace, ciclos P6, topologia, harnesses
- `reports/vm-fase7/` (33) — captura ftrace sem ptrace, parser de contabilidade, verificacoes

## Integridade da referencia

`reports/MANIFEST_EVIDENCIAS.sha256` cobre todo JSON, artefato e documento.
Conferir: `sha256sum -c reports/MANIFEST_EVIDENCIAS.sha256`

Os arquivos de evidencia estao **somente leitura**. Para regerar qualquer medicao, os
harnesses estao preservados em `reports/vm-fase2/` e `reports/vm-fase7/`.

## Selo

Manifesto: `reports/MANIFEST_EVIDENCIAS.sha256` (97 arquivos, todos OK em 17/11/2026)
SHA-256 do proprio manifesto: `b6b606d1e8ca4b11e14b3c3fbd0245dbfbf0edbfad4dce924c30d0126ea93ccc`

Tudo acima esta `r--r--r--`. Para editar algum documento depois:
`chmod +w <arquivo>` — e entao regerar o manifesto, senao a verificacao acusa divergencia.

## Selo

Manifesto: `reports/MANIFEST_EVIDENCIAS.sha256` — 97 arquivos, todos verificados OK em
17/11/2026 (JSON de evidencia, artefatos brutos das Fases 2 e 7, documentos de certificacao,
notas de release, somas e chave publica).

Conferir a qualquer momento:
```bash
sha256sum -c reports/MANIFEST_EVIDENCIAS.sha256    # evidencias e documentos
cd release && sha256sum -c SHA256SUMS              # as 4 ISOs
openssl dgst -sha256 -verify enyos-pnva.pubkey.pem \
  -signature enyos-pnva-v33.4-20261116.iso.sig enyos-pnva-v33.4-20261116.iso
```

Todo o conjunto esta em modo somente leitura (`r--r--r--`), inclusive as ISOs. Para editar
um documento depois: `chmod +w <arquivo>`, editar, e **regerar o manifesto** — senao a
verificacao passa a acusar divergencia (que e exatamente o que ele existe para detectar).
