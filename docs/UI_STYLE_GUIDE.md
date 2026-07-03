# ResearchWorkflow UI Style Guide

Updated: 2026-07-03

## Goal

ResearchWorkflow is a task-first research workspace. HTML pages should help the user decide what to do next, not expose every generated file as a top-level choice.

## Navigation Model

Use two navigation layers on user-facing HTML pages.

Primary navigation is fixed and limited to six modules:

| Module | Purpose | Default entry |
|---|---|---|
| 总览 | System-wide starting point | `study_dashboard.html` |
| 今日任务 | What to do next | `action_queue.html` |
| 阅读 | Daily reading and literature assets | `paper_reading/today.html` |
| 写作 | Manuscript production | `projects/<project>/manuscript/writing_panel.html` |
| 证据 | Evidence location and page verification | `projects/<project>/evidence/page_verification_queue.html` |
| 系统 | Status, audit, collaboration, archive policy | `workflow_state.html` |

Secondary navigation is contextual. It should show only pages that belong to the current module.

Low-frequency pages such as archive policy, workflow health, project collaboration, Vault Home, backup index, and CSV/JSON files must not appear as primary navigation items. They can appear in the System subnavigation, page cards, or primary action buttons.

## Page Shell

All major generated pages should use `rendering.ui.render_shell()`.

The standard header order is:

1. Module breadcrumb: `ResearchWorkflow / <module>`
2. Page title
3. One-sentence page purpose
4. Muted metadata such as project or generated time
5. Primary navigation
6. Current-module subnavigation
7. Optional primary action on the right

Do not create pages that only show "返回学习仪表盘" without the standard shell.

Core task pages should also include a `.page-guidance` panel near the top of the body. It answers three questions:

1. `这个页面用于：...`
2. `建议先做：...`
3. `完成后去：...`

The goal is fast orientation. Detailed professional terminology can stay in tables, notes, and metadata; the first screen should tell the user what to do next.

## Shared Assets

Use shared assets:

- CSS: `assets/app.css`
- JS: `assets/app.js`

Generated pages should link the CSS file instead of embedding a separate full style block. Page-specific scripts are allowed only for specialized interactions such as graph/search visualizations.

## Visual Rules

- Desktop content width: default `1240px`.
- Border radius: `7px` to `8px`.
- Button height: at least `40px`, preferably `44px`.
- Current navigation item: light blue background, blue border, blue text.
- Metadata: muted, small, never competing with the title.
- Primary action: one obvious action per page when possible.
- Copy-command buttons: secondary actions, grouped in the page body or advanced action area.
- Task guidance: one purpose, one recommended first action, one next destination.
- Navigation should scroll horizontally on narrow screens instead of wrapping into noisy multi-line bars.

## Component Classes

Common classes live in `assets/app.css`:

- Layout: `.wrap`, `.grid`, `.panel`, `.wide`
- Cards: `.metric`, `.item`, `.action`, `.project`, `.check`
- Navigation: `.global-nav`, `.subnav`
- Actions: `.button`, `.inline-button`, `.toolbar`
- Guidance: `.page-guidance`, `.guidance-grid`
- Reading content: `.md-view`, `.source-path`, `.wikilink`
- Status: `.status`, `.pass`, `.warn`, `.fail`

## Module Assignment

| Page | Module |
|---|---|
| `study_dashboard.html` | 总览 |
| `action_queue.html` | 今日任务 |
| `paper_reading/today.html` | 阅读 |
| `paper_reading/index.html` | 阅读 |
| `knowledge_cards/index.html` | 阅读 |
| `knowledge_cards/review_today.html` | 今日任务 |
| `projects/<project>/literature/incoming_pdf_triage.html` | 阅读 |
| `projects/<project>/literature/evidence_locator_table.html` | 证据 |
| `projects/<project>/evidence/page_verification_queue.html` | 证据 |
| `projects/<project>/manuscript/writing_panel.html` | 写作 |
| `workflow_state.html` | 系统 |
| `workflow_health.html` | 系统 |
| `project_collaboration.html` | 系统 |
| `archive_policy.html` | 系统 |
| `logs/index.html` | 系统 |

## Acceptance Checks

The workflow test suite should enforce:

- Primary navigation has at most six links.
- Main user-facing pages link `assets/app.css`.
- Context pages have a subnavigation.
- Dashboard interaction JS lives in `assets/app.js`, not repeated inline across every generated page.
- Core task pages include `.page-guidance` with purpose, first action, and next destination.
