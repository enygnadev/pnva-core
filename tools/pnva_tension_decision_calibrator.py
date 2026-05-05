#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import statistics
import time
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_SCOPES = {
    "canonical": "reports/pnva-canonical-events-sample-2026-05-05.jsonl",
    "native": "reports/pnva-native-events-demo-2026-05-05.jsonl",
}

DECISION_KINDS = {"collapse", "block", "observe", "prove", "reclassify"}


def _issue(target: list[dict[str, Any]], *, code: str, scope: str, subject: str, detail: str) -> None:
    target.append({"code": code, "scope": scope, "subject": subject, "detail": detail})


def _round(value: float, digits: int = 6) -> float:
    if not math.isfinite(value):
        return 0.0
    return round(float(value), digits)


def _ratio(part: int | float, total: int | float) -> float:
    return _round(float(part) / max(1.0, float(total)))


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _load_events(path: Path, scope: str, errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not path.exists():
        _issue(errors, code="EVENT_FILE_MISSING", scope=scope, subject=str(path), detail="missing event file")
        return events
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except Exception as exc:
                _issue(errors, code="JSONL_PARSE_ERROR", scope=scope, subject=f"line:{line_no}", detail=str(exc))
                continue
            if not isinstance(event, dict):
                _issue(errors, code="JSONL_NON_OBJECT", scope=scope, subject=f"line:{line_no}", detail="event is not an object")
                continue
            event["_line_no"] = line_no
            events.append(event)
    return events


def _decision(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("decision")
    return value if isinstance(value, dict) else {}


def _tension(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("tension")
    return value if isinstance(value, dict) else {}


def _rules(event: dict[str, Any]) -> list[str]:
    heuristics = event.get("heuristics")
    if not isinstance(heuristics, dict):
        return []
    rules = heuristics.get("rules")
    if not isinstance(rules, list):
        return []
    return [str(item) for item in rules if str(item)]


def _source_format(event: dict[str, Any]) -> str:
    source = event.get("source")
    if not isinstance(source, dict):
        return ""
    return str(source.get("format") or "")


def _is_native(event: dict[str, Any]) -> bool:
    proof = event.get("proof")
    proof_native = isinstance(proof, dict) and proof.get("native") is True
    return _source_format(event) == "native_pnva_event_v1" or proof_native


def _expected_gate_delta(tension: dict[str, Any]) -> float | None:
    score = tension.get("score")
    threshold = tension.get("threshold")
    margin = tension.get("margin", 0.0)
    if not (_is_number(score) and _is_number(threshold)):
        return None
    margin_f = float(margin) if _is_number(margin) else 0.0
    return float(score) - max(0.0, float(threshold) - margin_f)


def _stats(values: list[float]) -> dict[str, Any]:
    if not values:
        return {
            "count": 0,
            "min": 0.0,
            "max": 0.0,
            "median": 0.0,
            "mean": 0.0,
        }
    return {
        "count": len(values),
        "min": _round(min(values)),
        "max": _round(max(values)),
        "median": _round(statistics.median(values)),
        "mean": _round(statistics.mean(values)),
    }


def _gate_family(event_type: str) -> str:
    if event_type == "ETEV_GUARD_PASS":
        return "guard_pass"
    if event_type == "ETEV_GUARD_BLOCK":
        return "guard_block"
    return "general"


def _analyze_scope(scope: str, repo: Path, rel: str) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    events = _load_events(repo / rel, scope, errors)
    decision_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    rule_counts: Counter[str] = Counter()
    gate_family_counts: Counter[str] = Counter()
    calibration_counts: Counter[str] = Counter()
    gate_deltas: list[float] = []
    abs_margins: list[float] = []
    formula_mismatch_count = 0
    native_error_count = 0

    for event in events:
        event_id = str(event.get("event_id") or f"line:{event.get('_line_no')}")
        decision = _decision(event)
        tension = _tension(event)
        kind = str(decision.get("kind") or "unknown")
        action = str(decision.get("action") or "")
        reason = str(decision.get("reason") or "")
        event_type = str(event.get("event_type") or "")
        native = _is_native(event)
        target = errors if native else warnings

        decision_counts[kind] += 1
        action_counts[action] += 1
        reason_counts[reason] += 1
        for rule in _rules(event):
            rule_counts[rule] += 1
        gate_family_counts[_gate_family(event_type)] += 1

        if kind not in DECISION_KINDS:
            _issue(errors, code="UNKNOWN_DECISION_KIND", scope=scope, subject=event_id, detail=kind)
            if native:
                native_error_count += 1

        gate_delta = tension.get("gate_delta")
        expected_delta = _expected_gate_delta(tension)
        if not _is_number(gate_delta) or expected_delta is None:
            _issue(errors, code="MISSING_NUMERIC_TENSION", scope=scope, subject=event_id, detail="score/threshold/gate_delta")
            if native:
                native_error_count += 1
            continue
        gate_delta_f = float(gate_delta)
        gate_deltas.append(gate_delta_f)
        abs_margins.append(abs(gate_delta_f))
        if not math.isclose(gate_delta_f, expected_delta, rel_tol=0.0, abs_tol=0.0001):
            formula_mismatch_count += 1
            _issue(
                errors,
                code="GATE_DELTA_FORMULA_MISMATCH",
                scope=scope,
                subject=event_id,
                detail=f"expected={_round(expected_delta)} observed={_round(gate_delta_f)}",
            )
            if native:
                native_error_count += 1

        signal = "positive" if gate_delta_f >= 0 else "negative"
        calibration_counts[f"{kind}_{signal}"] += 1
        if kind == "collapse" and gate_delta_f < 0:
            code = "NATIVE_COLLAPSE_BELOW_THRESHOLD" if native else "LEGACY_COLLAPSE_BELOW_THRESHOLD"
            _issue(target, code=code, scope=scope, subject=event_id, detail=f"gate_delta={_round(gate_delta_f)} action={action}")
            if native:
                native_error_count += 1
        elif kind == "block" and gate_delta_f >= 0:
            code = "NATIVE_BLOCK_ABOVE_THRESHOLD" if native else "LEGACY_BLOCK_ABOVE_THRESHOLD"
            _issue(target, code=code, scope=scope, subject=event_id, detail=f"gate_delta={_round(gate_delta_f)} action={action}")
            if native:
                native_error_count += 1
        elif kind == "observe" and gate_delta_f >= 0:
            code = "NATIVE_OBSERVE_ABOVE_THRESHOLD" if native else "LEGACY_OBSERVE_ABOVE_THRESHOLD"
            _issue(target, code=code, scope=scope, subject=event_id, detail=f"gate_delta={_round(gate_delta_f)} action={action}")
            if native:
                native_error_count += 1

        if event_type == "ETEV_GUARD_PASS" and (kind != "collapse" or gate_delta_f < 0):
            _issue(errors, code="GUARD_PASS_NOT_COLLAPSE", scope=scope, subject=event_id, detail=f"kind={kind} gate_delta={_round(gate_delta_f)}")
            if native:
                native_error_count += 1
        if event_type == "ETEV_GUARD_BLOCK" and (kind != "block" or gate_delta_f >= 0):
            _issue(errors, code="GUARD_BLOCK_NOT_BLOCK", scope=scope, subject=event_id, detail=f"kind={kind} gate_delta={_round(gate_delta_f)}")
            if native:
                native_error_count += 1

    warning_codes = Counter(item["code"] for item in warnings)
    error_codes = Counter(item["code"] for item in errors)
    native_clean = native_error_count == 0 if scope == "native" else True
    return {
        "scope": scope,
        "event_file": rel,
        "event_count": len(events),
        "decision_counts": dict(sorted(decision_counts.items())),
        "calibration_counts": dict(sorted(calibration_counts.items())),
        "gate_family_counts": dict(sorted(gate_family_counts.items())),
        "top_actions": [{"action": key, "count": count} for key, count in action_counts.most_common(12)],
        "top_reasons": [{"reason": key, "count": count} for key, count in reason_counts.most_common(12)],
        "heuristic_rule_counts": dict(sorted(rule_counts.items())),
        "gate_delta_stats": _stats(gate_deltas),
        "absolute_margin_stats": _stats(abs_margins),
        "formula_mismatch_count": formula_mismatch_count,
        "legacy_calibration_warning_count": len(warnings) if scope != "native" else 0,
        "native_calibration_clean": native_clean,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "error_codes": dict(sorted(error_codes.items())),
        "warning_codes": dict(sorted(warning_codes.items())),
        "errors": errors,
        "warnings": warnings,
    }


def build_report(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    scopes = [_analyze_scope(scope, repo, rel) for scope, rel in DEFAULT_SCOPES.items()]
    total_errors = sum(int(scope.get("error_count", 0)) for scope in scopes)
    total_warnings = sum(int(scope.get("warning_count", 0)) for scope in scopes)
    total_events = sum(int(scope.get("event_count", 0)) for scope in scopes)
    native_scope = next((scope for scope in scopes if scope.get("scope") == "native"), {})
    canonical_scope = next((scope for scope in scopes if scope.get("scope") == "canonical"), {})
    native_clean = bool(native_scope.get("native_calibration_clean"))
    if total_errors:
        classification = "TENSION_DECISION_CALIBRATION_FAIL"
    elif total_warnings:
        classification = "TENSION_DECISION_READY_WITH_LEGACY_WARNINGS"
    else:
        classification = "TENSION_DECISION_READY"
    return {
        "schema_version": "pnva.tension_decision_calibration.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": "Gustavo de Aguiar Martins",
        "project": "PNVA-Core",
        "classification": classification,
        "pass": total_errors == 0,
        "scope_count": len(scopes),
        "event_count": total_events,
        "error_count": total_errors,
        "warning_count": total_warnings,
        "native_calibration_clean": native_clean,
        "legacy_calibration_warning_count": int(canonical_scope.get("legacy_calibration_warning_count", 0)),
        "scopes": scopes,
        "summary": {
            "validated_scopes": [scope.get("scope") for scope in scopes],
            "total_event_count": total_events,
            "native_calibration_clean": native_clean,
            "canonical_legacy_warning_count": int(canonical_scope.get("legacy_calibration_warning_count", 0)),
            "native_warning_count": int(native_scope.get("warning_count", 0)),
            "legacy_warning_policy": "canonical bridge calibration warnings are preserved as migration evidence; native runtime calibration must remain error-free",
        },
        "interpretation": {
            "purpose": "Validate alignment between PNVA tension values, threshold margins, decision kind, guard events and action labels.",
            "sovereignty": "A no-tick runtime is stronger when every collapse, block or observe decision can be traced to tension crossing or not crossing threshold.",
            "boundary": "This guard checks calibration semantics; policy, schema, replay and graph validators keep their own authority and topology responsibilities.",
        },
        "recommendations": [
            "Treat native collapse below threshold as release-blocking.",
            "Treat native block above threshold as release-blocking.",
            "Keep canonical bridge calibration warnings visible until legacy logs are replaced by native pnva.event.v1 emission.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate PNVA tension/decision calibration.")
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--write", default="")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    report = build_report(repo)
    raw = json.dumps(report, indent=2, ensure_ascii=True, sort_keys=True) + "\n"
    if args.write:
        out = Path(args.write)
        if not out.is_absolute():
            out = repo / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
