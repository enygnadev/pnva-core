#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import statistics
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_SCOPES = {
    "canonical": "reports/pnva-canonical-events-sample-2026-05-05.jsonl",
    "native": "reports/pnva-native-events-demo-2026-05-05.jsonl",
}


def _issue(target: list[dict[str, Any]], *, code: str, scope: str, subject: str, detail: str) -> None:
    target.append({"code": code, "scope": scope, "subject": subject, "detail": detail})


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _round(value: float, digits: int = 6) -> float:
    if not math.isfinite(value):
        return 0.0
    return round(float(value), digits)


def _safe_ratio(part: int | float, total: int | float) -> float:
    return _round(float(part) / max(1.0, float(total)))


def _gap_stats(gaps: list[float]) -> dict[str, Any]:
    if not gaps:
        return {
            "count": 0,
            "min_seconds": 0.0,
            "max_seconds": 0.0,
            "median_seconds": 0.0,
            "mean_seconds": 0.0,
            "most_common_gap_seconds": 0.0,
            "most_common_gap_count": 0,
            "most_common_gap_ratio": 0.0,
        }
    rounded = [round(float(item), 3) for item in gaps]
    common_gap, common_count = Counter(rounded).most_common(1)[0]
    return {
        "count": len(gaps),
        "min_seconds": _round(min(gaps), 3),
        "max_seconds": _round(max(gaps), 3),
        "median_seconds": _round(statistics.median(gaps), 3),
        "mean_seconds": _round(statistics.mean(gaps), 3),
        "most_common_gap_seconds": common_gap,
        "most_common_gap_count": common_count,
        "most_common_gap_ratio": _safe_ratio(common_count, len(gaps)),
    }


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


def _analyze_scope(scope: str, repo: Path, rel: str) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    events = _load_events(repo / rel, scope, errors)
    if not events:
        _issue(errors, code="NO_EVENTS", scope=scope, subject=rel, detail="scope has no events")

    parsed: list[tuple[int, dict[str, Any], datetime]] = []
    chain_seen: dict[str, list[tuple[int, dict[str, Any], datetime]]] = defaultdict(list)
    decision_counts: Counter[str] = Counter()
    chain_counts: Counter[str] = Counter()
    event_type_counts: Counter[str] = Counter()

    for index, event in enumerate(events):
        event_id = str(event.get("event_id") or f"line:{event.get('_line_no', index + 1)}")
        timestamp = _parse_timestamp(event.get("timestamp"))
        if timestamp is None:
            _issue(errors, code="BAD_TIMESTAMP", scope=scope, subject=event_id, detail=str(event.get("timestamp")))
            continue
        chain_id = event.get("causal_chain_id")
        if not isinstance(chain_id, str) or not chain_id:
            _issue(errors, code="MISSING_CAUSAL_CHAIN", scope=scope, subject=event_id, detail=str(chain_id))
            chain_id = "<missing>"
        parsed.append((index, event, timestamp))
        chain_seen[chain_id].append((index, event, timestamp))
        chain_counts[chain_id] += 1
        decision_counts[str(event.get("decision", {}).get("kind"))] += 1
        event_type_counts[str(event.get("event_type"))] += 1

    global_gaps: list[float] = []
    positive_gaps: list[float] = []
    backward_count = 0
    zero_gap_count = 0
    previous: tuple[int, dict[str, Any], datetime] | None = None
    for item in parsed:
        if previous is not None:
            gap = (item[2] - previous[2]).total_seconds()
            global_gaps.append(gap)
            if gap < 0:
                backward_count += 1
                code = "NATIVE_BACKWARD_TIME" if scope == "native" else "LEGACY_BACKWARD_TIME"
                target = errors if scope == "native" else warnings
                _issue(target, code=code, scope=scope, subject=str(item[1].get("event_id")), detail=f"gap_seconds={gap}")
            elif gap == 0:
                zero_gap_count += 1
            else:
                positive_gaps.append(gap)
        previous = item

    chain_backward_count = 0
    chain_zero_gap_count = 0
    chain_gaps: list[float] = []
    chain_summaries: dict[str, dict[str, Any]] = {}
    for chain_id, items in chain_seen.items():
        items_sorted = sorted(items, key=lambda item: item[0])
        local_gaps: list[float] = []
        local_backward = 0
        local_zero = 0
        previous_item: tuple[int, dict[str, Any], datetime] | None = None
        for item in items_sorted:
            if previous_item is not None:
                gap = (item[2] - previous_item[2]).total_seconds()
                local_gaps.append(gap)
                chain_gaps.append(gap)
                if gap < 0:
                    local_backward += 1
                elif gap == 0:
                    local_zero += 1
            previous_item = item
        chain_backward_count += local_backward
        chain_zero_gap_count += local_zero
        chain_summaries[chain_id] = {
            "event_count": len(items_sorted),
            "first_timestamp": items_sorted[0][2].isoformat().replace("+00:00", "Z") if items_sorted else "",
            "last_timestamp": items_sorted[-1][2].isoformat().replace("+00:00", "Z") if items_sorted else "",
            "backward_count": local_backward,
            "zero_gap_count": local_zero,
            "gap_stats": _gap_stats(local_gaps),
        }

    if scope == "canonical":
        if zero_gap_count and _safe_ratio(zero_gap_count, max(0, len(parsed) - 1)) > 0.50:
            _issue(
                warnings,
                code="LEGACY_BATCH_TIMESTAMP_COMPACTION",
                scope=scope,
                subject="global",
                detail=f"zero_gap_count={zero_gap_count}",
            )
    else:
        if zero_gap_count:
            _issue(warnings, code="NATIVE_ZERO_GAP_EVENTS", scope=scope, subject="global", detail=f"zero_gap_count={zero_gap_count}")

    positive_stats = _gap_stats(positive_gaps)
    if len(positive_gaps) >= 10 and positive_stats["most_common_gap_ratio"] > 0.75:
        target = warnings if scope == "canonical" else errors
        _issue(
            target,
            code="FIXED_INTERVAL_DOMINANCE",
            scope=scope,
            subject="global",
            detail=f"gap={positive_stats['most_common_gap_seconds']} ratio={positive_stats['most_common_gap_ratio']}",
        )

    first_ts = parsed[0][2] if parsed else None
    last_ts = parsed[-1][2] if parsed else None
    span = (last_ts - first_ts).total_seconds() if first_ts and last_ts else 0.0
    return {
        "scope": scope,
        "event_file": rel,
        "event_count": len(events),
        "parsed_timestamp_count": len(parsed),
        "chain_count": len(chain_seen),
        "first_timestamp": first_ts.isoformat().replace("+00:00", "Z") if first_ts else "",
        "last_timestamp": last_ts.isoformat().replace("+00:00", "Z") if last_ts else "",
        "span_seconds": _round(span, 3),
        "global_backward_count": backward_count,
        "global_zero_gap_count": zero_gap_count,
        "global_zero_gap_ratio": _safe_ratio(zero_gap_count, max(0, len(parsed) - 1)),
        "chain_backward_count": chain_backward_count,
        "chain_zero_gap_count": chain_zero_gap_count,
        "global_gap_stats": _gap_stats(global_gaps),
        "positive_gap_stats": positive_stats,
        "chain_gap_stats": _gap_stats(chain_gaps),
        "decision_counts": dict(sorted(decision_counts.items())),
        "event_type_counts": dict(event_type_counts.most_common(12)),
        "top_chains": [
            {"causal_chain_id": key, "event_count": count}
            for key, count in chain_counts.most_common(10)
        ],
        "chain_summaries": dict(sorted(chain_summaries.items())),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


def build_report(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    scopes = [_analyze_scope(scope, repo, rel) for scope, rel in DEFAULT_SCOPES.items()]
    total_errors = sum(int(scope.get("error_count", 0)) for scope in scopes)
    total_warnings = sum(int(scope.get("warning_count", 0)) for scope in scopes)
    total_events = sum(int(scope.get("event_count", 0)) for scope in scopes)
    total_chains = sum(int(scope.get("chain_count", 0)) for scope in scopes)
    total_backward = sum(int(scope.get("global_backward_count", 0)) for scope in scopes)
    native_scope = next((scope for scope in scopes if scope.get("scope") == "native"), {})
    native_clean = int(native_scope.get("error_count", 0)) == 0 and int(native_scope.get("global_backward_count", 0)) == 0
    if total_errors:
        classification = "CAUSAL_CHRONOLOGY_FAIL"
    elif total_warnings:
        classification = "CAUSAL_CHRONOLOGY_READY_WITH_LEGACY_WARNINGS"
    else:
        classification = "CAUSAL_CHRONOLOGY_READY"
    return {
        "schema_version": "pnva.causal_chronology.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": "Gustavo de Aguiar Martins",
        "project": "PNVA-Core",
        "classification": classification,
        "pass": total_errors == 0,
        "scope_count": len(scopes),
        "event_count": total_events,
        "chain_count": total_chains,
        "global_backward_count": total_backward,
        "error_count": total_errors,
        "warning_count": total_warnings,
        "native_chronology_clean": native_clean,
        "scopes": scopes,
        "summary": {
            "validated_scopes": [scope.get("scope") for scope in scopes],
            "total_event_count": total_events,
            "total_chain_count": total_chains,
            "total_global_backward_count": total_backward,
            "native_chronology_clean": native_clean,
            "legacy_warning_policy": "canonical bridge chronology warnings are preserved as legacy migration evidence; native events are expected to be monotonic and clean",
        },
        "interpretation": {
            "purpose": "Validate timestamp order, causal-chain chronology and time-gap evidence for public PNVA event logs.",
            "sovereignty": "PNVA/no-tick does not use time as a blind execution motor, but it must still preserve time as an auditable trace dimension.",
            "boundary": "This guard checks chronology and cadence evidence; replay, policy, graph, schema and proof-chain validators remain responsible for their own layers.",
        },
        "recommendations": [
            "Treat native backward time as release-blocking.",
            "Keep canonical legacy chronology warnings explicit instead of rewriting historical sample order.",
            "Prefer native event emission for future proof logs so timestamp order is monotonic by construction.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate PNVA causal chronology and no-tick time evidence.")
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
