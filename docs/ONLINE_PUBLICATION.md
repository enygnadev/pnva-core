# Online Publication Plan

## 1. Git repository

Criar um repositorio publico:

```text
pnva-core
```

Estrutura recomendada:

```text
README.md
LICENSE
LICENSE-DOCS
docs/
paper/
proofs/sanitized/
release/
tools/
```

Nao publicar `proofs/raw/` sem revisar.

## 2. GitHub Release

Criar tag:

```text
v0.1.0-production-evidence
```

Anexar:

- ZIP da release;
- `SHA256SUMS.txt`;
- `MANIFEST.json`;
- paper PDF/Markdown;
- provas sanitizadas.

## 3. GitHub Pages / Vercel

Publicar o app NextJS como visualizador de documentacao:

```text
appdoc-netx
```

Antes de subir:

- remover `node_modules`;
- publicar apenas fonte;
- garantir que APIs locais nao exponham caminhos de usuario, como `<HOME>`;
- usar conteudo sanitizado.

## 4. DOI

Depois do GitHub Release:

1. Conectar repo ao Zenodo.
2. Criar release GitHub.
3. Gerar DOI.
4. Inserir DOI no README e paper.

## 5. Preprint

Preparar preprint curto:

```text
PNVA-Core: A Causal Architecture for State/Event-Oriented No-Tick Runtime Validation
```

Enviar como:

- OSF Preprints;
- Zenodo;
- arXiv apenas se o texto estiver em formato academico suficiente.

## 6. Public claim

Usar sempre:

```text
local live-field validation
```

Evitar:

```text
universal proof
```

## 7. Arquivos finais de lancamento

Postagem autoral final:

```text
release/POST_01_PROFISSIONAL_AUTORAL.md
```

Checklist de publicacao:

```text
docs/REPOSITORY_PUBLISHING_CHECKLIST.md
```

Posicionamento publico:

```text
docs/PUBLIC_POSITIONING.md
```
