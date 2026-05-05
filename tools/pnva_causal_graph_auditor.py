#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_events(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except Exception as exc:
                errors.append({"line": line_no, "code": "JSON_PARSE_ERROR", "message": str(exc)})
                continue
            if not isinstance(event, dict):
                errors.append({"line": line_no, "code": "EVENT_NOT_OBJECT"})
                continue
            event["_line"] = line_no
            events.append(event)
    return events, errors


def _load_entities(path: Path) -> dict[str, dict[str, Any]]:
    data = _load_json(path)
    entities = data.get("entities", []) if isinstance(data, dict) else []
    result: dict[str, dict[str, Any]] = {}
    for entity in entities:
        if isinstance(entity, dict) and entity.get("entity_id"):
            result[str(entity["entity_id"])] = entity
    return result


def _decision_kind(event: dict[str, Any]) -> str:
    decision = event.get("decision", {}) if isinstance(event.get("decision"), dict) else {}
    return str(decision.get("kind") or "unknown")


def _risk_flags(event: dict[str, Any]) -> list[str]:
    heuristics = event.get("heuristics", {}) if isinstance(event.get("heuristics"), dict) else {}
    flags = heuristics.get("risk_flags", [])
    if not isinstance(flags, list):
        return []
    return [str(flag) for flag in flags if str(flag)]


def _chain_id(event: dict[str, Any]) -> str:
    return str(event.get("causal_chain_id") or "chain_unknown")


def _edge_key(source: str, target: str, relation: str) -> tuple[str, str, str]:
    return (source, target, relation)


def _node_type(entity: dict[str, Any]) -> str:
    return str(entity.get("entity_type") or "unknown")


def build_graph(events: list[dict[str, Any]], entities: dict[str, dict[str, Any]]) -> dict[str, Any]:
    node_events: dict[str, list[dict[str, Any]]] = defaultdict(list)
    chain_events: dict[str, list[dict[str, Any]]] = defaultdict(list)
    relation_edges: Counter[tuple[str, str, str]] = Counter()
    chain_edges: Counter[tuple[str, str, str]] = Counter()
    missing_event_entities: list[dict[str, Any]] = []
    missing_relation_targets: list[dict[str, Any]] = []

    for event in events:
        entity_id = str(event.get("entity_id") or "entity_unknown")
        node_events[entity_id].append(event)
        chain_events[_chain_id(event)].append(event)
        if entity_id not in entities:
            missing_event_entities.append(
                {
                    "line": event.get("_line"),
                    "event_id": event.get("event_id"),
                    "entity_id": entity_id,
                }
            )
        relations = event.get("relations", {}) if isinstance(event.get("relations"), dict) else {}
        target = str(relations.get("target_entity_id") or "")
        relation = str(relations.get("relation") or "")
        if target:
            relation_edges[_edge_key(entity_id, target, relation or "relates_to")] += 1
            if target not in entities:
                missing_relation_targets.append(
                    {
                        "line": event.get("_line"),
                        "event_id": event.get("event_id"),
                        "source_entity_id": entity_id,
                        "target_entity_id": target,
                        "relation": relation,
                    }
                )

    for chain_id, items in chain_events.items():
        previous = None
        for event in items:
            current = str(event.get("entity_id") or "entity_unknown")
            if previous and previous != current:
                chain_edges[_edge_key(previous, current, f"precedes:{chain_id}")] += 1
            previous = current

    incoming: Counter[str] = Counter()
    outgoing: Counter[str] = Counter()
    for source, target, _relation in list(relation_edges) + list(chain_edges):
        outgoing[source] += 1
        incoming[target] += 1

    nodes = []
    for entity_id in sorted(set(entities) | set(node_events)):
        entity = entities.get(entity_id, {})
        items = node_events.get(entity_id, [])
        decisions = Counter(_decision_kind(event) for event in items)
        event_types = Counter(str(event.get("event_type") or "") for event in items)
        risks = Counter(flag for event in items for flag in _risk_flags(event))
        chains = sorted({_chain_id(event) for event in items})
        nodes.append(
            {
                "entity_id": entity_id,
                "entity_type": _node_type(entity),
                "observed": bool(items),
                "event_count": len(items),
                "chain_count": len(chains),
                "incoming_edges": incoming.get(entity_id, 0),
                "outgoing_edges": outgoing.get(entity_id, 0),
                "decision_mix": decisions.most_common(),
                "top_event_types": event_types.most_common(8),
                "risk_flags": risks.most_common(8),
            }
        )

    def edge_items(edges: Counter[tuple[str, str, str]]) -> list[dict[str, Any]]:
        return [
            {"source": source, "target": target, "relation": relation, "count": count}
            for (source, target, relation), count in sorted(edges.items())
        ]

    relation_edge_items = edge_items(relation_edges)
    chain_edge_items = edge_items(chain_edges)
    graph_seed = {
        "nodes": [
            {
                "entity_id": node["entity_id"],
                "entity_type": node["entity_type"],
                "event_count": node["event_count"],
                "incoming_edges": node["incoming_edges"],
                "outgoing_edges": node["outgoing_edges"],
            }
            for node in nodes
        ],
        "relation_edges": relation_edge_items,
        "chain_edges": chain_edge_items,
    }
    graph_hash = "sha256:" + _sha(json.dumps(graph_seed, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
    return {
        "nodes": nodes,
        "relation_edges": relation_edge_items,
        "chain_edges": chain_edge_items,
        "graph_hash": graph_hash,
        "chain_count": len(chain_events),
        "chain_lengths": Counter({chain_id: len(items) for chain_id, items in chain_events.items()}).most_common(),
        "missing_event_entities": missing_event_entities,
        "missing_relation_targets": missing_relation_targets,
        "observed_entity_count": len(node_events),
        "catalog_entity_count": len(entities),
        "relation_edge_count": sum(relation_edges.values()),
        "chain_edge_count": sum(chain_edges.values()),
        "isolated_observed_entities": [
            node["entity_id"]
            for node in nodes
            if node["observed"] and node["incoming_edges"] == 0 and node["outgoing_edges"] == 0
        ],
    }


def build_report(events_path: Path, entity_catalog_path: Path) -> dict[str, Any]:
    events, parse_errors = _load_events(events_path)
    entities = _load_entities(entity_catalog_path)
    graph = build_graph(events, entities)
    errors = list(parse_errors)
    warnings: list[dict[str, Any]] = []
    if graph["missing_event_entities"]:
        errors.append({"code": "EVENT_ENTITY_NOT_IN_CATALOG", "count": len(graph["missing_event_entities"])})
    if graph["missing_relation_targets"]:
        errors.append({"code": "RELATION_TARGET_NOT_IN_CATALOG", "count": len(graph["missing_relation_targets"])})
    if not graph["nodes"]:
        errors.append({"code": "EMPTY_GRAPH"})
    if graph["isolated_observed_entities"]:
        warnings.append({"code": "ISOLATED_OBSERVED_ENTITIES", "entities": graph["isolated_observed_entities"]})
    classification = "CAUSAL_GRAPH_READY" if not errors else "CAUSAL_GRAPH_INVALID"
    return {
        "schema_version": "pnva.causal_graph.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": "Gustavo de Aguiar Martins",
        "project": "PNVA-Core",
        "events_ref": str(events_path),
        "entity_catalog_ref": str(entity_catalog_path),
        "pass": not errors,
        "classification": classification,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "event_count": len(events),
            "catalog_entity_count": graph["catalog_entity_count"],
            "observed_entity_count": graph["observed_entity_count"],
            "chain_count": graph["chain_count"],
            "relation_edge_count": graph["relation_edge_count"],
            "chain_edge_count": graph["chain_edge_count"],
            "graph_hash": graph["graph_hash"],
            "isolated_observed_entity_count": len(graph["isolated_observed_entities"]),
        },
        "graph": graph,
        "interpretation": {
            "entity_meaning": "Every observed event should map to a cataloged PNVA entity.",
            "relation_meaning": "Relations expose guard, routing and causal links instead of leaving entities as isolated labels.",
            "graph_hash": "The graph hash is a stable public digest over nodes and edges.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit PNVA event/entity causal graph structure.")
    parser.add_argument("--events", default="reports/pnva-canonical-events-sample-2026-05-05.jsonl")
    parser.add_argument("--entity-catalog", default="reports/pnva-entity-catalog-2026-05-05.json")
    parser.add_argument("--write", default="")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    events_path = Path(args.events)
    if not events_path.is_absolute():
        events_path = repo / events_path
    entity_catalog_path = Path(args.entity_catalog)
    if not entity_catalog_path.is_absolute():
        entity_catalog_path = repo / entity_catalog_path
    report = build_report(events_path, entity_catalog_path)
    for key in ("events_ref", "entity_catalog_ref"):
        path = Path(str(report[key]))
        report[key] = str(path.relative_to(repo)) if path.is_relative_to(repo) else path.name
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
