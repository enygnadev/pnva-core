# PNVA Sovereignty Publication Scale

Base publica escolhida: `https://github.com/enygnadev`

## Objetivo

Publicar PNVA com reconhecimento, prioridade publica e autoridade tecnica, sem entregar cedo demais o motor comercial.

Soberania aqui significa:

```text
controlar autoria, narrativa, prova, codigo, marca e ritmo de abertura.
```

## Escala S0-S8

### S0 - Nucleo privado absoluto

Nao postar.

Conteudo:

- pesos reais;
- thresholds finos;
- tuning automatico;
- heuristicas comerciais;
- orquestracao sensivel;
- automacoes de renda;
- scripts que mexem em ambiente pessoal.

Meta:

```text
manter vantagem competitiva.
```

### S1 - Registro interno verificavel

Postar apenas hash/checksum ou manter privado.

Conteudo:

- `MANIFEST.json`;
- `SHA256SUMS.txt`;
- tarball privado;
- backups de reclassificacao;
- data/hora.

Meta:

```text
provar anterioridade sem abrir tudo.
```

### S2 - Evidencia sanitizada

Pode postar.

Conteudo:

- proofs sanitizados;
- matriz de PASS;
- production-candidate PASS;
- sem caminhos pessoais;
- sem logs brutos sensiveis.

Meta:

```text
mostrar que existe prova, sem expor intimidade do sistema.
```

### S3 - Arquitetura academica

Pode postar.

Conteudo:

- PNVA Architecture;
- Validation Protocol;
- Proof Matrix;
- Limitations;
- Paper;
- equacao veonica formal.

Meta:

```text
ganhar reconhecimento tecnico e academico.
```

### S4 - Release publica com DOI

Postar depois do GitHub.

Conteudo:

- GitHub release;
- Zenodo DOI;
- paper;
- provas sanitizadas;
- checksums.

Meta:

```text
tornar citavel.
```

### S5 - Codigo aberto minimo

Postar apenas nucleo demonstravel.

Conteudo:

- exemplo minimalista PNVA;
- runtime pequeno;
- benchmark loop vs PNVA;
- logs fake/sinteticos;
- sem motor comercial real.

Meta:

```text
permitir reproducao externa sem entregar produto.
```

### S6 - Comunidade e reproducao

Postar issues, roadmap e chamadas para reproducao.

Conteudo:

- templates de issue;
- comando de reproducao;
- metas de hardware externo;
- resultados de terceiros.

Meta:

```text
transformar ideia em movimento tecnico.
```

### S7 - Produto/licenca

Nao abrir completamente.

Conteudo:

- app visual;
- dashboard;
- agente local;
- pacote pago;
- consultoria;
- licenca dual.

Meta:

```text
gerar renda.
```

### S8 - Institucional/global

Postar como governanca, nao como hype.

Conteudo:

- whitepaper;
- aplicacoes juridicas/sociais/educacionais;
- etica;
- privacidade;
- auditoria;
- direito de contestacao.

Meta:

```text
adocao seria por instituicoes e pesquisadores.
```

## Ordem de publicacao escolhida

### Hoje - Postagem 1

Canal:

```text
GitHub perfil enygnadev + LinkedIn/Dev.to depois
```

Acao:

```text
criar repositorio pnva-core no github.com/enygnadev
subir apenas pnva-public-release sem proofs/raw
postar manifesto curto anunciando production-candidate PASS local
```

Nao postar hoje:

- codigo completo do orquestrador;
- thresholds privados;
- arquivos raw;
- scripts Steam/CS2;
- dados pessoais do sistema.

### Semana 1

1. GitHub publico.
2. README forte.
3. Release `v0.1.0-production-evidence`.
4. Zenodo DOI.
5. Post LinkedIn com link do DOI.

### Semana 2

1. Paper refinado em ingles.
2. OSF preprint.
3. App documental em GitHub Pages/Vercel.
4. Chamada para reproducao externa.

### Mes 1

1. Nucleo minimo open-source.
2. Benchmark loop vs PNVA.
3. Issues para reproducao.
4. Roadmap comercial.

### Mes 2-3

1. Produto fechado ou licenca dual.
2. Consultoria/implementacao.
3. Whitepaper setorial.
4. Busca de parceiros.

## Repositorios sugeridos

Principal:

```text
https://github.com/enygnadev/pnva-core
```

Alternativas:

```text
https://github.com/enygnadev/pnva-veonic-core
https://github.com/enygnadev/pnva-post-temporal
https://github.com/enygnadev/pnva-lab
```

Minha escolha:

```text
pnva-core
```

Motivo:

```text
e claro, serio, facil de citar e nao depende de explicar veonico logo no nome.
```

## Primeiro commit publico

Arquivos para subir:

```text
README.md
LICENSE
LICENSE-DOCS
MANIFEST.json
SHA256SUMS.txt
docs/
paper/
proofs/sanitized/
release/
tools/sanitize_proofs.py
```

Arquivos para NAO subir agora:

```text
proofs/raw/
node_modules/
.next/
scripts pessoais de sistema
logs brutos
arquivos Steam/CS2
qualquer caminho com dado sensivel
```

## Regra de ouro

```text
publicar prova e arquitetura;
proteger motor, tuning e produto.
```

