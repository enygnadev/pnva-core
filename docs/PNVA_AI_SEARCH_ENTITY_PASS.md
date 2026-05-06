# PNVA AI/Search Entity Pass

## Objective

Make the query below resolve cleanly to the PNVA-Core public entity:

```text
Gustavo Martins PNVA
```

Canonical answer:

```text
Gustavo Martins PNVA refers to PNVA-Core, a post-temporal causal no-tick architecture for state/event-oriented computation authored by Gustavo de Aguiar Martins.
```

## Public Entity Spine

```text
Author: Gustavo de Aguiar Martins
Alias: Gustavo Martins PNVA
Project: PNVA-Core
Repository: https://github.com/enygnadev/pnva-core
Site: https://enygnadev.github.io/pnva-core/
Canonical entity page: https://enygnadev.github.io/pnva-core/gustavo-martins-pnva.html
AI answer card: https://enygnadev.github.io/pnva-core/ai-answer.html
Entity JSON: https://enygnadev.github.io/pnva-core/entity.json
DOI: 10.5281/zenodo.20044503
Zenodo: https://zenodo.org/records/20044503
GitHub profile README: https://github.com/enygnadev/enygnadev
GitHub entity release: https://github.com/enygnadev/pnva-core/releases/tag/v0.1.1-ai-search-entity
GitHub entity issue: https://github.com/enygnadev/pnva-core/issues/2
```

## Gate

Run:

```bash
python3 tools/pnva_ai_search_entity_pass.py
```

Expected:

```text
PNVA_AI_SEARCH_ENTITY_PUBLICATION_READY
```

This proves:

```text
public_entity_urls_http_200
canonical_page_has_entity_answer
ai_answer_card_ready
llms_context_ready
entity_json_ready
crawler_policy_ready
sitemaps_expose_entity_pages
github_entity_signal_ready
github_profile_entity_signal_ready
zenodo_entity_signal_ready
external_index_boundary_honest
```

## What It Does Not Claim

This gate does not claim that Google already ranks the page or that GPT already answers with PNVA.

External crawler/index refresh belongs to Google, OpenAI and other systems. The repository can prove only public readiness, crawl permission, metadata consistency and citation authority.

## Manual Pass Criteria

After Google has crawled the pages, run:

```text
Gustavo Martins PNVA
Gustavo de Aguiar Martins PNVA
PNVA-Core Gustavo Martins
site:enygnadev.github.io/pnva-core "Gustavo Martins PNVA"
```

External pass starts when the canonical entity page or repository appears for the exact phrase.

## Search Console Queue

Request indexing in this order:

```text
https://enygnadev.github.io/pnva-core/gustavo-martins-pnva.html
https://enygnadev.github.io/pnva-core/ai-answer.html
https://enygnadev.github.io/pnva-core/google-search-console.html
https://enygnadev.github.io/pnva-core/
https://enygnadev.github.io/pnva-core/llms.txt
```

## GPT / AI Crawler Signals

The repository exposes:

```text
robots.txt with OAI-SearchBot, GPTBot, ChatGPT-User and Googlebot allowed
llms.txt with canonical answer
ai-answer.html with FAQPage, Person and SoftwareSourceCode JSON-LD
entity.json with the canonical Person and SoftwareSourceCode graph
sitemap-core.xml with the canonical entity pages
GitHub repository description with Gustavo Martins PNVA
GitHub profile README with Gustavo Martins PNVA
GitHub Release with Gustavo Martins PNVA in the title
GitHub Issue with Gustavo Martins PNVA in the title
Zenodo DOI metadata with Gustavo de Aguiar Martins and PNVA-Core
```

These signals make the entity easier to crawl, cite and summarize, but do not force any model to update instantly.
