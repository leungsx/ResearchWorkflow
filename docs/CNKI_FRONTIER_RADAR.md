# CNKI Frontier Radar

This is a lightweight learning-and-discussion layer on top of the CNKI workflow.
It is designed to avoid two common failures:

- reading too many papers superficially and remembering none of them
- treating CNKI metadata summaries as if they were full-text reading

## Optimized Routine

Use four levels.

1. **Frontier radar**: import a CNKI export, then select 5-7 recent/frontier
   candidates for discussion.
2. **Daily learning recommendation**: choose one primary paper per active Codex
   session, following a learning path from high-impact foundations to reviews,
   recent work, and methods.
3. **One-paper discussion card**: choose one paper from the radar or daily
   recommendation and create a
   focused brief for seminar-style discussion.
4. **Full-paper reader**: only after the user legally obtains the full text,
   build a source-grounded reader with original text, Chinese explanation,
   figures/tables, source map, and reading notes.

## Commands

Import CNKI metadata:

```bash
make import-cnki INPUT=library/cnki_exports/<file> TAG=<project_slug>
```

Generate a frontier digest:

```bash
make cnki-frontier TAG=<project_slug> TOPIC="生成式人工智能与知识服务"
```

Generate today's learning recommendation:

```bash
make cnki-daily PROJECT=<project_slug> TOPIC="生成式人工智能与知识服务"
```

Create a one-paper discussion card:

```bash
make paper-brief CITEKEY=<citekey>
```

Upgrade to a source-grounded reader after legal full-text access:

```bash
make paper-reader PROJECT=<project_slug> CITEKEY=<citekey> PDF=library/pdfs/<paper>.pdf
make evidence-gate PROJECT=<project_slug>
```

## Daily Use

Codex cannot autonomously run when no Codex session exists. Treat "daily" as:

- when a Codex session is active that day, Codex checks whether a fresh CNKI
  export exists
- if an export exists, Codex imports it and generates a radar digest
- if a project matrix exists, Codex generates a daily learning recommendation
  with `make cnki-daily`
- if no export exists, Codex prepares the CNKI search strategy and asks the user
  to authorize/login/export

## Digest Quality Rules

- Select 5-7 papers, not more.
- Include at least one "possibly important but not obviously aligned" paper to
  reduce confirmation bias.
- Do not mark a metadata-only paper as read.
- Do not use a paper as manuscript evidence until the original full text has
  been read and the relevant claim has a source locator.
- The deterministic reader command extracts source-grounded blocks, but it does
  not automatically mark a paper as `human-read` or `verified`.
- For 《图书情报工作》 projects, each digest should ask whether the candidate helps
  with information resource management contribution, method design, data
  governance, or practical service scenarios.

## Full-Text Boundary

The original paper file must come from legal CNKI/institutional access. Codex
can organize and read local files provided by the user, but must not bypass
CNKI access controls, CAPTCHA, paywalls, or download limits.
