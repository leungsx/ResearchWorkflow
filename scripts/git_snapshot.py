#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

RISKY_SUFFIXES = {
    ".pdf",
    ".caj",
    ".kdh",
    ".zip",
    ".docx",
    ".xlsx",
    ".xls",
    ".pptx",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".mp4",
    ".mov",
}


def run(cmd: list[str], *, check: bool = True, capture: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        check=check,
    )


def in_git_repo() -> bool:
    result = run(["git", "rev-parse", "--is-inside-work-tree"], check=False)
    return result.returncode == 0 and result.stdout.strip() == "true"


def git_init_if_needed() -> None:
    if in_git_repo():
        return
    result = run(["git", "init", "-b", "main"], check=False)
    if result.returncode != 0:
        run(["git", "init"], capture=False)
        run(["git", "branch", "-M", "main"], capture=False)
    print("Initialized local Git repository.")


def is_ignored(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    result = run(["git", "check-ignore", "-q", "--", rel], check=False, capture=False)
    return result.returncode == 0


def guard_risky_unignored_files(max_file_mb: int, allow_risky: bool) -> None:
    risky: list[str] = []
    max_bytes = max_file_mb * 1024 * 1024
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if is_ignored(path):
            continue
        rel = path.relative_to(ROOT).as_posix()
        suffix = path.suffix.lower()
        size = path.stat().st_size
        if suffix in RISKY_SUFFIXES or size > max_bytes:
            risky.append(f"{rel} ({size / 1024 / 1024:.2f} MB)")
    if risky and not allow_risky:
        sample = "\n".join(f"- {item}" for item in risky[:30])
        raise SystemExit(
            "Refusing to snapshot because risky unignored files would enter Git:\n"
            f"{sample}\n"
            "Update .gitignore or rerun with --allow-risky if this is intentional."
        )


def guard_embedded_repositories() -> None:
    embedded: list[str] = []
    for git_dir in ROOT.rglob(".git"):
        if git_dir == ROOT / ".git":
            continue
        parent = git_dir.parent
        if not is_ignored(parent):
            embedded.append(parent.relative_to(ROOT).as_posix())
    if embedded:
        sample = "\n".join(f"- {item}" for item in embedded[:20])
        raise SystemExit(
            "Refusing to snapshot embedded Git repositories that are not ignored:\n"
            f"{sample}\n"
            "Add them to .gitignore or convert them to intentional submodules."
        )


def current_branch() -> str:
    result = run(["git", "branch", "--show-current"], check=False)
    branch = result.stdout.strip()
    return branch or "main"


def has_remote(name: str) -> bool:
    result = run(["git", "remote", "get-url", name], check=False)
    return result.returncode == 0 and bool(result.stdout.strip())


def changed_paths() -> list[str]:
    result = run(["git", "status", "--porcelain"])
    return [line for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a safe Git snapshot for ResearchWorkflow text assets.")
    parser.add_argument("--date", help="YYYY-MM-DD; defaults to today")
    parser.add_argument("--note", default="", help="Commit message note.")
    parser.add_argument("--push", action="store_true", help="Push to origin after committing.")
    parser.add_argument("--init", action="store_true", help="Initialize the repository if needed.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be committed without staging or committing.")
    parser.add_argument("--allow-empty", action="store_true", help="Create a commit even when there are no changes.")
    parser.add_argument("--allow-risky", action="store_true", help="Allow large/binary files that are not ignored.")
    parser.add_argument("--max-file-mb", type=int, default=8, help="Abort if an unignored file is larger than this.")
    args = parser.parse_args()

    day = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    if args.init:
        git_init_if_needed()
    if not in_git_repo():
        raise SystemExit("Not a Git repository. Run `git init -b main` or rerun with --init.")

    guard_risky_unignored_files(args.max_file_mb, args.allow_risky)
    guard_embedded_repositories()

    if args.dry_run:
        changes = changed_paths()
        print(f"Dry run: {len(changes)} changed paths would be considered by Git.")
        for line in changes[:80]:
            print(line)
        return 0

    run(["git", "add", "-A", "--", "."], capture=False)
    changes = changed_paths()
    if not changes and not args.allow_empty:
        print("No Git changes to snapshot.")
    else:
        message = f"workflow snapshot {day.isoformat()}"
        if args.note:
            message += f"\n\n{args.note}"
        commit_cmd = ["git", "commit", "-m", message]
        if args.allow_empty:
            commit_cmd.insert(2, "--allow-empty")
        run(commit_cmd, capture=False)

    if args.push:
        if not has_remote("origin"):
            raise SystemExit("No origin remote configured; create or add a remote before pushing.")
        branch = current_branch()
        run(["git", "push", "-u", "origin", branch], capture=False)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
