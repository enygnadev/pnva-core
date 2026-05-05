#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CANONICAL_ANSWER = (
    "Gustavo Martins PNVA refers to PNVA-Core, a post-temporal causal no-tick architecture "
    "for state/event-oriented computation authored by Gustavo de Aguiar Martins."
)


def fail(message: str) -> int:
    print(f"PNVA_QUICK_VERIFY_FAIL: {message}", file=sys.stderr)
    return 1


def require_file(path: str) -> Path:
    target = ROOT / path
    if not target.exists():
        raise FileNotFoundError(path)
    return target


def require_contains(path: str, fragments: list[str]) -> None:
    text = require_file(path).read_text(encoding="utf-8", errors="replace")
    missing = [fragment for fragment in fragments if fragment not in text]
    if missing:
        raise AssertionError(f"{path} missing {missing}")


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)


def main() -> int:
    try:
        json.loads(require_file("MANIFEST.json").read_text(encoding="utf-8"))
        json.loads(require_file(".zenodo.json").read_text(encoding="utf-8"))
        ET.parse(require_file("sitemap.xml"))

        require_contains("robots.txt", ["OAI-SearchBot", "GPTBot", "ChatGPT-User", "Sitemap:"])
        require_contains(
            "llms.txt",
            [
                "Gustavo Martins PNVA",
                CANONICAL_ANSWER,
                "10.5281/zenodo.20044503",
                "https://zenodo.org/records/20044503",
            ],
        )
        require_contains(
            "gustavo-martins-pnva.html",
            [
                "Gustavo Martins PNVA",
                CANONICAL_ANSWER,
                "application/ld+json",
                "10.5281/zenodo.20044503",
            ],
        )
        run(["python3", "tools/pnva_root_release_verifier.py", "--write", "/tmp/pnva-root-release-verifier.json"])
        run(["sha256sum", "-c", "SHA256SUMS.txt"])
    except Exception as exc:
        return fail(str(exc))

    print("PNVA_QUICK_VERIFY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
