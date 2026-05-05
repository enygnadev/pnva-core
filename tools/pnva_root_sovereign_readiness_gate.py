#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any


AUTHOR = "Gustavo de Aguiar Martins"
PROJECT = "PNVA-Core"
ROOT_RELEASE_HASH = "sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc"

REPORTS = {
    "sovereignty_guard": "reports/pnva-root-sovereignty-guard-2026-05-05.json",
    "causal_intelligence": "reports/pnva-root-causal-intelligence-2026-05-05.json",
    "release_verifier": "reports/pnva-root-release-verifier-2026-05-05.json",
    "publication_gate": "reports/pnva-root-publication-gate-2026-05-05.json",
    "claim_boundary": "reports/pnva-root-claim-boundary-guard-2026-05-05.json",
    "invariant_firewall": "reports/pnva-root-invariant-firewall-2026-05-05.json",
    "regression_sentinel": "reports/pnva-root-regression-sentinel-2026-05-05.json",
    "no_tick_contract": "reports/pnva-root-no-tick-causal-contract-2026-05-05.json",
    "runtime_admission": "reports/pnva-root-runtime-admission-controller-2026-05-05.json",
    "admission_matrix": "reports/pnva-root-entity-heuristic-admission-matrix-2026-05-05.json",
    "negative_controls": "reports/pnva-root-admission-negative-controls-2026-05-05.json",
    "event_identity": "reports/pnva-root-event-identity-ledger-2026-05-05.json",
    "runtime_growth_budget": "reports/pnva-root-runtime-growth-budget-2026-05-05.json",
    "causal_mesh": "reports/pnva-root-causal-mesh-ledger-2026-05-05.json",
    "efficiency_proof": "reports/pnva-root-efficiency-proof-ledger-2026-05-05.json",
    "equation_consistency": "reports/pnva-root-equation-consistency-ledger-2026-05-05.json",
    "legacy_quarantine": "reports/pnva-root-legacy-quarantine-ledger-2026-05-05.json",
    "evidence_chronology": "reports/pnva-root-evidence-chronology-ledger-2026-05-05.json",
}

EXPECTED_CLASSIFICATIONS = {
    "sovereignty_guard": "PNVA_ROOT_SOVEREIGNTY_GUARD_READY",
    "causal_intelligence": "PNVA_ROOT_CAUSAL_INTELLIGENCE_READY",
    "release_verifier": "PNVA_ROOT_RELEASE_VERIFIED",
    "publication_gate": "PNVA_ROOT_PUBLICATION_GATE_READY",
    "claim_boundary": "PNVA_ROOT_CLAIM_BOUNDARY_GUARD_READY",
    "invariant_firewall": "PNVA_ROOT_INVARIANT_FIREWALL_READY",
    "regression_sentinel": "PNVA_ROOT_REGRESSION_SENTINEL_READY",
    "no_tick_contract": "PNVA_ROOT_NO_TICK_CAUSAL_CONTRACT_READY",
    "runtime_admission": "PNVA_ROOT_RUNTIME_ADMISSION_READY",
    "admission_matrix": "PNVA_ROOT_ENTITY_HEURISTIC_ADMISSION_MATRIX_READY",
    "negative_controls": "PNVA_ROOT_ADMISSION_NEGATIVE_CONTROLS_PASS",
    "event_identity": "PNVA_ROOT_EVENT_IDENTITY_LEDGER_READY",
    "runtime_growth_budget": "PNVA_ROOT_RUNTIME_GROWTH_BUDGET_READY",
    "causal_mesh": "PNVA_ROOT_CAUSAL_MESH_LEDGER_READY",
    "efficiency_proof": "PNVA_ROOT_EFFICIENCY_PROOF_LEDGER_READY",
    "equation_consistency": "PNVA_ROOT_EQUATION_CONSISTENCY_LEDGER_READY",
    "legacy_quarantine": "PNVA_ROOT_LEGACY_QUARANTINE_LEDGER_READY",
    "evidence_chronology": "PNVA_ROOT_EVIDENCE_CHRONOLOGY_LEDGER_READY",
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _dig(data: Any, path: str, default: Any = None) -> Any:
    current = data
    for key in path.split("."):
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


def _num(value: Any, default: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    return numeric if math.isfinite(numeric) else default


def _same(values: dict[str, Any], *, tolerance: float = 0.0) -> bool:
    numbers = [_num(value) for value in values.values()]
    if not numbers:
        return False
    first = numbers[0]
    return all(abs(item - first) <= tolerance for item in numbers)


def _sha_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _check(name: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "pass": bool(passed), "evidence": evidence}


def _source_checks(reports: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for name, expected in EXPECTED_CLASSIFICATIONS.items():
        report = reports[name]
        rows.append(
            {
                "name": name,
                "classification": report.get("classification"),
                "expected": expected,
                "pass": report.get("classification") == expected and report.get("pass") is True,
            }
        )
    return rows


def build_report(repo: Path) -> dict[str, Any]:
    reports = {name: _read_json(repo / rel) for name, rel in REPORTS.items()}
    source_checks = _source_checks(reports)

    no_tick = reports["no_tick_contract"]
    runtime = reports["runtime_admission"]
    identity = reports["event_identity"]
    growth = reports["runtime_growth_budget"]
    mesh = reports["causal_mesh"]
    efficiency = reports["efficiency_proof"]
    equation = reports["equation_consistency"]
    legacy = reports["legacy_quarantine"]
    intelligence = reports["causal_intelligence"]
    publication = reports["publication_gate"]
    claim = reports["claim_boundary"]
    chronology = reports["evidence_chronology"]
    negative = reports["negative_controls"]
    matrix = reports["admission_matrix"]
    verifier = reports["release_verifier"]

    event_counts = {
        "no_tick_contract": no_tick.get("event_count"),
        "runtime_admission": runtime.get("event_count"),
        "event_identity": identity.get("event_count"),
        "growth_budget": growth.get("event_count"),
        "causal_mesh": mesh.get("event_count"),
        "causal_intelligence": _dig(intelligence, "no_tick_aggregate.event_count"),
    }
    suppressed_counts = {
        "no_tick_contract": no_tick.get("suppressed_count"),
        "runtime_admission": runtime.get("suppressed_count"),
        "growth_budget": growth.get("suppressed_count"),
        "causal_mesh": mesh.get("suppressed_count"),
        "causal_intelligence": _dig(intelligence, "no_tick_aggregate.suppressed_count"),
    }
    decision_counts = {
        "collapse": {
            "no_tick_contract": no_tick.get("collapse_count"),
            "event_identity": _dig(identity, "decision_counts.collapse"),
            "causal_intelligence": _dig(intelligence, "no_tick_aggregate.collapse_count"),
        },
        "observe": {
            "no_tick_contract": no_tick.get("observe_count"),
            "event_identity": _dig(identity, "decision_counts.observe"),
            "causal_intelligence": _dig(intelligence, "no_tick_aggregate.observe_count"),
        },
        "block": {
            "no_tick_contract": no_tick.get("block_count"),
            "event_identity": _dig(identity, "decision_counts.block"),
            "causal_intelligence": _dig(intelligence, "no_tick_aggregate.block_count"),
        },
        "prove": {
            "no_tick_contract": no_tick.get("prove_count"),
            "event_identity": _dig(identity, "decision_counts.prove"),
        },
    }
    identity_counts = {
        "event_count": identity.get("event_count"),
        "event_id_count": identity.get("event_id_count"),
        "unique_event_id_count": identity.get("unique_event_id_count"),
        "proof_hash_count": identity.get("proof_hash_count"),
        "unique_proof_hash_count": identity.get("unique_proof_hash_count"),
        "proof_valid_count": no_tick.get("proof_valid_count"),
    }
    entity_rule_counts = {
        "entity_count": {
            "event_identity": identity.get("entity_binding_count"),
            "causal_mesh": mesh.get("entity_count"),
        },
        "rule_count": {
            "event_identity": identity.get("rule_count"),
            "causal_mesh": mesh.get("rule_count"),
        },
        "rule_event_edge_count": {
            "event_identity": identity.get("rule_event_edge_count"),
            "causal_mesh": mesh.get("rule_event_edge_count"),
            "admission_matrix": matrix.get("rule_event_edge_count"),
        },
        "entity_rule_edge_count": {
            "causal_mesh": mesh.get("entity_rule_edge_count"),
            "admission_matrix": matrix.get("entity_rule_edge_count"),
            "growth_budget": growth.get("entity_rule_edge_count"),
        },
    }
    budget = growth.get("budget_policy", {})
    root_hashes = {
        name: report.get("root_release_hash")
        for name, report in reports.items()
        if report.get("root_release_hash")
    }
    root_hashes["release_verifier_recomputed"] = verifier.get("recomputed_root_release_hash")
    root_hash_set = {value for value in root_hashes.values() if value}

    checks = [
        _check("source_reports_ready", all(item["pass"] for item in source_checks), {"reports": source_checks}),
        _check(
            "no_tick_metrics_agree",
            _same(event_counts)
            and _same(suppressed_counts)
            and all(_same(values) for values in decision_counts.values())
            and no_tick.get("suppression_ratio") == growth.get("suppression_ratio") == mesh.get("suppression_ratio"),
            {
                "event_counts": event_counts,
                "suppressed_counts": suppressed_counts,
                "decision_counts": decision_counts,
                "suppression_ratio": no_tick.get("suppression_ratio"),
            },
        ),
        _check(
            "event_identity_and_proof_ready",
            identity_counts["event_count"] == identity_counts["event_id_count"] == identity_counts["unique_event_id_count"] == identity_counts["proof_hash_count"] == identity_counts["unique_proof_hash_count"] == identity_counts["proof_valid_count"] == 589
            and identity.get("r3_pair_failure_count") == 0
            and identity.get("projected_event_count") == 0
            and no_tick.get("projection_event_count") == 0,
            {
                "identity_counts": identity_counts,
                "r3_pair_failure_count": identity.get("r3_pair_failure_count"),
                "projected_event_count": identity.get("projected_event_count"),
                "native_count": identity.get("native_count"),
            },
        ),
        _check(
            "entities_and_heuristics_ready",
            _same(entity_rule_counts["entity_count"])
            and _same(entity_rule_counts["rule_count"])
            and _same(entity_rule_counts["rule_event_edge_count"])
            and _same(entity_rule_counts["entity_rule_edge_count"])
            and mesh.get("unknown_entity_count") == 0
            and mesh.get("unknown_rule_count") == 0
            and mesh.get("denied_edge_count") == 0
            and matrix.get("denied_edge_count") == 0,
            {
                "entity_rule_counts": entity_rule_counts,
                "unknown_entity_count": mesh.get("unknown_entity_count"),
                "unknown_rule_count": mesh.get("unknown_rule_count"),
                "denied_edge_count": matrix.get("denied_edge_count"),
            },
        ),
        _check(
            "runtime_growth_is_controlled",
            runtime.get("admission_decision") == "ADMIT_RESTRICTED_ROOT_RUNTIME_PLANNING"
            and budget.get("growth_mode") == "SMALL_BATCH_RESTRICTED"
            and budget.get("max_new_events_per_batch") == 118
            and budget.get("max_new_r3_chains_per_batch") == 7
            and budget.get("max_new_entity_rule_edges_per_batch") == 8
            and budget.get("max_denied_edges") == 0
            and budget.get("max_unknown_entities") == 0
            and budget.get("max_unknown_rules") == 0
            and budget.get("max_projected_events") == 0,
            {"admission_decision": runtime.get("admission_decision"), "budget_policy": budget},
        ),
        _check(
            "efficiency_proof_is_attributed",
            efficiency.get("efficiency_score") == 100.0
            and efficiency.get("event_count") == no_tick.get("event_count") == 589
            and efficiency.get("suppressed_count") == no_tick.get("suppressed_count") == 285
            and efficiency.get("avoided_action_count") == no_tick.get("suppressed_count") == 285
            and efficiency.get("avoided_action_ratio") == no_tick.get("suppression_ratio")
            and efficiency.get("entity_row_count") == mesh.get("entity_count") == 13
            and efficiency.get("rule_row_count") == mesh.get("rule_count") == 9
            and efficiency.get("rule_event_edge_count") == mesh.get("rule_event_edge_count") == 1350
            and efficiency.get("suppressed_proof_failure_count") == 0
            and efficiency.get("strict_threshold_violation_count") == 0,
            {
                "efficiency_score": efficiency.get("efficiency_score"),
                "avoided_action_count": efficiency.get("avoided_action_count"),
                "avoided_action_ratio": efficiency.get("avoided_action_ratio"),
                "entity_row_count": efficiency.get("entity_row_count"),
                "rule_row_count": efficiency.get("rule_row_count"),
                "rule_event_edge_count": efficiency.get("rule_event_edge_count"),
                "suppressed_proof_failure_count": efficiency.get("suppressed_proof_failure_count"),
                "strict_threshold_violation_count": efficiency.get("strict_threshold_violation_count"),
            },
        ),
        _check(
            "equation_consistency_is_strict",
            equation.get("equation_consistency_score") == 100.0
            and equation.get("event_count") == no_tick.get("event_count") == 589
            and equation.get("suppressed_count") == no_tick.get("suppressed_count") == 285
            and equation.get("avoided_action_ratio") == no_tick.get("suppression_ratio")
            and equation.get("formula_mismatch_count") == 0
            and equation.get("missing_equation_field_count") == 0
            and equation.get("strict_native_r3_violation_count") == 0
            and equation.get("entity_binding_count") == mesh.get("entity_count") == 13
            and equation.get("rule_count") == mesh.get("rule_count") == 9
            and equation.get("rule_event_edge_count") == mesh.get("rule_event_edge_count") == 1350,
            {
                "equation_consistency_score": equation.get("equation_consistency_score"),
                "formula_mismatch_count": equation.get("formula_mismatch_count"),
                "missing_equation_field_count": equation.get("missing_equation_field_count"),
                "strict_native_r3_violation_count": equation.get("strict_native_r3_violation_count"),
                "canonical_legacy_warning_count": equation.get("canonical_legacy_warning_count"),
                "canonical_legacy_threshold_exception_count": equation.get("canonical_legacy_threshold_exception_count"),
            },
        ),
        _check(
            "legacy_quarantine_is_bounded",
            legacy.get("legacy_quarantine_score") == 100.0
            and legacy.get("legacy_warning_count") == legacy.get("canonical_legacy_warning_count") == 384
            and legacy.get("native_legacy_warning_count") == 0
            and legacy.get("runtime_r3_legacy_warning_count") == 0
            and legacy.get("bounded_legacy_edge_count") == 5
            and legacy.get("controlled_legacy_rule_count") == 1
            and legacy.get("strict_native_r3_violation_count") == 0
            and legacy.get("projected_event_count") == 0
            and legacy.get("denied_edge_count") == 0,
            {
                "legacy_quarantine_score": legacy.get("legacy_quarantine_score"),
                "legacy_warning_count": legacy.get("legacy_warning_count"),
                "canonical_legacy_warning_count": legacy.get("canonical_legacy_warning_count"),
                "native_legacy_warning_count": legacy.get("native_legacy_warning_count"),
                "runtime_r3_legacy_warning_count": legacy.get("runtime_r3_legacy_warning_count"),
                "bounded_legacy_edge_count": legacy.get("bounded_legacy_edge_count"),
                "controlled_legacy_rule_count": legacy.get("controlled_legacy_rule_count"),
            },
        ),
        _check(
            "negative_controls_and_firewall_ready",
            negative.get("detected_count") == negative.get("control_count") == 8
            and negative.get("undetected_count") == 0
            and reports["invariant_firewall"].get("failure_count") == 0
            and reports["regression_sentinel"].get("failure_count") == 0,
            {
                "negative_controls": {
                    "control_count": negative.get("control_count"),
                    "detected_count": negative.get("detected_count"),
                    "undetected_count": negative.get("undetected_count"),
                },
                "invariant_firewall_failures": reports["invariant_firewall"].get("failure_count"),
                "regression_sentinel_failures": reports["regression_sentinel"].get("failure_count"),
            },
        ),
        _check(
            "publication_and_claim_boundary_clean",
            publication.get("path_leak_count") == 0
            and claim.get("unbounded_high_risk_occurrence_count") == 0
            and publication.get("checksum_count", 0) + 1 == publication.get("manifest_file_count", 0)
            and chronology.get("checksum_count") == publication.get("checksum_count")
            and chronology.get("manifest_file_count") == publication.get("manifest_file_count"),
            {
                "manifest_file_count": publication.get("manifest_file_count"),
                "checksum_count": publication.get("checksum_count"),
                "path_leak_count": publication.get("path_leak_count"),
                "claim_scanned_file_count": claim.get("scanned_file_count"),
                "unbounded_high_risk_occurrence_count": claim.get("unbounded_high_risk_occurrence_count"),
                "chronology_manifest_file_count": chronology.get("manifest_file_count"),
                "chronology_checksum_count": chronology.get("checksum_count"),
            },
        ),
        _check(
            "root_release_hash_aligned",
            root_hash_set == {ROOT_RELEASE_HASH}
            and verifier.get("root_release_hash") == ROOT_RELEASE_HASH
            and verifier.get("recomputed_root_release_hash") == ROOT_RELEASE_HASH,
            {"root_hashes": root_hashes, "expected": ROOT_RELEASE_HASH},
        ),
    ]
    failures = [item for item in checks if not item["pass"]]
    classification = "PNVA_ROOT_SOVEREIGN_READINESS_GATE_PASS" if not failures else "PNVA_ROOT_SOVEREIGN_READINESS_GATE_FAIL"
    seed = {
        "classification": classification,
        "checks": [{"name": item["name"], "pass": item["pass"]} for item in checks],
        "event_count": no_tick.get("event_count"),
        "suppressed_count": no_tick.get("suppressed_count"),
        "avoided_action_count": efficiency.get("avoided_action_count"),
        "avoided_action_ratio": efficiency.get("avoided_action_ratio"),
        "equation_consistency_score": equation.get("equation_consistency_score"),
        "legacy_warning_count": legacy.get("legacy_warning_count"),
        "native_legacy_warning_count": legacy.get("native_legacy_warning_count"),
        "entity_count": mesh.get("entity_count"),
        "rule_count": mesh.get("rule_count"),
        "root_release_hash": ROOT_RELEASE_HASH,
    }

    return {
        "schema_version": "pnva.root_sovereign_readiness_gate.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "readiness_score": round(100.0 * (len(checks) - len(failures)) / max(1, len(checks)), 2),
        "check_count": len(checks),
        "failure_count": len(failures),
        "event_count": no_tick.get("event_count"),
        "suppressed_count": no_tick.get("suppressed_count"),
        "suppression_ratio": no_tick.get("suppression_ratio"),
        "avoided_action_count": efficiency.get("avoided_action_count"),
        "avoided_action_ratio": efficiency.get("avoided_action_ratio"),
        "efficiency_score": efficiency.get("efficiency_score"),
        "equation_consistency_score": equation.get("equation_consistency_score"),
        "formula_mismatch_count": equation.get("formula_mismatch_count"),
        "strict_native_r3_violation_count": equation.get("strict_native_r3_violation_count"),
        "legacy_quarantine_score": legacy.get("legacy_quarantine_score"),
        "legacy_warning_count": legacy.get("legacy_warning_count"),
        "native_legacy_warning_count": legacy.get("native_legacy_warning_count"),
        "runtime_r3_legacy_warning_count": legacy.get("runtime_r3_legacy_warning_count"),
        "bounded_legacy_edge_count": legacy.get("bounded_legacy_edge_count"),
        "controlled_legacy_rule_count": legacy.get("controlled_legacy_rule_count"),
        "collapse_count": no_tick.get("collapse_count"),
        "observe_count": no_tick.get("observe_count"),
        "block_count": no_tick.get("block_count"),
        "prove_count": no_tick.get("prove_count"),
        "entity_count": mesh.get("entity_count"),
        "rule_count": mesh.get("rule_count"),
        "rule_event_edge_count": mesh.get("rule_event_edge_count"),
        "entity_rule_edge_count": mesh.get("entity_rule_edge_count"),
        "r3_chain_count": no_tick.get("r3_chain_count"),
        "proof_valid_count": no_tick.get("proof_valid_count"),
        "native_count": identity.get("native_count"),
        "projected_event_count": identity.get("projected_event_count"),
        "admission_decision": runtime.get("admission_decision"),
        "growth_mode": budget.get("growth_mode"),
        "negative_detected_count": negative.get("detected_count"),
        "manifest_file_count": publication.get("manifest_file_count"),
        "checksum_count": publication.get("checksum_count"),
        "path_leak_count": publication.get("path_leak_count"),
        "unbounded_high_risk_occurrence_count": claim.get("unbounded_high_risk_occurrence_count"),
        "root_release_hash": ROOT_RELEASE_HASH,
        "sovereign_readiness_gate_hash": _sha_text(json.dumps(seed, sort_keys=True, separators=(",", ":"), ensure_ascii=True)),
        "checks": checks,
        "source_classification_checks": source_checks,
        "interpretation": {
            "purpose": "Collapse root PNVA evidence into one final readiness gate across no-tick metrics, logs, heuristics, entities, runtime admission, growth, publication and validator registry.",
            "sovereignty": "A PNVA root system is sovereign only when its event identity, proof identity, entity/rule mesh, growth policy, negative controls and public boundaries remain aligned together.",
            "boundary": "This gate audits public evidence only. It does not execute actions, restart live gates, alter mining workloads or claim private threshold performance.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PNVA root sovereign readiness gate.")
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
