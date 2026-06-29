# GB/T 7714 And Chinese Reference Audit

Generated: 2026-06-19T21:05:33
Project: `starter_project`
Paper: `/Users/leung/ResearchWorkflow/projects/starter_project/manuscript/paper.md`
References: `/Users/leung/ResearchWorkflow/projects/starter_project/manuscript/references.bib`

This is a deterministic heuristic audit. It catches common problems before submission, but it does not replace manual journal proofing.

## Summary

| Metric | Value |
|---|---:|
| Status | PASS |
| Numbered in-text citation labels | 0 |
| Markdown reference entries | 0 |
| BibTeX entries | 0 |
| ERROR issues | 0 |
| WARN issues | 1 |
| INFO issues | 0 |
| Evidence gate status | PASS |
| Evidence gate ERROR issues | 0 |
| Evidence gate WARN issues | 0 |

## Issues

| Severity | Location | Issue | Suggested action |
|---|---|---|---|
| WARN | `/Users/leung/ResearchWorkflow/projects/starter_project/manuscript/paper.md` | 未检测到参考文献条目。 | 写作阶段可以为空；投稿前必须补齐并运行本审计。 |

## What This Checks

- GB/T 7714-style sequential citation consistency.
- Missing publication years and document type markers such as `[J]`, `[M]`, `[D]`, `[EB/OL]`.
- Chinese references that appear to lack English translation information.
- Overlong Chinese author lists that may need `等`.
- DOI/URL hygiene issues.
- Evidence-state problems for cited or claim-linked sources when a project is provided.

## Manual Checks Still Required

- Whether each cited source actually supports the local claim.
- Whether every Chinese reference's English translation matches the official title/source.
- Whether final punctuation, capitalization, and spacing match the latest journal template.
