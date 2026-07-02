#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "library" / "papers"
TEXT_DIR = ROOT / "library" / "text"


def extract_pages_with_pymupdf(pdf: Path) -> list[tuple[int, str]] | None:
    try:
        import fitz  # type: ignore
    except Exception:
        return None
    doc = fitz.open(pdf)
    try:
        return [(index + 1, page.get_text() or "") for index, page in enumerate(doc)]
    finally:
        doc.close()


def extract_pages_with_pdfplumber(pdf: Path) -> list[tuple[int, str]] | None:
    try:
        import pdfplumber  # type: ignore
    except Exception:
        return None
    pages = []
    with pdfplumber.open(pdf) as doc:
        for index, page in enumerate(doc.pages, start=1):
            pages.append((index, page.extract_text() or ""))
    return pages


def extract_pages_with_pypdf(pdf: Path) -> list[tuple[int, str]] | None:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return None
    reader = PdfReader(str(pdf))
    return [(index + 1, page.extract_text() or "") for index, page in enumerate(reader.pages)]


def extract_pages_with_pdftotext(pdf: Path) -> list[tuple[int, str]] | None:
    exe = shutil.which("pdftotext")
    if not exe:
        return None
    result = subprocess.run(
        [exe, "-layout", str(pdf), "-"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    chunks = result.stdout.split("\f")
    return [(index, text) for index, text in enumerate(chunks, start=1) if text.strip()]


def check_pdf_header(pdf: Path) -> None:
    header = pdf.read_bytes()[:16]
    if not header.startswith(b"%PDF-"):
        if header.startswith(b"KDH "):
            raise RuntimeError(
                f"{pdf} is a true CNKI CAJ/KDH file, not a PDF. "
                "Run `make caj-convert PROJECT=<slug> CITEKEY=<citekey> RUN_READER=1 UPDATE=1` first."
            )
        raise RuntimeError(f"{pdf} does not look like a PDF file.")


def non_empty_pages(pages: Iterable[tuple[int, str]]) -> list[tuple[int, str]]:
    return [(page, text) for page, text in pages if text and text.strip()]


def extract_pages(pdf: Path) -> list[tuple[int, str]]:
    check_pdf_header(pdf)
    for method in (
        extract_pages_with_pymupdf,
        extract_pages_with_pdfplumber,
        extract_pages_with_pypdf,
        extract_pages_with_pdftotext,
    ):
        pages = method(pdf)
        if pages:
            clean_pages = non_empty_pages(pages)
            if clean_pages:
                return clean_pages
    raise RuntimeError("No PDF extraction backend available. Install pymupdf, pdfplumber, pypdf, or poppler.")


def extract(pdf: Path) -> str:
    return "\n\n".join(text for _page, text in extract_pages(pdf))


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract text from PDFs.")
    parser.add_argument("--pdf-dir", type=Path, default=PDF_DIR)
    parser.add_argument("--output-dir", type=Path, default=TEXT_DIR)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(args.pdf_dir.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {args.pdf_dir}")
        return 0

    failed = 0
    for pdf in pdfs:
        dest = args.output_dir / f"{pdf.stem}.txt"
        if dest.exists() and not args.overwrite:
            print(f"[SKIP] {dest.name}")
            continue
        try:
            text = extract(pdf)
            dest.write_text(text, encoding="utf-8", errors="replace")
            print(f"[OK] {pdf.name} -> {dest.name}")
        except Exception as exc:
            print(f"[FAIL] {pdf.name}: {exc}")
            failed += 1
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
