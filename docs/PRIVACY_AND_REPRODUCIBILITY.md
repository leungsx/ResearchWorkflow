# Privacy And Reproducibility Guardrails

Last updated: 2026-07-02

## Repository Privacy Modes

| Mode | Use case | Default action |
|---|---|---|
| `public-demo-mode` | Public template or demo repository. | Keep real manuscripts, logs, data extracts, credentials, and review material out of Git. Run `make privacy-audit STRICT=1` before publishing. |
| `private-research-mode` | Personal private research repository. | Text assets may be versioned, but secrets and raw participant/internal materials stay out of Git. |
| `institutional-confidential-mode` | Shared institutional or collaboration repository. | Treat manuscripts, review letters, raw comments, interview notes, and collaboration notes as confidential unless explicitly approved. |

## Commands

```bash
make privacy-audit
make privacy-audit STRICT=1
make literature-matrix-validate
make claim-evidence-links PROJECT=library_short_video
make experiment PROJECT=library_short_video NAME=pilot INPUTS="data/processed/input.csv" OUTPUTS="results/out.csv" SEED=42 CMD="python analysis/python/analysis.py"
```

## Evidence Boundary

- `machine-prepared`: PDF/Reader/source map exists, but the user has not confirmed the evidence boundary.
- `human-validated`: the user has read the relevant source and can explain the claim boundary.
- `publication-ready`: the source has page/table/locator checks and is linked to a claim or manuscript passage.

Use `projects/<slug>/evidence/claim_evidence_links.csv` for structured claim-source links. Keep Markdown maps for human reading, but use CSV for audit and downstream writing checks.
