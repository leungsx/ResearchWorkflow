#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from workflow_config import active_project_slug


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class MenuItem:
    number: int
    title: str
    when: str
    open_path: str
    command: str


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def menu_items(project: str) -> list[MenuItem]:
    project_root = ROOT / "projects" / project
    review_state = read_json(ROOT / "vault" / "14_Review_Queue" / "review_state.json")
    due_count = review_state.get("summary", {}).get("due_count", 0) if isinstance(review_state, dict) else 0
    return [
        MenuItem(1, "今天该做什么", "先看今日主任务和候选任务。", "study_dashboard.html", "make daily"),
        MenuItem(2, f"处理到期复习（{due_count} 项）", "有到期知识卡时优先主动回忆。", "knowledge_cards/review_today.html", "make review-server-ensure"),
        MenuItem(3, "开始今日精读", "需要继续论文阅读和知识卡沉淀时。", "paper_reading/today.html", "make learning-dashboard"),
        MenuItem(4, "分拣 incoming PDF", "新下载文献进入 incoming 后。", rel(project_root / "literature" / "incoming_pdf_triage.html"), f"make incoming-triage PROJECT={project}"),
        MenuItem(5, "核验证据页码", "写作证据缺页码或需要人工核页时。", rel(project_root / "evidence" / "page_verification_queue.html"), f"make manuscript-panel PROJECT={project}"),
        MenuItem(6, "推进论文写作", "需要把已读文献转成问题、变量和段落时。", rel(project_root / "manuscript" / "writing_panel.html"), f"make manuscript-panel PROJECT={project}"),
        MenuItem(7, "日常轻量刷新", "刷新状态、页面和只读审计。", "study_dashboard.html", "make daily"),
        MenuItem(8, "系统体检", "改页面、改脚本或提交前检查。", "workflow_health.html", "make workflow-audit-readonly"),
    ]


def render_menu(items: list[MenuItem], project: str) -> str:
    lines = [
        "ResearchWorkflow 简易菜单",
        f"当前项目: {project}",
        "",
        "用法:",
        "  python scripts/rw.py",
        "  python scripts/rw.py --command 5",
        "",
    ]
    for item in items:
        lines.extend(
            [
                f"{item.number}. {item.title}",
                f"   适用: {item.when}",
                f"   打开: {item.open_path}",
                f"   命令: {item.command}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Print the task-first ResearchWorkflow menu.")
    parser.add_argument("--project", default=active_project_slug())
    parser.add_argument("--command", type=int, help="Print only the command for the selected menu item.")
    args = parser.parse_args()

    items = menu_items(args.project)
    if args.command is not None:
        for item in items:
            if item.number == args.command:
                print(item.command)
                return 0
        raise SystemExit(f"Unknown menu item: {args.command}")
    print(render_menu(items, args.project), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
