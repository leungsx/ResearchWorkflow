#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
from dataclasses import dataclass, field


@dataclass
class CommandCheck:
    name: str
    command: str
    purpose: str
    candidates: list[str] = field(default_factory=list)
    check_version: bool = True


COMMANDS = [
    CommandCheck("Python", sys.executable, "Current Python interpreter"),
    CommandCheck("R", "Rscript", "R statistics and figures"),
    CommandCheck("MATLAB", "matlab", "MATLAB simulation and toolboxes"),
    CommandCheck("Pandoc", "pandoc", "Markdown to DOCX/LaTeX"),
    CommandCheck("Tectonic", "tectonic", "LaTeX to PDF"),
    CommandCheck("MuPDF", "mutool", "CAJ/PDF conversion support"),
    CommandCheck(
        "caj2pdf",
        "caj2pdf",
        "CNKI CAJ/KDH to PDF converter",
        candidates=[str(Path(__file__).resolve().parents[1] / "tools" / "caj2pdf" / "caj2pdf")],
        check_version=False,
    ),
    CommandCheck(
        "Gephi",
        "gephi",
        "Network visualization GUI",
        candidates=["/Applications/Gephi.app/Contents/MacOS/gephi"],
        check_version=False,
    ),
    CommandCheck(
        "Typora",
        "typora",
        "Markdown preview and editing GUI",
        candidates=["/Applications/Typora.app", str(Path.home() / "Applications" / "Typora.app")],
        check_version=False,
    ),
]

PYTHON_PACKAGES = [
    ("pandas", "tables and data frames"),
    ("numpy", "numerical computing"),
    ("scipy", "scientific computing"),
    ("statsmodels", "statistical models"),
    ("matplotlib", "figures"),
    ("seaborn", "statistical figures"),
    ("networkx", "network analysis"),
    ("openpyxl", "Excel .xlsx import for CNKI exports"),
    ("fitz", "PDF text extraction via PyMuPDF"),
    ("pdfplumber", "PDF text/table extraction"),
    ("pypdf", "PDF fallback extraction"),
]


def command_version(path: str) -> str:
    candidates = [
        [path, "--version"],
        [path, "-version"],
        [path, "-v"],
    ]
    for cmd in candidates:
        try:
            result = subprocess.run(
                cmd,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=5,
            )
        except Exception:
            continue
        line = (result.stdout or "").splitlines()
        if line:
            return line[0][:120]
    return "version unknown"


def resolve_command(item: CommandCheck) -> str | None:
    path = shutil.which(item.command)
    if path:
        return path
    for candidate in item.candidates:
        if Path(candidate).exists():
            return candidate
    return None


def main() -> int:
    print(f"Current Python executable: {sys.executable}\n")
    print("== Command checks ==")
    missing = []
    for item in COMMANDS:
        path = resolve_command(item)
        if path:
            version = command_version(path) if item.check_version else "installed"
            print(f"[OK]   {item.name:<8} {path} ({version})")
        else:
            print(f"[MISS] {item.name:<8} not found in PATH - {item.purpose}")
            missing.append(item.name)

    print("\n== Python package checks ==")
    pkg_missing = []
    for module, purpose in PYTHON_PACKAGES:
        if importlib.util.find_spec(module):
            print(f"[OK]   {module:<12} {purpose}")
        else:
            print(f"[MISS] {module:<12} {purpose}")
            pkg_missing.append(module)

    print("\n== Summary ==")
    if missing:
        print("Missing commands:", ", ".join(missing))
    else:
        print("All expected commands are available.")
    if pkg_missing:
        print("Missing Python packages can be installed with:")
        print(f"{sys.executable} -m pip install -r requirements.txt")
    else:
        print("All checked Python packages are importable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
