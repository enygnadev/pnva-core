#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "proofs" / "raw"
OUT = ROOT / "proofs" / "sanitized"

def scrub(value):
    if isinstance(value, dict):
        return {str(k): scrub(v) for k, v in value.items()}
    if isinstance(value, list):
        return [scrub(v) for v in value]
    if isinstance(value, str):
        return re.sub(r"/home/[^/\s\"']+", "<HOME>", value)
    return value


def summarize_long_run(data):
    live = data.get("series", {}).get("live", {})
    summary = live.get("summary", {})
    return {
        "timestamp": data.get("timestamp"),
        "pass": data.get("pass"),
        "canonical_pass": data.get("canonical_pass", data.get("pass")),
        "classification": data.get("classification", ""),
        "gate_request": scrub(data.get("gate_request", {})),
        "checks": data.get("checks", {}),
        "canonical_checks": data.get("canonical_checks", {}),
        "live_summary": {
            key: summary.get(key)
            for key in (
                "sample_count",
                "steady_sample_count",
                "steady_quiet_sample_count",
                "steady_quiet_ratio",
                "steady_quiet_wakeups_max",
                "wakeups_drift",
                "loop_drift_ms",
                "dirty_spike_unique_count",
                "allowlist_growth",
                "allowlist_max",
                "same_family_recovery_growth",
                "fieldcomms_running_all_samples",
                "fieldcomms_schema_ok",
                "runtime_phase_end",
            )
        },
        "reclassification": scrub(data.get("reclassification", {})),
    }


def summarize_g1(data):
    return {
        "timestamp": data.get("timestamp"),
        "phase_id": data.get("phase_id"),
        "proof_name": data.get("proof_name"),
        "pass": data.get("pass"),
        "status": data.get("status"),
        "classification": data.get("classification"),
        "checks": data.get("checks", {}),
        "monitor": scrub(data.get("monitor", {})),
        "capture": scrub(data.get("capture", {})),
    }


def summarize_generic(data):
    pass_value = data.get("pass")
    if pass_value is None and data.get("overall_status") == "PASS":
        pass_value = True
    return scrub(
        {
            "timestamp": data.get("timestamp"),
            "phase_id": data.get("phase_id", data.get("phase", "")),
            "proof_name": data.get("proof_name", ""),
            "pass": pass_value,
            "overall_status": data.get("overall_status", ""),
            "classification": data.get("classification", ""),
            "checks": data.get("checks", {}),
            "pass_fail_por_item": data.get("pass_fail_por_item", {}),
            "details": data.get("details", {}),
        }
    )


def summarize(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    name = path.name
    if name.startswith("prove-long-run-stability-"):
        return summarize_long_run(data)
    if name == "prove-real-stable-opportunity-capture.json":
        return summarize_g1(data)
    return summarize_generic(data)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    index = []
    for path in sorted(RAW.glob("*.json")):
        summary = summarize(path)
        out_path = OUT / path.name
        out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        index.append(
            {
                "artifact": path.name,
                "sanitized": str(out_path.relative_to(ROOT)),
                "pass": summary.get("pass", summary.get("overall_status")),
                "classification": summary.get("classification", ""),
            }
        )
    (OUT / "INDEX.json").write_text(json.dumps(index, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
