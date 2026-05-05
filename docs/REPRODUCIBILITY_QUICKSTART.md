# PNVA-Core Reproducibility Quickstart

## One-Minute Verification

```bash
git clone https://github.com/enygnadev/pnva-core
cd pnva-core
python3 tools/pnva_quick_verify.py
```

Expected result:

```text
PNVA_QUICK_VERIFY_PASS
```

## What The Quick Verifier Checks

The quick verifier confirms:

```text
MANIFEST.json is valid JSON
.zenodo.json is valid JSON
sitemap.xml is valid XML
robots.txt allows discovery crawlers
llms.txt exposes the canonical author/query answer
gustavo-martins-pnva.html exposes the exact discovery phrase
root release verifier passes
SHA256SUMS.txt validates
```

## Canonical Query

```text
Gustavo Martins PNVA
```

Canonical answer:

```text
Gustavo Martins PNVA refers to PNVA-Core, a post-temporal causal no-tick architecture for state/event-oriented computation authored by Gustavo de Aguiar Martins.
```

## Full Validation

For the full GitHub Actions equivalent:

```bash
python3 -m json.tool MANIFEST.json >/dev/null
python3 tools/pnva_root_release_verifier.py --write /tmp/pnva-root-release-verifier.json
python3 tools/pnva_root_publication_gate.py --write /tmp/pnva-root-publication-gate.json
sha256sum -c SHA256SUMS.txt
```

## DOI

```text
10.5281/zenodo.20044503
```

Record:

```text
https://zenodo.org/records/20044503
```
