#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


AUTHOR = "Gustavo de Aguiar Martins"
PROJECT = "PNVA-Core"
ROOT_RELEASE_HASH = "sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc"

REPORTS = {
    "traceability": "reports/pnva-root-traceability-matrix-2026-05-05.json",
    "sovereignty": "reports/pnva-root-sovereignty-guard-2026-05-05.json",
    "causal_intelligence": "reports/pnva-root-causal-intelligence-2026-05-05.json",
    "adversarial_sentry": "reports/pnva-root-adversarial-sentry-2026-05-05.json",
    "release_seal": "reports/pnva-root-release-seal-2026-05-05.json",
    "release_verifier": "reports/pnva-root-release-verifier-2026-05-05.json",
    "observability": "reports/pnva-root-observability-index-2026-05-05.json",
    "invariant_firewall": "reports/pnva-root-invariant-firewall-2026-05-05.json",
    "regression_sentinel": "reports/pnva-root-regression-sentinel-2026-05-05.json",
    "proof_theorem": "reports/pnva-root-proof-theorem-ledger-2026-05-05.json",
    "evolution_governor": "reports/pnva-root-evolution-governor-2026-05-05.json",
    "heuristic_weight": "reports/pnva-root-heuristic-weight-ledger-2026-05-05.json",
    "entity_capability": "reports/pnva-root-entity-capability-ledger-2026-05-05.json",
    "dependency_graph": "reports/pnva-root-dependency-graph-2026-05-05.json",
    "field_topology": "reports/pnva-root-field-topology-ledger-2026-05-05.json",
    "no_tick_contract": "reports/pnva-root-no-tick-causal-contract-2026-05-05.json",
    "runtime_admission": "reports/pnva-root-runtime-admission-controller-2026-05-05.json",
    "admission_matrix": "reports/pnva-root-entity-heuristic-admission-matrix-2026-05-05.json",
    "negative_controls": "reports/pnva-root-admission-negative-controls-2026-05-05.json",
    "event_identity": "reports/pnva-root-event-identity-ledger-2026-05-05.json",
    "claim_boundary": "reports/pnva-root-claim-boundary-guard-2026-05-05.json",
    "publication_gate": "reports/pnva-root-publication-gate-2026-05-05.json",
    "runtime_growth_budget": "reports/pnva-root-runtime-growth-budget-2026-05-05.json",
    "causal_mesh": "reports/pnva-root-causal-mesh-ledger-2026-05-05.json",
    "efficiency_proof": "reports/pnva-root-efficiency-proof-ledger-2026-05-05.json",
    "equation_consistency": "reports/pnva-root-equation-consistency-ledger-2026-05-05.json",
    "legacy_quarantine": "reports/pnva-root-legacy-quarantine-ledger-2026-05-05.json",
}

EXPECTED_CLASSIFICATIONS = {
    "traceability": "PNVA_ROOT_TRACEABILITY_MATRIX_READY",
    "sovereignty": "PNVA_ROOT_SOVEREIGNTY_GUARD_READY",
    "causal_intelligence": "PNVA_ROOT_CAUSAL_INTELLIGENCE_READY",
    "adversarial_sentry": "PNVA_ROOT_ADVERSARIAL_SENTRY_PASS",
    "release_seal": "PNVA_ROOT_RELEASE_SEALED",
    "release_verifier": "PNVA_ROOT_RELEASE_VERIFIED",
    "observability": "PNVA_ROOT_OBSERVABILITY_INDEX_READY",
    "invariant_firewall": "PNVA_ROOT_INVARIANT_FIREWALL_READY",
    "regression_sentinel": "PNVA_ROOT_REGRESSION_SENTINEL_READY",
    "proof_theorem": "PNVA_ROOT_PROOF_THEOREM_LEDGER_READY",
    "evolution_governor": "PNVA_ROOT_EVOLUTION_GOVERNOR_READY",
    "heuristic_weight": "PNVA_ROOT_HEURISTIC_WEIGHT_LEDGER_READY",
    "entity_capability": "PNVA_ROOT_ENTITY_CAPABILITY_LEDGER_READY",
    "dependency_graph": "PNVA_ROOT_DEPENDENCY_GRAPH_READY",
    "field_topology": "PNVA_ROOT_FIELD_TOPOLOGY_LEDGER_READY",
    "no_tick_contract": "PNVA_ROOT_NO_TICK_CAUSAL_CONTRACT_READY",
    "runtime_admission": "PNVA_ROOT_RUNTIME_ADMISSION_READY",
    "admission_matrix": "PNVA_ROOT_ENTITY_HEURISTIC_ADMISSION_MATRIX_READY",
    "negative_controls": "PNVA_ROOT_ADMISSION_NEGATIVE_CONTROLS_PASS",
    "event_identity": "PNVA_ROOT_EVENT_IDENTITY_LEDGER_READY",
    "claim_boundary": "PNVA_ROOT_CLAIM_BOUNDARY_GUARD_READY",
    "publication_gate": "PNVA_ROOT_PUBLICATION_GATE_READY",
    "runtime_growth_budget": "PNVA_ROOT_RUNTIME_GROWTH_BUDGET_READY",
    "causal_mesh": "PNVA_ROOT_CAUSAL_MESH_LEDGER_READY",
    "efficiency_proof": "PNVA_ROOT_EFFICIENCY_PROOF_LEDGER_READY",
    "equation_consistency": "PNVA_ROOT_EQUATION_CONSISTENCY_LEDGER_READY",
    "legacy_quarantine": "PNVA_ROOT_LEGACY_QUARANTINE_LEDGER_READY",
}

PHASES = {
    "sealed_core": [
        "traceability",
        "sovereignty",
        "causal_intelligence",
        "adversarial_sentry",
        "release_seal",
        "release_verifier",
    ],
    "post_seal_root_ledgers": [
        "observability",
        "invariant_firewall",
        "regression_sentinel",
        "proof_theorem",
        "evolution_governor",
        "heuristic_weight",
        "entity_capability",
        "dependency_graph",
        "field_topology",
        "no_tick_contract",
        "runtime_admission",
        "admission_matrix",
        "negative_controls",
        "event_identity",
    ],
    "publication_and_growth": [
        "claim_boundary",
        "publication_gate",
        "runtime_growth_budget",
        "causal_mesh",
        "efficiency_proof",
        "equation_consistency",
        "legacy_quarantine",
    ],
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _check(name: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "pass": bool(passed), "evidence": evidence}


def _source_checks(reports: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "classification": reports[name].get("classification"),
            "expected": expected,
            "pass": reports[name].get("classification") == expected and reports[name].get("pass") is True,
        }
        for name, expected in EXPECTED_CLASSIFICATIONS.items()
    ]


def _phase_window(times: dict[str, datetime | None], names: list[str]) -> dict[str, Any]:
    present = [times[name] for name in names if times.get(name) is not None]
    return {
        "report_count": len(names),
        "with_generated_at": len(present),
        "start": _iso(min(present)) if present else None,
        "end": _iso(max(present)) if present else None,
    }


def build_report(repo: Path) -> dict[str, Any]:
    reports = {name: _read_json(repo / rel) for name, rel in REPORTS.items()}
    times = {name: _parse_time(report.get("generated_at")) for name, report in reports.items()}
    source_checks = _source_checks(reports)

    missing_generated_at = [name for name, value in times.items() if value is None]
    root_hashes = {
        name: report.get("root_release_hash")
        for name, report in reports.items()
        if report.get("root_release_hash")
    }
    root_hashes["release_verifier_recomputed"] = reports["release_verifier"].get("recomputed_root_release_hash")
    root_hash_set = set(value for value in root_hashes.values() if value)

    seal_time = times["release_seal"]
    verifier_time = times["release_verifier"]
    sealed_inputs = ["traceability", "sovereignty", "causal_intelligence", "adversarial_sentry"]
    sealed_after_seal = [
        name for name in sealed_inputs if seal_time is not None and times.get(name) is not None and times[name] > seal_time
    ]
    post_seal_names = PHASES["post_seal_root_ledgers"] + PHASES["publication_and_growth"]
    post_seal_before_verifier = [
        name for name in post_seal_names if verifier_time is not None and times.get(name) is not None and times[name] < verifier_time
    ]
    publication_names = PHASES["publication_and_growth"]
    causal_mesh_time = times["causal_mesh"]
    efficiency_time = times["efficiency_proof"]
    equation_time = times["equation_consistency"]
    legacy_time = times["legacy_quarantine"]
    claim_time = times["claim_boundary"]
    growth_time = times["runtime_growth_budget"]
    mesh_after_growth_and_claim = bool(
        causal_mesh_time
        and claim_time
        and growth_time
        and causal_mesh_time >= claim_time
        and causal_mesh_time >= growth_time
    )
    efficiency_after_mesh_growth_and_claim = bool(
        efficiency_time
        and causal_mesh_time
        and claim_time
        and growth_time
        and efficiency_time >= causal_mesh_time
        and efficiency_time >= claim_time
        and efficiency_time >= growth_time
    )
    equation_after_efficiency_and_mesh = bool(
        equation_time
        and efficiency_time
        and causal_mesh_time
        and equation_time >= efficiency_time
        and equation_time >= causal_mesh_time
    )
    legacy_after_equation_and_efficiency = bool(
        legacy_time
        and equation_time
        and efficiency_time
        and legacy_time >= equation_time
        and legacy_time >= efficiency_time
    )

    phase_windows = {phase: _phase_window(times, names) for phase, names in PHASES.items()}
    chronological_edges = [
        {
            "edge": "sealed_inputs_before_or_equal_release_seal",
            "pass": not sealed_after_seal,
            "violations": sealed_after_seal,
        },
        {
            "edge": "release_verifier_after_release_seal",
            "pass": bool(seal_time and verifier_time and verifier_time >= seal_time),
            "release_seal": _iso(seal_time),
            "release_verifier": _iso(verifier_time),
        },
        {
            "edge": "post_seal_reports_after_release_verifier",
            "pass": not post_seal_before_verifier,
            "violations": post_seal_before_verifier,
        },
        {
            "edge": "causal_mesh_after_growth_and_claim",
            "pass": mesh_after_growth_and_claim,
            "causal_mesh": _iso(causal_mesh_time),
            "claim_boundary": _iso(claim_time),
            "runtime_growth_budget": _iso(growth_time),
        },
        {
            "edge": "efficiency_after_mesh_growth_and_claim",
            "pass": efficiency_after_mesh_growth_and_claim,
            "efficiency_proof": _iso(efficiency_time),
            "causal_mesh": _iso(causal_mesh_time),
            "claim_boundary": _iso(claim_time),
            "runtime_growth_budget": _iso(growth_time),
        },
        {
            "edge": "equation_after_efficiency_and_mesh",
            "pass": equation_after_efficiency_and_mesh,
            "equation_consistency": _iso(equation_time),
            "efficiency_proof": _iso(efficiency_time),
            "causal_mesh": _iso(causal_mesh_time),
        },
        {
            "edge": "legacy_after_equation_and_efficiency",
            "pass": legacy_after_equation_and_efficiency,
            "legacy_quarantine": _iso(legacy_time),
            "equation_consistency": _iso(equation_time),
            "efficiency_proof": _iso(efficiency_time),
        },
    ]

    claim = reports["claim_boundary"]
    publication = reports["publication_gate"]
    mesh = reports["causal_mesh"]
    growth = reports["runtime_growth_budget"]
    checks = [
        _check("source_reports_ready", all(item["pass"] for item in source_checks), {"reports": source_checks}),
        _check("generated_at_present", not missing_generated_at, {"missing_generated_at": missing_generated_at}),
        _check("sealed_core_order_valid", not sealed_after_seal, {"violations": sealed_after_seal, "seal_time": _iso(seal_time)}),
        _check(
            "release_verifier_after_seal",
            bool(seal_time and verifier_time and verifier_time >= seal_time),
            {"release_seal": _iso(seal_time), "release_verifier": _iso(verifier_time)},
        ),
        _check(
            "post_seal_reports_are_after_verifier",
            not post_seal_before_verifier,
            {"violations": post_seal_before_verifier, "release_verifier": _iso(verifier_time)},
        ),
        _check(
            "causal_mesh_after_growth_and_claim",
            mesh_after_growth_and_claim,
            {
                "causal_mesh": _iso(causal_mesh_time),
                "claim_boundary": _iso(claim_time),
                "runtime_growth_budget": _iso(growth_time),
            },
        ),
        _check(
            "efficiency_after_mesh_growth_and_claim",
            efficiency_after_mesh_growth_and_claim,
            {
                "efficiency_proof": _iso(efficiency_time),
                "causal_mesh": _iso(causal_mesh_time),
                "claim_boundary": _iso(claim_time),
                "runtime_growth_budget": _iso(growth_time),
            },
        ),
        _check(
            "equation_after_efficiency_and_mesh",
            equation_after_efficiency_and_mesh,
            {
                "equation_consistency": _iso(equation_time),
                "efficiency_proof": _iso(efficiency_time),
                "causal_mesh": _iso(causal_mesh_time),
            },
        ),
        _check(
            "legacy_after_equation_and_efficiency",
            legacy_after_equation_and_efficiency,
            {
                "legacy_quarantine": _iso(legacy_time),
                "equation_consistency": _iso(equation_time),
                "efficiency_proof": _iso(efficiency_time),
            },
        ),
        _check(
            "public_counts_current",
            claim.get("scanned_file_count", 0) >= 83
            and publication.get("manifest_file_count") == mesh.get("manifest_file_count")
            and publication.get("checksum_count") == mesh.get("checksum_count")
            and publication.get("manifest_file_count") == publication.get("checksum_count", 0) + 1
            and growth.get("event_count") == mesh.get("event_count") == 589,
            {
                "claim_scanned_file_count": claim.get("scanned_file_count"),
                "publication_manifest_file_count": publication.get("manifest_file_count"),
                "publication_checksum_count": publication.get("checksum_count"),
                "mesh_manifest_file_count": mesh.get("manifest_file_count"),
                "mesh_checksum_count": mesh.get("checksum_count"),
                "growth_event_count": growth.get("event_count"),
                "mesh_event_count": mesh.get("event_count"),
            },
        ),
        _check(
            "root_hash_chronology_aligned",
            root_hash_set == {ROOT_RELEASE_HASH},
            {"root_hashes": root_hashes, "expected": ROOT_RELEASE_HASH},
        ),
    ]
    failures = [item for item in checks if not item["pass"]]
    classification = "PNVA_ROOT_EVIDENCE_CHRONOLOGY_LEDGER_READY" if not failures else "PNVA_ROOT_EVIDENCE_CHRONOLOGY_LEDGER_FAIL"
    seed = {
        "classification": classification,
        "checks": [{"name": item["name"], "pass": item["pass"]} for item in checks],
        "phase_windows": phase_windows,
        "root_release_hash": ROOT_RELEASE_HASH,
        "chronological_edges": chronological_edges,
    }

    return {
        "schema_version": "pnva.root_evidence_chronology_ledger.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "chronology_score": round(100.0 * (len(checks) - len(failures)) / max(1, len(checks)), 2),
        "check_count": len(checks),
        "failure_count": len(failures),
        "report_count": len(REPORTS),
        "phase_windows": phase_windows,
        "chronological_edges": chronological_edges,
        "claim_scanned_file_count": claim.get("scanned_file_count"),
        "manifest_file_count": publication.get("manifest_file_count"),
        "checksum_count": publication.get("checksum_count"),
        "mesh_event_count": mesh.get("event_count"),
        "mesh_suppressed_count": mesh.get("suppressed_count"),
        "mesh_entity_count": mesh.get("entity_count"),
        "mesh_rule_count": mesh.get("rule_count"),
        "path_leak_count": publication.get("path_leak_count"),
        "unbounded_high_risk_occurrence_count": claim.get("unbounded_high_risk_occurrence_count"),
        "root_release_hash": ROOT_RELEASE_HASH,
        "evidence_chronology_ledger_hash": _sha_text(json.dumps(seed, sort_keys=True, separators=(",", ":"), ensure_ascii=True)),
        "checks": checks,
        "source_classification_checks": source_checks,
        "interpretation": {
            "purpose": "Prove that root evidence reports have a coherent sealed-core, post-seal and publication chronology.",
            "sovereignty": "A root proof system is stronger when evidence order is explicit and post-seal reports cite the sealed root hash without rewriting it.",
            "boundary": "This ledger audits public report chronology only. It does not execute actions, change live gates or alter runtime workloads.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PNVA root evidence chronology ledger.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--write", help="Optional report path.")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    report = build_report(repo)
    text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.write:
        path = Path(args.write)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
