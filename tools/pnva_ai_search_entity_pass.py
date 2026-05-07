#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


AUTHOR = "Gustavo de Aguiar Martins"
PROJECT = "PNVA-Core"
PUBLIC_SITE = "https://enygnadev.github.io/pnva-core/"
CANONICAL_URL = PUBLIC_SITE + "gustavo-martins-pnva.html"
AI_ANSWER_URL = PUBLIC_SITE + "ai-answer.html"
DISCOVERY_INDEX_URL = PUBLIC_SITE + "discovery-index.html"
RECOGNITION_UPDATE_URL = PUBLIC_SITE + "updates/gustavo-martins-pnva-recognition-pass.html"
FEED_URL = PUBLIC_SITE + "feed.xml"
LLMS_URL = PUBLIC_SITE + "llms.txt"
HUMANS_URL = PUBLIC_SITE + "humans.txt"
ENTITY_URL = PUBLIC_SITE + "entity.json"
JSONLD_URL = PUBLIC_SITE + "pnva-core.jsonld"
CODEMETA_URL = PUBLIC_SITE + "codemeta.json"
ROBOTS_URL = PUBLIC_SITE + "robots.txt"
SITEMAP_CORE_URL = PUBLIC_SITE + "sitemap-core.xml"
SITEMAP_FULL_URL = PUBLIC_SITE + "sitemap.xml"
GITHUB_API_URL = "https://api.github.com/repos/enygnadev/pnva-core"
GITHUB_PROFILE_API_URL = "https://api.github.com/repos/enygnadev/enygnadev"
GITHUB_RELEASE_API_URL = "https://api.github.com/repos/enygnadev/pnva-core/releases/tags/v0.1.1-ai-search-entity"
GITHUB_RECOGNITION_RELEASE_API_URL = "https://api.github.com/repos/enygnadev/pnva-core/releases/tags/v0.1.2-recognition-feed"
GITHUB_ISSUE_API_URL = "https://api.github.com/repos/enygnadev/pnva-core/issues/2"
GITHUB_GIST_URL = "https://gist.github.com/enygnadev/ca6cdad84bbdc52a0edb690c9b2a6672"
GITHUB_GIST_API_URL = "https://api.github.com/gists/ca6cdad84bbdc52a0edb690c9b2a6672"
ZENODO_URL = "https://zenodo.org/records/20044503"
DEFAULT_REPORT = "reports/pnva-ai-search-entity-pass-2026-05-06.json"

CANONICAL_ANSWER = (
    "Gustavo Martins PNVA refers to PNVA-Core, a post-temporal causal no-tick architecture "
    "for state/event-oriented computation authored by Gustavo de Aguiar Martins."
)

PUBLIC_URLS = [
    CANONICAL_URL,
    AI_ANSWER_URL,
    DISCOVERY_INDEX_URL,
    RECOGNITION_UPDATE_URL,
    FEED_URL,
    LLMS_URL,
    HUMANS_URL,
    ENTITY_URL,
    JSONLD_URL,
    CODEMETA_URL,
    ROBOTS_URL,
    SITEMAP_CORE_URL,
    SITEMAP_FULL_URL,
    ZENODO_URL,
]


def _fetch(url: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "PNVA-AI-Search-Entity-Pass/1.0",
            "Accept": "*/*",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            body = response.read()
            return {
                "ok": 200 <= int(response.status) < 300,
                "status": int(response.status),
                "url": url,
                "final_url": response.geturl(),
                "text": body.decode("utf-8", errors="replace"),
                "bytes": len(body),
                "content_type": response.headers.get("content-type", ""),
            }
    except Exception as exc:
        return {
            "ok": False,
            "status": 0,
            "url": url,
            "final_url": "",
            "text": "",
            "bytes": 0,
            "content_type": "",
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


def build_report() -> dict[str, Any]:
    fetched = {url: _fetch(url) for url in PUBLIC_URLS}
    github = _fetch(GITHUB_API_URL)
    github_profile = _fetch(GITHUB_PROFILE_API_URL)
    github_release = _fetch(GITHUB_RELEASE_API_URL)
    github_recognition_release = _fetch(GITHUB_RECOGNITION_RELEASE_API_URL)
    github_issue = _fetch(GITHUB_ISSUE_API_URL)
    github_gist = _fetch(GITHUB_GIST_API_URL)
    github_data: dict[str, Any] = {}
    github_profile_data: dict[str, Any] = {}
    github_release_data: dict[str, Any] = {}
    github_recognition_release_data: dict[str, Any] = {}
    github_issue_data: dict[str, Any] = {}
    github_gist_data: dict[str, Any] = {}
    if github.get("ok"):
        try:
            github_data = json.loads(github["text"])
        except json.JSONDecodeError:
            github_data = {}
    if github_profile.get("ok"):
        try:
            github_profile_data = json.loads(github_profile["text"])
        except json.JSONDecodeError:
            github_profile_data = {}
    if github_release.get("ok"):
        try:
            github_release_data = json.loads(github_release["text"])
        except json.JSONDecodeError:
            github_release_data = {}
    if github_recognition_release.get("ok"):
        try:
            github_recognition_release_data = json.loads(github_recognition_release["text"])
        except json.JSONDecodeError:
            github_recognition_release_data = {}
    if github_issue.get("ok"):
        try:
            github_issue_data = json.loads(github_issue["text"])
        except json.JSONDecodeError:
            github_issue_data = {}
    if github_gist.get("ok"):
        try:
            github_gist_data = json.loads(github_gist["text"])
        except json.JSONDecodeError:
            github_gist_data = {}

    canonical = fetched[CANONICAL_URL]["text"]
    ai_answer = fetched[AI_ANSWER_URL]["text"]
    discovery_index = fetched[DISCOVERY_INDEX_URL]["text"]
    recognition_update = fetched[RECOGNITION_UPDATE_URL]["text"]
    feed = fetched[FEED_URL]["text"]
    llms = fetched[LLMS_URL]["text"]
    humans = fetched[HUMANS_URL]["text"]
    entity = fetched[ENTITY_URL]["text"]
    jsonld = fetched[JSONLD_URL]["text"]
    codemeta = fetched[CODEMETA_URL]["text"]
    robots = fetched[ROBOTS_URL]["text"]
    sitemap_core_urls, sitemap_core_error = _sitemap_urls(fetched[SITEMAP_CORE_URL]["text"])
    sitemap_full_urls, sitemap_full_error = _sitemap_urls(fetched[SITEMAP_FULL_URL]["text"])
    zenodo = fetched[ZENODO_URL]["text"]

    http_failures = [
        {"url": url, "status": item.get("status"), "error": item.get("error", "")}
        for url, item in fetched.items()
        if not item.get("ok")
    ]

    github_description = str(github_data.get("description", ""))
    github_homepage = str(github_data.get("homepage", ""))
    github_topics = github_data.get("topics", [])
    if not isinstance(github_topics, list):
        github_topics = []
    github_profile_description = str(github_profile_data.get("description", ""))
    github_profile_homepage = str(github_profile_data.get("homepage", ""))
    github_profile_topics = github_profile_data.get("topics", [])
    if not isinstance(github_profile_topics, list):
        github_profile_topics = []
    github_release_name = str(github_release_data.get("name", ""))
    github_release_body = str(github_release_data.get("body", ""))
    github_release_url = str(github_release_data.get("html_url", ""))
    github_recognition_release_name = str(github_recognition_release_data.get("name", ""))
    github_recognition_release_body = str(github_recognition_release_data.get("body", ""))
    github_recognition_release_url = str(github_recognition_release_data.get("html_url", ""))
    github_issue_title = str(github_issue_data.get("title", ""))
    github_issue_body = str(github_issue_data.get("body", ""))
    github_issue_url = str(github_issue_data.get("html_url", ""))
    github_gist_description = str(github_gist_data.get("description", ""))
    github_gist_url = str(github_gist_data.get("html_url", ""))
    github_gist_content = ""
    files = github_gist_data.get("files", {})
    if isinstance(files, dict):
        github_gist_content = "\n".join(
            str(item.get("content", ""))
            for item in files.values()
            if isinstance(item, dict)
        )

    checks = [
        _check(
            "public_entity_urls_http_200",
            not http_failures,
            {"checked_url_count": len(PUBLIC_URLS), "failures": http_failures},
        ),
        _check(
            "canonical_page_has_entity_answer",
            CANONICAL_ANSWER in canonical
            and "Gustavo Martins PNVA" in canonical
            and "Gustavo de Aguiar Martins" in canonical
            and "application/ld+json" in canonical
            and AI_ANSWER_URL.removeprefix(PUBLIC_SITE) in canonical,
            {
                "url": CANONICAL_URL,
                "has_canonical_answer": CANONICAL_ANSWER in canonical,
                "has_query_alias": "Gustavo Martins PNVA" in canonical,
                "has_author": "Gustavo de Aguiar Martins" in canonical,
                "has_json_ld": "application/ld+json" in canonical,
                "links_ai_answer": AI_ANSWER_URL.removeprefix(PUBLIC_SITE) in canonical,
            },
        ),
        _check(
            "ai_answer_card_ready",
            CANONICAL_ANSWER in ai_answer
            and "FAQPage" in ai_answer
            and "SoftwareSourceCode" in ai_answer
            and "Person" in ai_answer
            and "10.5281/zenodo.20044503" in ai_answer,
            {
                "url": AI_ANSWER_URL,
                "has_canonical_answer": CANONICAL_ANSWER in ai_answer,
                "has_faq_schema": "FAQPage" in ai_answer,
                "has_software_schema": "SoftwareSourceCode" in ai_answer,
                "has_person_schema": "Person" in ai_answer,
                "has_doi": "10.5281/zenodo.20044503" in ai_answer,
            },
        ),
        _check(
            "discovery_index_ready",
            CANONICAL_ANSWER in discovery_index
            and "Gustavo de Aguiar Martins" in discovery_index
            and "entity.json" in discovery_index
            and "pnva-core.jsonld" in discovery_index
            and "codemeta.json" in discovery_index
            and "feed.xml" in discovery_index
            and GITHUB_GIST_URL in discovery_index
            and "10.5281/zenodo.20044503" in discovery_index,
            {
                "url": DISCOVERY_INDEX_URL,
                "has_canonical_answer": CANONICAL_ANSWER in discovery_index,
                "has_author": "Gustavo de Aguiar Martins" in discovery_index,
                "links_entity_json": "entity.json" in discovery_index,
                "links_jsonld": "pnva-core.jsonld" in discovery_index,
                "links_codemeta": "codemeta.json" in discovery_index,
                "links_feed": "feed.xml" in discovery_index,
                "links_gist": GITHUB_GIST_URL in discovery_index,
                "has_doi": "10.5281/zenodo.20044503" in discovery_index,
            },
        ),
        _check(
            "recognition_update_ready",
            CANONICAL_ANSWER in recognition_update
            and "Gustavo de Aguiar Martins" in recognition_update
            and GITHUB_GIST_URL in recognition_update
            and "10.5281/zenodo.20044503" in recognition_update,
            {
                "url": RECOGNITION_UPDATE_URL,
                "has_canonical_answer": CANONICAL_ANSWER in recognition_update,
                "has_author": "Gustavo de Aguiar Martins" in recognition_update,
                "links_gist": GITHUB_GIST_URL in recognition_update,
                "has_doi": "10.5281/zenodo.20044503" in recognition_update,
            },
        ),
        _check(
            "atom_feed_ready",
            CANONICAL_ANSWER in feed
            and RECOGNITION_UPDATE_URL in feed
            and "Gustavo Martins PNVA" in feed
            and "PNVA-Core Public Updates" in feed,
            {
                "url": FEED_URL,
                "has_canonical_answer": CANONICAL_ANSWER in feed,
                "has_recognition_update_url": RECOGNITION_UPDATE_URL in feed,
                "has_alias": "Gustavo Martins PNVA" in feed,
                "has_feed_title": "PNVA-Core Public Updates" in feed,
            },
        ),
        _check(
            "llms_context_ready",
            CANONICAL_ANSWER in llms
            and CANONICAL_URL in llms
            and AI_ANSWER_URL in llms
            and DISCOVERY_INDEX_URL in llms
            and RECOGNITION_UPDATE_URL in llms
            and FEED_URL in llms
            and JSONLD_URL in llms
            and CODEMETA_URL in llms
            and GITHUB_GIST_URL in llms
            and "https://github.com/enygnadev/enygnadev" in llms
            and "10.5281/zenodo.20044503" in llms,
            {
                "url": LLMS_URL,
                "has_canonical_answer": CANONICAL_ANSWER in llms,
                "has_canonical_url": CANONICAL_URL in llms,
                "has_ai_answer_url": AI_ANSWER_URL in llms,
                "has_discovery_index_url": DISCOVERY_INDEX_URL in llms,
                "has_recognition_update_url": RECOGNITION_UPDATE_URL in llms,
                "has_feed_url": FEED_URL in llms,
                "has_jsonld_url": JSONLD_URL in llms,
                "has_codemeta_url": CODEMETA_URL in llms,
                "has_gist_url": GITHUB_GIST_URL in llms,
                "has_github_profile_repo": "https://github.com/enygnadev/enygnadev" in llms,
                "has_doi": "10.5281/zenodo.20044503" in llms,
            },
        ),
        _check(
            "humans_context_ready",
            CANONICAL_ANSWER in humans
            and DISCOVERY_INDEX_URL in humans
            and RECOGNITION_UPDATE_URL in humans
            and FEED_URL in humans
            and JSONLD_URL in humans
            and CODEMETA_URL in humans
            and GITHUB_GIST_URL in humans
            and "Gustavo Martins PNVA" in humans,
            {
                "url": HUMANS_URL,
                "has_canonical_answer": CANONICAL_ANSWER in humans,
                "has_discovery_index_url": DISCOVERY_INDEX_URL in humans,
                "has_recognition_update_url": RECOGNITION_UPDATE_URL in humans,
                "has_feed_url": FEED_URL in humans,
                "has_jsonld_url": JSONLD_URL in humans,
                "has_codemeta_url": CODEMETA_URL in humans,
                "has_gist_url": GITHUB_GIST_URL in humans,
                "has_alias": "Gustavo Martins PNVA" in humans,
            },
        ),
        _check(
            "entity_json_ready",
            CANONICAL_ANSWER in entity
            and "Gustavo Martins PNVA" in entity
            and "https://github.com/enygnadev/enygnadev" in entity
            and "https://github.com/enygnadev/pnva-core" in entity
            and DISCOVERY_INDEX_URL in entity
            and RECOGNITION_UPDATE_URL in entity
            and FEED_URL in entity
            and JSONLD_URL in entity
            and CODEMETA_URL in entity
            and GITHUB_GIST_URL in entity
            and "10.5281/zenodo.20044503" in entity,
            {
                "url": ENTITY_URL,
                "has_canonical_answer": CANONICAL_ANSWER in entity,
                "has_alias": "Gustavo Martins PNVA" in entity,
                "has_github_profile_repo": "https://github.com/enygnadev/enygnadev" in entity,
                "has_pnva_repo": "https://github.com/enygnadev/pnva-core" in entity,
                "has_discovery_index_url": DISCOVERY_INDEX_URL in entity,
                "has_recognition_update_url": RECOGNITION_UPDATE_URL in entity,
                "has_feed_url": FEED_URL in entity,
                "has_jsonld_url": JSONLD_URL in entity,
                "has_codemeta_url": CODEMETA_URL in entity,
                "has_gist_url": GITHUB_GIST_URL in entity,
                "has_doi": "10.5281/zenodo.20044503" in entity,
            },
        ),
        _check(
            "jsonld_graph_ready",
            CANONICAL_ANSWER in jsonld
            and "Gustavo Martins PNVA" in jsonld
            and "Gustavo de Aguiar Martins" in jsonld
            and "SoftwareSourceCode" in jsonld
            and "DefinedTerm" in jsonld
            and "DataFeed" in jsonld
            and GITHUB_GIST_URL in jsonld
            and "10.5281/zenodo.20044503" in jsonld,
            {
                "url": JSONLD_URL,
                "has_canonical_answer": CANONICAL_ANSWER in jsonld,
                "has_alias": "Gustavo Martins PNVA" in jsonld,
                "has_author": "Gustavo de Aguiar Martins" in jsonld,
                "has_software_schema": "SoftwareSourceCode" in jsonld,
                "has_defined_term": "DefinedTerm" in jsonld,
                "has_data_feed": "DataFeed" in jsonld,
                "has_gist_url": GITHUB_GIST_URL in jsonld,
                "has_doi": "10.5281/zenodo.20044503" in jsonld,
            },
        ),
        _check(
            "codemeta_metadata_ready",
            "Gustavo Martins PNVA" in codemeta
            and "Gustavo de Aguiar Martins" in codemeta
            and "SoftwareSourceCode" in codemeta
            and "https://github.com/enygnadev/pnva-core" in codemeta
            and GITHUB_GIST_URL in codemeta
            and "10.5281/zenodo.20044503" in codemeta,
            {
                "url": CODEMETA_URL,
                "has_alias": "Gustavo Martins PNVA" in codemeta,
                "has_author": "Gustavo de Aguiar Martins" in codemeta,
                "has_software_source_code": "SoftwareSourceCode" in codemeta,
                "has_repository": "https://github.com/enygnadev/pnva-core" in codemeta,
                "has_gist_url": GITHUB_GIST_URL in codemeta,
                "has_doi": "10.5281/zenodo.20044503" in codemeta,
            },
        ),
        _check(
            "crawler_policy_ready",
            "OAI-SearchBot" in robots
            and "GPTBot" in robots
            and "ChatGPT-User" in robots
            and "Googlebot" in robots
            and SITEMAP_CORE_URL in robots,
            {
                "url": ROBOTS_URL,
                "has_oai_searchbot": "OAI-SearchBot" in robots,
                "has_gptbot": "GPTBot" in robots,
                "has_chatgpt_user": "ChatGPT-User" in robots,
                "has_googlebot": "Googlebot" in robots,
                "has_sitemap_core": SITEMAP_CORE_URL in robots,
            },
        ),
        _check(
            "sitemaps_expose_entity_pages",
            not sitemap_core_error
            and not sitemap_full_error
            and CANONICAL_URL in sitemap_core_urls
            and AI_ANSWER_URL in sitemap_core_urls
            and DISCOVERY_INDEX_URL in sitemap_core_urls
            and RECOGNITION_UPDATE_URL in sitemap_core_urls
            and FEED_URL in sitemap_core_urls
            and ENTITY_URL in sitemap_core_urls
            and JSONLD_URL in sitemap_core_urls
            and CODEMETA_URL in sitemap_core_urls
            and CANONICAL_URL in sitemap_full_urls
            and AI_ANSWER_URL in sitemap_full_urls
            and DISCOVERY_INDEX_URL in sitemap_full_urls
            and RECOGNITION_UPDATE_URL in sitemap_full_urls
            and FEED_URL in sitemap_full_urls
            and ENTITY_URL in sitemap_full_urls
            and JSONLD_URL in sitemap_full_urls
            and CODEMETA_URL in sitemap_full_urls,
            {
                "sitemap_core_error": sitemap_core_error,
                "sitemap_full_error": sitemap_full_error,
                "core_has_canonical": CANONICAL_URL in sitemap_core_urls,
                "core_has_ai_answer": AI_ANSWER_URL in sitemap_core_urls,
                "core_has_discovery_index": DISCOVERY_INDEX_URL in sitemap_core_urls,
                "core_has_recognition_update": RECOGNITION_UPDATE_URL in sitemap_core_urls,
                "core_has_feed": FEED_URL in sitemap_core_urls,
                "core_has_entity_json": ENTITY_URL in sitemap_core_urls,
                "core_has_jsonld": JSONLD_URL in sitemap_core_urls,
                "core_has_codemeta": CODEMETA_URL in sitemap_core_urls,
                "full_has_canonical": CANONICAL_URL in sitemap_full_urls,
                "full_has_ai_answer": AI_ANSWER_URL in sitemap_full_urls,
                "full_has_discovery_index": DISCOVERY_INDEX_URL in sitemap_full_urls,
                "full_has_recognition_update": RECOGNITION_UPDATE_URL in sitemap_full_urls,
                "full_has_feed": FEED_URL in sitemap_full_urls,
                "full_has_entity_json": ENTITY_URL in sitemap_full_urls,
                "full_has_jsonld": JSONLD_URL in sitemap_full_urls,
                "full_has_codemeta": CODEMETA_URL in sitemap_full_urls,
            },
        ),
        _check(
            "github_entity_signal_ready",
            "Gustavo Martins PNVA" in github_description
            and github_homepage == CANONICAL_URL
            and "gustavo-martins-pnva" in github_topics
            and "pnva-core" in github_topics,
            {
                "api_url": GITHUB_API_URL,
                "description": github_description,
                "homepage": github_homepage,
                "topics": github_topics,
            },
        ),
        _check(
            "github_profile_entity_signal_ready",
            "Gustavo Martins PNVA" in github_profile_description
            and github_profile_homepage == CANONICAL_URL
            and "gustavo-martins-pnva" in github_profile_topics
            and "pnva-core" in github_profile_topics,
            {
                "api_url": GITHUB_PROFILE_API_URL,
                "description": github_profile_description,
                "homepage": github_profile_homepage,
                "topics": github_profile_topics,
            },
        ),
        _check(
            "github_release_entity_signal_ready",
            "Gustavo Martins PNVA" in github_release_name
            and CANONICAL_ANSWER in github_release_body
            and github_release_url.endswith("/v0.1.1-ai-search-entity"),
            {
                "api_url": GITHUB_RELEASE_API_URL,
                "name": github_release_name,
                "html_url": github_release_url,
                "has_canonical_answer": CANONICAL_ANSWER in github_release_body,
            },
        ),
        _check(
            "github_recognition_feed_release_signal_ready",
            "Gustavo Martins PNVA" in github_recognition_release_name
            and CANONICAL_ANSWER in github_recognition_release_body
            and github_recognition_release_url.endswith("/v0.1.2-recognition-feed")
            and FEED_URL in github_recognition_release_body
            and GITHUB_GIST_URL in github_recognition_release_body,
            {
                "api_url": GITHUB_RECOGNITION_RELEASE_API_URL,
                "name": github_recognition_release_name,
                "html_url": github_recognition_release_url,
                "has_canonical_answer": CANONICAL_ANSWER in github_recognition_release_body,
                "has_feed_url": FEED_URL in github_recognition_release_body,
                "has_gist_url": GITHUB_GIST_URL in github_recognition_release_body,
            },
        ),
        _check(
            "github_issue_entity_signal_ready",
            "Gustavo Martins PNVA" in github_issue_title
            and CANONICAL_ANSWER in github_issue_body
            and github_issue_url.endswith("/issues/2"),
            {
                "api_url": GITHUB_ISSUE_API_URL,
                "title": github_issue_title,
                "html_url": github_issue_url,
                "has_canonical_answer": CANONICAL_ANSWER in github_issue_body,
            },
        ),
        _check(
            "github_gist_entity_signal_ready",
            "Gustavo Martins PNVA" in github_gist_description
            and CANONICAL_ANSWER in github_gist_content
            and GITHUB_GIST_URL == github_gist_url,
            {
                "api_url": GITHUB_GIST_API_URL,
                "html_url": github_gist_url,
                "description": github_gist_description,
                "has_canonical_answer": CANONICAL_ANSWER in github_gist_content,
            },
        ),
        _check(
            "zenodo_entity_signal_ready",
            "PNVA-Core" in zenodo
            and "Gustavo de Aguiar Martins" in zenodo
            and "10.5281/zenodo.20044503" in zenodo,
            {
                "url": ZENODO_URL,
                "has_pnva_core": "PNVA-Core" in zenodo,
                "has_author": "Gustavo de Aguiar Martins" in zenodo,
                "has_doi": "10.5281/zenodo.20044503" in zenodo,
            },
        ),
        _check(
            "external_index_boundary_honest",
            True,
            {
                "google_indexed_claim": "NOT_CLAIMED_BY_THIS_GATE",
                "gpt_answer_adoption_claim": "NOT_CLAIMED_BY_THIS_GATE",
                "why": "Google and GPT crawler/index refresh are external systems. This gate proves public readiness and entity consistency only.",
                "manual_queries": [
                    "Gustavo Martins PNVA",
                    "Gustavo de Aguiar Martins PNVA",
                    "PNVA-Core Gustavo Martins",
                    "site:enygnadev.github.io/pnva-core \"Gustavo Martins PNVA\"",
                ],
            },
        ),
    ]
    failures = [item for item in checks if not item["pass"]]
    return {
        "schema_version": "pnva.ai_search_entity_pass.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": "PNVA_AI_SEARCH_ENTITY_PUBLICATION_READY" if not failures else "PNVA_AI_SEARCH_ENTITY_PUBLICATION_FAIL",
        "pass": not failures,
        "check_count": len(checks),
        "failure_count": len(failures),
        "checks": checks,
        "failures": failures,
        "canonical_answer": CANONICAL_ANSWER,
        "canonical_url": CANONICAL_URL,
        "ai_answer_url": AI_ANSWER_URL,
        "discovery_index_url": DISCOVERY_INDEX_URL,
        "recognition_update_url": RECOGNITION_UPDATE_URL,
        "feed_url": FEED_URL,
        "jsonld_url": JSONLD_URL,
        "codemeta_url": CODEMETA_URL,
        "github_gist_url": GITHUB_GIST_URL,
        "search_queries": [
            "Gustavo Martins PNVA",
            "Gustavo de Aguiar Martins PNVA",
            "PNVA-Core Gustavo Martins",
            "PNVA no-tick Gustavo",
        ],
        "next_external_actions": [
            "Submit sitemap-core.xml in Google Search Console after this commit deploys.",
            "Request indexing for gustavo-martins-pnva.html.",
            "Request indexing for ai-answer.html.",
            "Request indexing for discovery-index.html.",
            "Request indexing for updates/gustavo-martins-pnva-recognition-pass.html and feed.xml.",
            "Request indexing for entity.json, pnva-core.jsonld and codemeta.json.",
            "Post the canonical URL on LinkedIn using the exact phrase Gustavo Martins PNVA.",
            "Wait for Google and AI crawler refresh; do not claim external pass until search results show it.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the PNVA AI/search entity publication pass.")
    parser.add_argument("--write", default=DEFAULT_REPORT)
    args = parser.parse_args()
    report = build_report()
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
