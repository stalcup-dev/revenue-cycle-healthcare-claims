#!/usr/bin/env python3
"""Docs audit gate: canonical checks by default, optional all-doc reporting."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
README_PATH = REPO_ROOT / "README.md"
ALL_MD_FILES = [README_PATH] + sorted((REPO_ROOT / "docs").rglob("*.md"))

CANONICAL_ALLOWLIST = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "docs" / "START_HERE.md",
    REPO_ROOT / "docs" / "CASE_STUDY_ONE_PAGER.md",
    REPO_ROOT / "docs" / "INTERVIEW_WALKTHROUGH_90S.md",
    REPO_ROOT / "docs" / "DECISION_STANDARD.md",
    REPO_ROOT / "docs" / "executive_summary.md",
    REPO_ROOT / "docs" / "decision_memo_latest_complete_week.md",
    REPO_ROOT / "docs" / "story" / "README.md",
    REPO_ROOT / "docs" / "story" / "nb03_exec_overview.md",
    REPO_ROOT / "docs" / "story" / "nb04_driver_pareto.md",
    REPO_ROOT / "docs" / "story" / "nb05_workqueue.md",
]

README_REQUIRED_SECTIONS = {
    "Start Here (Hiring Manager, 2 minutes)",
    "Operator Deep Dive (Queue Volume Shift)",
}

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
    REPO_ROOT / "README.md",
    REPO_ROOT / "docs" / "START_HERE.md",
    REPO_ROOT / "docs" / "story" / "README.md",
]

MD_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
PLAIN_PATH_PATTERN = re.compile(
    r"\b(?:docs|notebooks|scripts|portfolio)/[A-Za-z0-9_./\-]+\.(?:md|png|ipynb|pdf|ps1|sql)\b"
)
CODE_BLOCK_PATTERN = re.compile(r"```.*?```", re.DOTALL)


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT.resolve())).replace("\\", "/")


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def normalize_local_target(target: str) -> str:
    cleaned = target.strip()
    if not cleaned:
        return ""
    if cleaned.startswith("#"):
        return ""
    if cleaned.startswith("http://") or cleaned.startswith("https://"):
        return ""
    return cleaned.split("#", 1)[0].split("?", 1)[0].strip()


def parse_readme_required_local_links() -> list[Path]:
    text = load_text(README_PATH)
    current_section = ""
    required: list[Path] = []

    for line in text.splitlines():
        if line.startswith("## "):
            current_section = line[3:].strip()
            continue
        if current_section not in README_REQUIRED_SECTIONS:
            continue
        for raw_target in MD_LINK_PATTERN.findall(line):
            local_target = normalize_local_target(raw_target)
            if not local_target:
                continue
            required.append((README_PATH.parent / local_target).resolve())

    seen: set[Path] = set()
    ordered: list[Path] = []
    for item in required:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def build_canonical_docs(readme_md_targets: list[Path]) -> list[Path]:
    docs: list[Path] = [README_PATH.resolve()]

    for path in CANONICAL_ALLOWLIST:
        if path.exists():
            docs.append(path.resolve())

    for path in readme_md_targets:
        if path.exists() and path.suffix.lower() == ".md":
            docs.append(path.resolve())

    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in docs:
        if path in seen:
            continue
        seen.add(path)
        deduped.append(path)
    return sorted(deduped)


def check_missing_readme_targets(required_targets: list[Path]) -> list[str]:
    missing: list[str] = []
    for path in required_targets:
        if not path.exists():
            missing.append(rel(path))
    return missing


def check_broken_links(md_files: list[Path]) -> list[tuple[str, str]]:
    broken: list[tuple[str, str]] = []
    for md in md_files:
        text = load_text(md)
        for raw_target in MD_LINK_PATTERN.findall(text):
            local_target = normalize_local_target(raw_target)
            if not local_target:
                continue
            resolved = (md.parent / local_target).resolve()
            if not resolved.exists():
                broken.append((rel(md), raw_target))
    return broken


def check_forbidden_phrases(md_files: list[Path]) -> list[tuple[str, int, str]]:
    hits: list[tuple[str, int, str]] = []
    for md in md_files:
        text = load_text(md)
        for pat in FORBIDDEN_PATTERNS:
            for match in pat.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                hits.append((rel(md), line, match.group(0)))
    return hits


def check_plain_path_refs(md_files: list[Path]) -> list[tuple[str, int, str]]:
    findings: list[tuple[str, int, str]] = []
    for md in md_files:
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


def print_section(title: str, lines: list[str]) -> None:
    if not lines:
        return
    print(f"\n{title}")
    for line in lines:
        print(f"- {line}")


def evaluate_scope(scope_files: list[Path], missing_readme_targets: list[str], include_reason_dup: bool) -> dict[str, list]:
    plain_scope = [p for p in PLAIN_PATH_ENFORCED_DOCS if p.exists() and p in scope_files]
    return {
        "missing_required": missing_readme_targets,
        "broken": check_broken_links(scope_files),
        "forbidden": check_forbidden_phrases(scope_files),
        "plain_refs": check_plain_path_refs(plain_scope),
        "reason_dups": check_reason_duplication() if include_reason_dup else [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit docs quality gates.")
    parser.add_argument("--all", action="store_true", help="Scan all docs for informational reporting.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="When used with --all, fail if all-doc findings exist.",
    )
    args = parser.parse_args()

    readme_required_targets = parse_readme_required_local_links()
    readme_md_targets = [p for p in readme_required_targets if p.suffix.lower() == ".md"]
    canonical_files = build_canonical_docs(readme_md_targets)
    missing_readme_targets = check_missing_readme_targets(readme_required_targets)

    canonical = evaluate_scope(canonical_files, missing_readme_targets, include_reason_dup=False)

    print("DOCS_AUDIT_REPORT")
    print(f"broken_links={len(canonical['missing_required']) + len(canonical['broken'])}")
    print(f"forbidden_hits={len(canonical['forbidden'])}")
    print(f"plain_path_refs={len(canonical['plain_refs'])}")
    print(f"reason_dup_hits={len(canonical['reason_dups'])}")

    print_section("MISSING_README_LINK_TARGETS", canonical["missing_required"])
    print_section("BROKEN_LINKS", [f"{f} -> {target}" for f, target in canonical["broken"]])
    print_section(
        "FORBIDDEN_PHRASES",
        [f"{f}:{line} -> {text}" for f, line, text in canonical["forbidden"]],
    )
    print_section(
        "PLAIN_PATH_REFS",
        [f"{f}:{line} -> {text}" for f, line, text in canonical["plain_refs"]],
    )
    print_section(
        "REASON_DUPLICATION",
        [f"{f} -> Reason: appears {count} times (max 1)" for f, count in canonical["reason_dups"]],
    )

    canonical_failed = any(
        [
            canonical["missing_required"],
            canonical["broken"],
            canonical["forbidden"],
            canonical["plain_refs"],
            canonical["reason_dups"],
        ]
    )

    if args.all:
        all_scope = evaluate_scope(ALL_MD_FILES, [], include_reason_dup=True)
        print("\nALL_DOCS_REPORT")
        print(f"all_broken_links={len(all_scope['broken'])}")
        print(f"all_forbidden_hits={len(all_scope['forbidden'])}")
        print(f"all_plain_path_refs={len(all_scope['plain_refs'])}")
        print(f"all_reason_dup_hits={len(all_scope['reason_dups'])}")

        print_section(
            "ALL_BROKEN_LINKS_SAMPLE",
            [f"{f} -> {target}" for f, target in all_scope["broken"][:20]],
        )
        print_section(
            "ALL_FORBIDDEN_PHRASES_SAMPLE",
            [f"{f}:{line} -> {text}" for f, line, text in all_scope["forbidden"][:20]],
        )
        print_section(
            "ALL_PLAIN_PATH_REFS_SAMPLE",
            [f"{f}:{line} -> {text}" for f, line, text in all_scope["plain_refs"][:20]],
        )
        print_section(
            "ALL_REASON_DUPLICATION_SAMPLE",
            [f"{f} -> Reason: appears {count} times (max 1)" for f, count in all_scope["reason_dups"][:20]],
        )

        all_failed = any(
            [
                all_scope["broken"],
                all_scope["forbidden"],
                all_scope["plain_refs"],
                all_scope["reason_dups"],
            ]
        )

        if args.strict:
            return 1 if (canonical_failed or all_failed) else 0
        return 0

    return 1 if canonical_failed else 0


if __name__ == "__main__":
    sys.exit(main())
