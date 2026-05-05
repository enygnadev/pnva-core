#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from collections import Counter
from pathlib import Path
from typing import Any


AUTHOR = "Gustavo de Aguiar Martins"
PROJECT = "PNVA-Core"
ROOT_RELEASE_HASH = "sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc"

EVENT_STREAMS = {
    "canonical": "reports/pnva-canonical-events-sample-2026-05-05.jsonl",
    "native": "reports/pnva-native-events-demo-2026-05-05.jsonl",
    "runtime_r3": "reports/pnva-r3-runtime-events-2026-05-05.jsonl",
}

REPORTS = {
    "equation_consistency": "reports/pnva-root-equation-consistency-ledger-2026-05-05.json",
    "no_tick_contract": "reports/pnva-root-no-tick-causal-contract-2026-05-05.json",
    "tension_calibration": "reports/pnva-tension-decision-calibration-2026-05-05.json",
    "admission_matrix": "reports/pnva-root-entity-heuristic-admission-matrix-2026-05-05.json",
    "heuristic_weight": "reports/pnva-root-heuristic-weight-ledger-2026-05-05.json",
    "entity_capability": "reports/pnva-root-entity-capability-ledger-2026-05-05.json",
    "efficiency_proof": "reports/pnva-root-efficiency-proof-ledger-2026-05-05.json",
    "publication_gate": "reports/pnva-root-publication-gate-2026-05-05.json",
    "claim_boundary": "reports/pnva-root-claim-boundary-guard-2026-05-05.json",
    "release_verifier": "reports/pnva-root-release-verifier-2026-05-05.json",
}

EXPECTED_CLASSIFICATIONS = {
    "equation_consistency": "PNVA_ROOT_EQUATION_CONSISTENCY_LEDGER_READY",
    "no_tick_contract": "PNVA_ROOT_NO_TICK_CAUSAL_CONTRACT_READY",
    "tension_calibration": "TENSION_DECISION_READY_WITH_LEGACY_WARNINGS",
    "admission_matrix": "PNVA_ROOT_ENTITY_HEURISTIC_ADMISSION_MATRIX_READY",
    "heuristic_weight": "PNVA_ROOT_HEURISTIC_WEIGHT_LEDGER_READY",
    "entity_capability": "PNVA_ROOT_ENTITY_CAPABILITY_LEDGER_READY",
    "efficiency_proof": "PNVA_ROOT_EFFICIENCY_PROOF_LEDGER_READY",
    "publication_gate": "PNVA_ROOT_PUBLICATION_GATE_READY",
    "claim_boundary": "PNVA_ROOT_CLAIM_BOUNDARY_GUARD_READY",
    "release_verifier": "PNVA_ROOT_RELEASE_VERIFIED",
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append({"line": line_no, "error": str(exc)})
            continue
        if not isinstance(item, dict):
            errors.append({"line": line_no, "error": "jsonl item is not an object"})
            continue
        item["_line"] = line_no
        rows.append(item)
    return rows, errors


def _dig(data: Any, path: str, default: Any = None) -> Any:
    current = data
    for key in path.split("."):
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


def _num(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) else None


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


def _top(counter: Counter[str], limit: int = 10) -> list[list[Any]]:
    return [[key, count] for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:limit]]


def _is_legacy_warning(scope: str, event: dict[str, Any]) -> bool:
    decision = str(_dig(event, "decision.kind", ""))
    gate_delta = _num(_dig(event, "tension.gate_delta"))
    if gate_delta is None:
        return False
    if scope == "canonical":
        return (decision == "collapse" and gate_delta < 0) or (decision == "observe" and gate_delta >= 0)
    return (decision == "collapse" and gate_delta < 0) or (decision in {"observe", "block"} and gate_delta >= 0)


def build_report(repo: Path) -> dict[str, Any]:
    reports = {name: _read_json(repo / rel) for name, rel in REPORTS.items()}
    source_checks = _source_checks(reports)

    parse_errors: list[dict[str, Any]] = []
    scope_counts: Counter[str] = Counter()
    legacy_scope_counts: Counter[str] = Counter()
    legacy_decision_counts: Counter[str] = Counter()
    legacy_entity_counts: Counter[str] = Counter()
    legacy_rule_counts: Counter[str] = Counter()
    legacy_action_counts: Counter[str] = Counter()
    native_or_r3_warnings: list[dict[str, Any]] = []
    legacy_events: list[dict[str, Any]] = []

    for scope, rel in EVENT_STREAMS.items():
        events, errors = _read_jsonl(repo / rel)
        parse_errors.extend({"scope": scope, **item} for item in errors)
        for event in events:
            scope_counts[scope] += 1
            if not _is_legacy_warning(scope, event):
                continue
            decision = str(_dig(event, "decision.kind", ""))
            gate_delta = _num(_dig(event, "tension.gate_delta"))
            item = {
                "scope": scope,
                "event_id": event.get("event_id"),
                "entity_id": event.get("entity_id"),
                "decision": decision,
                "gate_delta": gate_delta,
                "action": _dig(event, "decision.action", ""),
            }
            if scope != "canonical":
                native_or_r3_warnings.append(item)
            legacy_events.append(item)
            legacy_scope_counts[scope] += 1
            legacy_decision_counts[decision] += 1
            legacy_entity_counts[str(event.get("entity_id") or "")] += 1
            legacy_action_counts[str(_dig(event, "decision.action", ""))] += 1
            legacy_rule_counts.update(str(rule) for rule in _dig(event, "heuristics.rules", []) or [] if str(rule))

    equation = reports["equation_consistency"]
    no_tick = reports["no_tick_contract"]
    calibration = reports["tension_calibration"]
    admission = reports["admission_matrix"]
    heuristic = reports["heuristic_weight"]
    capability = reports["entity_capability"]
    efficiency = reports["efficiency_proof"]
    publication = reports["publication_gate"]
    claim = reports["claim_boundary"]
    verifier = reports["release_verifier"]

    root_hashes = {
        name: report.get("root_release_hash")
        for name, report in reports.items()
        if report.get("root_release_hash")
    }
    root_hashes["release_verifier_recomputed"] = verifier.get("recomputed_root_release_hash")
    root_hash_set = {value for value in root_hashes.values() if value}

    legacy_warning_count = sum(legacy_scope_counts.values())
    checks = [
        _check("source_reports_ready", all(item["pass"] for item in source_checks), {"reports": source_checks}),
        _check("event_streams_parse_clean", not parse_errors and sum(scope_counts.values()) == 589, {"parse_errors": parse_errors, "scope_counts": dict(scope_counts)}),
        _check(
            "legacy_warnings_are_canonical_only",
            legacy_scope_counts.get("canonical") == legacy_warning_count == 384
            and legacy_scope_counts.get("native", 0) == 0
            and legacy_scope_counts.get("runtime_r3", 0) == 0
            and not native_or_r3_warnings,
            {
                "legacy_scope_counts": dict(legacy_scope_counts),
                "native_or_r3_warnings": native_or_r3_warnings[:10],
            },
        ),
        _check(
            "legacy_warning_counts_match_equation_and_calibration",
            legacy_warning_count == equation.get("canonical_legacy_warning_count") == calibration.get("legacy_calibration_warning_count") == 384
            and no_tick.get("canonical_legacy_threshold_exception_count") == equation.get("canonical_legacy_threshold_exception_count") == 294,
            {
                "computed_legacy_warning_count": legacy_warning_count,
                "equation_legacy_warning_count": equation.get("canonical_legacy_warning_count"),
                "calibration_legacy_warning_count": calibration.get("legacy_calibration_warning_count"),
                "no_tick_threshold_exception_count": no_tick.get("canonical_legacy_threshold_exception_count"),
            },
        ),
        _check(
            "legacy_decision_mix_bounded",
            legacy_decision_counts.get("collapse") == 208
            and legacy_decision_counts.get("observe") == 176
            and legacy_decision_counts.get("block", 0) == 0,
            {
                "legacy_decision_counts": dict(legacy_decision_counts),
                "top_legacy_actions": _top(legacy_action_counts, 8),
            },
        ),
        _check(
            "legacy_entity_rule_attribution_visible",
            len(legacy_entity_counts) == 4
            and len(legacy_rule_counts) == 7
            and capability.get("entity_row_count") == 13
            and heuristic.get("controlled_legacy_rule_count") == 1,
            {
                "legacy_entity_count": len(legacy_entity_counts),
                "legacy_rule_count": len(legacy_rule_counts),
                "top_legacy_entities": _top(legacy_entity_counts, 8),
                "top_legacy_rules": _top(legacy_rule_counts, 8),
                "controlled_legacy_rule_count": heuristic.get("controlled_legacy_rule_count"),
            },
        ),
        _check(
            "admission_keeps_legacy_bounded",
            admission.get("bounded_legacy_edge_count") == 5
            and admission.get("denied_edge_count") == 0
            and admission.get("unknown_entity_count") == 0
            and admission.get("unknown_rule_count") == 0,
            {
                "bounded_legacy_edge_count": admission.get("bounded_legacy_edge_count"),
                "denied_edge_count": admission.get("denied_edge_count"),
                "unknown_entity_count": admission.get("unknown_entity_count"),
                "unknown_rule_count": admission.get("unknown_rule_count"),
                "status_counts": admission.get("status_counts"),
            },
        ),
        _check(
            "clean_runtime_path_preserves_efficiency",
            equation.get("strict_native_r3_violation_count") == 0
            and efficiency.get("strict_threshold_violation_count") == 0
            and efficiency.get("projected_event_count") == 0
            and efficiency.get("avoided_action_count") == 285,
            {
                "equation_strict_native_r3_violation_count": equation.get("strict_native_r3_violation_count"),
                "efficiency_strict_threshold_violation_count": efficiency.get("strict_threshold_violation_count"),
                "projected_event_count": efficiency.get("projected_event_count"),
                "avoided_action_count": efficiency.get("avoided_action_count"),
            },
        ),
        _check(
            "public_boundaries_and_root_hash_stable",
            publication.get("path_leak_count") == 0
            and claim.get("unbounded_high_risk_occurrence_count") == 0
            and root_hash_set == {ROOT_RELEASE_HASH}
            and verifier.get("root_release_hash") == ROOT_RELEASE_HASH
            and verifier.get("recomputed_root_release_hash") == ROOT_RELEASE_HASH,
            {
                "path_leak_count": publication.get("path_leak_count"),
                "unbounded_high_risk_occurrence_count": claim.get("unbounded_high_risk_occurrence_count"),
                "root_hashes": root_hashes,
            },
        ),
    ]
    failures = [item for item in checks if not item["pass"]]
    classification = "PNVA_ROOT_LEGACY_QUARANTINE_LEDGER_READY" if not failures else "PNVA_ROOT_LEGACY_QUARANTINE_LEDGER_FAIL"
    seed = {
        "classification": classification,
        "checks": [{"name": item["name"], "pass": item["pass"]} for item in checks],
        "legacy_warning_count": legacy_warning_count,
        "legacy_entity_count": len(legacy_entity_counts),
        "legacy_rule_count": len(legacy_rule_counts),
        "bounded_legacy_edge_count": admission.get("bounded_legacy_edge_count"),
        "root_release_hash": ROOT_RELEASE_HASH,
    }

    return {
        "schema_version": "pnva.root_legacy_quarantine_ledger.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "legacy_quarantine_score": round(100.0 * (len(checks) - len(failures)) / max(1, len(checks)), 2),
        "check_count": len(checks),
        "failure_count": len(failures),
        "event_count": sum(scope_counts.values()),
        "legacy_warning_count": legacy_warning_count,
        "canonical_legacy_warning_count": legacy_scope_counts.get("canonical", 0),
        "native_legacy_warning_count": legacy_scope_counts.get("native", 0),
        "runtime_r3_legacy_warning_count": legacy_scope_counts.get("runtime_r3", 0),
        "canonical_legacy_threshold_exception_count": no_tick.get("canonical_legacy_threshold_exception_count"),
        "legacy_decision_counts": dict(legacy_decision_counts),
        "legacy_entity_count": len(legacy_entity_counts),
        "legacy_rule_count": len(legacy_rule_counts),
        "bounded_legacy_edge_count": admission.get("bounded_legacy_edge_count"),
        "controlled_legacy_rule_count": heuristic.get("controlled_legacy_rule_count"),
        "denied_edge_count": admission.get("denied_edge_count"),
        "unknown_entity_count": admission.get("unknown_entity_count"),
        "unknown_rule_count": admission.get("unknown_rule_count"),
        "strict_native_r3_violation_count": equation.get("strict_native_r3_violation_count"),
        "projected_event_count": efficiency.get("projected_event_count"),
        "path_leak_count": publication.get("path_leak_count"),
        "unbounded_high_risk_occurrence_count": claim.get("unbounded_high_risk_occurrence_count"),
        "root_release_hash": ROOT_RELEASE_HASH,
        "legacy_quarantine_ledger_hash": _sha_text(json.dumps(seed, sort_keys=True, separators=(",", ":"), ensure_ascii=True)),
        "checks": checks,
        "source_classification_checks": source_checks,
        "legacy_entity_rows": _top(legacy_entity_counts, 12),
        "legacy_rule_rows": _top(legacy_rule_counts, 12),
        "legacy_action_rows": _top(legacy_action_counts, 12),
        "interpretation": {
            "purpose": "Quarantine canonical legacy warnings so they remain visible and cannot be mistaken for clean native/R3 runtime evidence.",
            "sovereignty": "A root proof system is stronger when legacy debt is measured, attributed, bounded and excluded from strict runtime claims.",
            "boundary": "This ledger audits public evidence only. It does not execute actions, alter gates, rewrite legacy logs or publish private tuning.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PNVA root legacy quarantine ledger.")
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
