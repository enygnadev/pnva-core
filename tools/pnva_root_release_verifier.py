#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any


sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import pnva_root_release_seal as release_seal


AUTHOR = "Gustavo de Aguiar Martins"
PROJECT = "PNVA-Core"
SEAL_REPORT = "reports/pnva-root-release-seal-2026-05-05.json"
CHECKSUMS = "SHA256SUMS.txt"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dig(data: Any, path: list[str], default: Any = None) -> Any:
    current = data
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


def _load_checksums(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    checksums: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue
        checksums[parts[1].strip()] = parts[0].strip()
    return checksums


def _verification(name: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": name,
        "pass": bool(passed),
        "evidence": evidence,
    }


def _recomputed_release(repo: Path) -> dict[str, Any]:
    artifacts = [release_seal._artifact(repo, spec) for spec in release_seal.ARTIFACTS]
    seed = [
        {
            "id": item["id"],
            "path": item["path"],
            "stable_sha256": item.get("stable_sha256", ""),
            "classification": item.get("classification", ""),
            "pass": item.get("pass", False),
        }
        for item in artifacts
    ]
    root_release_hash = "sha256:" + release_seal._sha_text(
        json.dumps(seed, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    )
    return {
        "artifacts": artifacts,
        "root_release_hash": root_release_hash,
        "failure_count": sum(1 for item in artifacts if not item.get("pass")),
        "seed": seed,
    }


def build_report(repo: Path) -> dict[str, Any]:
    seal_path = repo / SEAL_REPORT
    seal = _read_json(seal_path)
    recomputed = _recomputed_release(repo)
    checksums = _load_checksums(repo / CHECKSUMS)

    sealed_artifact_paths = [item["path"] for item in recomputed["artifacts"]]
    checksum_mismatches = []
    checksum_missing = []
    for rel in sealed_artifact_paths + [SEAL_REPORT]:
        expected = checksums.get(rel)
        actual = _sha_file(repo / rel)
        if expected is None:
            checksum_missing.append(rel)
        elif expected != actual:
            checksum_mismatches.append({"path": rel, "expected": expected, "actual": actual})

    recomputed_by_id = {item["id"]: item for item in recomputed["artifacts"]}
    seal_artifacts = {item["id"]: item for item in seal.get("artifacts", [])}
    stable_hash_mismatches = []
    classification_mismatches = []
    for artifact_id, current in recomputed_by_id.items():
        sealed = seal_artifacts.get(artifact_id, {})
        if current.get("stable_sha256") != sealed.get("stable_sha256"):
            stable_hash_mismatches.append(
                {
                    "id": artifact_id,
                    "path": current.get("path"),
                    "sealed_stable_sha256": sealed.get("stable_sha256"),
                    "current_stable_sha256": current.get("stable_sha256"),
                }
            )
        if current.get("classification") != sealed.get("classification") or current.get("pass") != sealed.get("pass"):
            classification_mismatches.append(
                {
                    "id": artifact_id,
                    "path": current.get("path"),
                    "sealed_classification": sealed.get("classification"),
                    "current_classification": current.get("classification"),
                    "sealed_pass": sealed.get("pass"),
                    "current_pass": current.get("pass"),
                }
            )

    not_claimed = set(_dig(seal, ["claim_boundary", "not_claimed"], []))
    required_boundaries = {
        "universal performance improvement",
        "private deployment validation",
        "hardware-level energy gain without separate counters",
        "physical particle or physics proof",
    }

    verifications = [
        _verification(
            "seal_report_ready",
            seal.get("classification") == "PNVA_ROOT_RELEASE_SEALED" and seal.get("pass") is True,
            {
                "classification": seal.get("classification"),
                "pass": seal.get("pass"),
                "report": SEAL_REPORT,
            },
        ),
        _verification(
            "root_release_hash_recomputes",
            seal.get("root_release_hash") == recomputed["root_release_hash"],
            {
                "sealed_hash": seal.get("root_release_hash"),
                "recomputed_hash": recomputed["root_release_hash"],
            },
        ),
        _verification(
            "sealed_artifact_count_matches",
            int(seal.get("sealed_artifact_count", -1)) == len(recomputed["artifacts"]) == len(release_seal.ARTIFACTS),
            {
                "sealed_artifact_count": seal.get("sealed_artifact_count"),
                "recomputed_artifact_count": len(recomputed["artifacts"]),
            },
        ),
        _verification(
            "sealed_artifacts_still_pass",
            recomputed["failure_count"] == 0,
            {
                "recomputed_failure_count": recomputed["failure_count"],
                "failed_artifacts": [item["id"] for item in recomputed["artifacts"] if not item.get("pass")],
            },
        ),
        _verification(
            "stable_artifact_hashes_match_seal",
            not stable_hash_mismatches,
            {"mismatch_count": len(stable_hash_mismatches), "mismatches": stable_hash_mismatches[:10]},
        ),
        _verification(
            "artifact_classifications_match_seal",
            not classification_mismatches,
            {"mismatch_count": len(classification_mismatches), "mismatches": classification_mismatches[:10]},
        ),
        _verification(
            "checksums_cover_sealed_artifacts",
            not checksum_missing and not checksum_mismatches,
            {
                "checked_path_count": len(sealed_artifact_paths) + 1,
                "missing_count": len(checksum_missing),
                "mismatch_count": len(checksum_mismatches),
                "missing": checksum_missing[:10],
                "mismatches": checksum_mismatches[:10],
            },
        ),
        _verification(
            "release_vector_is_closed",
            _dig(seal, ["release_vector", "root_score"]) == 100.0
            and _dig(seal, ["release_vector", "root_causal_intelligence_score"]) == 100.0
            and _dig(seal, ["release_vector", "root_adversarial_detection_ratio"]) == "8/8"
            and _dig(seal, ["release_vector", "runtime_accepted_slots"]) == 35
            and _dig(seal, ["release_vector", "runtime_pending_slots"]) == 0,
            seal.get("release_vector", {}),
        ),
        _verification(
            "claim_boundaries_present",
            required_boundaries.issubset(not_claimed),
            {
                "required": sorted(required_boundaries),
                "present": sorted(not_claimed),
                "missing": sorted(required_boundaries - not_claimed),
            },
        ),
    ]
    failures = [item for item in verifications if not item["pass"]]
    classification = "PNVA_ROOT_RELEASE_VERIFIED" if not failures else "PNVA_ROOT_RELEASE_VERIFICATION_FAIL"
    return {
        "schema_version": "pnva.root_release_verifier.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "root_release_hash": seal.get("root_release_hash"),
        "recomputed_root_release_hash": recomputed["root_release_hash"],
        "verification_count": len(verifications),
        "failure_count": len(failures),
        "verifications": verifications,
        "failures": failures,
        "sealed_artifact_count": len(recomputed["artifacts"]),
        "checksum_checked_path_count": len(sealed_artifact_paths) + 1,
        "checksum_missing_count": len(checksum_missing),
        "checksum_mismatch_count": len(checksum_mismatches),
        "stable_hash_mismatch_count": len(stable_hash_mismatches),
        "classification_mismatch_count": len(classification_mismatches),
        "interpretation": {
            "purpose": "Verify that the PNVA root release seal can be recomputed from current public artifacts.",
            "sovereignty": "A seal is stronger when a separate verifier proves its hash, artifact classifications, checksum coverage and claim boundaries.",
            "boundary": "This verifier consumes the seal and is intentionally outside the seal hash to avoid self-reference.",
        },
        "recommendations": [
            "Run this verifier after generating the root release seal and refreshing SHA256SUMS.txt.",
            "Treat any hash mismatch, classification mismatch or missing claim boundary as a release blocker.",
            "Keep this verifier outside the root release hash because it verifies the hash.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the PNVA root release seal.")
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
