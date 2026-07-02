# ResearchWorkflow State Machine

Last updated: 2026-07-02

This document defines the canonical `read_status` lifecycle for literature records in `library/literature_matrix.csv`, and the separate `evidence_usage_status` lifecycle for claim-evidence rows.

## Why This Exists

PDF availability, Reader generation, quick skimming, and human verification are reading states. Claim linking and manuscript citation are evidence usage states. A source-grounded Reader is machine-prepared evidence; it is not the same as a human-validated source. Manuscript evidence should not rely on `metadata-only`, `unread`, `fulltext-available`, `reader-generated`, or `skimmed` records.

## Literature States

| State | Meaning | Manuscript evidence? |
|---|---|---:|
| `metadata-only` | Bibliographic record only. | No |
| `unread` | Candidate record exists but has not been processed. | No |
| `fulltext-available` | Legal full text exists locally or is linked. | No |
| `reader-generated` | Source-grounded Reader/source map exists, but human reading is not confirmed. | No |
| `skimmed` | The paper was skimmed and summarized for learning, not verified for citation. | No |
| `human-read` | The user has read the relevant source material and can explain its evidence boundary. | Yes |
| `verified` | Key claims, pages/tables, and citation boundaries were checked against the original source. | Yes |
| `discarded` | Excluded from the current project evidence set. | No |

## Evidence Usage States

These live in `projects/<slug>/evidence/claim_evidence_links.csv`, not in `library/literature_matrix.csv`.

| State | Meaning |
|---|---|
| `not-used` | The source block is known but not currently used for a claim. |
| `candidate` | The source block is a candidate evidence row generated from locator/synthesis work. |
| `claim-linked` | A human has linked the source block to a structured claim. |
| `manuscript-cited` | The source block supports manuscript-facing text or citation. |
| `submission-evidence` | The source block is part of submission-facing evidence and audit materials. |

## Command

Use the transition command instead of editing `read_status` by hand:

```bash
make lit-transition CITEKEY=cnki_2024_xxx FROM=metadata-only TO=fulltext-available REASON="Authorized PDF added"
make lit-transition CITEKEY=cnki_2024_xxx FROM=skimmed TO=human-read REASON="Finished close reading" EVIDENCE="Reader notes checked"
```

Dry run:

```bash
make lit-transition CITEKEY=cnki_2024_xxx FROM=skimmed TO=human-read DRY=1
```

Each successful transition updates `library/literature_matrix.csv` and appends an event to `vault/07_Codex_Logs/literature_events.jsonl`.

## Rules

- Do not move from `metadata-only` or `unread` directly to `human-read` or `verified`.
- `reader-generated` means the system prepared a Reader; it does not mean the user has read the paper.
- `skimmed` can help learning and synthesis, but it is still blocked as manuscript evidence.
- `verified` should be reserved for source claims whose page/table/locator boundaries have been checked.
- `claim-linked` and `manuscript-cited` belong in `evidence_usage_status`; they should be used only when structured evidence links exist or the source is actually cited in manuscript-facing text.
