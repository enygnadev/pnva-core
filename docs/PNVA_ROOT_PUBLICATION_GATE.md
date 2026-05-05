# PNVA Root Publication Gate

Author: Gustavo de Aguiar Martins
Project: PNVA-Core
Edition: Open Research / Production Evidence Edition

## Purpose

The PNVA root publication gate checks whether the public package is ready to be posted, indexed and reviewed.

It runs after the root seal, root verifier and claim boundary guard.

## Tool

```text
tools/pnva_root_publication_gate.py
```

## Report

```text
reports/pnva-root-publication-gate-2026-05-05.json
```

## Classification

```text
PNVA_ROOT_PUBLICATION_GATE_READY
```

## Current Result

```text
publication_score: 100.0
check_count: 9
failure_count: 0
manifest_file_count: 252
checksum_count: 251
sitemap_url_count: 83
path_leak_count: 0
root_release_hash: sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc
```

## Checks

The gate verifies:

```text
root reports are ready
root release hashes agree
Manifest and checksums are closed
required publication files exist
robots.txt allows discovery
sitemap.xml exposes canonical pages
llms.txt exposes root boundaries
claim boundary guard is ready
public files have no local path leaks
```

## Boundary

This gate validates the public package. It does not validate external deployments or private runtime evidence.

## Command

```bash
python3 tools/pnva_root_publication_gate.py \
  --write reports/pnva-root-publication-gate-2026-05-05.json
```
