#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any


AUTHOR = "Gustavo de Aguiar Martins"
PROJECT = "PNVA-Core"

ROOT_SEAL = "reports/pnva-root-release-seal-2026-05-05.json"
ROOT_VERIFIER = "reports/pnva-root-release-verifier-2026-05-05.json"
MANIFEST = "MANIFEST.json"

REQUIRED_NOT_CLAIMED = {
    "universal performance improvement",
    "private deployment validation",
    "hardware-level energy gain without separate counters",
    "physical particle or physics proof",
}

REQUIRED_BOUNDARY_FILES = [
    "README.md",
    "llms.txt",
    "docs/LIMITATIONS.md",
    "docs/PNVA_ROOT_RELEASE_SEAL.md",
    "docs/PNVA_ROOT_RELEASE_VERIFIER.md",
    "docs/PNVA_ROOT_TRACEABILITY_MATRIX.md",
    "paper/PNVA_CORE_OPEN_RESEARCH_PAPER.md",
]

REQUIRED_BOUNDARY_PHRASES = [
    "not a universal proof",
    "not evidence that a veon is a physical particle",
    "local live-field validation",
    "does not claim private deployment coverage",
    "universal performance improvement",
    "private deployment validation",
    "hardware-level energy gain without separate counters",
    "physical particle or physics proof",
]

HIGH_RISK_PATTERNS = [
    "universal proof",
    "universal performance",
    "universal speedup",
    "universal physical theory",
    "miracle optimization",
    "physical particle",
    "boson de higgs",
    "bóson de higgs",
    "create matter",
    "criar materia",
    "private deployment",
    "hardware-level energy",
    "economia de energia em qualquer",
    "garante economia",
    "substitui todo tick",
    "medical system",
    "legal system",
    "prova fisica",
]

BOUNDARY_TOKENS = [
    "not",
    "does not",
    "do not",
    "not claimed",
    "not a",
    "not evidence",
    "not presented",
    "no ",
    "avoid",
    "limitation",
    "boundary",
    "honest",
    "nao",
    "não",
    "evitar",
    "nao e",
    "nao estou",
    "nao prova",
    "ainda nao e correto afirmar",
    "ainda nao",
    "not allowed",
    "claims not allowed",
    "does not claim",
]

OLD_ROOT_HASHES = {
    "sha256:1f0632d902dee286bbca1918cc3a959aaf086b6872c8cf4975265bb8a495f2e4",
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _dig(data: Any, path: list[str], default: Any = None) -> Any:
    current = data
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _public_text_files(repo: Path, manifest: dict[str, Any]) -> list[Path]:
    files = []
    for rel in manifest.get("files", []):
        if not isinstance(rel, str):
            continue
        if rel.startswith(("reports/", "proofs/", "schemas/")):
            continue
        if Path(rel).suffix.lower() not in {".md", ".txt", ".html", ".cff"}:
            continue
        path = repo / rel
        if path.exists():
            files.append(path)
    return sorted(files)


def _context(text: str, start: int, end: int, radius: int = 260) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    return re.sub(r"\s+", " ", text[left:right]).strip()


def _is_bounded(context: str) -> bool:
    lowered = context.lower()
    return any(token in lowered for token in BOUNDARY_TOKENS)


def _scan_high_risk(repo: Path, files: list[Path]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    occurrences: list[dict[str, Any]] = []
    unbounded: list[dict[str, Any]] = []
    for path in files:
        rel = str(path.relative_to(repo))
        lowered = _text(path).lower()
        for phrase in HIGH_RISK_PATTERNS:
            for match in re.finditer(re.escape(phrase.lower()), lowered):
                ctx = _context(lowered, match.start(), match.end())
                item = {
                    "path": rel,
                    "phrase": phrase,
                    "context": ctx,
                    "bounded": _is_bounded(ctx),
                }
                occurrences.append(item)
                if not item["bounded"]:
                    unbounded.append(item)
    return occurrences, unbounded


def _check(name: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "pass": bool(passed), "evidence": evidence}


def build_report(repo: Path) -> dict[str, Any]:
    manifest = _read_json(repo / MANIFEST)
    seal = _read_json(repo / ROOT_SEAL)
    verifier = _read_json(repo / ROOT_VERIFIER)
    files = _public_text_files(repo, manifest)
    full_text = "\n".join(_text(path).lower() for path in files)
    occurrences, unbounded = _scan_high_risk(repo, files)

    required_files_missing = [rel for rel in REQUIRED_BOUNDARY_FILES if not (repo / rel).exists()]
    missing_phrases = [phrase for phrase in REQUIRED_BOUNDARY_PHRASES if phrase.lower() not in full_text]
    old_hash_hits = []
    for path in files:
        content = _text(path)
        for old_hash in OLD_ROOT_HASHES:
            if old_hash in content:
                old_hash_hits.append({"path": str(path.relative_to(repo)), "hash": old_hash})

    seal_not_claimed = set(_dig(seal, ["claim_boundary", "not_claimed"], []))
    manifest_policy = manifest.get("public_data_policy", {})
    root_hash = seal.get("root_release_hash")

    checks = [
        _check(
            "root_seal_claim_boundary_present",
            seal.get("classification") == "PNVA_ROOT_RELEASE_SEALED"
            and seal.get("pass") is True
            and REQUIRED_NOT_CLAIMED.issubset(seal_not_claimed),
            {
                "seal_classification": seal.get("classification"),
                "seal_pass": seal.get("pass"),
                "required_not_claimed": sorted(REQUIRED_NOT_CLAIMED),
                "present_not_claimed": sorted(seal_not_claimed),
                "missing_not_claimed": sorted(REQUIRED_NOT_CLAIMED - seal_not_claimed),
            },
        ),
        _check(
            "root_verifier_claim_boundary_passed",
            verifier.get("classification") == "PNVA_ROOT_RELEASE_VERIFIED"
            and verifier.get("pass") is True
            and any(item.get("name") == "claim_boundaries_present" and item.get("pass") is True for item in verifier.get("verifications", [])),
            {
                "verifier_classification": verifier.get("classification"),
                "verifier_pass": verifier.get("pass"),
                "root_release_hash": verifier.get("root_release_hash"),
            },
        ),
        _check(
            "required_boundary_files_present",
            not required_files_missing,
            {
                "required_file_count": len(REQUIRED_BOUNDARY_FILES),
                "missing": required_files_missing,
            },
        ),
        _check(
            "required_boundary_phrases_present",
            not missing_phrases,
            {
                "required_phrase_count": len(REQUIRED_BOUNDARY_PHRASES),
                "missing": missing_phrases,
            },
        ),
        _check(
            "high_risk_claims_are_bounded",
            not unbounded,
            {
                "occurrence_count": len(occurrences),
                "unbounded_count": len(unbounded),
                "unbounded": unbounded[:20],
            },
        ),
        _check(
            "public_data_policy_is_sanitized",
            "raw local proofs" in str(manifest_policy.get("not_published", ""))
            and "sensitive environment paths" in str(manifest_policy.get("not_published", ""))
            and "commercial tuning" in str(manifest_policy.get("not_published", "")),
            manifest_policy,
        ),
        _check(
            "root_release_hash_is_current",
            root_hash == verifier.get("root_release_hash") and not old_hash_hits,
            {
                "seal_root_release_hash": root_hash,
                "verifier_root_release_hash": verifier.get("root_release_hash"),
                "old_hash_hits": old_hash_hits,
            },
        ),
    ]
    failures = [item for item in checks if not item["pass"]]
    score = round(100.0 * (len(checks) - len(failures)) / max(1, len(checks)), 2)
    classification = "PNVA_ROOT_CLAIM_BOUNDARY_GUARD_READY" if not failures else "PNVA_ROOT_CLAIM_BOUNDARY_GUARD_FAIL"

    return {
        "schema_version": "pnva.root_claim_boundary_guard.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "claim_boundary_score": score,
        "check_count": len(checks),
        "failure_count": len(failures),
        "checks": checks,
        "failures": failures,
        "scanned_file_count": len(files),
        "high_risk_occurrence_count": len(occurrences),
        "unbounded_high_risk_occurrence_count": len(unbounded),
        "root_release_hash": root_hash,
        "bounded_occurrences_sample": occurrences[:40],
        "interpretation": {
            "purpose": "Verify that public PNVA claims stay inside the evidence boundary established by the root release seal.",
            "sovereignty": "A strong public architecture must prove what it does not claim, not only what it claims.",
            "boundary": "This guard audits public text and release claim boundaries; it does not validate private deployments.",
        },
        "recommendations": [
            "Run this guard after the root release verifier and before public posting.",
            "Treat any unbounded high-risk claim as a publication blocker.",
            "Keep this guard outside the root release seal because it validates post-seal public language.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate PNVA public claim boundaries.")
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
