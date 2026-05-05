#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


AUTHOR = "Gustavo de Aguiar Martins"
PROJECT = "PNVA-Core"
PUBLIC_SITE = "https://enygnadev.github.io/pnva-core/"
CHECKSUMS = "SHA256SUMS.txt"
SELF_REPORT = "reports/pnva-root-publication-gate-2026-05-05.json"

REPORTS = {
    "root_release_seal": "reports/pnva-root-release-seal-2026-05-05.json",
    "root_release_verifier": "reports/pnva-root-release-verifier-2026-05-05.json",
    "root_claim_boundary_guard": "reports/pnva-root-claim-boundary-guard-2026-05-05.json",
    "root_traceability_matrix": "reports/pnva-root-traceability-matrix-2026-05-05.json",
    "root_sovereignty_guard": "reports/pnva-root-sovereignty-guard-2026-05-05.json",
    "root_causal_intelligence": "reports/pnva-root-causal-intelligence-2026-05-05.json",
    "root_adversarial_sentry": "reports/pnva-root-adversarial-sentry-2026-05-05.json",
}

EXPECTED_CLASSIFICATIONS = {
    "root_release_seal": "PNVA_ROOT_RELEASE_SEALED",
    "root_release_verifier": "PNVA_ROOT_RELEASE_VERIFIED",
    "root_claim_boundary_guard": "PNVA_ROOT_CLAIM_BOUNDARY_GUARD_READY",
    "root_traceability_matrix": "PNVA_ROOT_TRACEABILITY_MATRIX_READY",
    "root_sovereignty_guard": "PNVA_ROOT_SOVEREIGNTY_GUARD_READY",
    "root_causal_intelligence": "PNVA_ROOT_CAUSAL_INTELLIGENCE_READY",
    "root_adversarial_sentry": "PNVA_ROOT_ADVERSARIAL_SENTRY_PASS",
}

REQUIRED_FILES = [
    "README.md",
    "MANIFEST.json",
    "SHA256SUMS.txt",
    "LICENSE",
    "LICENSE-DOCS",
    "CITATION.cff",
    "SECURITY.md",
    "robots.txt",
    "sitemap.xml",
    "llms.txt",
    "index.html",
    "author.html",
    "pnva-core.html",
    "proofs.html",
    "veonic-model.html",
    "docs/LIMITATIONS.md",
    "docs/ONLINE_PUBLICATION.md",
    "docs/REPOSITORY_PUBLISHING_CHECKLIST.md",
    "docs/PUBLIC_POSITIONING.md",
    "docs/PNVA_SOVEREIGN_LOGS_ENTITIES_HEURISTICS.md",
    "paper/PNVA_CORE_OPEN_RESEARCH_PAPER.md",
]

REQUIRED_CRAWLERS = [
    "OAI-SearchBot",
    "GPTBot",
    "ChatGPT-User",
    "Googlebot",
    "Bingbot",
    "PerplexityBot",
    "ClaudeBot",
    "Sitemap:",
]

REQUIRED_SITEMAP_URLS = [
    PUBLIC_SITE,
    PUBLIC_SITE + "author.html",
    PUBLIC_SITE + "pnva-core.html",
    PUBLIC_SITE + "proofs.html",
    PUBLIC_SITE + "veonic-model.html",
    PUBLIC_SITE + "llms.txt",
    PUBLIC_SITE + "docs/PNVA_SOVEREIGN_LOGS_ENTITIES_HEURISTICS.md",
]

REQUIRED_LLMS_PHRASES = [
    "PNVA_ROOT_RELEASE_SEALED",
    "PNVA_ROOT_RELEASE_VERIFIED",
    "PNVA_ROOT_CLAIM_BOUNDARY_GUARD_READY",
    "PNVA_ROOT_TRACEABILITY_MATRIX_READY",
    "PNVA-Core is not presented",
]

PATH_LEAK_MARKERS = [
    "/" + "home" + "/",
    "Desktop/" + "document",
    "documenta" + "\u00e7\u00e3o" + "Academinafinal",
    "documentacao" + "Academinafinal",
]


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_checksums(path: Path) -> dict[str, str]:
    checksums: dict[str, str] = {}
    if not path.exists():
        return checksums
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            checksums[parts[1].strip()] = parts[0].strip()
    return checksums


def _dig(data: Any, path: list[str], default: Any = None) -> Any:
    current = data
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


def _check(name: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "pass": bool(passed), "evidence": evidence}


def _manifest_checksum_status(repo: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    files = [str(item) for item in manifest.get("files", []) if isinstance(item, str)]
    checksums = _load_checksums(repo / CHECKSUMS)
    expected = [rel for rel in files if rel not in {CHECKSUMS, SELF_REPORT}]
    missing_files = [rel for rel in files if not (repo / rel).exists()]
    missing_checksums = [rel for rel in expected if rel not in checksums]
    mismatches = []
    for rel in expected:
        path = repo / rel
        if not path.exists() or rel not in checksums:
            continue
        actual = _sha_file(path)
        if checksums[rel] != actual:
            mismatches.append({"path": rel, "expected": checksums[rel], "actual": actual})
    duplicate_files = sorted({rel for rel in files if files.count(rel) > 1})
    extra_checksums = sorted(set(checksums) - set(expected) - {SELF_REPORT})
    return {
        "manifest_file_count": len(files),
        "expected_checksum_count": len(expected),
        "checksum_count": len(checksums),
        "missing_file_count": len(missing_files),
        "missing_checksum_count": len(missing_checksums),
        "mismatch_count": len(mismatches),
        "duplicate_file_count": len(duplicate_files),
        "extra_checksum_count": len(extra_checksums),
        "missing_files": missing_files[:20],
        "missing_checksums": missing_checksums[:20],
        "mismatches": mismatches[:20],
        "duplicate_files": duplicate_files[:20],
        "extra_checksums": extra_checksums[:20],
        "self_report_excluded_from_live_checksum_compare": SELF_REPORT,
    }


def _sitemap_urls(path: Path) -> tuple[list[str], str]:
    try:
        root = ET.parse(path).getroot()
    except Exception as exc:
        return [], str(exc)
    urls = []
    for elem in root.iter():
        if elem.tag.endswith("loc") and elem.text:
            urls.append(elem.text.strip())
    return urls, ""


def _path_leaks(repo: Path, manifest: dict[str, Any]) -> list[dict[str, str]]:
    leaks = []
    for rel in manifest.get("files", []):
        if not isinstance(rel, str):
            continue
        path = repo / rel
        if not path.exists() or path.is_dir():
            continue
        if path.suffix.lower() not in {".md", ".txt", ".html", ".json", ".jsonl", ".cff", ".yml", ".yaml"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for marker in PATH_LEAK_MARKERS:
            if marker in text:
                leaks.append({"path": rel, "marker": marker})
                break
    return leaks


def build_report(repo: Path) -> dict[str, Any]:
    manifest = _read_json(repo / "MANIFEST.json")
    reports = {name: _read_json(repo / rel) for name, rel in REPORTS.items()}
    checksums = _manifest_checksum_status(repo, manifest)
    robots = (repo / "robots.txt").read_text(encoding="utf-8", errors="replace") if (repo / "robots.txt").exists() else ""
    sitemap_urls, sitemap_error = _sitemap_urls(repo / "sitemap.xml")
    llms = (repo / "llms.txt").read_text(encoding="utf-8", errors="replace") if (repo / "llms.txt").exists() else ""
    path_leaks = _path_leaks(repo, manifest)

    missing_required_files = [rel for rel in REQUIRED_FILES if not (repo / rel).exists()]
    missing_crawlers = [item for item in REQUIRED_CRAWLERS if item not in robots]
    missing_sitemap_urls = [url for url in REQUIRED_SITEMAP_URLS if url not in sitemap_urls]
    missing_llms_phrases = [phrase for phrase in REQUIRED_LLMS_PHRASES if phrase not in llms]

    root_hashes = {
        name: report.get("root_release_hash")
        for name, report in reports.items()
        if report.get("root_release_hash")
    }
    root_hash_set = set(root_hashes.values())
    expected_hash = reports["root_release_seal"].get("root_release_hash")

    classification_failures = []
    for name, expected in EXPECTED_CLASSIFICATIONS.items():
        report = reports[name]
        if report.get("classification") != expected or report.get("pass") is not True:
            classification_failures.append(
                {
                    "name": name,
                    "classification": report.get("classification"),
                    "expected": expected,
                    "pass": report.get("pass"),
                }
            )

    checks = [
        _check(
            "root_reports_ready",
            not classification_failures,
            {"classification_failures": classification_failures},
        ),
        _check(
            "root_hashes_agree",
            len(root_hash_set) == 1 and expected_hash in root_hash_set,
            {"root_hashes": root_hashes, "expected_hash": expected_hash},
        ),
        _check(
            "manifest_and_checksums_closed",
            checksums["missing_file_count"] == 0
            and checksums["missing_checksum_count"] == 0
            and checksums["mismatch_count"] == 0
            and checksums["duplicate_file_count"] == 0
            and checksums["extra_checksum_count"] == 0,
            checksums,
        ),
        _check(
            "required_publication_files_present",
            not missing_required_files,
            {"required_file_count": len(REQUIRED_FILES), "missing": missing_required_files},
        ),
        _check(
            "robots_allows_public_discovery",
            not missing_crawlers,
            {"required": REQUIRED_CRAWLERS, "missing": missing_crawlers},
        ),
        _check(
            "sitemap_exposes_canonical_pages",
            not sitemap_error and not missing_sitemap_urls,
            {
                "sitemap_error": sitemap_error,
                "url_count": len(sitemap_urls),
                "required": REQUIRED_SITEMAP_URLS,
                "missing": missing_sitemap_urls,
            },
        ),
        _check(
            "llms_file_exposes_root_boundaries",
            not missing_llms_phrases,
            {"required_phrase_count": len(REQUIRED_LLMS_PHRASES), "missing": missing_llms_phrases},
        ),
        _check(
            "claim_boundary_guard_ready",
            reports["root_claim_boundary_guard"].get("claim_boundary_score") == 100.0
            and reports["root_claim_boundary_guard"].get("unbounded_high_risk_occurrence_count") == 0,
            {
                "claim_boundary_score": reports["root_claim_boundary_guard"].get("claim_boundary_score"),
                "unbounded_high_risk_occurrence_count": reports["root_claim_boundary_guard"].get("unbounded_high_risk_occurrence_count"),
            },
        ),
        _check(
            "public_files_have_no_local_path_leaks",
            not path_leaks,
            {"path_leak_count": len(path_leaks), "path_leaks": path_leaks[:20]},
        ),
    ]
    failures = [item for item in checks if not item["pass"]]
    score = round(100.0 * (len(checks) - len(failures)) / max(1, len(checks)), 2)
    classification = "PNVA_ROOT_PUBLICATION_GATE_READY" if not failures else "PNVA_ROOT_PUBLICATION_GATE_FAIL"

    return {
        "schema_version": "pnva.root_publication_gate.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "publication_score": score,
        "check_count": len(checks),
        "failure_count": len(failures),
        "checks": checks,
        "failures": failures,
        "root_release_hash": expected_hash,
        "manifest_file_count": checksums["manifest_file_count"],
        "checksum_count": checksums["checksum_count"],
        "sitemap_url_count": len(sitemap_urls),
        "path_leak_count": len(path_leaks),
        "public_site": manifest.get("public_site", PUBLIC_SITE),
        "publication_post": manifest.get("publication_post"),
        "interpretation": {
            "purpose": "Validate that the root PNVA evidence package is ready for public repository publication and AI/search discovery.",
            "sovereignty": "Publication readiness requires evidence PASS, checksum closure, discovery metadata, public boundaries and no local path leakage.",
            "boundary": "This gate validates the public package, not external deployments or private runtime evidence.",
        },
        "recommendations": [
            "Run this gate after the root release verifier and claim boundary guard.",
            "Refresh SHA256SUMS.txt after regenerating this report.",
            "Treat any publication gate failure as a blocker before public posting.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate PNVA root publication readiness.")
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--write", default="")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    report = build_report(repo)
    raw = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    if args.write:
        out = Path(args.write)
        if not out.is_absolute():
            out = repo / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0 if report.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
