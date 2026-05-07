#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


AUTHOR = "Gustavo de Aguiar Martins"
PROJECT = "PNVA-Core"
HOST = "enygnadev.github.io"
SITE_ROOT = "https://enygnadev.github.io/pnva-core"
KEY = "pnva-core-gustavo-martins-pnva-20260506"
KEY_LOCATION = f"{SITE_ROOT}/{KEY}.txt"
ENDPOINT = "https://api.indexnow.org/indexnow"
DEFAULT_REPORT = "reports/pnva-indexnow-submission-2026-05-06.json"

URLS = [
    f"{SITE_ROOT}/",
    f"{SITE_ROOT}/gustavo-martins-pnva.html",
    f"{SITE_ROOT}/ai-answer.html",
    f"{SITE_ROOT}/gustavo-martins-pnva.txt",
    f"{SITE_ROOT}/gustavo-martins-pnva.md",
    f"{SITE_ROOT}/ai-answer.json",
    f"{SITE_ROOT}/discovery-index.html",
    f"{SITE_ROOT}/updates/gustavo-martins-pnva-recognition-pass.html",
    f"{SITE_ROOT}/feed.xml",
    f"{SITE_ROOT}/entity.json",
    f"{SITE_ROOT}/pnva-core.jsonld",
    f"{SITE_ROOT}/codemeta.json",
    f"{SITE_ROOT}/llms.txt",
    f"{SITE_ROOT}/humans.txt",
    f"{SITE_ROOT}/sitemap-core.xml",
    f"{SITE_ROOT}/google-search-console.html",
    f"{SITE_ROOT}/docs/PNVA_AI_SEARCH_ENTITY_PASS.md",
    f"{SITE_ROOT}/docs/PNVA_EXTERNAL_RECOGNITION_PASS.md",
    f"{SITE_ROOT}/reports/pnva-ai-search-entity-pass-2026-05-06.json",
]


def _request(url: str, method: str = "GET", data: bytes | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "User-Agent": "PNVA-IndexNow-Submitter/1.0",
            **(headers or {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            body = response.read()
            return {
                "ok": 200 <= int(response.status) < 300,
                "status": int(response.status),
                "final_url": response.geturl(),
                "text": body.decode("utf-8", errors="replace"),
            }
    except urllib.error.HTTPError as exc:
        body = exc.read()
        return {
            "ok": False,
            "status": int(exc.code),
            "final_url": exc.geturl(),
            "text": body.decode("utf-8", errors="replace"),
            "error": str(exc),
        }
    except Exception as exc:
        return {"ok": False, "status": 0, "final_url": "", "text": "", "error": str(exc)}


def build_report(submit: bool = False) -> dict[str, Any]:
    key_fetch = _request(KEY_LOCATION)
    key_ready = key_fetch.get("ok") and key_fetch.get("text", "").strip() == KEY
    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": URLS,
    }
    submission = {
        "attempted": False,
        "status": "SKIPPED",
        "endpoint": ENDPOINT,
        "http_status": None,
        "body_preview": "",
    }
    if submit:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        result = _request(
            ENDPOINT,
            method="POST",
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        submission = {
            "attempted": True,
            "status": "SUBMITTED" if result.get("status") in {200, 202} else "SUBMISSION_FAILED",
            "endpoint": ENDPOINT,
            "http_status": result.get("status"),
            "body_preview": result.get("text", "")[:300],
            "error": result.get("error", ""),
        }

    checks = [
        {
            "name": "indexnow_key_file_ready",
            "pass": bool(key_ready),
            "evidence": {
                "key_location": KEY_LOCATION,
                "http_status": key_fetch.get("status"),
                "content_matches_key": key_fetch.get("text", "").strip() == KEY,
            },
        },
        {
            "name": "indexnow_payload_ready",
            "pass": len(URLS) >= 10 and all(url.startswith(SITE_ROOT) for url in URLS),
            "evidence": {
                "host": HOST,
                "url_count": len(URLS),
                "key": KEY,
                "key_location": KEY_LOCATION,
            },
        },
        {
            "name": "indexnow_submission_accepted_or_deferred",
            "pass": not submit or submission["status"] == "SUBMITTED",
            "evidence": submission,
        },
    ]
    failures = [item for item in checks if not item["pass"]]
    return {
        "schema_version": "pnva.indexnow_submitter.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": "PNVA_INDEXNOW_SUBMISSION_READY" if not failures else "PNVA_INDEXNOW_SUBMISSION_FAIL",
        "pass": not failures,
        "check_count": len(checks),
        "failure_count": len(failures),
        "checks": checks,
        "failures": failures,
        "payload": payload,
        "submission": submission,
        "truth_boundary": "IndexNow notifies participating search engines. It does not submit URLs to Google and does not guarantee ranking or indexing.",
        "official_reference": "https://www.indexnow.org/documentation.html",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Submit PNVA entity URLs to IndexNow.")
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--write", default=DEFAULT_REPORT)
    args = parser.parse_args()
    report = build_report(submit=args.submit)
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
