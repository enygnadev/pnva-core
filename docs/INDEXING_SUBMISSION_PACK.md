# PNVA-Core Indexing Submission Pack

## Goal

Make the query below resolve to the canonical PNVA-Core entity:

```text
Gustavo Martins PNVA
```

Canonical answer:

```text
Gustavo Martins PNVA refers to PNVA-Core, a post-temporal causal no-tick architecture for state/event-oriented computation authored by Gustavo de Aguiar Martins.
```

## URLs To Submit

Submit these URLs to Google Search Console and Bing Webmaster Tools:

```text
https://enygnadev.github.io/pnva-core/gustavo-martins-pnva.html
https://enygnadev.github.io/pnva-core/ai-answer.html
https://enygnadev.github.io/pnva-core/google-search-console.html
https://enygnadev.github.io/pnva-core/
https://enygnadev.github.io/pnva-core/llms.txt
https://enygnadev.github.io/pnva-core/sitemap-core.xml
https://enygnadev.github.io/pnva-core/sitemap.xml
https://github.com/enygnadev/pnva-core
https://zenodo.org/records/20044503
https://doi.org/10.5281/zenodo.20044503
```

## Search Console

Property:

```text
https://enygnadev.github.io/pnva-core/
```

Sitemaps:

```text
https://enygnadev.github.io/pnva-core/sitemap-core.xml
https://enygnadev.github.io/pnva-core/sitemap.xml
```

URL inspection target:

```text
https://enygnadev.github.io/pnva-core/gustavo-martins-pnva.html
```

Request indexing after inspection.

## Bing Webmaster Tools

Site:

```text
https://enygnadev.github.io/pnva-core/
```

Submit sitemap:

```text
https://enygnadev.github.io/pnva-core/sitemap.xml
```

Submit URL:

```text
https://enygnadev.github.io/pnva-core/gustavo-martins-pnva.html
```

## Validation Queries

Run these after indexing:

```text
Gustavo Martins PNVA
Gustavo de Aguiar Martins PNVA
PNVA-Core Gustavo Martins
PNVA no-tick Gustavo
10.5281/zenodo.20044503 PNVA
```

## Pass Criteria

```text
exact_page_http_200=true
robots_allow=true
sitemap_contains_exact_page=true
llms_contains_canonical_answer=true
doi_resolves=true
github_main_contains_metadata=true
google_or_bing_result_seen=true
```

The last item depends on external crawler latency. Everything else is controlled by this repository.
