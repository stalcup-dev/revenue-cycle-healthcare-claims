#!/usr/bin/env python3
"""Docs audit gate: canonical checks by default, optional full-repo reporting."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"
ALL_MD_FILES = [README] + sorted((REPO_ROOT / "docs").rglob("*.md"))

CANONICAL_DOC_HINTS = [
    REPO_ROOT / "docs" / "CASE_STUDY_ONE_PAGER.md",
    REPO_ROOT / "docs" / "HIRING_SHOWCASE_BRIEF.md",
    REPO_ROOT / "docs" / "INTERVIEW_WALKTHROUGH_90S.md",
    REPO_ROOT / "docs" / "DECISION_STANDARD.md",
    REPO_ROOT / "docs" / "executive_summary.md",
    REPO_ROOT / "docs" / "decision_memo_latest_complete_week.md",
    REPO_ROOT / "docs" / "QUEUE_VOLUME_SHIFT_PLAYBOOK_1PAGE.md",
    REPO_ROOT / "docs" / "DATA_CONTRACT_QUEUE_BRIEF.md",
    REPO_ROOT / "docs" / "QA_CHECKLIST_QUEUE_BRIEF.md",
    REPO_ROOT / "docs" / "story" / "README.md",
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

PLAIN_PATH_ENFORCED_DOCS = [
    README,
    REPO_ROOT / "docs" / "HIRING_SHOWCASE_BRIEF.md",
    REPO_ROOT / "docs" / "story" / "README.md",
]

REQUIRED_README_SECTIONS = {
    "Start Here (Hiring Manager, 2 minutes)",
    "Operator Deep Dive (Queue Volume Shift)",
}

MD_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
PLAIN_PATH_PATTERN = re.compile(
    r"\b(?:docs|notebooks|scripts|portfolio)/[A-Za-z0-9_./\-]+\.(?:md|png|ipynb|pdf|ps1|sql)\b"
)
CODE_BLOCK_PATTERN = re.compile(r"```.*?```", re.DOTALL)


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def local_link_target(raw_target: str) -> str:
    target = raw_target.strip()
    if not target:
        return ""
    if target.startswith("#") or target.startswith("http://") or target.startswith("https://"):
        return ""
    return target.split("#", 1)[0].split("?", 1)[0].strip()


def parse_readme_required_links() -> list[Path]:
    required: list[Path] = []
    text = load_text(README)
    current_section = ""

    for line in text.splitlines():
        if line.startswith("## "):
            current_section = line[3:].strip()
            continue
        if current_section not in REQUIRED_README_SECTIONS:
            continue
        for raw_target in MD_LINK_PATTERN.findall(line):
            target = local_link_target(raw_target)
            if not target:
                continue
            required.append((README.parent / target).resolve())

    # Deduplicate while preserving order
    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in required:
        if path in seen:
            continue
        seen.add(path)
        deduped.append(path)
    return deduped


def build_canonical_md_set(required_links: list[Path]) -> list[Path]:
    docs: list[Path] = [README]

    for path in CANONICAL_DOC_HINTS:
        if path.exists():
            docs.append(path)

    for path in required_links:
        if path.suffix.lower() == ".md" and path.exists():
            docs.append(path)

    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in docs:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        deduped.append(resolved)
    return sorted(deduped)


def check_missing_required_links(required_links: list[Path]) -> list[str]:
    missing: list[str] = []
    for path in required_links:
        if not path.exists():
            missing.append(rel(path))
    return missing


def check_broken_links(files: list[Path]) -> list[tuple[str, str]]:
    broken: list[tuple[str, str]] = []
    for md in files:
        text = load_text(md)
        for target in MD_LINK_PATTERN.findall(text):
            path_part = local_link_target(target)
            if not path_part:
                continue
            resolved = (md.parent / path_part).resolve()
            if not resolved.exists():
                broken.append((rel(md), target))
    return broken


def check_forbidden_phrases(files: list[Path]) -> list[tuple[str, int, str]]:
    hits: list[tuple[str, int, str]] = []
    for md in files:
        text = load_text(md)
        for pat in FORBIDDEN_PATTERNS:
            for match in pat.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                hits.append((rel(md), line, match.group(0)))
    return hits


def check_plain_path_refs(files: list[Path]) -> list[tuple[str, int, str]]:
    findings: list[tuple[str, int, str]] = []
    for md in files:
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


def print_section(title: str, rows: list[str]) -> None:
    if not rows:
        return
    print(f"\n{title}")
    for row in rows:
        print(f"- {row}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit canonical docs and optionally report legacy debt.")
    parser.add_argument("--all", action="store_true", help="Report findings for all markdown docs.")
    parser.add_argument(
        "--all-strict",
        action="store_true",
        help="When used with --all, fail on all-doc findings (not only canonical findings).",
    )
    args = parser.parse_args()

    required_links = parse_readme_required_links()
    canonical_docs = build_canonical_md_set(required_links)

    missing_required = check_missing_required_links(required_links)
    broken = check_broken_links(canonical_docs)
    forbidden = check_forbidden_phrases(canonical_docs)
    plain_docs = [p for p in PLAIN_PATH_ENFORCED_DOCS if p.exists()]
    plain_refs = check_plain_path_refs(plain_docs)
    reason_dups = check_reason_duplication()

    print("DOCS_AUDIT_REPORT")
    print(f"broken_links={len(broken) + len(missing_required)}")
    print(f"forbidden_hits={len(forbidden)}")
    print(f"plain_path_refs={len(plain_refs)}")
    print(f"reason_dup_hits={len(reason_dups)}")

    print_section("MISSING_README_LINK_TARGETS", missing_required)
    print_section("BROKEN_LINKS", [f"{f} -> {t}" for f, t in broken])
    print_section("FORBIDDEN_PHRASES", [f"{f}:{line} -> {text}" for f, line, text in forbidden])
    print_section("PLAIN_PATH_REFS", [f"{f}:{line} -> {text}" for f, line, text in plain_refs])
    print_section("REASON_DUPLICATION", [f"{f} -> Reason: appears {count} times (max 1)" for f, count in reason_dups])

    canonical_failed = bool(missing_required or broken or forbidden or plain_refs or reason_dups)

    all_failed = False
    if args.all:
        all_broken = check_broken_links(ALL_MD_FILES)
        all_forbidden = check_forbidden_phrases(ALL_MD_FILES)
        all_plain = check_plain_path_refs(ALL_MD_FILES)

        print("\nALL_DOCS_REPORT")
        print(f"all_broken_links={len(all_broken)}")
        print(f"all_forbidden_hits={len(all_forbidden)}")
        print(f"all_plain_path_refs={len(all_plain)}")

        # Show only a manageable preview for legacy debt reporting.
        print_section(
            "ALL_BROKEN_LINKS_SAMPLE",
            [f"{f} -> {t}" for f, t in all_broken[:20]],
        )
        print_section(
            "ALL_FORBIDDEN_PHRASES_SAMPLE",
            [f"{f}:{line} -> {text}" for f, line, text in all_forbidden[:20]],
        )
        print_section(
            "ALL_PLAIN_PATH_REFS_SAMPLE",
            [f"{f}:{line} -> {text}" for f, line, text in all_plain[:20]],
        )

        all_failed = bool(all_broken or all_forbidden or all_plain)

    if args.all and args.all_strict:
        return 1 if (canonical_failed or all_failed) else 0

    return 1 if canonical_failed else 0


if __name__ == "__main__":
    sys.exit(main())
