#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from scan_incoming_pdfs import duplicate_key  # noqa: E402
from transition_literature_state import parse_state_schema, transition_allowed  # noqa: E402
from validate_literature_matrix import validate_matrix  # noqa: E402
from privacy_audit import audit_paths  # noqa: E402
from run_experiment import hash_target  # noqa: E402
from workflow_config import active_project_slug, read_workflow_config  # noqa: E402


ACTIVE_PROJECT = active_project_slug()


def project_path(*parts: str) -> Path:
    return ROOT / "projects" / ACTIVE_PROJECT / Path(*parts)


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        for name, value in attrs:
            if name == "href" and value:
                self.hrefs.append(value)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def hrefs(path: Path) -> list[str]:
    parser = LinkParser()
    parser.feed(read_text(path))
    return parser.hrefs


def local_target(page: Path, href: str) -> Path | None:
    parsed = urlparse(href)
    if parsed.scheme or parsed.netloc:
        return None
    if parsed.path in {"", "."}:
        return None
    target = unquote(parsed.path)
    if target.startswith("#"):
        return None
    return (page.parent / target).resolve()


def user_html_pages() -> list[Path]:
    pages: list[Path] = [
        ROOT / "study_dashboard.html",
        ROOT / "workflow_state.html",
        ROOT / "action_queue.html",
        ROOT / "project_collaboration.html",
        ROOT / "archive_policy.html",
        ROOT / "workflow_health.html",
    ]
    for directory in [
        ROOT / "paper_reading",
        ROOT / "knowledge_cards",
        ROOT / "knowledge_graph",
        ROOT / "search",
        ROOT / "logs",
        project_path("literature"),
        project_path("manuscript"),
        project_path("evidence"),
    ]:
        if directory.exists():
            pages.extend(sorted(directory.rglob("*.html")))
    return sorted({path.resolve() for path in pages if path.exists()})


class WorkflowSmokeTests(unittest.TestCase):
    def test_active_project_config_points_to_existing_project(self) -> None:
        config = read_workflow_config()
        self.assertEqual(config.get("active_project"), ACTIVE_PROJECT)
        self.assertTrue((ROOT / "config" / "workflow.yaml").exists())
        self.assertTrue(project_path("project.yaml").exists())

    def test_literature_state_machine_schema_is_enforced(self) -> None:
        schema = parse_state_schema(ROOT / "schemas" / "literature_state.schema.yaml")
        states = set(schema["states"])
        self.assertIn("reader-generated", states)
        self.assertIn("verified", states)
        self.assertTrue(transition_allowed(schema, "metadata-only", "fulltext-available"))
        self.assertTrue(transition_allowed(schema, "skimmed", "human-read"))
        self.assertFalse(transition_allowed(schema, "metadata-only", "manuscript-cited"))
        self.assertEqual("vault/07_Codex_Logs/literature_events.jsonl", schema["event_log"])

    def test_required_entrypoints_exist_and_have_basic_html_scaffold(self) -> None:
        required = [
            ROOT / "study_dashboard.html",
            ROOT / "paper_reading" / "today.html",
            ROOT / "paper_reading" / "index.html",
            ROOT / "knowledge_cards" / "index.html",
            ROOT / "knowledge_cards" / "review_today.html",
            ROOT / "knowledge_graph" / "index.html",
            ROOT / "search" / "index.html",
            ROOT / "workflow_state.html",
            ROOT / "action_queue.html",
            ROOT / "project_collaboration.html",
            ROOT / "archive_policy.html",
            ROOT / "workflow_health.html",
            project_path("literature", "incoming_pdf_triage.html"),
            project_path("literature", "evidence_locator_table.html"),
            project_path("evidence", "page_verification_queue.html"),
            project_path("manuscript", "writing_panel.html"),
        ]
        for page in required:
            with self.subTest(page=page.relative_to(ROOT).as_posix()):
                self.assertTrue(page.exists(), f"missing {page}")
                text = read_text(page)
                self.assertIn("<meta name=\"viewport\"", text)
                self.assertRegex(text, r"<h1\b")
                self.assertLess(page.stat().st_size, 2_500_000)

    def test_generated_entry_links_do_not_open_markdown_sources(self) -> None:
        offenders: list[str] = []
        for page in user_html_pages():
            for href in hrefs(page):
                target = local_target(page, href)
                if target and target.suffix.lower() == ".md":
                    offenders.append(f"{page.relative_to(ROOT)} -> {href}")
        self.assertEqual([], offenders)

    def test_key_local_links_resolve(self) -> None:
        key_pages = [
            ROOT / "study_dashboard.html",
            ROOT / "paper_reading" / "index.html",
            ROOT / "paper_reading" / "today.html",
            ROOT / "knowledge_cards" / "index.html",
            ROOT / "knowledge_cards" / "review_today.html",
            ROOT / "knowledge_graph" / "index.html",
            ROOT / "search" / "index.html",
            ROOT / "workflow_state.html",
            ROOT / "action_queue.html",
            ROOT / "project_collaboration.html",
            ROOT / "archive_policy.html",
            ROOT / "workflow_health.html",
            project_path("literature", "incoming_pdf_triage.html"),
            project_path("literature", "evidence_locator_table.html"),
            project_path("evidence", "page_verification_queue.html"),
            project_path("manuscript", "writing_panel.html"),
        ]
        missing: list[str] = []
        for page in key_pages:
            for href in hrefs(page):
                target = local_target(page, href)
                if target and not target.exists():
                    missing.append(f"{page.relative_to(ROOT)} -> {href}")
        self.assertEqual([], missing)

    def test_manifest_tracks_core_display_assets(self) -> None:
        manifest = ROOT / "vault" / "13_Knowledge_Graph" / "artifact_manifest.csv"
        rows = csv_rows(manifest)
        self.assertGreater(len(rows), 50)
        self.assertIn("asset_role", rows[0])
        required_types = {
            "dashboard",
            "review_today",
            "knowledge_graph",
            "incoming_pdf_triage",
            "evidence_locator_table",
            "page_verification_queue",
            "manuscript_writing_panel",
        }
        seen_types = {row["display_type"] for row in rows}
        self.assertTrue(required_types <= seen_types)
        md_displays = [row["display_path"] for row in rows if row["display_path"].endswith(".md")]
        self.assertEqual([], md_displays)

    def test_workflow_audit_report_records_mode(self) -> None:
        report_path = ROOT / "vault" / "13_Knowledge_Graph" / "workflow_audit_report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertIn(report.get("audit_mode"), {"readonly", "refresh_then_audit"})
        self.assertRegex(str(report.get("pre_refresh_state_hash", "")), r"^[0-9a-f]{64}$")
        self.assertRegex(str(report.get("post_refresh_state_hash", "")), r"^[0-9a-f]{64}$")

    def test_literature_matrix_schema_has_no_failures(self) -> None:
        _fields, issues = validate_matrix(ROOT / "library" / "literature_matrix.csv")
        failures = [issue for issue in issues if issue.status == "FAIL"]
        self.assertEqual([], failures)

    def test_structured_claim_evidence_links_exist(self) -> None:
        path = project_path("evidence", "claim_evidence_links.csv")
        rows = csv_rows(path)
        self.assertGreater(len(rows), 10)
        self.assertEqual(
            [
                "claim_id",
                "claim_text",
                "citekey",
                "evidence_type",
                "source_block_id",
                "page",
                "locator_status",
                "read_status",
                "strength",
                "risk",
                "used_in_manuscript",
                "source_path",
            ],
            list(rows[0].keys()),
        )
        self.assertTrue(all(row["used_in_manuscript"] in {"true", "false"} for row in rows))

    def test_page_verification_queue_connects_claims_to_sources(self) -> None:
        csv_path = project_path("evidence", "page_verification_queue.csv")
        json_path = project_path("evidence", "page_verification_queue.json")
        html_path = project_path("evidence", "page_verification_queue.html")
        rows = csv_rows(csv_path)
        queue = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertTrue(html_path.exists())
        self.assertGreater(len(rows), 10)
        self.assertEqual("ResearchWorkflow.PageVerificationQueue.v1", queue["schema_version"])
        self.assertEqual(len(rows), queue["summary"]["total_items"])
        self.assertEqual(len(rows), len(queue["items"]))
        self.assertIn("needs_page_locator", {row["verification_status"] for row in rows})
        for field in ["claim_id", "citekey", "source_block_id", "page", "read_status", "next_action"]:
            self.assertIn(field, rows[0])
        html_text = read_text(html_path)
        self.assertIn("Claim -> Source Block -> Page -> Read Status", html_text)
        self.assertNotRegex(html_text, r'href="[^"]+\.md')

    def test_privacy_audit_has_no_secret_failures(self) -> None:
        issues = audit_paths()
        failures = [issue for issue in issues if issue.status == "FAIL"]
        self.assertEqual([], failures[:10])

    def test_experiment_hash_target_records_file_hash(self) -> None:
        tmp = ROOT / ".tmp" / "workflow-test-input.txt"
        tmp.parent.mkdir(exist_ok=True)
        tmp.write_text("workflow test\n", encoding="utf-8")
        try:
            record = hash_target(tmp)
            self.assertTrue(record["exists"])
            self.assertEqual("file", record["kind"])
            self.assertRegex(str(record["sha256"]), r"^[0-9a-f]{64}$")
        finally:
            tmp.unlink(missing_ok=True)

    def test_project_state_prioritizes_unread_incoming_candidates(self) -> None:
        state = json.loads(project_path("project_state.json").read_text(encoding="utf-8"))
        candidates = state["literature"]["next_reading_candidates"]
        self.assertGreaterEqual(len(candidates), 3)
        top_statuses = {candidate["read_status"] for candidate in candidates[:5]}
        self.assertNotIn("skimmed", top_statuses)
        self.assertTrue(any(candidate.get("has_incoming_pdf") for candidate in candidates[:5]))
        self.assertTrue(any(candidate.get("next_action") == "intake_incoming_pdf" for candidate in candidates[:5]))

    def test_incoming_triage_handles_copy_suffix_duplicates(self) -> None:
        self.assertEqual(duplicate_key("抖音阅读推广短视频传播效果影响因素研究_杨达森"), duplicate_key("抖音阅读推广短视频传播效果影响因素研究_杨达森 (1)"))
        path = project_path("literature", "incoming_pdf_triage.csv")
        rows = csv_rows(path)
        copy_rows = [row for row in rows if re.search(r"[\(（]\d+[\)）]", row["file_name"])]
        for row in copy_rows:
            with self.subTest(file=row["file_name"]):
                self.assertGreater(int(row["duplicate_group_size"]), 1)
                self.assertEqual("duplicate_keep_one_then_archive", row["next_action"])

    def test_review_page_has_writeback_controls_and_fallback_command(self) -> None:
        text = read_text(ROOT / "knowledge_cards" / "review_today.html")
        self.assertIn("class=\"inline-button review-mark\"", text)
        self.assertIn("data-review-id=", text)
        self.assertIn("http://127.0.0.1:8765/review/studied", text)
        self.assertIn("make review-server-ensure", text)
        self.assertIn("make review-studied ID=", text)

    def test_graph_defaults_to_project_scope_and_keeps_core_chain_view(self) -> None:
        text = read_text(ROOT / "knowledge_graph" / "index.html")
        self.assertIn('data-kind="project_scope" class="active"', text)
        self.assertIn('data-kind="core_chain"', text)
        self.assertIn('let activeKind = "project_scope"', text)

    def test_evidence_locator_and_writing_panel_are_populated(self) -> None:
        evidence = csv_rows(project_path("literature", "evidence_locator_table.csv"))
        self.assertGreater(len(evidence), 10)
        self.assertTrue(all(row["locator_status"] in {"page_pending", "page_located_needs_human_check"} for row in evidence))
        writing = read_text(project_path("manuscript", "writing_panel.html"))
        self.assertIn("Variable And Indicator Draft", writing)
        self.assertIn("Claim Evidence Traceability", writing)
        self.assertIn("Research Question Evidence Trace", writing)
        self.assertIn("Variable And Indicator Evidence Trace", writing)
        self.assertIn("Paragraph Queue", writing)
        self.assertIn("Evidence Readiness", writing)
        self.assertIn("Page Verification Queue", writing)
        self.assertIn("Top Verification Tasks", writing)
        self.assertNotIn("<p>|", writing)
        trace = json.loads(project_path("manuscript", "writing_traceability.json").read_text(encoding="utf-8"))
        self.assertEqual("ResearchWorkflow.WritingTraceability.v1", trace["schema_version"])
        self.assertGreater(trace["summary"]["claim_link_rows"], 10)
        self.assertGreater(trace["verification_queue_summary"]["total_items"], 10)
        self.assertGreaterEqual(len(trace["top_verification_tasks"]), 3)
        self.assertGreaterEqual(len(trace["research_question_traces"]), 3)
        self.assertGreaterEqual(len(trace["variable_traces"]), 4)
        self.assertGreaterEqual(len(trace["paragraph_traces"]), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
