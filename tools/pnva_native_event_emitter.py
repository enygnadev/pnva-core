#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


AUTHOR = "Gustavo de Aguiar Martins"
PROJECT = "PNVA-Core"
SCHEMA_VERSION = "pnva.event.v1"


def _sha(value: str, size: int = 64) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:size]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        numeric = float(value)
    except Exception:
        return float(default)
    if numeric != numeric:
        return float(default)
    return float(numeric)


def _round(value: float, digits: int = 8) -> float:
    return round(float(value), digits)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def calculate_tension(
    *,
    event_weight: float,
    state_gradient: float,
    cost: float,
    memory: float,
    alpha: float = 0.4,
    beta: float = 0.3,
    gamma: float = 0.2,
    mu: float = 0.1,
) -> float:
    return (
        alpha * _safe_float(event_weight)
        + beta * _safe_float(state_gradient)
        - gamma * _safe_float(cost)
        + mu * _safe_float(memory)
    )


def proof_seed(event: dict[str, Any]) -> str:
    source = event.get("source", {}) if isinstance(event.get("source"), dict) else {}
    payload = {
        "source": source.get("file_name", ""),
        "line": source.get("line", 0),
        "timestamp": event.get("timestamp", ""),
        "entity_id": event.get("entity_id", ""),
        "event_type": event.get("event_type", ""),
        "decision": event.get("decision", {}),
        "tension": event.get("tension", {}),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def proof_hash(event: dict[str, Any]) -> str:
    return "sha256:" + _sha(proof_seed(event), 64)


@dataclass
class EntityState:
    entity_id: str
    entity_type: str
    sovereignty_domain: str = "runtime"
    state: str = "observing"
    capabilities: set[str] = field(default_factory=set)
    event_count: int = 0
    first_seen: str = ""
    last_seen: str = ""
    decisions: Counter[str] = field(default_factory=Counter)
    risk_flags: Counter[str] = field(default_factory=Counter)

    def observe(self, event: dict[str, Any]) -> None:
        timestamp = str(event.get("timestamp") or "")
        if not self.first_seen or timestamp < self.first_seen:
            self.first_seen = timestamp
        if not self.last_seen or timestamp > self.last_seen:
            self.last_seen = timestamp
        self.event_count += 1
        decision = event.get("decision", {}) if isinstance(event.get("decision"), dict) else {}
        self.decisions[str(decision.get("kind") or "unknown")] += 1
        heuristics = event.get("heuristics", {}) if isinstance(event.get("heuristics"), dict) else {}
        for flag in heuristics.get("risk_flags", []) if isinstance(heuristics.get("risk_flags"), list) else []:
            self.risk_flags[str(flag)] += 1
        self.capabilities.add("emit_native_pnva_event")
        if str(event.get("event_type") or "").startswith("ETEV_GUARD"):
            self.capabilities.add("guard_decision")
        if decision.get("kind") == "collapse":
            self.state = "active"
        elif decision.get("kind") == "block":
            self.state = "blocked"

    def snapshot(self, proof_ref: str) -> dict[str, Any]:
        confidence = 0.96 if self.event_count >= 2 else 0.88
        return {
            "schema_version": "pnva.entity.v1",
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "sovereignty_domain": self.sovereignty_domain,
            "state": self.state,
            "capabilities": sorted(self.capabilities),
            "evidence": {
                "proof_ref": proof_ref,
                "confidence": confidence,
                "last_seen": self.last_seen,
                "notes": "Native PNVA event emitter demo entity.",
            },
            "stats": {
                "event_count": self.event_count,
                "first_seen": self.first_seen,
                "last_seen": self.last_seen,
                "decision_mix": self.decisions.most_common(),
                "risk_flags": self.risk_flags.most_common(),
            },
        }


class PNVANativeEmitter:
    def __init__(self, *, source_name: str = "native-runtime-demo", causal_chain_id: str = "chain_native_runtime_demo") -> None:
        self.source_name = source_name
        self.causal_chain_id = causal_chain_id
        self.seq = 0
        self.entities: dict[str, EntityState] = {}
        self.events: list[dict[str, Any]] = []

    def _entity(self, entity_id: str, entity_type: str) -> EntityState:
        if entity_id not in self.entities:
            self.entities[entity_id] = EntityState(entity_id=entity_id, entity_type=entity_type)
        return self.entities[entity_id]

    def emit(
        self,
        *,
        timestamp: str,
        entity_id: str,
        entity_type: str,
        event_type: str,
        state_before: str,
        state_after: str,
        event_weight: float,
        state_gradient: float,
        cost: float,
        memory: float,
        threshold: float,
        margin: float = 0.0,
        decision_kind: str | None = None,
        action: str = "",
        reason: str = "",
        confidence: float = 0.86,
        rules: list[str] | None = None,
        risk_flags: list[str] | None = None,
        relations: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.seq += 1
        score = calculate_tension(event_weight=event_weight, state_gradient=state_gradient, cost=cost, memory=memory)
        threshold_f = _safe_float(threshold)
        margin_f = _safe_float(margin)
        gate_delta = score - max(0.0, threshold_f - margin_f)
        if decision_kind is None:
            decision_kind = "collapse" if gate_delta >= 0 else "observe"
        action = action or ("EXECUTE" if decision_kind == "collapse" else "NO_ACTION")
        reason = reason or ("tension_above_threshold" if decision_kind == "collapse" else "tension_below_threshold")
        event = {
            "schema_version": SCHEMA_VERSION,
            "event_id": "",
            "timestamp": timestamp,
            "causal_chain_id": self.causal_chain_id,
            "entity_id": entity_id,
            "entity_type": entity_type,
            "event_type": event_type,
            "field": {
                "state_before": state_before,
                "state_after": state_after,
                "phi": _round(score),
                "gradient": _round(state_gradient),
                "hessian": _round(memory),
            },
            "tension": {
                "score": _round(score),
                "threshold": _round(threshold_f),
                "margin": _round(margin_f),
                "gate_delta": _round(gate_delta),
                "components": {
                    "event_weight": _round(event_weight),
                    "state_gradient": _round(state_gradient),
                    "cost": _round(cost),
                    "memory": _round(memory),
                    "alpha": 0.4,
                    "beta": 0.3,
                    "gamma": 0.2,
                    "mu": 0.1,
                },
            },
            "decision": {
                "kind": decision_kind,
                "action": action,
                "reason": reason,
                "confidence": _round(confidence, 4),
            },
            "heuristics": {
                "rules": sorted(set(rules or ["native_event_emitter"])),
                "risk_flags": sorted(set(risk_flags or [])),
            },
            "proof": {
                "proof_hash": "",
                "proof_ref": f"native-emitter:{self.source_name}:{self.seq}",
                "valid": True,
                "canonical": True,
                "native": True,
            },
            "source": {
                "format": "native_pnva_event_v1",
                "file_name": self.source_name,
                "line": self.seq,
                "sanitized": True,
            },
        }
        if relations:
            event["relations"] = dict(relations)
        seed = proof_seed(event)
        event["event_id"] = f"evt_native_{self.seq:06d}_{_sha(seed, 12)}"
        event["proof"]["proof_hash"] = proof_hash(event)
        self.events.append(event)
        self._entity(entity_id, entity_type).observe(event)
        target = relations.get("target_entity_id") if isinstance(relations, dict) else ""
        if target:
            target_type = "worker" if str(target).startswith("zano-entity-") else "event_source"
            self._entity(str(target), target_type).capabilities.add("receive_guard_decision")
        return event

    def entity_catalog(self, proof_ref: str) -> dict[str, Any]:
        entities = [entity.snapshot(proof_ref) for entity in sorted(self.entities.values(), key=lambda item: item.entity_id)]
        return {
            "schema_version": "pnva.entity_catalog.v1",
            "generated_at": _now(),
            "author": AUTHOR,
            "project": PROJECT,
            "entity_count": len(entities),
            "entities": entities,
        }


def build_demo() -> PNVANativeEmitter:
    emitter = PNVANativeEmitter()
    emitter.emit(
        timestamp="2026-05-05T04:40:00Z",
        entity_id="pnva-field-demo",
        entity_type="field",
        event_type="FIELD_OBSERVED",
        state_before="idle",
        state_after="observing",
        event_weight=0.20,
        state_gradient=0.12,
        cost=0.40,
        memory=0.10,
        threshold=0.60,
        decision_kind="observe",
        action="NO_ACTION",
        reason="field_change_below_threshold",
        confidence=0.78,
        rules=["native_event_emitter", "legacy_observer"],
    )
    emitter.emit(
        timestamp="2026-05-05T04:40:02Z",
        entity_id="pnva-etev-guard",
        entity_type="guard",
        event_type="ETEV_GUARD_PASS",
        state_before="observing",
        state_after="candidate",
        event_weight=1.20,
        state_gradient=0.80,
        cost=0.15,
        memory=0.30,
        threshold=0.70,
        margin=0.02,
        decision_kind="collapse",
        action="AUTHORIZE_COLLAPSE",
        reason="guard_signal_above_threshold",
        confidence=0.94,
        rules=["native_event_emitter", "adaptive_threshold", "etev_guard"],
        relations={"target_entity_id": "zano-entity-00", "relation": "guards"},
    )
    emitter.emit(
        timestamp="2026-05-05T04:40:04Z",
        entity_id="zano-entity-00",
        entity_type="worker",
        event_type="RUNTIME_COLLAPSE",
        state_before="candidate",
        state_after="active",
        event_weight=0.92,
        state_gradient=0.66,
        cost=0.22,
        memory=0.44,
        threshold=0.54,
        margin=0.02,
        decision_kind="collapse",
        action="EXECUTE",
        reason="authorized_causal_collapse",
        confidence=0.91,
        rules=["native_event_emitter", "field_scheduler", "memory4d"],
    )
    emitter.emit(
        timestamp="2026-05-05T04:40:06Z",
        entity_id="pnva-thermal-guard",
        entity_type="guard",
        event_type="THERMAL_PRESSURE",
        state_before="active",
        state_after="observing",
        event_weight=0.45,
        state_gradient=0.22,
        cost=0.72,
        memory=0.30,
        threshold=0.68,
        decision_kind="observe",
        action="HOLD_PRESSURE",
        reason="thermal_pressure_visible_but_below_collapse",
        confidence=0.84,
        rules=["native_event_emitter", "power_orchestrator"],
        risk_flags=["THERMAL_PRESSURE"],
    )
    emitter.emit(
        timestamp="2026-05-05T04:40:08Z",
        entity_id="pnva-etev-guard",
        entity_type="guard",
        event_type="ETEV_GUARD_BLOCK",
        state_before="observing",
        state_after="blocked",
        event_weight=0.28,
        state_gradient=0.20,
        cost=0.44,
        memory=0.12,
        threshold=0.70,
        decision_kind="block",
        action="BLOCK_EXECUTION",
        reason="guard_signal_below_threshold",
        confidence=0.92,
        rules=["native_event_emitter", "adaptive_threshold", "etev_guard"],
        risk_flags=["STALE_PRESSURE"],
        relations={"target_entity_id": "zano-entity-01", "relation": "guards"},
    )
    emitter.emit(
        timestamp="2026-05-05T04:40:10Z",
        entity_id="zano-entity-01",
        entity_type="worker",
        event_type="STALE_JOB_PRESSURE",
        state_before="candidate",
        state_after="blocked",
        event_weight=0.35,
        state_gradient=0.15,
        cost=0.52,
        memory=0.18,
        threshold=0.62,
        decision_kind="block",
        action="DROP_STALE",
        reason="stale_job_pressure_blocked",
        confidence=0.88,
        rules=["native_event_emitter", "field_scheduler"],
        risk_flags=["STALE_PRESSURE"],
    )
    emitter.emit(
        timestamp="2026-05-05T04:40:12Z",
        entity_id="pnva-proof-native-demo",
        entity_type="proof",
        event_type="PROOF_SEALED",
        state_before="observing",
        state_after="passed",
        event_weight=0.82,
        state_gradient=0.40,
        cost=0.10,
        memory=0.70,
        threshold=0.45,
        decision_kind="prove",
        action="SEAL_PROOF",
        reason="native_event_sequence_sealed",
        confidence=0.97,
        rules=["native_event_emitter"],
    )
    return emitter


def build_summary(emitter: PNVANativeEmitter, *, events_ref: str, entity_catalog_ref: str) -> dict[str, Any]:
    decisions = Counter(str(event.get("decision", {}).get("kind") or "") for event in emitter.events)
    event_types = Counter(str(event.get("event_type") or "") for event in emitter.events)
    risks = Counter(
        str(flag)
        for event in emitter.events
        for flag in event.get("heuristics", {}).get("risk_flags", [])
        if isinstance(event.get("heuristics"), dict)
    )
    native_count = sum(1 for event in emitter.events if event.get("source", {}).get("format") == "native_pnva_event_v1")
    suppressed = decisions.get("observe", 0) + decisions.get("block", 0)
    return {
        "schema_version": "pnva.native_emitter_summary.v1",
        "generated_at": _now(),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": "NATIVE_EMITTER_READY" if native_count == len(emitter.events) and suppressed > 0 else "NATIVE_EMITTER_NEEDS_HARDENING",
        "pass": native_count == len(emitter.events) and suppressed > 0,
        "events_ref": events_ref,
        "entity_catalog_ref": entity_catalog_ref,
        "event_count": len(emitter.events),
        "native_event_count": native_count,
        "entity_count": len(emitter.entities),
        "suppressed_count": suppressed,
        "decision_mix": decisions.most_common(),
        "top_event_types": event_types.most_common(),
        "risk_flags": risks.most_common(),
        "proof_policy": "proof_hash is deterministic over native source, line, timestamp, entity, event type, decision and tension",
        "runtime_policy": "new PNVA runtimes should emit this envelope directly before any legacy bridge is needed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit native PNVA pnva.event.v1 demo events and entity catalog.")
    parser.add_argument("--events", default="reports/pnva-native-events-demo-2026-05-05.jsonl")
    parser.add_argument("--entity-catalog", default="reports/pnva-native-entity-catalog-demo-2026-05-05.json")
    parser.add_argument("--summary", default="reports/pnva-native-emitter-summary-2026-05-05.json")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    events_path = Path(args.events)
    if not events_path.is_absolute():
        events_path = repo / events_path
    entity_catalog_path = Path(args.entity_catalog)
    if not entity_catalog_path.is_absolute():
        entity_catalog_path = repo / entity_catalog_path
    summary_path = Path(args.summary)
    if not summary_path.is_absolute():
        summary_path = repo / summary_path

    emitter = build_demo()
    for path in (events_path, entity_catalog_path, summary_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    events_path.write_text(
        "".join(json.dumps(event, sort_keys=True, ensure_ascii=True, separators=(",", ":")) + "\n" for event in emitter.events),
        encoding="utf-8",
    )
    entity_catalog = emitter.entity_catalog(str(events_path.relative_to(repo)) if events_path.is_relative_to(repo) else events_path.name)
    entity_catalog_path.write_text(json.dumps(entity_catalog, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    summary = build_summary(
        emitter,
        events_ref=str(events_path.relative_to(repo)) if events_path.is_relative_to(repo) else events_path.name,
        entity_catalog_ref=str(entity_catalog_path.relative_to(repo)) if entity_catalog_path.is_relative_to(repo) else entity_catalog_path.name,
    )
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=True, sort_keys=True))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
