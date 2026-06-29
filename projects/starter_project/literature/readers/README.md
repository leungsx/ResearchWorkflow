# Paper Reader Packages

Use this folder for full-paper, source-grounded reading outputs when a paper is
important enough that later writing should cite exact locations.

Recommended package shape:

```text
literature/readers/<paper_key>/
  paper.md
  source_map.json
  translation_notes.md
  assets/
```

Minimum expectations:

- `paper.md` keeps original/Chinese or original/summary blocks with stable source IDs.
- `source_map.json` records page, block ID, block type, original text, and extraction confidence.
- `translation_notes.md` records uncertain extraction, skipped material, terminology choices, and figure/table issues.
- `assets/` contains extracted figures or tables only when needed.

Do not treat this as a summary-only folder. If the output is only a summary, put
it in the literature synthesis or Obsidian paper note instead.
