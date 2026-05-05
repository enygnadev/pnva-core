# Repository Publishing Checklist

Autor: Gustavo de Aguiar Martins  
Projeto: PNVA-Core / Enygnalab / EnyOS  
Repositorio alvo: https://github.com/enygnadev/pnva-core

Este checklist define a publicacao profissional do PNVA-Core como repositorio tecnico, academico e auditavel.

## 1. Antes de publicar

- Confirmar que o repositorio publico contem apenas `proofs/sanitized/`.
- Nao publicar `proofs/raw/` sem revisao manual.
- Confirmar que nenhum arquivo contem caminhos locais sensiveis.
- Confirmar que `MANIFEST.json` descreve somente os artefatos publicados.
- Confirmar que `SHA256SUMS.txt` valida todos os arquivos rastreados.
- Rodar a validacao local:

```bash
sha256sum -c SHA256SUMS.txt
python3 -m json.tool MANIFEST.json >/dev/null
for f in proofs/sanitized/*.json; do python3 -m json.tool "$f" >/dev/null; done
```

## 2. Criacao do repositorio

Nome recomendado:

```text
pnva-core
```

Descricao curta:

```text
Post-temporal causal architecture for state/event-oriented no-tick computation, with auditable proof logs.
```

Topicos GitHub:

```text
pnva
no-tick
causal-computing
event-driven
runtime
operating-systems
linux
observability
proof-logs
open-research
```

## 3. Primeiro commit

Mensagem recomendada:

```text
Initial PNVA-Core open research release
```

Tag recomendada:

```text
v0.1.0-production-evidence
```

## 4. GitHub Release

Titulo:

```text
PNVA-Core v0.1.0 - Production Evidence Open Research Release
```

Descricao curta:

```text
First public release of PNVA-Core, including architecture, validation protocol, proof matrix, sanitized JSON evidence and production-candidate PASS closure.
```

Anexar:

- pacote `.tar.gz` ou `.zip`;
- `SHA256SUMS.txt`;
- `MANIFEST.json`;
- paper em Markdown;
- provas sanitizadas.

## 5. Postagem publica

Usar:

```text
release/POST_01_PROFISSIONAL_AUTORAL.md
```

Publicar primeiro no LinkedIn ou Dev.to. Depois publicar o link no GitHub Discussions, se o repositorio estiver com Discussions ativo.

## 6. Ordem de leitura para visitantes

1. `README.md`
2. `docs/PNVA_ARCHITECTURE.md`
3. `docs/VALIDATION_PROTOCOL.md`
4. `docs/PROOF_MATRIX.md`
5. `docs/LIMITATIONS.md`
6. `paper/PNVA_CORE_OPEN_RESEARCH_PAPER.md`

## 7. Claim permitido

```text
PNVA/no-tick was locally validated in a live field with 15m, 8h, 12h, 24h, G1, guard rails, distribution-gate and production-candidate PASS, using auditable JSON proof logs and documented canonical reclassification criteria.
```

## 8. Claim proibido

Nao publicar:

```text
PNVA prova uma nova fisica.
PNVA substitui todo tick do Linux.
PNVA garante ganho universal.
PNVA elimina toda falha.
Veon e uma particula fisica descoberta.
```

## 9. Proxima camada

Depois da primeira publicacao:

- abrir issues para reproducao externa;
- preparar benchmark isolado loop vs PNVA;
- gerar paper PDF;
- conectar Zenodo para DOI;
- publicar o app visual como documentacao interativa;
- manter tuning comercial e thresholds sensiveis fora do repo publico.
