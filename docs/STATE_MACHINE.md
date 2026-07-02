# ResearchWorkflow State Machine

Last updated: 2026-07-02

This document defines the canonical `read_status` lifecycle for literature records in `library/literature_matrix.csv`.

## Why This Exists

PDF availability, Reader generation, quick skimming, human reading, and manuscript citation are different states. A source-grounded Reader is machine-prepared evidence; it is not the same as a human-validated source. Manuscript evidence should not rely on `metadata-only`, `unread`, `fulltext-available`, `reader-generated`, or `skimmed` records.

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
| `claim-linked` | The source is linked to a structured claim/evidence record. | Yes |
| `manuscript-cited` | The source is used in manuscript or submission-facing evidence. | Yes |
| `discarded` | Excluded from the current project evidence set. | No |

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

- Do not move from `metadata-only` or `unread` directly to `human-read`, `verified`, `claim-linked`, or `manuscript-cited`.
- `reader-generated` means the system prepared a Reader; it does not mean the user has read the paper.
- `skimmed` can help learning and synthesis, but it is still blocked as manuscript evidence.
- `verified` should be reserved for source claims whose page/table/locator boundaries have been checked.
- `claim-linked` and `manuscript-cited` should be used only when structured evidence links exist or the source is actually cited in manuscript-facing text.
