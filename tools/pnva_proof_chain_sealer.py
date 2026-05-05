#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any


GENESIS_LABEL = "pnva.proof_chain.v1"


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


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


def _canonical_event_hash(event: dict[str, Any]) -> str:
    clean = {key: value for key, value in event.items() if key != "_line"}
    raw = json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return _sha(raw)


def _proof_ok(event: dict[str, Any]) -> bool:
    proof = event.get("proof", {}) if isinstance(event.get("proof"), dict) else {}
    return proof.get("valid") is True and str(proof.get("proof_hash") or "").startswith("sha256:")


def _source_format(event: dict[str, Any]) -> str:
    source = event.get("source", {}) if isinstance(event.get("source"), dict) else {}
    return str(source.get("format") or "unknown")


def seal_events(events: list[dict[str, Any]], *, checkpoint_interval: int) -> dict[str, Any]:
    event_ids: set[str] = set()
    duplicates: list[dict[str, Any]] = []
    checkpoints: list[dict[str, Any]] = []
    event_types: Counter[str] = Counter()
    decisions: Counter[str] = Counter()
    sources: Counter[str] = Counter()
    proof_ok = 0
    proof_bad = 0
    genesis_hash = _sha(GENESIS_LABEL)
    previous = genesis_hash
    first_event_hash = ""
    last_event_hash = ""

    for index, event in enumerate(events, start=1):
        event_id = str(event.get("event_id") or "")
        if event_id in event_ids:
            duplicates.append({"line": event.get("_line", index), "event_id": event_id})
        event_ids.add(event_id)
        event_hash = _canonical_event_hash(event)
        if index == 1:
            first_event_hash = event_hash
        last_event_hash = event_hash
        previous = _sha(
            json.dumps(
                {
                    "index": index,
                    "previous_chain_hash": previous,
                    "event_id": event_id,
                    "event_hash": event_hash,
                },
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            )
        )
        event_types[str(event.get("event_type") or "")] += 1
        decision = event.get("decision", {}) if isinstance(event.get("decision"), dict) else {}
        decisions[str(decision.get("kind") or "unknown")] += 1
        sources[_source_format(event)] += 1
        if _proof_ok(event):
            proof_ok += 1
        else:
            proof_bad += 1
        if index == 1 or index % max(1, checkpoint_interval) == 0 or index == len(events):
            checkpoints.append(
                {
                    "index": index,
                    "event_id": event_id,
                    "event_hash": event_hash,
                    "chain_hash": previous,
                }
            )

    return {
        "event_count": len(events),
        "unique_event_ids": len(event_ids),
        "duplicate_event_ids": duplicates,
        "proof_ok": proof_ok,
        "proof_bad": proof_bad,
        "genesis_hash": genesis_hash,
        "first_event_hash": first_event_hash,
        "last_event_hash": last_event_hash,
        "final_chain_hash": previous if events else genesis_hash,
        "checkpoint_interval": checkpoint_interval,
        "checkpoints": checkpoints,
        "top_event_types": event_types.most_common(12),
        "decision_mix": decisions.most_common(),
        "source_formats": sources.most_common(),
    }


def build_report(events_path: Path, *, checkpoint_interval: int = 64) -> dict[str, Any]:
    events, parse_errors = _load_events(events_path)
    seal = seal_events(events, checkpoint_interval=checkpoint_interval)
    errors = list(parse_errors)
    if seal["duplicate_event_ids"]:
        errors.append({"code": "DUPLICATE_EVENT_IDS", "items": seal["duplicate_event_ids"][:12]})
    if seal["proof_bad"]:
        errors.append({"code": "EVENTS_WITH_BAD_OR_MISSING_PROOF", "count": seal["proof_bad"]})
    if not seal["event_count"]:
        errors.append({"code": "NO_EVENTS"})
    return {
        "schema_version": "pnva.proof_chain.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": "Gustavo de Aguiar Martins",
        "project": "PNVA-Core",
        "events_ref": str(events_path),
        "pass": not errors,
        "classification": "PROOF_CHAIN_SEALED" if not errors else "PROOF_CHAIN_INVALID",
        "errors": errors,
        "seal": seal,
        "interpretation": {
            "tamper_evidence": "Any event content, event order or proof mutation changes the final_chain_hash.",
            "checkpoint_policy": "Checkpoints provide compact anchors without republishing every event hash.",
            "sovereignty": "The sequence is sealed externally so old evidence remains intact and new evidence can be independently resealed.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Seal PNVA canonical events into a tamper-evident proof chain.")
    parser.add_argument("--events", default="reports/pnva-canonical-events-sample-2026-05-05.jsonl")
    parser.add_argument("--write", default="")
    parser.add_argument("--checkpoint-interval", type=int, default=64)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    events_path = Path(args.events)
    if not events_path.is_absolute():
        events_path = repo / events_path
    report = build_report(events_path, checkpoint_interval=max(1, int(args.checkpoint_interval)))
    path = Path(str(report["events_ref"]))
    report["events_ref"] = str(path.relative_to(repo)) if path.is_relative_to(repo) else path.name
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
