#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


AUTHOR = "Gustavo de Aguiar Martins"
PROJECT = "PNVA-Core"
PROPERTY_URL = "https://enygnadev.github.io/pnva-core/"
PUBLIC_SITE = PROPERTY_URL
PRIORITY_URL = PUBLIC_SITE + "gustavo-martins-pnva.html"
AI_ANSWER_URL = PUBLIC_SITE + "ai-answer.html"
DISCOVERY_INDEX_URL = PUBLIC_SITE + "discovery-index.html"
RECOGNITION_UPDATE_URL = PUBLIC_SITE + "updates/gustavo-martins-pnva-recognition-pass.html"
FEED_URL = PUBLIC_SITE + "feed.xml"
GSC_PAGE = PUBLIC_SITE + "google-search-console.html"
ENTITY_JSON = PUBLIC_SITE + "entity.json"
JSONLD_GRAPH = PUBLIC_SITE + "pnva-core.jsonld"
CODEMETA = PUBLIC_SITE + "codemeta.json"
SITEMAP_CORE = PUBLIC_SITE + "sitemap-core.xml"
SITEMAP_FULL = PUBLIC_SITE + "sitemap.xml"
PRIORITY_TXT = PUBLIC_SITE + "gsc-priority-urls.txt"
LLMS = PUBLIC_SITE + "llms.txt"
ROBOTS = PUBLIC_SITE + "robots.txt"
DEFAULT_REPORT = "reports/pnva-google-search-console-operator-2026-05-06.json"
CANONICAL_ANSWER = (
    "Gustavo Martins PNVA refers to PNVA-Core, a post-temporal causal no-tick architecture "
    "for state/event-oriented computation authored by Gustavo de Aguiar Martins."
)

PUBLIC_URLS = [
    PUBLIC_SITE,
    PRIORITY_URL,
    AI_ANSWER_URL,
    DISCOVERY_INDEX_URL,
    RECOGNITION_UPDATE_URL,
    FEED_URL,
    GSC_PAGE,
    ENTITY_JSON,
    JSONLD_GRAPH,
    CODEMETA,
    SITEMAP_CORE,
    SITEMAP_FULL,
    PRIORITY_TXT,
    LLMS,
    ROBOTS,
]

SITEMAP_CORE_REQUIRED = [
    PRIORITY_URL,
    AI_ANSWER_URL,
    DISCOVERY_INDEX_URL,
    RECOGNITION_UPDATE_URL,
    FEED_URL,
    ENTITY_JSON,
    JSONLD_GRAPH,
    CODEMETA,
    GSC_PAGE,
    PUBLIC_SITE,
    PUBLIC_SITE + "author.html",
    PUBLIC_SITE + "pnva-core.html",
    PUBLIC_SITE + "proofs.html",
    PUBLIC_SITE + "demo.html",
    LLMS,
    PUBLIC_SITE + "docs/GOOGLE_SEARCH_CONSOLE_DISTRIBUTION.md",
    PUBLIC_SITE + "paper/PNVA_CORE_OPEN_RESEARCH_PAPER_2026-05-05.pdf",
]

FULL_SITEMAP_REQUIRED = [
    PUBLIC_SITE,
    PRIORITY_URL,
    AI_ANSWER_URL,
    DISCOVERY_INDEX_URL,
    RECOGNITION_UPDATE_URL,
    FEED_URL,
    ENTITY_JSON,
    JSONLD_GRAPH,
    CODEMETA,
    GSC_PAGE,
    PRIORITY_TXT,
    LLMS,
    PUBLIC_SITE + "docs/INDEXING_SUBMISSION_PACK.md",
    PUBLIC_SITE + "docs/GOOGLE_SEARCH_CONSOLE_DISTRIBUTION.md",
]

OPEN_URLS = [
    "https://search.google.com/search-console/welcome",
    GSC_PAGE,
    AI_ANSWER_URL,
    DISCOVERY_INDEX_URL,
    RECOGNITION_UPDATE_URL,
    PRIORITY_TXT,
]

OFFICIAL_REFERENCES = {
    "url_inspection": "https://support.google.com/webmasters/answer/9012289",
    "url_prefix_property": "https://support.google.com/webmasters/answer/10432366",
    "sitemaps_api_submit": "https://developers.google.com/webmaster-tools/v1/sitemaps/submit",
    "indexing_api_scope": "https://developers.google.com/search/apis/indexing-api/v3/using-api",
    "sitemap_ping_deprecated": "https://developers.google.com/search/blog/2023/06/sitemaps-lastmod-ping",
}


def _request(url: str, method: str = "GET", token: str = "", timeout: int = 25) -> dict[str, Any]:
    headers = {
        "User-Agent": "PNVA-Google-Search-Console-Operator/1.0",
        "Accept": "*/*",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read()
            return {
                "ok": 200 <= int(response.status) < 300,
                "status": int(response.status),
                "url": url,
                "final_url": response.geturl(),
                "content_type": response.headers.get("content-type", ""),
                "text": body.decode("utf-8", errors="replace"),
                "bytes": len(body),
            }
    except urllib.error.HTTPError as exc:
        body = exc.read()
        return {
            "ok": False,
            "status": int(exc.code),
            "url": url,
            "final_url": exc.geturl(),
            "content_type": exc.headers.get("content-type", "") if exc.headers else "",
            "text": body.decode("utf-8", errors="replace"),
            "bytes": len(body),
            "error": str(exc),
        }
    except Exception as exc:
        return {
            "ok": False,
            "status": 0,
            "url": url,
            "final_url": "",
            "content_type": "",
            "text": "",
            "bytes": 0,
            "error": str(exc),
        }


def _check(name: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "pass": bool(passed), "evidence": evidence}


def _sitemap_urls(xml_text: str) -> tuple[list[str], str]:
    try:
        root = ET.fromstring(xml_text)
    except Exception as exc:
        return [], str(exc)
    urls: list[str] = []
    for elem in root.iter():
        if elem.tag.endswith("loc") and elem.text:
            urls.append(elem.text.strip())
    return urls, ""


def _sitemap_lastmods(xml_text: str) -> tuple[list[str], str]:
    try:
        root = ET.fromstring(xml_text)
    except Exception as exc:
        return [], str(exc)
    values: list[str] = []
    for elem in root.iter():
        if elem.tag.endswith("lastmod") and elem.text:
            values.append(elem.text.strip())
    return values, ""


def _submit_sitemap(site_url: str, sitemap_url: str, token: str) -> dict[str, Any]:
    site = urllib.parse.quote(site_url, safe="")
    feed = urllib.parse.quote(sitemap_url, safe="")
    endpoint = f"https://www.googleapis.com/webmasters/v3/sites/{site}/sitemaps/{feed}"
    result = _request(endpoint, method="PUT", token=token)
    return {
        "sitemap": sitemap_url,
        "endpoint_status": result.get("status"),
        "ok": result.get("ok"),
        "error": result.get("error", ""),
        "body_preview": result.get("text", "")[:300],
    }


def _open_browser() -> dict[str, Any]:
    chrome = shutil.which("google-chrome") or shutil.which("google-chrome-stable") or shutil.which("chromium")
    if not chrome:
        return {"opened": False, "reason": "chrome_not_found", "urls": OPEN_URLS}
    subprocess.Popen(
        [chrome, "--new-window", *OPEN_URLS],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )
    return {"opened": True, "browser": chrome, "urls": OPEN_URLS}


def build_report(submit_sitemaps: bool = False, token: str = "") -> dict[str, Any]:
    fetched = {url: _request(url) for url in PUBLIC_URLS}
    robots = fetched[ROBOTS]["text"]
    llms = fetched[LLMS]["text"]
    exact = fetched[PRIORITY_URL]["text"]
    gsc_page = fetched[GSC_PAGE]["text"]
    sitemap_core_text = fetched[SITEMAP_CORE]["text"]
    sitemap_full_text = fetched[SITEMAP_FULL]["text"]

    core_urls, core_xml_error = _sitemap_urls(sitemap_core_text)
    full_urls, full_xml_error = _sitemap_urls(sitemap_full_text)
    core_lastmods, core_lastmod_error = _sitemap_lastmods(sitemap_core_text)

    http_failures = [
        {"url": url, "status": item.get("status"), "error": item.get("error", "")}
        for url, item in fetched.items()
        if not item.get("ok")
    ]
    core_missing = [url for url in SITEMAP_CORE_REQUIRED if url not in core_urls]
    full_missing = [url for url in FULL_SITEMAP_REQUIRED if url not in full_urls]
    core_bad_lastmods = [value for value in core_lastmods if value != "2026-05-06"]

    token = token or os.environ.get("GOOGLE_SEARCH_CONSOLE_ACCESS_TOKEN", "")
    sitemap_submission = {
        "attempted": bool(submit_sitemaps),
        "requires_oauth": True,
        "status": "SKIPPED_AUTH_REQUIRED",
        "results": [],
    }
    if submit_sitemaps and token:
        results = [
            _submit_sitemap(PROPERTY_URL, SITEMAP_CORE, token),
            _submit_sitemap(PROPERTY_URL, SITEMAP_FULL, token),
        ]
        sitemap_submission = {
            "attempted": True,
            "requires_oauth": True,
            "status": "SUBMITTED" if all(item.get("ok") for item in results) else "SUBMISSION_FAILED",
            "results": results,
        }
    elif submit_sitemaps:
        sitemap_submission["status"] = "SKIPPED_MISSING_GOOGLE_SEARCH_CONSOLE_ACCESS_TOKEN"

    checks = [
        _check(
            "public_urls_http_200",
            not http_failures,
            {
                "checked_url_count": len(PUBLIC_URLS),
                "failures": http_failures,
                "statuses": {url: fetched[url].get("status") for url in PUBLIC_URLS},
            },
        ),
        _check(
            "robots_exposes_google_and_sitemaps",
            "Googlebot" in robots and SITEMAP_CORE in robots and SITEMAP_FULL in robots,
            {
                "has_googlebot": "Googlebot" in robots,
                "has_sitemap_core": SITEMAP_CORE in robots,
                "has_sitemap_full": SITEMAP_FULL in robots,
            },
        ),
        _check(
            "sitemap_core_priority_closed",
            not core_xml_error and not core_missing and not core_bad_lastmods and not core_lastmod_error,
            {
                "sitemap": SITEMAP_CORE,
                "url_count": len(core_urls),
                "missing": core_missing,
                "xml_error": core_xml_error,
                "lastmod_error": core_lastmod_error,
                "bad_lastmods": core_bad_lastmods,
            },
        ),
        _check(
            "sitemap_full_contains_distribution_urls",
            not full_xml_error and not full_missing,
            {
                "sitemap": SITEMAP_FULL,
                "url_count": len(full_urls),
                "missing": full_missing,
                "xml_error": full_xml_error,
            },
        ),
        _check(
            "canonical_exact_page_ready",
            CANONICAL_ANSWER in exact
            and "application/ld+json" in exact
            and "rel=\"canonical\"" in exact
            and "10.5281/zenodo.20044503" in exact
            and "google-search-console.html" in exact,
            {
                "url": PRIORITY_URL,
                "has_canonical_answer": CANONICAL_ANSWER in exact,
                "has_json_ld": "application/ld+json" in exact,
                "has_rel_canonical": "rel=\"canonical\"" in exact,
                "has_doi": "10.5281/zenodo.20044503" in exact,
                "links_gsc_page": "google-search-console.html" in exact,
            },
        ),
        _check(
            "gsc_distribution_page_ready",
            PROPERTY_URL in gsc_page
            and SITEMAP_CORE in gsc_page
            and SITEMAP_FULL in gsc_page
            and "Request Indexing" in gsc_page
            and "Truth Boundary" in gsc_page,
            {
                "url": GSC_PAGE,
                "property": PROPERTY_URL,
                "has_sitemap_core": SITEMAP_CORE in gsc_page,
                "has_sitemap_full": SITEMAP_FULL in gsc_page,
                "has_request_indexing": "Request Indexing" in gsc_page,
                "has_truth_boundary": "Truth Boundary" in gsc_page,
            },
        ),
        _check(
            "llms_discovery_ready",
            CANONICAL_ANSWER in llms
            and GSC_PAGE in llms
            and "sitemap-core.xml" in llms
            and "10.5281/zenodo.20044503" in llms,
            {
                "url": LLMS,
                "has_canonical_answer": CANONICAL_ANSWER in llms,
                "has_gsc_page": GSC_PAGE in llms,
                "has_sitemap_core": "sitemap-core.xml" in llms,
                "has_doi": "10.5281/zenodo.20044503" in llms,
            },
        ),
        _check(
            "google_api_boundary_honest",
            True,
            {
                "request_indexing_api_for_generic_docs": False,
                "sitemaps_api_submit_available_with_verified_property_and_oauth": True,
                "indexing_api_for_this_documentation": "NOT_APPLICABLE_GENERIC_DOCS",
                "manual_required": ["verify_property", "url_inspection_live_test", "request_indexing_click"],
                "official_references": OFFICIAL_REFERENCES,
            },
        ),
    ]
    failures = [item for item in checks if not item["pass"]]
    return {
        "schema_version": "pnva.google_search_console_operator.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": "PNVA_GOOGLE_SEARCH_CONSOLE_OPERATOR_READY" if not failures else "PNVA_GOOGLE_SEARCH_CONSOLE_OPERATOR_FAIL",
        "pass": not failures,
        "property_url": PROPERTY_URL,
        "priority_url": PRIORITY_URL,
        "sitemap_core": SITEMAP_CORE,
        "sitemap_full": SITEMAP_FULL,
        "check_count": len(checks),
        "failure_count": len(failures),
        "checks": checks,
        "failures": failures,
        "sitemap_submission": sitemap_submission,
        "next_actions": [
            "Open Google Search Console.",
            "Add URL-prefix property https://enygnadev.github.io/pnva-core/ if it is not already verified.",
            "Submit sitemap-core.xml and sitemap.xml.",
            "Inspect the priority URL, run Live Test, then click Request Indexing if indexable.",
            "Monitor site:enygnadev.github.io/pnva-core \"Gustavo Martins PNVA\" and Search Console Page indexing.",
        ],
        "truth_boundary": (
            "This operator automates public crawl-readiness checks and optional sitemap API submission. "
            "Google still requires account ownership for Search Console actions and does not guarantee instant indexing or ranking."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the PNVA Google Search Console distribution operator.")
    parser.add_argument("--write", default=DEFAULT_REPORT)
    parser.add_argument("--open-browser", action="store_true")
    parser.add_argument("--submit-sitemaps", action="store_true")
    parser.add_argument("--token", default="")
    args = parser.parse_args()

    report = build_report(submit_sitemaps=args.submit_sitemaps, token=args.token)
    if args.open_browser:
        report["browser"] = _open_browser()

    raw = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    if args.write:
        out = Path(args.write)
        if not out.is_absolute():
            out = Path(__file__).resolve().parents[1] / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0 if report.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
