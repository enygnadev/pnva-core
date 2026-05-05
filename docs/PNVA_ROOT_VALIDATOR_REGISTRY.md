# PNVA Root Validator Registry

Author: Gustavo de Aguiar Martins
Project: PNVA-Core
Edition: Open Research / Production Evidence Edition

## Purpose

The PNVA root validator registry proves that every root validator is discoverable across:

```text
tool
report
document
Manifest
checksum
CI workflow
README
llms.txt
sovereign documentation
```

The goal is to prevent root evidence from depending on memory or manual convention.

## Tool

```text
tools/pnva_root_validator_registry.py
```

## Report

```text
reports/pnva-root-validator-registry-2026-05-05.json
```

## Classification

```text
PNVA_ROOT_VALIDATOR_REGISTRY_READY
```

## Current Result

```text
registry_score: 100.0
check_count: 8
failure_count: 0
registry_count: 28
manifest_file_count: 252
checksum_count: 251
workflow_registered_count: 28
public_doc_registered_count: 28
report_pass_count: 28
root_release_hash: sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc
```

## Checks

The registry requires:

```text
root_validator_entries_present
root_validator_files_exist
root_validator_manifest_refs_complete
root_validator_checksums_complete
root_validator_reports_pass
root_validator_workflow_registered
root_validator_public_docs_registered
root_validator_hashes_aligned
```

## Production Interpretation

This layer prevents silent proof drift. A root validator is not considered part of the sovereign package unless its tool, report and document exist, are listed in the Manifest, are covered by checksums, are called by CI and are visible in public documentation.

## Boundary

This registry audits public repository structure only. It does not execute actions, change live gates, alter mining workloads or publish private tuning.

## Command

```bash
python3 tools/pnva_root_validator_registry.py \
  --write reports/pnva-root-validator-registry-2026-05-05.json
```
