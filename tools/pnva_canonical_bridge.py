#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


LOCAL_LOG_CANDIDATES = [
    Path.home() / ".local" / "state" / "miniggpueny" / "pnva_decisions.jsonl",
    Path.home() / ".local" / "state" / "miniggpueny" / "pnva_causal_events.jsonl",
    Path.home() / ".local" / "state" / "miniggpueny" / "zano_pnva_heuristics.jsonl",
    Path.home() / "logs" / "pnva-miner-events.jsonl",
]

SAFE_METRIC_KEYS = [
    "signal",
    "theta",
    "margin",
    "gate_delta",
    "field_tension",
    "pnva_phi",
    "pnva_theta",
    "pnva_gate_margin",
    "pnva_quality_median",
    "pnva_quality_mad",
    "pnva_chi",
    "pnva_mu",
    "hash4d_score",
    "runtime_hash4d_score",
    "job_freshness",
    "stale_risk",
    "stale_rate",
    "reject_rate",
    "invalid_rate",
    "duplicate_rate",
    "thermal_pressure",
    "temperature_c",
    "power_w",
    "gpu_temp_c",
    "gpu_power_w",
    "raw_mhs",
    "runtime_sustained_raw_mhs",
    "runtime_helper_health",
    "runtime_throughput_stability",
    "veon_density",
    "veon_flow",
    "veon_intensity_total",
    "veon_collapse_count",
    "queue_depth",
    "workers_alive",
    "workers_active",
    "logical_parallelism",
    "physical_parallelism",
    "planned_ranges_count",
]


def _sha(value: str, size: int = 16) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:size]


def _stable_id(prefix: str, value: Any, *, fallback: str = "unknown") -> str:
    text = str(value or "").strip()
    if not text:
        text = fallback
    safe_worker = text.lower()
    if safe_worker.startswith("zano-entity-") and len(safe_worker) <= 64:
        return safe_worker
    if safe_worker in {"pnva-core", "gustavo-de-aguiar-martins", "enyos", "enygnalab"}:
        return safe_worker
    return f"{prefix}_{_sha(text, 12)}"


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        numeric = float(value)
    except Exception:
        return float(default)
    if numeric != numeric:
        return float(default)
    return float(numeric)


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "pass", "passed"}
    return bool(value)


def _timestamp(data: dict[str, Any]) -> str:
    ts = str(data.get("ts") or data.get("timestamp") or "").strip()
    if ts:
        try:
            if ts.replace(".", "", 1).isdigit():
                return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(float(ts)))
        except Exception:
            pass
        return ts
    ts_epoch = data.get("ts_epoch")
    if ts_epoch is not None:
        try:
            return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(float(ts_epoch)))
        except Exception:
            pass
    return "1970-01-01T00:00:00Z"


def _nested_get(data: dict[str, Any], *path: str) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _unwrap_causal_record(data: dict[str, Any]) -> dict[str, Any]:
    if isinstance(data.get("payload"), dict):
        payload = dict(data["payload"])
        payload.setdefault("kind", data.get("kind"))
        payload.setdefault("cause", data.get("cause"))
        payload.setdefault("seal", data.get("seal"))
        payload.setdefault("seq", data.get("seq"))
        payload.setdefault("ts", data.get("ts"))
        return payload
    return dict(data)


def _event_type(data: dict[str, Any]) -> str:
    return str(data.get("event") or data.get("kind") or data.get("event_type") or "legacy_event").strip() or "legacy_event"


def _raw_entity_value(data: dict[str, Any], event_type: str) -> str:
    if "guard" in event_type.lower() or "etev" in event_type.lower():
        return event_type
    for key in (
        "entity_id",
        "orbital_id",
        "hot_worker_entity_id",
        "worker_id",
        "component",
        "gate",
        "proof_name",
        "event_type",
    ):
        value = str(data.get(key) or "").strip()
        if value:
            return value
    route_worker = _nested_get(data, "route", "chosen_worker_id")
    if route_worker:
        return str(route_worker)
    return _event_type(data)


def _target_entity_id(data: dict[str, Any], event_type: str) -> str:
    if "guard" not in event_type.lower() and "etev" not in event_type.lower():
        return ""
    for key in ("entity_id", "orbital_id", "worker_id", "reason"):
        value = str(data.get(key) or "").strip()
        if value:
            return _stable_id("entity", value)
    return ""


def _entity_type(data: dict[str, Any], event_type: str) -> str:
    lowered = event_type.lower()
    if "runtime" in lowered or "snapshot" in lowered or "pnva_engine" in lowered:
        return "field"
    if "guard" in lowered or "etev" in lowered:
        return "guard"
    if "gate" in lowered:
        return "gate"
    if "proof" in lowered or "prove" in lowered:
        return "proof"
    if data.get("entity_id") or data.get("orbital_id") or data.get("hot_worker_entity_id"):
        return "worker"
    if any(str(key).startswith("veon_") for key in data):
        return "heuristic"
    if "memory" in data:
        return "memory"
    return "event_source"


def _decision(data: dict[str, Any], event_type: str) -> dict[str, Any]:
    action = str(
        data.get("decision")
        or data.get("pnva_decision")
        or data.get("runtime_decision_action")
        or data.get("action")
        or event_type
    ).strip() or event_type
    lowered = f"{event_type} {action}".lower()
    passed = data.get("passed")
    if passed is None:
        passed = data.get("pass")
    if "block" in lowered or passed is False:
        kind = "block"
    elif "proof" in lowered or "prove" in lowered:
        kind = "prove"
    elif "reclass" in lowered:
        kind = "reclassify"
    elif (
        "pass" in lowered
        or action in {"EXECUTE", "RESIZE_BATCH", "COOLDOWN_GPU", "SWITCH_INTENSITY", "DROP_STALE", "FLUSH_DUPLICATE"}
        or passed is True
    ):
        kind = "collapse"
    else:
        kind = "observe"
    reason = str(
        data.get("reason")
        or data.get("runtime_decision_reason")
        or data.get("cause")
        or ("threshold_passed" if kind == "collapse" else "observed")
    ).strip()
    confidence = 0.72
    if kind == "collapse":
        confidence = 0.86
    elif kind == "block":
        confidence = 0.82
    elif kind == "prove":
        confidence = 0.90
    return {
        "kind": kind,
        "action": action,
        "reason": reason,
        "confidence": round(confidence, 4),
    }


def _tension(data: dict[str, Any]) -> dict[str, Any]:
    score = (
        data.get("signal")
        if data.get("signal") is not None
        else data.get("field_tension")
        if data.get("field_tension") is not None
        else data.get("pnva_phi")
        if data.get("pnva_phi") is not None
        else data.get("runtime_hash4d_score")
        if data.get("runtime_hash4d_score") is not None
        else data.get("hash4d_score")
        if data.get("hash4d_score") is not None
        else _nested_get(data, "guard", "signal")
    )
    threshold = (
        data.get("theta")
        if data.get("theta") is not None
        else data.get("pnva_theta")
        if data.get("pnva_theta") is not None
        else _nested_get(data, "threshold", "theta")
        if _nested_get(data, "threshold", "theta") is not None
        else _nested_get(data, "guard", "theta")
    )
    margin = (
        data.get("margin")
        if data.get("margin") is not None
        else data.get("pnva_gate_margin")
        if data.get("pnva_gate_margin") is not None
        else _nested_get(data, "threshold", "margin")
        if _nested_get(data, "threshold", "margin") is not None
        else _nested_get(data, "guard", "margin")
    )
    score_f = _safe_float(score)
    threshold_f = _safe_float(threshold)
    margin_f = _safe_float(margin)
    gate_delta = data.get("gate_delta")
    if gate_delta is None:
        gate_delta = _nested_get(data, "guard", "gate_delta")
    gate_delta_f = _safe_float(gate_delta, score_f - max(0.0, threshold_f - margin_f))
    components = {}
    for key in SAFE_METRIC_KEYS:
        if key in data:
            components[key] = _safe_float(data.get(key))
    guard = data.get("guard")
    if isinstance(guard, dict):
        for key in ("signal", "theta", "margin", "gate_delta"):
            if key in guard:
                components[f"guard_{key}"] = _safe_float(guard.get(key))
    return {
        "score": round(score_f, 8),
        "threshold": round(threshold_f, 8),
        "margin": round(margin_f, 8),
        "gate_delta": round(gate_delta_f, 8),
        "components": components,
    }


def _field(data: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    state_after = str(data.get("state_after") or data.get("state") or data.get("state_label") or decision["action"]).strip()
    state_after = state_after.lower() if state_after else "observed"
    return {
        "state_before": str(data.get("state_before") or "observing"),
        "state_after": state_after,
        "phi": _safe_float(data.get("pnva_phi", data.get("field_tension", 0.0))),
        "gradient": _safe_float(data.get("pnva_chi", 0.0)),
        "hessian": _safe_float(data.get("pnva_mu", 0.0)),
    }


def _heuristics(data: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    rules = []
    if data.get("pnva_theta") is not None or data.get("theta") is not None or isinstance(data.get("threshold"), dict):
        rules.append("adaptive_threshold")
    if "etev" in str(data.get("event") or data.get("event_type") or data.get("kind") or "").lower():
        rules.append("etev_guard")
    if isinstance(data.get("memory"), dict):
        rules.append("memory4d")
    if isinstance(data.get("route"), dict):
        rules.append("affinity_router")
    if isinstance(data.get("power"), dict):
        rules.append("power_orchestrator")
    if any(str(key).startswith("veon_") for key in data):
        rules.append("veonic_layer")
    if data.get("runtime_decision_reason") or data.get("reason"):
        rules.append("field_scheduler")
    if not rules:
        rules.append("legacy_observer")
    risk_flags = []
    reason = str(decision.get("reason") or "").lower()
    action = str(decision.get("action") or "").lower()
    if "thermal" in reason or _safe_float(data.get("thermal_pressure", 0.0)) >= 0.80:
        risk_flags.append("THERMAL_PRESSURE")
    if "resize" in action:
        risk_flags.append("RESIZE_BATCH_PRESSURE")
    if _safe_float(data.get("stale_risk", data.get("stale_rate", 0.0))) >= 0.45:
        risk_flags.append("STALE_PRESSURE")
    if _safe_float(data.get("invalid_rate", 0.0)) > 0.0:
        risk_flags.append("INVALID_PRESSURE")
    if _safe_float(data.get("duplicate_rate", 0.0)) >= 0.20:
        risk_flags.append("DUPLICATE_PRESSURE")
    if any(str(key).startswith("veon_") for key in data):
        risk_flags.append("VEONIC_TRACE")
    return {
        "rules": sorted(set(rules)),
        "risk_flags": sorted(set(risk_flags)),
    }


def _chain_id(data: dict[str, Any], source_name: str) -> str:
    value = data.get("session_id") or data.get("job_id") or data.get("job_seal") or data.get("seal") or data.get("cause") or source_name
    return _stable_id("chain", value, fallback=source_name)


def canonicalize_record(data: dict[str, Any], *, source_name: str, line_no: int) -> dict[str, Any]:
    data = _unwrap_causal_record(data)
    event_type = _event_type(data)
    raw_entity = _raw_entity_value(data, event_type)
    entity_type = _entity_type(data, event_type)
    entity_id = _stable_id("entity", raw_entity, fallback=event_type)
    decision = _decision(data, event_type)
    field = _field(data, decision)
    tension = _tension(data)
    heuristics = _heuristics(data, decision)
    event_seed = json.dumps(
        {
            "source": source_name,
            "line": line_no,
            "timestamp": _timestamp(data),
            "entity_id": entity_id,
            "event_type": event_type,
            "decision": decision,
            "tension": tension,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    proof_hash = "sha256:" + _sha(event_seed, 64)
    event = {
        "schema_version": "pnva.event.v1",
        "event_id": f"evt_{_sha(source_name, 8)}_{line_no:06d}_{_sha(event_seed, 8)}",
        "timestamp": _timestamp(data),
        "causal_chain_id": _chain_id(data, source_name),
        "entity_id": entity_id,
        "entity_type": entity_type,
        "event_type": event_type,
        "field": field,
        "tension": tension,
        "decision": decision,
        "heuristics": heuristics,
        "proof": {
            "proof_hash": proof_hash,
            "proof_ref": f"sanitized-legacy-log:{source_name}:{line_no}",
            "valid": True,
            "canonical": True,
        },
        "source": {
            "format": "legacy_jsonl",
            "file_name": source_name,
            "line": line_no,
            "sanitized": True,
        },
    }
    target_entity = _target_entity_id(data, event_type)
    if target_entity:
        event["relations"] = {
            "target_entity_id": target_entity,
            "relation": "guards"
        }
    return event


@dataclass
class EntityAccumulator:
    entity_id: str
    entity_type: str
    events: Counter[str] = field(default_factory=Counter)
    decisions: Counter[str] = field(default_factory=Counter)
    risk_flags: Counter[str] = field(default_factory=Counter)
    first_seen: str = ""
    last_seen: str = ""

    def observe(self, event: dict[str, Any]) -> None:
        timestamp = str(event.get("timestamp") or "")
        if not self.first_seen or timestamp < self.first_seen:
            self.first_seen = timestamp
        if not self.last_seen or timestamp > self.last_seen:
            self.last_seen = timestamp
        self.events[str(event.get("event_type") or "")] += 1
        self.decisions[str(event.get("decision", {}).get("action") or "")] += 1
        for flag in event.get("heuristics", {}).get("risk_flags", []):
            self.risk_flags[str(flag)] += 1

    def snapshot(self) -> dict[str, Any]:
        capabilities = sorted(
            {
                "emit_events",
                *(
                    "guard_decision" if "GUARD" in event else "runtime_observation"
                    for event in self.events
                    if event
                ),
            }
        )
        state = "active" if self.events else "observing"
        confidence = 0.90 if sum(self.events.values()) >= 10 else 0.72
        return {
            "schema_version": "pnva.entity.v1",
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "sovereignty_domain": "runtime",
            "state": state,
            "capabilities": capabilities,
            "evidence": {
                "proof_ref": "reports/pnva-canonical-events-sample-2026-05-05.jsonl",
                "confidence": confidence,
                "last_seen": self.last_seen,
                "notes": "Sanitized entity derived from canonicalized local PNVA legacy logs."
            },
            "stats": {
                "event_count": sum(self.events.values()),
                "top_events": self.events.most_common(8),
                "top_decisions": self.decisions.most_common(8),
                "risk_flags": self.risk_flags.most_common(8),
                "first_seen": self.first_seen,
                "last_seen": self.last_seen,
            }
        }


def _iter_input_records(paths: Iterable[Path], *, limit_per_input: int, max_events: int) -> Iterable[tuple[Path, int, dict[str, Any]]]:
    emitted = 0
    for path in paths:
        if not path.exists():
            continue
        emitted_for_input = 0
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line_no, line in enumerate(handle, start=1):
                if emitted >= max_events:
                    return
                if emitted_for_input >= limit_per_input:
                    break
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except Exception:
                    continue
                if not isinstance(data, dict):
                    continue
                emitted += 1
                emitted_for_input += 1
                yield path, line_no, data


def demo_records() -> list[dict[str, Any]]:
    return [
        {
            "event": "ETEV_GUARD_PASS",
            "entity_id": "zano-entity-00",
            "session_id": "demo-session",
            "ts": "2026-05-05T00:00:00Z",
            "signal": 0.82,
            "theta": 0.70,
            "margin": 0.02,
            "gate_delta": 0.14,
            "passed": True,
            "reason": "signal_above_threshold",
        },
        {
            "event": "range_plan_built",
            "hot_worker_entity_id": "zano-entity-01",
            "session_id": "demo-session",
            "ts": "2026-05-05T00:00:02Z",
            "pnva_phi": 0.48,
            "pnva_theta": 0.44,
            "runtime_decision_action": "RESIZE_BATCH",
            "runtime_decision_reason": "cpu_host_thermal_taper",
            "thermal_pressure": 0.91,
            "veon_density": 3.2,
            "veon_collapse_count": 2,
        },
    ]


def run_bridge(
    *,
    inputs: list[Path],
    output: Path,
    entity_catalog: Path,
    summary: Path,
    limit_per_input: int,
    max_events: int,
    demo: bool,
) -> dict[str, Any]:
    repo = Path(__file__).resolve().parents[1]

    def rel(path: Path) -> str:
        try:
            return str(path.resolve().relative_to(repo))
        except Exception:
            return path.name

    output.parent.mkdir(parents=True, exist_ok=True)
    entity_catalog.parent.mkdir(parents=True, exist_ok=True)
    summary.parent.mkdir(parents=True, exist_ok=True)
    entities: dict[str, EntityAccumulator] = {}
    counters: dict[str, Counter[str]] = defaultdict(Counter)
    written = 0
    with output.open("w", encoding="utf-8") as out:
        if demo:
            iterable = [(Path("demo.jsonl"), index, item) for index, item in enumerate(demo_records(), start=1)]
        else:
            iterable = _iter_input_records(inputs, limit_per_input=limit_per_input, max_events=max_events)
        for path, line_no, data in iterable:
            event = canonicalize_record(data, source_name=path.name, line_no=line_no)
            out.write(json.dumps(event, ensure_ascii=True, sort_keys=True) + "\n")
            written += 1
            counters["event_types"][event["event_type"]] += 1
            counters["entity_types"][event.get("entity_type", "")] += 1
            counters["decision_kinds"][event["decision"]["kind"]] += 1
            counters["actions"][event["decision"]["action"]] += 1
            for flag in event.get("heuristics", {}).get("risk_flags", []):
                counters["risk_flags"][flag] += 1
            entity_id = event["entity_id"]
            if entity_id not in entities:
                entities[entity_id] = EntityAccumulator(entity_id=entity_id, entity_type=event.get("entity_type", "event_source"))
            entities[entity_id].observe(event)

    catalog = {
        "schema_version": "pnva.entity_catalog.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": "Gustavo de Aguiar Martins",
        "project": "PNVA-Core",
        "source": "sanitized canonical bridge",
        "entity_count": len(entities),
        "entities": [item.snapshot() for item in sorted(entities.values(), key=lambda x: x.entity_id)],
    }
    entity_catalog.write_text(json.dumps(catalog, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    summary_data = {
        "schema_version": "pnva.canonical_bridge_summary.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": "Gustavo de Aguiar Martins",
        "project": "PNVA-Core",
        "demo_mode": bool(demo),
        "event_count": written,
        "entity_count": len(entities),
        "output": rel(output),
        "entity_catalog": rel(entity_catalog),
        "top_event_types": counters["event_types"].most_common(12),
        "top_entity_types": counters["entity_types"].most_common(12),
        "top_decision_kinds": counters["decision_kinds"].most_common(12),
        "top_actions": counters["actions"].most_common(12),
        "risk_flags": counters["risk_flags"].most_common(12),
        "public_safety": {
            "raw_ids_published": False,
            "raw_paths_published": False,
            "ids_hashed": True,
            "file_names_only": True,
        },
    }
    summary.write_text(json.dumps(summary_data, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    return summary_data


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert legacy PNVA JSONL logs into pnva.event.v1 envelopes.")
    parser.add_argument("--input", action="append", default=[], help="Legacy JSONL input. May be repeated.")
    parser.add_argument("--output", default="reports/pnva-canonical-events-sample-2026-05-05.jsonl")
    parser.add_argument("--entity-catalog", default="reports/pnva-entity-catalog-2026-05-05.json")
    parser.add_argument("--summary", default="reports/pnva-canonical-bridge-summary-2026-05-05.json")
    parser.add_argument("--limit", type=int, default=512, help="Maximum total canonical events to emit.")
    parser.add_argument("--limit-per-input", type=int, default=128, help="Maximum records to read from each input.")
    parser.add_argument("--demo", action="store_true", help="Use built-in demo records instead of local/private logs.")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    inputs = [Path(item).expanduser() for item in args.input] if args.input else LOCAL_LOG_CANDIDATES
    output = Path(args.output)
    if not output.is_absolute():
        output = repo / output
    entity_catalog = Path(args.entity_catalog)
    if not entity_catalog.is_absolute():
        entity_catalog = repo / entity_catalog
    summary = Path(args.summary)
    if not summary.is_absolute():
        summary = repo / summary
    result = run_bridge(
        inputs=inputs,
        output=output,
        entity_catalog=entity_catalog,
        summary=summary,
        limit_per_input=max(1, int(args.limit_per_input)),
        max_events=max(1, int(args.limit)),
        demo=bool(args.demo),
    )
    print(json.dumps(result, indent=2, ensure_ascii=True, sort_keys=True))
    return 0 if result["event_count"] > 0 and result["entity_count"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
