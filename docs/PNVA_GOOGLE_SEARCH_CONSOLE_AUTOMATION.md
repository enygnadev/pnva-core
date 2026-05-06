# PNVA Google Search Console Automation

## Purpose

This document defines the automated Google Search Console operating layer for PNVA-Core.

The goal is to make the public documentation discoverable as quickly as possible through legitimate Google mechanisms while preserving honest boundaries.

## Automated Operator

Run:

```bash
python3 tools/pnva_google_search_console_operator.py --open-browser
```

Expected classification:

```text
PNVA_GOOGLE_SEARCH_CONSOLE_OPERATOR_READY
```

The operator validates:

```text
public_urls_http_200
robots_exposes_google_and_sitemaps
sitemap_core_priority_closed
sitemap_full_contains_distribution_urls
canonical_exact_page_ready
gsc_distribution_page_ready
llms_discovery_ready
google_api_boundary_honest
```

It writes:

```text
reports/pnva-google-search-console-operator-2026-05-06.json
```

## Property

Use a URL-prefix property scoped exactly to the GitHub Pages site:

```text
https://enygnadev.github.io/pnva-core/
```

## Sitemaps

Submit:

```text
https://enygnadev.github.io/pnva-core/sitemap-core.xml
https://enygnadev.github.io/pnva-core/sitemap.xml
```

## Priority URL

Inspect first:

```text
https://enygnadev.github.io/pnva-core/gustavo-martins-pnva.html
```

Then:

```text
1. Run Live Test.
2. Confirm the URL is indexable.
3. Click Request Indexing.
```

## Optional Sitemap API Submission

Google provides a Search Console API endpoint for sitemap submission. It requires a verified property and an OAuth access token with Search Console permissions.

If an access token is available:

```bash
GOOGLE_SEARCH_CONSOLE_ACCESS_TOKEN=REDACTED \
python3 tools/pnva_google_search_console_operator.py --submit-sitemaps
```

Without OAuth, the operator records:

```text
SKIPPED_AUTH_REQUIRED
```

This is not a failure. It is the correct boundary for account-owned Google actions.

## What Cannot Be Fully Automated

Google does not provide a public generic-document API that clicks `Request Indexing` for ordinary documentation pages.

Manual or authenticated steps remain:

```text
verify_property
url_inspection_live_test
request_indexing_click
search_console_coverage_monitoring
```

## What Not To Use

Do not use the old sitemap ping endpoint. Google deprecated sitemap ping.

Do not use the Google Indexing API for PNVA documentation. Google restricts that API to `JobPosting` and `BroadcastEvent` pages.

## Operating Rhythm

For every major PNVA publication update:

```text
1. Update the canonical page and sitemap-core.xml.
2. Push to GitHub Pages.
3. Run pnva_google_search_console_operator.py.
4. Submit sitemap-core.xml in Search Console.
5. Inspect the priority URL.
6. Request indexing if live test is indexable.
7. Monitor site queries and Search Console coverage.
```

## Pass Criteria

```text
PNVA_GOOGLE_SEARCH_CONSOLE_OPERATOR_READY
priority_url_http_200=true
robots_googlebot_allowed=true
sitemap_core_contains_priority_url=true
canonical_answer_present=true
llms_context_present=true
gsc_property_verified=true
sitemap_core_submitted=true
priority_url_request_indexing_clicked=true
```

The first five criteria are automated by the repository. The last three belong to the verified Google account.
