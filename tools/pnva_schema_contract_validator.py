#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_SCOPES = {
    "canonical": {
        "events": "reports/pnva-canonical-events-sample-2026-05-05.jsonl",
        "entity_catalog": "reports/pnva-entity-catalog-2026-05-05.json",
    },
    "native": {
        "events": "reports/pnva-native-events-demo-2026-05-05.jsonl",
        "entity_catalog": "reports/pnva-native-entity-catalog-demo-2026-05-05.json",
    },
}

EVENT_REQUIRED = {
    "schema_version",
    "event_id",
    "timestamp",
    "causal_chain_id",
    "entity_id",
    "event_type",
    "field",
    "tension",
    "decision",
    "proof",
}

ENTITY_REQUIRED = {
    "schema_version",
    "entity_id",
    "entity_type",
    "sovereignty_domain",
    "state",
    "capabilities",
    "evidence",
}

EVENT_DECISIONS = {"collapse", "block", "observe", "reclassify", "prove"}
ENTITY_TYPES = {
    "field",
    "event_source",
    "worker",
    "gate",
    "guard",
    "proof",
    "memory",
    "heuristic",
    "publication",
    "author",
}
SOVEREIGNTY_DOMAINS = {"runtime", "validation", "publication", "human_author", "external"}
ENTITY_STATES = {"idle", "observing", "candidate", "active", "blocked", "passed", "failed", "retired"}
HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
FORBIDDEN_PUBLIC_MARKERS = (
    "/" + "home" + "/",
    "Desktop/" + "document",
    "wallet",
    "secret",
    "token",
    "private" + "_key",
)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _parse_time(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def _contains_forbidden_public_marker(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_contains_forbidden_public_marker(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_forbidden_public_marker(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower()
        return any(marker.lower() in lowered for marker in FORBIDDEN_PUBLIC_MARKERS)
    return False


def _issue(target: list[dict[str, Any]], *, code: str, scope: str, subject: str, detail: str) -> None:
    target.append({"code": code, "scope": scope, "subject": subject, "detail": detail})


def _load_jsonl(path: Path, scope: str, errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
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
                _issue(errors, code="JSONL_NON_OBJECT", scope=scope, subject=f"line:{line_no}", detail="event line is not a JSON object")
                continue
            event["_line_no"] = line_no
            events.append(event)
    return events


def _validate_entity_catalog(scope: str, data: Any) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    entities_by_id: dict[str, dict[str, Any]] = {}
    entity_types: Counter[str] = Counter()
    entity_states: Counter[str] = Counter()

    if not isinstance(data, dict):
        _issue(errors, code="ENTITY_CATALOG_NON_OBJECT", scope=scope, subject="catalog", detail="catalog is not a JSON object")
        return {}, errors, warnings, {}
    if data.get("schema_version") != "pnva.entity_catalog.v1":
        _issue(errors, code="ENTITY_CATALOG_BAD_SCHEMA", scope=scope, subject="catalog", detail=str(data.get("schema_version")))

    entities = data.get("entities")
    if not isinstance(entities, list):
        _issue(errors, code="ENTITY_CATALOG_MISSING_ENTITIES", scope=scope, subject="catalog", detail="entities must be a list")
        entities = []
    if int(data.get("entity_count", -1)) != len(entities):
        _issue(errors, code="ENTITY_COUNT_MISMATCH", scope=scope, subject="catalog", detail=f"declared={data.get('entity_count')} actual={len(entities)}")

    duplicate_ids = set()
    for index, entity in enumerate(entities, 1):
        subject = f"entity:{index}"
        if not isinstance(entity, dict):
            _issue(errors, code="ENTITY_NON_OBJECT", scope=scope, subject=subject, detail="entity is not a JSON object")
            continue
        entity_id = str(entity.get("entity_id", ""))
        if entity_id:
            subject = entity_id
            if entity_id in entities_by_id:
                duplicate_ids.add(entity_id)
            entities_by_id[entity_id] = entity
        missing = sorted(ENTITY_REQUIRED.difference(entity))
        if missing:
            _issue(errors, code="ENTITY_MISSING_REQUIRED", scope=scope, subject=subject, detail=",".join(missing))
        if entity.get("schema_version") != "pnva.entity.v1":
            _issue(errors, code="ENTITY_BAD_SCHEMA", scope=scope, subject=subject, detail=str(entity.get("schema_version")))
        entity_type = entity.get("entity_type")
        if entity_type not in ENTITY_TYPES:
            _issue(errors, code="ENTITY_BAD_TYPE", scope=scope, subject=subject, detail=str(entity_type))
        else:
            entity_types[str(entity_type)] += 1
        state = entity.get("state")
        if state not in ENTITY_STATES:
            _issue(errors, code="ENTITY_BAD_STATE", scope=scope, subject=subject, detail=str(state))
        else:
            entity_states[str(state)] += 1
        if entity.get("sovereignty_domain") not in SOVEREIGNTY_DOMAINS:
            _issue(errors, code="ENTITY_BAD_DOMAIN", scope=scope, subject=subject, detail=str(entity.get("sovereignty_domain")))
        capabilities = entity.get("capabilities")
        if not isinstance(capabilities, list) or not capabilities or not all(isinstance(item, str) and item for item in capabilities):
            _issue(errors, code="ENTITY_BAD_CAPABILITIES", scope=scope, subject=subject, detail="capabilities must be a non-empty string list")
        elif len(set(capabilities)) != len(capabilities):
            _issue(warnings, code="ENTITY_DUPLICATE_CAPABILITY", scope=scope, subject=subject, detail="capabilities contain duplicates")
        evidence = entity.get("evidence")
        if not isinstance(evidence, dict):
            _issue(errors, code="ENTITY_BAD_EVIDENCE", scope=scope, subject=subject, detail="evidence must be object")
        else:
            if not isinstance(evidence.get("proof_ref"), str) or not evidence.get("proof_ref"):
                _issue(errors, code="ENTITY_MISSING_PROOF_REF", scope=scope, subject=subject, detail="evidence.proof_ref")
            if not _is_number(evidence.get("confidence")) or not 0 <= float(evidence.get("confidence")) <= 1:
                _issue(errors, code="ENTITY_BAD_CONFIDENCE", scope=scope, subject=subject, detail=str(evidence.get("confidence")))
            if evidence.get("last_seen") is not None and not _parse_time(evidence.get("last_seen")):
                _issue(warnings, code="ENTITY_LAST_SEEN_UNPARSEABLE", scope=scope, subject=subject, detail=str(evidence.get("last_seen")))
        if _contains_forbidden_public_marker(entity):
            _issue(errors, code="ENTITY_PUBLIC_MARKER_LEAK", scope=scope, subject=subject, detail="entity contains forbidden public marker")

    for entity_id in sorted(duplicate_ids):
        _issue(errors, code="ENTITY_DUPLICATE_ID", scope=scope, subject=entity_id, detail="duplicate entity_id")

    summary = {
        "entity_count": len(entities),
        "unique_entity_ids": len(entities_by_id),
        "entity_type_counts": dict(sorted(entity_types.items())),
        "entity_state_counts": dict(sorted(entity_states.items())),
        "declared_entity_count": data.get("entity_count"),
    }
    return summary, errors, warnings, entities_by_id


def _validate_event(scope: str, event: dict[str, Any], entities: dict[str, dict[str, Any]], seen_ids: set[str], errors: list[dict[str, Any]], warnings: list[dict[str, Any]], counters: dict[str, Counter[str]]) -> None:
    subject = str(event.get("event_id") or f"line:{event.get('_line_no')}")
    missing = sorted(EVENT_REQUIRED.difference(event))
    if missing:
        _issue(errors, code="EVENT_MISSING_REQUIRED", scope=scope, subject=subject, detail=",".join(missing))
    if event.get("schema_version") != "pnva.event.v1":
        _issue(errors, code="EVENT_BAD_SCHEMA", scope=scope, subject=subject, detail=str(event.get("schema_version")))
    event_id = event.get("event_id")
    if not isinstance(event_id, str) or len(event_id) < 6:
        _issue(errors, code="EVENT_BAD_ID", scope=scope, subject=subject, detail=str(event_id))
    elif event_id in seen_ids:
        _issue(errors, code="EVENT_DUPLICATE_ID", scope=scope, subject=subject, detail="duplicate event_id")
    else:
        seen_ids.add(event_id)
    if not _parse_time(event.get("timestamp")):
        _issue(errors, code="EVENT_BAD_TIMESTAMP", scope=scope, subject=subject, detail=str(event.get("timestamp")))
    if not isinstance(event.get("causal_chain_id"), str) or len(str(event.get("causal_chain_id"))) < 3:
        _issue(errors, code="EVENT_BAD_CAUSAL_CHAIN", scope=scope, subject=subject, detail=str(event.get("causal_chain_id")))
    entity_id = event.get("entity_id")
    if not isinstance(entity_id, str) or not entity_id:
        _issue(errors, code="EVENT_BAD_ENTITY_ID", scope=scope, subject=subject, detail=str(entity_id))
    elif entity_id not in entities:
        _issue(errors, code="EVENT_ENTITY_NOT_IN_CATALOG", scope=scope, subject=subject, detail=entity_id)
    else:
        catalog_type = entities[entity_id].get("entity_type")
        if event.get("entity_type") and catalog_type and event.get("entity_type") != catalog_type:
            _issue(warnings, code="EVENT_ENTITY_TYPE_DIFFERS_FROM_CATALOG", scope=scope, subject=subject, detail=f"event={event.get('entity_type')} catalog={catalog_type}")
    if not isinstance(event.get("event_type"), str) or not event.get("event_type"):
        _issue(errors, code="EVENT_BAD_TYPE", scope=scope, subject=subject, detail=str(event.get("event_type")))

    field = event.get("field")
    if not isinstance(field, dict):
        _issue(errors, code="EVENT_BAD_FIELD", scope=scope, subject=subject, detail="field must be object")
    else:
        for key in ("state_before", "state_after"):
            if not isinstance(field.get(key), str) or not field.get(key):
                _issue(errors, code="EVENT_FIELD_MISSING_STATE", scope=scope, subject=subject, detail=key)
        for key in ("phi", "gradient", "hessian"):
            if key in field and not _is_number(field.get(key)):
                _issue(errors, code="EVENT_FIELD_NON_NUMERIC", scope=scope, subject=subject, detail=key)

    tension = event.get("tension")
    if not isinstance(tension, dict):
        _issue(errors, code="EVENT_BAD_TENSION", scope=scope, subject=subject, detail="tension must be object")
    else:
        for key in ("score", "threshold", "gate_delta"):
            if not _is_number(tension.get(key)):
                _issue(errors, code="EVENT_TENSION_NON_NUMERIC", scope=scope, subject=subject, detail=key)
        if _is_number(tension.get("score")) and _is_number(tension.get("threshold")) and _is_number(tension.get("gate_delta")):
            margin = float(tension.get("margin", 0.0)) if _is_number(tension.get("margin", 0.0)) else 0.0
            expected_delta = round(float(tension["score"]) - max(0.0, float(tension["threshold"]) - margin), 8)
            observed_delta = round(float(tension["gate_delta"]), 8)
            if not math.isclose(expected_delta, observed_delta, abs_tol=0.0001):
                _issue(warnings, code="EVENT_GATE_DELTA_DRIFT", scope=scope, subject=subject, detail=f"expected={expected_delta} observed={observed_delta}")
        if "components" in tension and not isinstance(tension.get("components"), dict):
            _issue(errors, code="EVENT_TENSION_BAD_COMPONENTS", scope=scope, subject=subject, detail="components must be object")

    decision = event.get("decision")
    if not isinstance(decision, dict):
        _issue(errors, code="EVENT_BAD_DECISION", scope=scope, subject=subject, detail="decision must be object")
    else:
        kind = decision.get("kind")
        counters["decisions"][str(kind)] += 1
        if kind not in EVENT_DECISIONS:
            _issue(errors, code="EVENT_BAD_DECISION_KIND", scope=scope, subject=subject, detail=str(kind))
        for key in ("action", "reason"):
            if not isinstance(decision.get(key), str) or not decision.get(key):
                _issue(errors, code="EVENT_DECISION_MISSING_FIELD", scope=scope, subject=subject, detail=key)
        if decision.get("confidence") is not None and (not _is_number(decision.get("confidence")) or not 0 <= float(decision.get("confidence")) <= 1):
            _issue(errors, code="EVENT_BAD_DECISION_CONFIDENCE", scope=scope, subject=subject, detail=str(decision.get("confidence")))

    heuristics = event.get("heuristics")
    if not isinstance(heuristics, dict):
        _issue(errors, code="EVENT_BAD_HEURISTICS", scope=scope, subject=subject, detail="heuristics must be object")
    else:
        rules = heuristics.get("rules")
        if not isinstance(rules, list) or not rules or not all(isinstance(item, str) and item for item in rules):
            _issue(errors, code="EVENT_BAD_HEURISTIC_RULES", scope=scope, subject=subject, detail="rules must be a non-empty string list")
        else:
            for rule in rules:
                counters["heuristics"][rule] += 1
        risk_flags = heuristics.get("risk_flags")
        if risk_flags is not None and not isinstance(risk_flags, list):
            _issue(errors, code="EVENT_BAD_RISK_FLAGS", scope=scope, subject=subject, detail="risk_flags must be list")

    proof = event.get("proof")
    if not isinstance(proof, dict):
        _issue(errors, code="EVENT_BAD_PROOF", scope=scope, subject=subject, detail="proof must be object")
    else:
        if proof.get("canonical") is not True:
            _issue(errors, code="EVENT_PROOF_NOT_CANONICAL", scope=scope, subject=subject, detail=str(proof.get("canonical")))
        if proof.get("valid") is not True:
            _issue(errors, code="EVENT_PROOF_NOT_VALID", scope=scope, subject=subject, detail=str(proof.get("valid")))
        if not isinstance(proof.get("proof_ref"), str) or not proof.get("proof_ref"):
            _issue(errors, code="EVENT_MISSING_PROOF_REF", scope=scope, subject=subject, detail="proof.proof_ref")
        if not isinstance(proof.get("proof_hash"), str) or not HASH_RE.match(proof.get("proof_hash", "")):
            _issue(errors, code="EVENT_BAD_PROOF_HASH", scope=scope, subject=subject, detail=str(proof.get("proof_hash")))

    source = event.get("source")
    if not isinstance(source, dict):
        _issue(errors, code="EVENT_BAD_SOURCE", scope=scope, subject=subject, detail="source must be object")
    elif source.get("sanitized") is not True:
        _issue(errors, code="EVENT_SOURCE_NOT_SANITIZED", scope=scope, subject=subject, detail=str(source.get("sanitized")))

    relations = event.get("relations")
    if relations is not None:
        if not isinstance(relations, dict):
            _issue(errors, code="EVENT_BAD_RELATIONS", scope=scope, subject=subject, detail="relations must be object")
        else:
            target = relations.get("target_entity_id")
            if not isinstance(target, str) or not target:
                _issue(errors, code="EVENT_BAD_RELATION_TARGET", scope=scope, subject=subject, detail=str(target))
            elif target not in entities:
                _issue(errors, code="EVENT_RELATION_TARGET_NOT_IN_CATALOG", scope=scope, subject=subject, detail=target)
            counters["relations"][str(relations.get("relation"))] += 1

    if _contains_forbidden_public_marker(event):
        _issue(errors, code="EVENT_PUBLIC_MARKER_LEAK", scope=scope, subject=subject, detail="event contains forbidden public marker")


def _validate_scope(scope: str, repo: Path, event_rel: str, catalog_rel: str) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    event_path = repo / event_rel
    catalog_path = repo / catalog_rel
    if not event_path.exists():
        _issue(errors, code="EVENT_FILE_MISSING", scope=scope, subject=event_rel, detail="missing event file")
        return {"scope": scope, "errors": errors, "warnings": warnings}
    if not catalog_path.exists():
        _issue(errors, code="ENTITY_CATALOG_MISSING", scope=scope, subject=catalog_rel, detail="missing entity catalog")
        return {"scope": scope, "errors": errors, "warnings": warnings}

    catalog = _read_json(catalog_path)
    entity_summary, entity_errors, entity_warnings, entities_by_id = _validate_entity_catalog(scope, catalog)
    errors.extend(entity_errors)
    warnings.extend(entity_warnings)
    events = _load_jsonl(event_path, scope, errors)
    seen_ids: set[str] = set()
    counters: dict[str, Counter[str]] = {
        "decisions": Counter(),
        "heuristics": Counter(),
        "relations": Counter(),
    }
    for event in events:
        _validate_event(scope, event, entities_by_id, seen_ids, errors, warnings, counters)
    event_entity_ids = {str(event.get("entity_id")) for event in events if event.get("entity_id")}
    catalog_entity_ids = set(entities_by_id)
    unused_entities = sorted(catalog_entity_ids.difference(event_entity_ids))
    if unused_entities:
        _issue(warnings, code="CATALOG_ENTITY_NOT_OBSERVED", scope=scope, subject="catalog", detail=",".join(unused_entities[:20]))

    return {
        "scope": scope,
        "event_file": event_rel,
        "entity_catalog": catalog_rel,
        "event_count": len(events),
        "entity_count": entity_summary.get("entity_count", 0),
        "unique_event_ids": len(seen_ids),
        "observed_entity_count": len(event_entity_ids),
        "unused_entity_count": len(unused_entities),
        "entity_summary": entity_summary,
        "decision_counts": dict(sorted(counters["decisions"].items())),
        "heuristic_rule_counts": dict(sorted(counters["heuristics"].items())),
        "relation_counts": dict(sorted(counters["relations"].items())),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


def build_report(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    scopes = [
        _validate_scope(name, repo, spec["events"], spec["entity_catalog"])
        for name, spec in DEFAULT_SCOPES.items()
    ]
    total_events = sum(int(scope.get("event_count", 0)) for scope in scopes)
    total_entities = sum(int(scope.get("entity_count", 0)) for scope in scopes)
    total_errors = sum(int(scope.get("error_count", 0)) for scope in scopes)
    total_warnings = sum(int(scope.get("warning_count", 0)) for scope in scopes)
    total_relations = sum(sum(scope.get("relation_counts", {}).values()) for scope in scopes)
    all_rules = sorted({rule for scope in scopes for rule in scope.get("heuristic_rule_counts", {})})
    if total_errors:
        classification = "SCHEMA_CONTRACT_FAIL"
    elif total_warnings:
        classification = "SCHEMA_CONTRACT_READY_WITH_LEGACY_WARNINGS"
    else:
        classification = "SCHEMA_CONTRACT_READY"
    return {
        "schema_version": "pnva.schema_contract_validation.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": "Gustavo de Aguiar Martins",
        "project": "PNVA-Core",
        "classification": classification,
        "pass": total_errors == 0,
        "scope_count": len(scopes),
        "event_count": total_events,
        "entity_count": total_entities,
        "relation_count": total_relations,
        "heuristic_rule_count": len(all_rules),
        "error_count": total_errors,
        "warning_count": total_warnings,
        "scopes": scopes,
        "summary": {
            "validated_scopes": [scope.get("scope") for scope in scopes],
            "total_event_count": total_events,
            "total_entity_count": total_entities,
            "total_relation_count": total_relations,
            "total_heuristic_rule_count": len(all_rules),
            "heuristic_rules": all_rules,
            "contract_ready": total_errors == 0,
        },
        "interpretation": {
            "purpose": "Validate public PNVA event and entity evidence against the canonical contract without external dependencies.",
            "sovereignty": "A no-tick evidence package is stronger when every public event has schema version, entity identity, causal chain, tension, heuristic context, proof and sanitized source.",
            "boundary": "This validator checks public contract shape and safety; replay, policy, graph and proof-chain tools remain responsible for deeper causal semantics.",
        },
        "recommendations": [
            "Run this validator before attestation so contract failures become part of the evidence package.",
            "Treat any event/entity contract error as release-blocking.",
            "Keep legacy warnings visible, but require native runtime events to stay warning-light and error-free.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate PNVA public event/entity contract readiness.")
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
