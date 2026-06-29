#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects"
MATRIX = ROOT / "library" / "literature_matrix.csv"
LOCAL_CAJ2PDF = ROOT / "tools" / "caj2pdf" / "caj2pdf"


@dataclass
class ConversionResult:
    citekey: str
    source: Path
    source_kind: str
    output_pdf: Path
    report_path: Path
    ok: bool
    message: str


def load_rows(matrix: Path = MATRIX) -> list[dict[str, str]]:
    if not matrix.exists():
        return []
    with matrix.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(rows: list[dict[str, str]], matrix: Path = MATRIX) -> None:
    if not rows:
        return
    with matrix.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def project_has_tag(row: dict[str, str], project: str) -> bool:
    tags = [tag.strip() for tag in row.get("project_tags", "").split(";") if tag.strip()]
    return project in tags


def find_row(rows: list[dict[str, str]], citekey: str) -> dict[str, str]:
    for row in rows:
        if row.get("citekey") == citekey:
            return row
    raise KeyError(f"Citekey not found in literature matrix: {citekey}")


def detect_kind(path: Path) -> str:
    with path.open("rb") as handle:
        header = handle.read(64)
    if header.startswith(b"%PDF-"):
        return "pdf"
    if header.startswith(b"KDH "):
        return "kdh-caj"
    if b"CAJ" in header[:32]:
        return "caj"
    return "unknown"


def project_dirs(project: str) -> tuple[Path, Path, Path]:
    project_root = PROJECTS / project
    if not project_root.exists():
        raise FileNotFoundError(project_root)
    pdf_dir = ROOT / "library" / "pdfs" / project
    converted_dir = pdf_dir / "converted"
    report_dir = project_root / "literature" / "caj_conversion"
    converted_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    return pdf_dir, converted_dir, report_dir


def default_output(project: str, citekey: str, input_path: Path, output: Path | None) -> Path:
    if output:
        return output
    _, converted_dir, _ = project_dirs(project)
    stem = citekey or input_path.stem
    return converted_dir / f"{stem}.pdf"


def locate_converter(explicit: str = "") -> tuple[list[str] | None, str]:
    candidates: list[Path | str] = []
    if explicit:
        candidates.append(Path(explicit))
    if os.environ.get("CAJ2PDF_BIN"):
        candidates.append(Path(os.environ["CAJ2PDF_BIN"]))
    candidates.append(LOCAL_CAJ2PDF)
    found = shutil.which("caj2pdf")
    if found:
        candidates.append(found)

    for candidate in candidates:
        if isinstance(candidate, Path):
            if not candidate.exists():
                continue
            return [sys.executable, str(candidate)], str(candidate)
        return [candidate], candidate
    return None, "missing"


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def verify_pdf(pdf: Path, preview_dir: Path) -> tuple[bool, list[str]]:
    notes: list[str] = []
    if not pdf.exists():
        return False, ["Output PDF does not exist."]
    if detect_kind(pdf) != "pdf":
        return False, ["Output exists but does not start with %PDF-."]

    pdfinfo = shutil.which("pdfinfo")
    if pdfinfo:
        result = run([pdfinfo, str(pdf)])
        if result.returncode == 0:
            page_line = next((line for line in result.stdout.splitlines() if line.startswith("Pages:")), "")
            notes.append(page_line or "pdfinfo succeeded.")
        else:
            notes.append(f"pdfinfo warning: {result.stderr.strip()}")

    pdftotext = shutil.which("pdftotext")
    if pdftotext:
        result = run([pdftotext, "-layout", str(pdf), "-"])
        if result.returncode == 0:
            text = result.stdout.strip()
            notes.append(f"pdftotext characters: {len(text)}")
        else:
            notes.append(f"pdftotext warning: {result.stderr.strip()}")

    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm:
        preview_dir.mkdir(parents=True, exist_ok=True)
        prefix = preview_dir / "page-1"
        result = run([pdftoppm, "-f", "1", "-singlefile", "-png", str(pdf), str(prefix)])
        if result.returncode == 0:
            notes.append(f"Preview: {prefix}.png")
        else:
            notes.append(f"pdftoppm warning: {result.stderr.strip()}")
    return True, notes


def render_report(
    *,
    citekey: str,
    title: str,
    source: Path,
    source_kind: str,
    output_pdf: Path,
    ok: bool,
    message: str,
    converter_label: str,
    command: list[str],
    stdout: str,
    stderr: str,
    verify_notes: list[str],
    ran_reader: bool,
) -> str:
    status = "OK" if ok else "FAILED"
    lines = [
        f"# CAJ Conversion Report - {citekey or source.stem}",
        "",
        f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}",
        f"Status: {status}",
        f"Title: {title or 'unknown'}",
        f"Source: `{source}`",
        f"Detected source kind: `{source_kind}`",
        f"Output PDF: `{output_pdf}`",
        f"Converter: `{converter_label}`",
        "",
        "## Result",
        "",
        message,
        "",
        "## Verification",
        "",
    ]
    if verify_notes:
        lines.extend(f"- {note}" for note in verify_notes)
    else:
        lines.append("- No PDF verification notes.")
    lines.extend(
        [
            "",
            "## Command",
            "",
            "```bash",
            " ".join(command) if command else "(no external converter command)",
            "```",
            "",
            "## Stdout",
            "",
            "```text",
            stdout.strip() or "(empty)",
            "```",
            "",
            "## Stderr",
            "",
            "```text",
            stderr.strip() or "(empty)",
            "```",
            "",
            "## Reader",
            "",
            f"- paper-reader run: {'yes' if ran_reader else 'no'}",
            "",
            "## Fallback If Failed",
            "",
            "- If this file is `kdh-caj` and conversion failed, use an authorized CNKI/CAJViewer route to export/print a PDF, then run `make paper-reader PROJECT=<project> CITEKEY=<citekey> PDF=<exported.pdf> UPDATE=1`.",
            "- Do not upload unpublished or private documents to third-party conversion services without explicit consent.",
            "",
        ]
    )
    return "\n".join(lines)


def update_matrix_pdf(rows: list[dict[str, str]], citekey: str, pdf: Path, matrix: Path) -> None:
    changed = False
    for row in rows:
        if row.get("citekey") == citekey:
            row["pdf_path"] = str(pdf)
            changed = True
    if changed:
        write_rows(rows, matrix)


def run_reader(project: str, citekey: str, pdf: Path, update_matrix: bool) -> tuple[bool, str, str]:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "paper_reader.py"),
        "--project",
        project,
        "--citekey",
        citekey,
        "--pdf",
        str(pdf),
    ]
    if update_matrix:
        cmd.append("--update-matrix")
    result = run(cmd)
    return result.returncode == 0, result.stdout, result.stderr


def convert_one(
    *,
    project: str,
    citekey: str,
    title: str,
    source: Path,
    output_pdf: Path,
    report_dir: Path,
    converter_arg: str,
    overwrite: bool,
    update_matrix: bool,
    run_reader_after: bool,
    rows: list[dict[str, str]],
    matrix: Path,
) -> ConversionResult:
    source = source.expanduser().resolve()
    output_pdf = output_pdf.expanduser().resolve()
    source_kind = detect_kind(source)
    preview_dir = report_dir / f"{citekey or source.stem}_preview"
    command: list[str] = []
    stdout = ""
    stderr = ""
    converter_label = ""
    verify_notes: list[str] = []
    ran_reader = False

    if output_pdf.exists() and not overwrite:
        ok, verify_notes = verify_pdf(output_pdf, preview_dir)
        message = "Output PDF already exists; use OVERWRITE=1 to regenerate."
        converter_label = "not used (existing PDF)"
    elif source_kind == "pdf":
        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        if source == output_pdf:
            message = "Source is already the converted PDF path; verified in place."
        else:
            shutil.copy2(source, output_pdf)
            message = "Source file is already a PDF despite its extension; copied to converted PDF path."
        ok, verify_notes = verify_pdf(output_pdf, preview_dir)
    elif source_kind in {"kdh-caj", "caj"}:
        converter_cmd, converter_label = locate_converter(converter_arg)
        if converter_cmd is None:
            ok = False
            message = (
                "No caj2pdf converter was found. Install or clone caj2pdf, and ensure `mutool` from MuPDF is available. "
                "Expected local path: tools/caj2pdf/caj2pdf, or set CAJ2PDF_BIN."
            )
        else:
            output_pdf.parent.mkdir(parents=True, exist_ok=True)
            command = converter_cmd + ["convert", str(source), "-o", str(output_pdf)]
            result = run(command)
            stdout = result.stdout
            stderr = result.stderr
            if result.returncode == 0:
                ok, verify_notes = verify_pdf(output_pdf, preview_dir)
                message = "caj2pdf command completed; PDF verification passed." if ok else "caj2pdf command completed, but PDF verification failed."
            else:
                ok = False
                message = f"caj2pdf failed with exit code {result.returncode}."
    else:
        ok = False
        message = "Unknown source type; not safe to convert automatically."

    if ok and update_matrix and citekey:
        update_matrix_pdf(rows, citekey, output_pdf, matrix)

    if ok and run_reader_after and project and citekey:
        reader_ok, reader_out, reader_err = run_reader(project, citekey, output_pdf, update_matrix)
        ran_reader = True
        stdout = "\n".join(part for part in [stdout, reader_out] if part)
        stderr = "\n".join(part for part in [stderr, reader_err] if part)
        if not reader_ok:
            ok = False
            message = "PDF conversion succeeded, but paper-reader failed. See stderr."

    report_path = report_dir / f"{citekey or source.stem}.md"
    report_path.write_text(
        render_report(
            citekey=citekey,
            title=title,
            source=source,
            source_kind=source_kind,
            output_pdf=output_pdf,
            ok=ok,
            message=message,
            converter_label=converter_label or ("not needed" if source_kind == "pdf" else "missing"),
            command=command,
            stdout=stdout,
            stderr=stderr,
            verify_notes=verify_notes,
            ran_reader=ran_reader,
        ),
        encoding="utf-8",
    )
    return ConversionResult(citekey, source, source_kind, output_pdf, report_path, ok, message)


def scan_project(project: str, rows: list[dict[str, str]]) -> int:
    print(f"# CAJ scan for project: {project}")
    count = 0
    for row in rows:
        if not project_has_tag(row, project):
            continue
        path = row.get("pdf_path", "").strip()
        if not path:
            continue
        source = Path(path)
        if not source.exists():
            print(f"- MISSING {row.get('citekey')}: {source}")
            count += 1
            continue
        kind = detect_kind(source)
        if source.suffix.lower() == ".caj" or kind != "pdf":
            print(f"- {row.get('citekey')}: {kind} -> {source}")
            count += 1
    if count == 0:
        print("- No CAJ-like files found.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert CNKI CAJ/KDH files to verified local PDFs when possible.")
    parser.add_argument("--matrix", type=Path, default=MATRIX)
    parser.add_argument("--project", required=True)
    parser.add_argument("--citekey", default="")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--converter", default="", help="Path to caj2pdf executable/script; otherwise use CAJ2PDF_BIN, tools/caj2pdf/caj2pdf, or PATH.")
    parser.add_argument("--scan", action="store_true")
    parser.add_argument("--all", action="store_true", help="Convert every project-tagged row with an existing .caj path.")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--update-matrix", action="store_true")
    parser.add_argument("--run-reader", action="store_true")
    args = parser.parse_args()

    rows = load_rows(args.matrix)
    _, converted_dir, report_dir = project_dirs(args.project)

    if args.scan:
        return scan_project(args.project, rows)

    targets: list[tuple[str, str, Path, Path]] = []
    if args.all:
        for row in rows:
            if not project_has_tag(row, args.project):
                continue
            source_text = row.get("pdf_path", "").strip()
            if not source_text:
                continue
            source = Path(source_text)
            if source.exists() and (source.suffix.lower() == ".caj" or detect_kind(source) != "pdf"):
                citekey = row.get("citekey", "")
                targets.append((citekey, row.get("title", ""), source, converted_dir / f"{citekey}.pdf"))
    else:
        row = find_row(rows, args.citekey) if args.citekey else {}
        source = args.input or Path(row.get("pdf_path", ""))
        if not source:
            raise ValueError("Use --citekey with pdf_path in matrix, or provide --input.")
        citekey = args.citekey or row.get("citekey", "") or source.stem
        targets.append((citekey, row.get("title", ""), source, default_output(args.project, citekey, source, args.output)))

    failures = 0
    for citekey, title, source, output_pdf in targets:
        try:
            result = convert_one(
                project=args.project,
                citekey=citekey,
                title=title,
                source=source,
                output_pdf=output_pdf,
                report_dir=report_dir,
                converter_arg=args.converter,
                overwrite=args.overwrite,
                update_matrix=args.update_matrix,
                run_reader_after=args.run_reader,
                rows=rows,
                matrix=args.matrix,
            )
        except Exception as exc:
            failures += 1
            print(f"[FAIL] {citekey or source}: {exc}")
            continue
        tag = "OK" if result.ok else "FAIL"
        print(f"[{tag}] {result.citekey}: {result.source_kind} -> {result.output_pdf}")
        print(f"      Report: {result.report_path}")
        if not result.ok:
            print(f"      {result.message}")
            failures += 1

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
