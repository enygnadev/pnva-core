# Google Search Console Distribution Plan

## Objective

Make Google associate these queries with the PNVA-Core entity:

```text
Gustavo Martins PNVA
Gustavo de Aguiar Martins PNVA
PNVA-Core Gustavo Martins
PNVA no-tick Gustavo
```

Canonical answer:

```text
Gustavo Martins PNVA refers to PNVA-Core, a post-temporal causal no-tick architecture for state/event-oriented computation authored by Gustavo de Aguiar Martins.
```

## What Google Allows

Google supports two practical discovery paths for ordinary documentation pages:

```text
1. URL Inspection -> Request indexing
2. Sitemap submission with updated <lastmod>
```

Google does not guarantee instant inclusion. Request indexing adds the URL to a crawl queue, and Google states that indexing can take days and sometimes longer.

The Google Indexing API is not the right mechanism for PNVA documentation because Google limits that API to pages with `JobPosting` or `BroadcastEvent` inside `VideoObject`.

The old sitemap ping endpoint should not be used; Google deprecated sitemap ping. Use `robots.txt` plus Search Console sitemap submission.

## Search Console Setup

Property type:

```text
URL prefix
```

Property:

```text
https://enygnadev.github.io/pnva-core/
```

Submit sitemaps:

```text
https://enygnadev.github.io/pnva-core/sitemap-core.xml
https://enygnadev.github.io/pnva-core/sitemap.xml
```

## URL Inspection Priority

Inspect and request indexing in this order:

```text
https://enygnadev.github.io/pnva-core/gustavo-martins-pnva.html
https://enygnadev.github.io/pnva-core/ai-answer.html
https://enygnadev.github.io/pnva-core/discovery-index.html
https://enygnadev.github.io/pnva-core/google-search-console.html
https://enygnadev.github.io/pnva-core/
https://enygnadev.github.io/pnva-core/entity.json
https://enygnadev.github.io/pnva-core/pnva-core.jsonld
https://enygnadev.github.io/pnva-core/codemeta.json
https://enygnadev.github.io/pnva-core/author.html
https://enygnadev.github.io/pnva-core/pnva-core.html
https://enygnadev.github.io/pnva-core/proofs.html
https://enygnadev.github.io/pnva-core/demo.html
https://enygnadev.github.io/pnva-core/llms.txt
```

## Near Real-Time Operating Loop

Use this loop after each important public update:

```text
1. Update the canonical page and related documentation.
2. Keep sitemap-core.xml focused on the highest-priority URLs.
3. Set <lastmod> to the real update date.
4. Push to GitHub Pages.
5. Run pnva_google_search_console_operator.py.
6. Submit sitemap-core.xml in Search Console.
7. Use URL Inspection on the priority URL.
8. Run Live Test.
9. Click Request Indexing if the page is indexable.
10. Monitor site: queries and Search Console coverage.
```

This is the fastest legitimate workflow for ordinary documentation pages. It is not a guarantee of instant indexing or ranking.

Automated operator:

```bash
python3 tools/pnva_google_search_console_operator.py --open-browser
```

Expected:

```text
PNVA_GOOGLE_SEARCH_CONSOLE_OPERATOR_READY
```

## External Authority URLs

These should be linked from LinkedIn, GitHub profile, repository description and any future article:

```text
https://zenodo.org/records/20044503
https://doi.org/10.5281/zenodo.20044503
https://github.com/enygnadev/pnva-core
```

## Official Google References

```text
URL-prefix properties can include a path:
https://support.google.com/webmasters/answer/10432366

Add and verify a Search Console property:
https://support.google.com/webmasters/answer/34592

URL Inspection and Request Indexing:
https://support.google.com/webmasters/answer/9012289

Ask Google to recrawl pages:
https://developers.google.com/search/docs/advanced/crawling/ask-google-to-recrawl

Indexing API scope:
https://developers.google.com/search/apis/indexing-api/v3/using-api

Sitemap ping deprecation:
https://developers.google.com/search/blog/2023/06/sitemaps-lastmod-ping
```

## Daily Monitoring Queries

```text
site:enygnadev.github.io/pnva-core "Gustavo Martins PNVA"
site:enygnadev.github.io/pnva-core "PNVA-Core"
"Gustavo Martins PNVA" "PNVA-Core"
"Gustavo de Aguiar Martins" "PNVA-Core"
"10.5281/zenodo.20044503" "PNVA"
```

## Pass Criteria

```text
gsc_property_verified=true
sitemap_core_submitted=true
sitemap_full_submitted=true
priority_url_inspected=true
priority_url_request_indexing_clicked=true
priority_url_live_test_indexable=true
site_query_returns_priority_url=true
```

## If Google Shows "Discovered - Currently Not Indexed"

Do not keep resubmitting blindly. Improve signals:

```text
1. Add internal links to the priority page.
2. Post the exact URL publicly on LinkedIn.
3. Link it from the GitHub repository About/website field.
4. Keep the page focused and non-duplicative.
5. Wait and recheck.
```
