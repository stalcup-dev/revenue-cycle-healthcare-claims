#!/usr/bin/env python3
"""Docs audit gate: broken links, forbidden phrases, and plain path references."""

from __future__ import annotations

import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

ALL_MD_FILES = [REPO_ROOT / "README.md"] + sorted((REPO_ROOT / "docs").rglob("*.md"))

CANONICAL_DOCS = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "docs" / "CASE_STUDY_ONE_PAGER.md",
    REPO_ROOT / "docs" / "INTERVIEW_WALKTHROUGH_90S.md",
    REPO_ROOT / "docs" / "DECISION_STANDARD.md",
    REPO_ROOT / "docs" / "executive_summary.md",
    REPO_ROOT / "docs" / "decision_memo_latest_complete_week.md",
    REPO_ROOT / "docs" / "QUEUE_VOLUME_SHIFT_PLAYBOOK_1PAGE.md",
    REPO_ROOT / "docs" / "DATA_CONTRACT_QUEUE_BRIEF.md",
    REPO_ROOT / "docs" / "QA_CHECKLIST_QUEUE_BRIEF.md",
    REPO_ROOT / "docs" / "story" / "README.md",
    REPO_ROOT / "docs" / "story" / "nb03_exec_overview.md",
    REPO_ROOT / "docs" / "story" / "nb04_driver_pareto.md",
    REPO_ROOT / "docs" / "story" / "nb05_workqueue.md",
]

FORBIDDEN_PATTERNS = [
    re.compile(r"\b52[\s-]*week(s)?\b", re.IGNORECASE),
    re.compile(r"\bhistory\s*<\s*52\b", re.IGNORECASE),
    re.compile(r"\bcapacity index\b", re.IGNORECASE),
    re.compile(r"Status:\*\*\s*ARCHIVE", re.IGNORECASE),
    re.compile(r"ARCHIVE\s*\(reference-only\)", re.IGNORECASE),
]

REASON_DUP_DOCS = [
    REPO_ROOT / "docs" / "decision_memo_latest_complete_week.md",
    REPO_ROOT / "docs" / "executive_summary.md",
]

MD_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
PLAIN_PATH_PATTERN = re.compile(
    r"\b(?:docs|notebooks|scripts|portfolio)/[A-Za-z0-9_./\-]+\.(?:md|png|ipynb|pdf|ps1|sql)\b"
)
CODE_BLOCK_PATTERN = re.compile(r"```.*?```", re.DOTALL)


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def check_broken_links() -> list[tuple[str, str]]:
    broken: list[tuple[str, str]] = []
    for md in ALL_MD_FILES:
        text = load_text(md)
        for target in MD_LINK_PATTERN.findall(text):
            target = target.strip()
            if not target or target.startswith("#"):
                continue
            if target.startswith("http://") or target.startswith("https://"):
                continue
            path_part = target.split("#", 1)[0].split("?", 1)[0].strip()
            if not path_part:
                continue
            resolved = (md.parent / path_part).resolve()
            if not resolved.exists():
                broken.append((rel(md), target))
    return broken


def check_forbidden_phrases() -> list[tuple[str, int, str]]:
    hits: list[tuple[str, int, str]] = []
    for md in CANONICAL_DOCS:
        if not md.exists():
            hits.append((rel(md), 0, "MISSING_CANONICAL_DOC"))
            continue
        text = load_text(md)
        for pat in FORBIDDEN_PATTERNS:
            for match in pat.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                hits.append((rel(md), line, match.group(0)))
    return hits


def check_plain_path_refs() -> list[tuple[str, int, str]]:
    findings: list[tuple[str, int, str]] = []
    for md in CANONICAL_DOCS:
        if not md.exists():
            continue
        text = load_text(md)
        text_wo_code = CODE_BLOCK_PATTERN.sub("", text)
        link_spans = [m.span() for m in MD_LINK_PATTERN.finditer(text_wo_code)]

        for m in PLAIN_PATH_PATTERN.finditer(text_wo_code):
            start, end = m.span()
            if any(start >= a and end <= b for a, b in link_spans):
                continue
            line = text_wo_code.count("\n", 0, start) + 1
            findings.append((rel(md), line, m.group(0)))
    return findings


def check_reason_duplication() -> list[tuple[str, int]]:
    findings: list[tuple[str, int]] = []
    for md in REASON_DUP_DOCS:
        if not md.exists():
            continue
        count = len(re.findall(r"^Reason:", load_text(md), flags=re.MULTILINE))
        if count > 1:
            findings.append((rel(md), count))
    return findings


def main() -> int:
    broken = check_broken_links()
    forbidden = check_forbidden_phrases()
    plain_refs = check_plain_path_refs()
    reason_dups = check_reason_duplication()

    print("DOCS_AUDIT_REPORT")
    print(f"broken_links={len(broken)}")
    print(f"forbidden_hits={len(forbidden)}")
    print(f"plain_path_refs={len(plain_refs)}")
    print(f"reason_dup_hits={len(reason_dups)}")

    if broken:
        print("\nBROKEN_LINKS")
        for file_path, target in broken:
            print(f"- {file_path} -> {target}")

    if forbidden:
        print("\nFORBIDDEN_PHRASES")
        for file_path, line, text in forbidden:
            print(f"- {file_path}:{line} -> {text}")

    if plain_refs:
        print("\nPLAIN_PATH_REFS")
        for file_path, line, text in plain_refs:
            print(f"- {file_path}:{line} -> {text}")

    if reason_dups:
        print("\nREASON_DUPLICATION")
        for file_path, count in reason_dups:
            print(f"- {file_path} -> Reason: appears {count} times (max 1)")

    failed = bool(broken or forbidden or plain_refs or reason_dups)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
