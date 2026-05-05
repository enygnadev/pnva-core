#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any


AUTHOR = "Gustavo de Aguiar Martins"
PROJECT = "PNVA-Core"


REPORTS = {
    "canonical_no_tick": "reports/pnva-no-tick-invariants-2026-05-05.json",
    "native_no_tick": "reports/pnva-native-no-tick-invariants-2026-05-05.json",
    "runtime_no_tick": "reports/pnva-r3-runtime-no-tick-2026-05-05.json",
    "heuristic_influence": "reports/pnva-heuristic-influence-map-2026-05-05.json",
    "decision_trace": "reports/pnva-decision-trace-index-2026-05-05.json",
    "entity_no_tick": "reports/pnva-entity-no-tick-matrix-2026-05-05.json",
    "suppression_ledger": "reports/pnva-suppression-ledger-2026-05-05.json",
    "runtime_guard": "reports/pnva-r3-runtime-evidence-guard-2026-05-05.json",
    "runtime_contract": "reports/pnva-r3-runtime-contract-validation-2026-05-05.json",
    "root_traceability": "reports/pnva-root-traceability-matrix-2026-05-05.json",
    "root_causal_intelligence": "reports/pnva-root-causal-intelligence-2026-05-05.json",
    "root_sovereignty": "reports/pnva-root-sovereignty-guard-2026-05-05.json",
    "root_dependency_graph": "reports/pnva-root-dependency-graph-2026-05-05.json",
    "root_claim_boundary": "reports/pnva-root-claim-boundary-guard-2026-05-05.json",
    "root_publication": "reports/pnva-root-publication-gate-2026-05-05.json",
}

EVENT_STREAMS = {
    "canonical": "reports/pnva-canonical-events-sample-2026-05-05.jsonl",
    "native": "reports/pnva-native-events-demo-2026-05-05.jsonl",
    "runtime_r3": "reports/pnva-r3-runtime-events-2026-05-05.jsonl",
}

ENTITY_CATALOGS = {
    "canonical": "reports/pnva-entity-catalog-2026-05-05.json",
    "native": "reports/pnva-native-entity-catalog-demo-2026-05-05.json",
    "runtime_r3": "reports/pnva-r3-runtime-entity-catalog-2026-05-05.json",
}

EXPECTED_CLASSIFICATIONS = {
    "canonical_no_tick": "SOVEREIGN_NO_TICK_READY",
    "native_no_tick": "SOVEREIGN_NO_TICK_READY",
    "runtime_no_tick": "SOVEREIGN_NO_TICK_READY",
    "heuristic_influence": "HEURISTIC_INFLUENCE_MAP_READY_WITH_LEGACY_WARNINGS",
    "decision_trace": "DECISION_TRACE_INDEX_READY_WITH_LEGACY_WARNINGS",
    "entity_no_tick": "ENTITY_NO_TICK_MATRIX_READY_WITH_LEGACY_WARNINGS",
    "suppression_ledger": "SUPPRESSION_LEDGER_READY_WITH_LEGACY_WARNINGS",
    "runtime_guard": "R3_RUNTIME_EVIDENCE_ACCEPTED",
    "runtime_contract": "R3_RUNTIME_CONTRACT_VALIDATED_READY",
    "root_traceability": "PNVA_ROOT_TRACEABILITY_MATRIX_READY",
    "root_causal_intelligence": "PNVA_ROOT_CAUSAL_INTELLIGENCE_READY",
    "root_sovereignty": "PNVA_ROOT_SOVEREIGNTY_GUARD_READY",
    "root_dependency_graph": "PNVA_ROOT_DEPENDENCY_GRAPH_READY",
    "root_claim_boundary": "PNVA_ROOT_CLAIM_BOUNDARY_GUARD_READY",
    "root_publication": "PNVA_ROOT_PUBLICATION_GATE_READY",
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
        if isinstance(item, dict):
            rows.append(item)
        else:
            errors.append({"line": line_no, "error": "jsonl item is not an object"})
    return rows, errors


def _dig(data: Any, path: str, default: Any = None) -> Any:
    current = data
    for key in path.split("."):
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _sha_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _check(name: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "pass": bool(passed), "evidence": evidence}


def _counter_pairs(counter: Counter[str], limit: int = 12) -> list[list[Any]]:
    return [[key, count] for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:limit]]


def _event_stream_index(repo: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    index: dict[str, Any] = {}
    parse_errors: list[dict[str, Any]] = []
    for name, rel in EVENT_STREAMS.items():
        events, errors = _read_jsonl(repo / rel)
        parse_errors.extend({"stream": name, **item} for item in errors)
        decision_mix: Counter[str] = Counter()
        action_mix: Counter[str] = Counter()
        rule_mix: Counter[str] = Counter()
        risk_mix: Counter[str] = Counter()
        proof_hashes: list[str] = []
        native_count = 0
        projected_count = 0
        suppressed_count = 0
        collapse_count = 0
        for event in events:
            decision = str(_dig(event, "decision.kind", ""))
            action = str(_dig(event, "decision.action", ""))
            decision_mix.update([decision])
            action_mix.update([action])
            rule_mix.update(str(rule) for rule in _dig(event, "heuristics.rules", []) or [])
            risk_mix.update(str(flag) for flag in _dig(event, "heuristics.risk_flags", []) or [])
            proof_hash = str(_dig(event, "proof.proof_hash", ""))
            if proof_hash:
                proof_hashes.append(proof_hash)
            if _dig(event, "proof.native") is True:
                native_count += 1
            if _dig(event, "proof.projection") is True:
                projected_count += 1
            if decision in {"observe", "block"} or action == "NO_ACTION":
                suppressed_count += 1
            if decision == "collapse":
                collapse_count += 1
        index[name] = {
            "path": rel,
            "event_count": len(events),
            "parse_error_count": len(errors),
            "decision_mix": _counter_pairs(decision_mix),
            "action_mix": _counter_pairs(action_mix),
            "rule_mix": _counter_pairs(rule_mix),
            "risk_mix": _counter_pairs(risk_mix),
            "proof_hash_count": len(proof_hashes),
            "proof_hash_unique_count": len(set(proof_hashes)),
            "native_count": native_count,
            "projected_count": projected_count,
            "suppressed_count_observed": suppressed_count,
            "collapse_count_observed": collapse_count,
        }
    return index, parse_errors


def _entity_catalog_index(repo: Path) -> dict[str, Any]:
    scopes = {}
    state_mix: Counter[str] = Counter()
    type_mix: Counter[str] = Counter()
    capability_mix: Counter[str] = Counter()
    for name, rel in ENTITY_CATALOGS.items():
        data = _read_json(repo / rel)
        entities = [item for item in data.get("entities", []) if isinstance(item, dict)]
        for entity in entities:
            state_mix.update([str(entity.get("state", ""))])
            type_mix.update([str(entity.get("entity_type", ""))])
            capability_mix.update(str(capability) for capability in entity.get("capabilities", []) or [])
        scopes[name] = {
            "path": rel,
            "entity_count": len(entities),
            "schema_version": data.get("schema_version"),
            "states": _counter_pairs(Counter(str(entity.get("state", "")) for entity in entities)),
            "types": _counter_pairs(Counter(str(entity.get("entity_type", "")) for entity in entities)),
        }
    return {
        "scope_count": len(scopes),
        "total_entity_rows": sum(item["entity_count"] for item in scopes.values()),
        "scopes": scopes,
        "state_mix": _counter_pairs(state_mix),
        "type_mix": _counter_pairs(type_mix),
        "capability_mix": _counter_pairs(capability_mix),
    }


def build_report(repo: Path) -> dict[str, Any]:
    reports = {name: _read_json(repo / rel) for name, rel in REPORTS.items()}
    event_streams, parse_errors = _event_stream_index(repo)
    entity_catalogs = _entity_catalog_index(repo)

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

    no_tick_layers = {
        "canonical": reports["canonical_no_tick"].get("no_tick_efficiency", {}),
        "native": reports["native_no_tick"].get("no_tick_efficiency", {}),
        "runtime_r3": reports["runtime_no_tick"].get("no_tick_efficiency", {}),
    }
    aggregate_event_count = sum(int(_num(layer.get("event_count"))) for layer in no_tick_layers.values())
    aggregate_suppressed_count = sum(int(_num(layer.get("suppressed_count"))) for layer in no_tick_layers.values())
    aggregate_collapse_count = sum(int(_num(layer.get("collapse_count"))) for layer in no_tick_layers.values())
    aggregate_observe_count = sum(int(_num(layer.get("observe_count"))) for layer in no_tick_layers.values())
    aggregate_block_count = sum(int(_num(layer.get("block_count"))) for layer in no_tick_layers.values())
    aggregate_suppression_ratio = round(aggregate_suppressed_count / max(1, aggregate_event_count), 6)

    root_no_tick = reports["root_causal_intelligence"].get("no_tick_aggregate", {})
    no_tick_mismatches = []
    expected_no_tick = {
        "event_count": aggregate_event_count,
        "suppressed_count": aggregate_suppressed_count,
        "collapse_count": aggregate_collapse_count,
        "observe_count": aggregate_observe_count,
        "block_count": aggregate_block_count,
        "suppression_ratio": aggregate_suppression_ratio,
    }
    for key, expected_value in expected_no_tick.items():
        actual = root_no_tick.get(key)
        if isinstance(expected_value, float):
            if abs(_num(actual) - expected_value) > 0.000001:
                no_tick_mismatches.append({"field": key, "expected": expected_value, "actual": actual})
        elif int(_num(actual)) != expected_value:
            no_tick_mismatches.append({"field": key, "expected": expected_value, "actual": actual})

    stream_count_mismatches = []
    for name, stream in event_streams.items():
        report_count = int(_num(no_tick_layers[name].get("event_count")))
        if stream["event_count"] != report_count:
            stream_count_mismatches.append({"stream": name, "jsonl_count": stream["event_count"], "report_count": report_count})

    proof_coverage_failures = []
    for name, layer in no_tick_layers.items():
        if _num(layer.get("proof_integrity_ratio")) != 1.0:
            proof_coverage_failures.append({"layer": name, "proof_integrity_ratio": layer.get("proof_integrity_ratio")})
        if name != "runtime_r3" and _num(layer.get("guard_consistency_ratio")) != 1.0:
            proof_coverage_failures.append({"layer": name, "guard_consistency_ratio": layer.get("guard_consistency_ratio")})
    for name, stream in event_streams.items():
        if stream["proof_hash_count"] != stream["proof_hash_unique_count"]:
            proof_coverage_failures.append(
                {
                    "layer": name,
                    "proof_hash_count": stream["proof_hash_count"],
                    "proof_hash_unique_count": stream["proof_hash_unique_count"],
                }
            )

    native_clean_failures = []
    clean_fields = {
        "heuristic_influence.native_influence_clean": reports["heuristic_influence"].get("native_influence_clean"),
        "decision_trace.native_trace_clean": reports["decision_trace"].get("native_trace_clean"),
        "entity_no_tick.native_matrix_clean": reports["entity_no_tick"].get("native_matrix_clean"),
        "suppression_ledger.native_suppression_clean": reports["suppression_ledger"].get("native_suppression_clean"),
    }
    for name, value in clean_fields.items():
        if value is not True:
            native_clean_failures.append({"field": name, "value": value})
    if event_streams["runtime_r3"]["projected_count"] != 0:
        native_clean_failures.append({"field": "runtime_r3.projected_count", "value": event_streams["runtime_r3"]["projected_count"]})

    root_failures = []
    root_expectations = {
        "root_traceability.root_traceability_score": reports["root_traceability"].get("root_traceability_score"),
        "root_causal_intelligence.root_causal_intelligence_score": reports["root_causal_intelligence"].get("root_causal_intelligence_score"),
        "root_sovereignty.root_score": reports["root_sovereignty"].get("root_score"),
        "root_dependency_graph.dependency_score": reports["root_dependency_graph"].get("dependency_score"),
        "root_claim_boundary.claim_boundary_score": reports["root_claim_boundary"].get("claim_boundary_score"),
        "root_publication.publication_score": reports["root_publication"].get("publication_score"),
    }
    for field, value in root_expectations.items():
        if _num(value) != 100.0:
            root_failures.append({"field": field, "value": value})

    runtime_guard = reports["runtime_guard"]
    runtime_contract = reports["runtime_contract"]
    runtime_failures = []
    if int(_num(runtime_guard.get("accepted_slot_count"))) != 35:
        runtime_failures.append({"field": "runtime_guard.accepted_slot_count", "value": runtime_guard.get("accepted_slot_count")})
    if int(_num(runtime_guard.get("pending_slot_count"))) != 0:
        runtime_failures.append({"field": "runtime_guard.pending_slot_count", "value": runtime_guard.get("pending_slot_count")})
    if int(_num(runtime_guard.get("rejected_event_count"))) != 0:
        runtime_failures.append({"field": "runtime_guard.rejected_event_count", "value": runtime_guard.get("rejected_event_count")})
    if int(_num(runtime_contract.get("failure_count"))) != 0:
        runtime_failures.append({"field": "runtime_contract.failure_count", "value": runtime_contract.get("failure_count")})
    if int(_num(runtime_guard.get("no_tick_pair_failure_count"))) != 0:
        runtime_failures.append({"field": "runtime_guard.no_tick_pair_failure_count", "value": runtime_guard.get("no_tick_pair_failure_count")})

    checks = [
        _check("required_observability_reports_ready", not classification_failures, {"classification_failures": classification_failures}),
        _check("event_streams_parse_and_match_reports", not parse_errors and not stream_count_mismatches, {"parse_errors": parse_errors[:20], "stream_count_mismatches": stream_count_mismatches}),
        _check("aggregate_no_tick_matches_root_causal_intelligence", not no_tick_mismatches, {"expected_no_tick": expected_no_tick, "mismatches": no_tick_mismatches}),
        _check("proof_and_guard_coverage_closed", not proof_coverage_failures, {"proof_coverage_failures": proof_coverage_failures}),
        _check("native_and_runtime_scope_clean", not native_clean_failures, {"native_clean_failures": native_clean_failures}),
        _check("runtime_slots_contract_and_guard_closed", not runtime_failures, {"runtime_failures": runtime_failures}),
        _check("root_scores_all_maxed", not root_failures, {"root_failures": root_failures, "root_scores": root_expectations}),
        _check("claim_and_publication_boundary_clean", reports["root_claim_boundary"].get("unbounded_high_risk_occurrence_count") == 0 and reports["root_publication"].get("path_leak_count") == 0, {"unbounded_high_risk_occurrence_count": reports["root_claim_boundary"].get("unbounded_high_risk_occurrence_count"), "path_leak_count": reports["root_publication"].get("path_leak_count")}),
    ]
    failures = [item for item in checks if not item["pass"]]
    score = round(100.0 * (len(checks) - len(failures)) / max(1, len(checks)), 2)
    classification = "PNVA_ROOT_OBSERVABILITY_INDEX_READY" if not failures else "PNVA_ROOT_OBSERVABILITY_INDEX_FAIL"

    fingerprint = {
        "classification": classification,
        "checks": [{"name": item["name"], "pass": item["pass"]} for item in checks],
        "no_tick": expected_no_tick,
        "event_streams": {name: {"event_count": item["event_count"], "proof_hash_unique_count": item["proof_hash_unique_count"]} for name, item in event_streams.items()},
        "entity_catalogs": {name: {"entity_count": item["entity_count"]} for name, item in entity_catalogs["scopes"].items()},
        "root_scores": root_expectations,
    }

    return {
        "schema_version": "pnva.root_observability_index.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "observability_score": score,
        "check_count": len(checks),
        "failure_count": len(failures),
        "checks": checks,
        "no_tick_observability": {
            "layers": no_tick_layers,
            "aggregate_event_count": aggregate_event_count,
            "aggregate_suppressed_count": aggregate_suppressed_count,
            "aggregate_collapse_count": aggregate_collapse_count,
            "aggregate_observe_count": aggregate_observe_count,
            "aggregate_block_count": aggregate_block_count,
            "aggregate_suppression_ratio": aggregate_suppression_ratio,
            "root_causal_intelligence_aggregate": root_no_tick,
        },
        "log_observability": event_streams,
        "entity_observability": entity_catalogs,
        "heuristic_observability": {
            "heuristic_rule_count": reports["heuristic_influence"].get("heuristic_rule_count"),
            "influence_edge_count": reports["heuristic_influence"].get("influence_edge_count"),
            "heuristic_coverage_ratio": reports["heuristic_influence"].get("heuristic_coverage_ratio"),
            "proof_event_coverage_ratio": reports["heuristic_influence"].get("proof_event_coverage_ratio"),
            "native_influence_clean": reports["heuristic_influence"].get("native_influence_clean"),
            "low_authority_legacy_context": {
                "heuristic_low_authority_strong_edge_count": reports["heuristic_influence"].get("low_authority_strong_edge_count"),
                "entity_legacy_low_authority_warning_count": reports["entity_no_tick"].get("legacy_low_authority_warning_count"),
                "decision_trace_low_authority_trace_count": reports["decision_trace"].get("low_authority_trace_count"),
                "controlled_boundary": "legacy warnings are preserved as canonical migration evidence; native and R3 runtime scopes are clean",
            },
        },
        "runtime_observability": {
            "accepted_slot_count": runtime_guard.get("accepted_slot_count"),
            "pending_slot_count": runtime_guard.get("pending_slot_count"),
            "rejected_event_count": runtime_guard.get("rejected_event_count"),
            "no_tick_pair_integrity_count": runtime_guard.get("no_tick_pair_integrity_count"),
            "no_tick_pair_failure_count": runtime_guard.get("no_tick_pair_failure_count"),
            "negative_control_detected_count": runtime_guard.get("negative_control_detected_count"),
            "negative_control_count": runtime_guard.get("negative_control_count"),
            "contract_check_count": runtime_contract.get("contract_check_count"),
            "contract_failure_count": runtime_contract.get("failure_count"),
        },
        "root_observability": {
            "root_release_hash": reports["root_publication"].get("root_release_hash"),
            "root_scores": root_expectations,
            "dependency_graph_hash": reports["root_dependency_graph"].get("dependency_graph_hash"),
            "publication_path_leak_count": reports["root_publication"].get("path_leak_count"),
            "unbounded_high_risk_occurrence_count": reports["root_claim_boundary"].get("unbounded_high_risk_occurrence_count"),
        },
        "observability_index_hash": _sha_text(json.dumps(fingerprint, sort_keys=True, separators=(",", ":"))),
        "interpretation": {
            "purpose": "Expose one root laboratory view for PNVA/no-tick logs, entities, heuristics, runtime slots and public proof gates.",
            "sovereignty": "A root system is stronger when every PASS can be traced to observable log, entity, heuristic and proof metrics.",
            "boundary": "This index is a public observability layer over existing reports; it does not change the root release seal or claim private deployment validation.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PNVA root observability index.")
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
