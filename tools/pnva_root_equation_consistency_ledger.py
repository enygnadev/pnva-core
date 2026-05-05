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
    "tension_calibration": "reports/pnva-tension-decision-calibration-2026-05-05.json",
    "no_tick_contract": "reports/pnva-root-no-tick-causal-contract-2026-05-05.json",
    "event_identity": "reports/pnva-root-event-identity-ledger-2026-05-05.json",
    "efficiency_proof": "reports/pnva-root-efficiency-proof-ledger-2026-05-05.json",
    "causal_mesh": "reports/pnva-root-causal-mesh-ledger-2026-05-05.json",
    "publication_gate": "reports/pnva-root-publication-gate-2026-05-05.json",
    "claim_boundary": "reports/pnva-root-claim-boundary-guard-2026-05-05.json",
    "release_verifier": "reports/pnva-root-release-verifier-2026-05-05.json",
}

EXPECTED_CLASSIFICATIONS = {
    "tension_calibration": "TENSION_DECISION_READY_WITH_LEGACY_WARNINGS",
    "no_tick_contract": "PNVA_ROOT_NO_TICK_CAUSAL_CONTRACT_READY",
    "event_identity": "PNVA_ROOT_EVENT_IDENTITY_LEDGER_READY",
    "efficiency_proof": "PNVA_ROOT_EFFICIENCY_PROOF_LEDGER_READY",
    "causal_mesh": "PNVA_ROOT_CAUSAL_MESH_LEDGER_READY",
    "publication_gate": "PNVA_ROOT_PUBLICATION_GATE_READY",
    "claim_boundary": "PNVA_ROOT_CLAIM_BOUNDARY_GUARD_READY",
    "release_verifier": "PNVA_ROOT_RELEASE_VERIFIED",
}

SUPPRESSED_DECISIONS = {"observe", "block"}
EXECUTION_DECISIONS = {"collapse"}


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
        item["_source_file"] = path.name
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


def _ratio(numerator: int | float, denominator: int | float) -> float:
    return round(float(numerator) / float(denominator), 6) if denominator else 0.0


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


def _expected_gate_delta(event: dict[str, Any]) -> float | None:
    score = _num(_dig(event, "tension.score"))
    threshold = _num(_dig(event, "tension.threshold"))
    margin = _num(_dig(event, "tension.margin")) or 0.0
    if score is None or threshold is None:
        return None
    return score - max(0.0, threshold - max(0.0, margin))


def build_report(repo: Path) -> dict[str, Any]:
    reports = {name: _read_json(repo / rel) for name, rel in REPORTS.items()}
    source_checks = _source_checks(reports)

    parse_errors: list[dict[str, Any]] = []
    all_events: list[tuple[str, dict[str, Any]]] = []
    scope_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    rule_counts: Counter[str] = Counter()
    entity_counts: Counter[str] = Counter()
    formula_mismatches: list[dict[str, Any]] = []
    missing_equation_fields: list[dict[str, Any]] = []
    strict_native_r3_violations: list[dict[str, Any]] = []
    canonical_legacy_warnings: list[dict[str, Any]] = []

    for scope, rel in EVENT_STREAMS.items():
        rows, errors = _read_jsonl(repo / rel)
        parse_errors.extend({"scope": scope, **item} for item in errors)
        for event in rows:
            all_events.append((scope, event))
            scope_counts[scope] += 1
            decision = str(_dig(event, "decision.kind", ""))
            gate_delta = _num(_dig(event, "tension.gate_delta"))
            expected = _expected_gate_delta(event)
            decision_counts[decision] += 1
            entity_counts[f"{scope}:{event.get('entity_id')}"] += 1
            rule_counts.update(str(rule) for rule in _dig(event, "heuristics.rules", []) or [] if str(rule))

            if gate_delta is None or expected is None:
                missing_equation_fields.append({"scope": scope, "event_id": event.get("event_id"), "line": event.get("_line")})
                continue
            if not math.isclose(gate_delta, expected, rel_tol=0.0, abs_tol=0.0001):
                formula_mismatches.append(
                    {
                        "scope": scope,
                        "event_id": event.get("event_id"),
                        "line": event.get("_line"),
                        "score": _dig(event, "tension.score"),
                        "threshold": _dig(event, "tension.threshold"),
                        "margin": _dig(event, "tension.margin"),
                        "gate_delta": gate_delta,
                        "expected_gate_delta": round(expected, 6),
                    }
                )

            if scope in {"native", "runtime_r3"}:
                if decision in EXECUTION_DECISIONS and gate_delta < 0:
                    strict_native_r3_violations.append({"scope": scope, "event_id": event.get("event_id"), "decision": decision, "gate_delta": gate_delta})
                if decision in SUPPRESSED_DECISIONS and gate_delta >= 0:
                    strict_native_r3_violations.append({"scope": scope, "event_id": event.get("event_id"), "decision": decision, "gate_delta": gate_delta})
            elif scope == "canonical":
                if decision in EXECUTION_DECISIONS and gate_delta < 0:
                    canonical_legacy_warnings.append({"event_id": event.get("event_id"), "decision": decision, "gate_delta": gate_delta})
                if decision == "observe" and gate_delta >= 0:
                    canonical_legacy_warnings.append({"event_id": event.get("event_id"), "decision": decision, "gate_delta": gate_delta})

    event_count = len(all_events)
    suppressed_count = sum(decision_counts.get(kind, 0) for kind in SUPPRESSED_DECISIONS)
    collapse_count = decision_counts.get("collapse", 0)
    prove_count = decision_counts.get("prove", 0)
    avoided_action_ratio = _ratio(suppressed_count, event_count)

    calibration = reports["tension_calibration"]
    no_tick = reports["no_tick_contract"]
    identity = reports["event_identity"]
    efficiency = reports["efficiency_proof"]
    mesh = reports["causal_mesh"]
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

    checks = [
        _check("source_reports_ready", all(item["pass"] for item in source_checks), {"reports": source_checks}),
        _check(
            "event_streams_parse_and_match_root",
            not parse_errors and event_count == no_tick.get("event_count") == identity.get("event_count") == efficiency.get("event_count") == 589,
            {"parse_errors": parse_errors, "scope_counts": dict(scope_counts), "event_count": event_count},
        ),
        _check(
            "equation_fields_complete",
            not missing_equation_fields,
            {"missing_equation_field_count": len(missing_equation_fields), "missing_equation_fields": missing_equation_fields[:10]},
        ),
        _check(
            "gate_delta_formula_consistent",
            not formula_mismatches,
            {
                "formula": "gate_delta = score - max(0, threshold - margin)",
                "formula_mismatch_count": len(formula_mismatches),
                "formula_mismatches": formula_mismatches[:10],
            },
        ),
        _check(
            "native_r3_threshold_semantics_strict",
            not strict_native_r3_violations
            and no_tick.get("strict_threshold_violation_count") == 0
            and calibration.get("native_calibration_clean") is True,
            {
                "strict_native_r3_violation_count": len(strict_native_r3_violations),
                "strict_native_r3_violations": strict_native_r3_violations[:10],
                "no_tick_strict_threshold_violation_count": no_tick.get("strict_threshold_violation_count"),
                "native_calibration_clean": calibration.get("native_calibration_clean"),
            },
        ),
        _check(
            "canonical_legacy_exceptions_bounded",
            len(canonical_legacy_warnings) == calibration.get("legacy_calibration_warning_count") == 384
            and no_tick.get("canonical_legacy_threshold_exception_count") == 294,
            {
                "canonical_legacy_warning_count": len(canonical_legacy_warnings),
                "tension_calibration_legacy_warning_count": calibration.get("legacy_calibration_warning_count"),
                "no_tick_canonical_legacy_threshold_exception_count": no_tick.get("canonical_legacy_threshold_exception_count"),
                "policy": "canonical bridge warnings remain bounded legacy evidence and do not apply to native/R3 strict runtime paths",
            },
        ),
        _check(
            "equation_supports_efficiency_proof",
            suppressed_count == no_tick.get("suppressed_count") == efficiency.get("avoided_action_count") == 285
            and collapse_count == no_tick.get("collapse_count") == efficiency.get("collapse_count") == 303
            and prove_count == no_tick.get("prove_count") == efficiency.get("prove_count") == 1
            and avoided_action_ratio == no_tick.get("suppression_ratio") == efficiency.get("avoided_action_ratio"),
            {
                "suppressed_count": suppressed_count,
                "collapse_count": collapse_count,
                "prove_count": prove_count,
                "avoided_action_ratio": avoided_action_ratio,
            },
        ),
        _check(
            "entity_rule_attribution_closed",
            len(entity_counts) == identity.get("entity_binding_count") == mesh.get("entity_count") == efficiency.get("entity_row_count") == 13
            and len(rule_counts) == identity.get("rule_count") == mesh.get("rule_count") == efficiency.get("rule_row_count") == 9
            and sum(rule_counts.values()) == identity.get("rule_event_edge_count") == mesh.get("rule_event_edge_count") == efficiency.get("rule_event_edge_count") == 1350,
            {
                "entity_binding_count": len(entity_counts),
                "rule_count": len(rule_counts),
                "rule_event_edge_count": sum(rule_counts.values()),
                "top_rules": _top(rule_counts, 9),
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
    classification = "PNVA_ROOT_EQUATION_CONSISTENCY_LEDGER_READY" if not failures else "PNVA_ROOT_EQUATION_CONSISTENCY_LEDGER_FAIL"
    seed = {
        "classification": classification,
        "checks": [{"name": item["name"], "pass": item["pass"]} for item in checks],
        "event_count": event_count,
        "suppressed_count": suppressed_count,
        "avoided_action_ratio": avoided_action_ratio,
        "formula_mismatch_count": len(formula_mismatches),
        "strict_native_r3_violation_count": len(strict_native_r3_violations),
        "root_release_hash": ROOT_RELEASE_HASH,
    }

    return {
        "schema_version": "pnva.root_equation_consistency_ledger.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "equation_consistency_score": round(100.0 * (len(checks) - len(failures)) / max(1, len(checks)), 2),
        "check_count": len(checks),
        "failure_count": len(failures),
        "event_count": event_count,
        "scope_counts": dict(scope_counts),
        "decision_counts": dict(decision_counts),
        "suppressed_count": suppressed_count,
        "collapse_count": collapse_count,
        "prove_count": prove_count,
        "avoided_action_ratio": avoided_action_ratio,
        "formula_mismatch_count": len(formula_mismatches),
        "missing_equation_field_count": len(missing_equation_fields),
        "strict_native_r3_violation_count": len(strict_native_r3_violations),
        "canonical_legacy_warning_count": len(canonical_legacy_warnings),
        "canonical_legacy_threshold_exception_count": no_tick.get("canonical_legacy_threshold_exception_count"),
        "entity_binding_count": len(entity_counts),
        "rule_count": len(rule_counts),
        "rule_event_edge_count": sum(rule_counts.values()),
        "path_leak_count": publication.get("path_leak_count"),
        "unbounded_high_risk_occurrence_count": claim.get("unbounded_high_risk_occurrence_count"),
        "root_release_hash": ROOT_RELEASE_HASH,
        "equation_consistency_ledger_hash": _sha_text(json.dumps(seed, sort_keys=True, separators=(",", ":"), ensure_ascii=True)),
        "checks": checks,
        "source_classification_checks": source_checks,
        "interpretation": {
            "purpose": "Prove that public PNVA tension, threshold, margin and gate_delta fields agree with decision semantics and no-tick efficiency evidence.",
            "sovereignty": "The no-tick claim is stronger when the equation behind suppression and collapse is finite, replayable, threshold-bound and entity/rule-attributed.",
            "boundary": "This ledger audits public proof logs only. It does not publish private thresholds, execute actions, alter gates or claim hardware-level performance.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PNVA root equation consistency ledger.")
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
