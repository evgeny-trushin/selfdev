#!/usr/bin/env python3
"""Rename legacy selfdev folders and rewrite their internal path references."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


LEGACY_TODO_DIRNAMES = ("requirements", "requirments")
LEGACY_HOW_DIRNAMES = ("principles",)
TODO_DIRNAME = "todo"
HOW_DIRNAME = "how"

TEXT_REPLACEMENTS = (
    ("../requirements/", "../todo/"),
    ("../requirments/", "../todo/"),
    ("../principles/", "../how/"),
    ("./requirements/", "./todo/"),
    ("./requirments/", "./todo/"),
    ("./principles/", "./how/"),
    ("/requirements/", "/todo/"),
    ("/requirments/", "/todo/"),
    ("/principles/", "/how/"),
    ("requirements/", "todo/"),
    ("requirments/", "todo/"),
    ("principles/", "how/"),
    ("`requirements`", "`todo`"),
    ("`requirments`", "`todo`"),
    ("`principles`", "`how`"),
    ("'requirements'", "'todo'"),
    ("'requirments'", "'todo'"),
    ("'principles'", "'how'"),
    ('"requirements"', '"todo"'),
    ('"requirments"', '"todo"'),
    ('"principles"', '"how"'),
)


class MigrationError(RuntimeError):
    """Raised when migration cannot proceed safely."""


@dataclass
class MigrationReport:
    renamed: list[tuple[str, str]] = field(default_factory=list)
    updated_files: list[Path] = field(default_factory=list)
    skipped_files: list[Path] = field(default_factory=list)


def rewrite_text(text: str) -> str:
    """Rewrite path-like legacy folder references to current folder names."""
    for old, new in TEXT_REPLACEMENTS:
        text = text.replace(old, new)
    return text


def existing_dirs(root: Path, names: Iterable[str]) -> list[Path]:
    return [root / name for name in names if (root / name).is_dir()]


def choose_single_source(root: Path, names: Iterable[str], target_name: str) -> Path | None:
    sources = existing_dirs(root, names)
    if len(sources) > 1:
        formatted = ", ".join(f"{path.name}/" for path in sources)
        raise MigrationError(
            f"Multiple legacy folders match {target_name}/: {formatted}. "
            "Rename one manually before running this migration."
        )
    return sources[0] if sources else None


def rename_legacy_dir(
    root: Path,
    source_names: Iterable[str],
    target_name: str,
    report: MigrationReport,
    dry_run: bool,
) -> Path | None:
    source = choose_single_source(root, source_names, target_name)
    target = root / target_name
    if source is None:
        return target if target.is_dir() else None
    if target.exists():
        raise MigrationError(f"Refusing to overwrite existing target directory: {target}")
    if not dry_run:
        source.rename(target)
    report.renamed.append((source.name, target.name))
    return target


def iter_text_candidates(root: Path) -> Iterable[Path]:
    for dirname in (TODO_DIRNAME, HOW_DIRNAME):
        directory = root / dirname
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*")):
            if path.is_file():
                yield path


def update_internal_references(root: Path, report: MigrationReport, dry_run: bool) -> None:
    for path in iter_text_candidates(root):
        try:
            before = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            report.skipped_files.append(path)
            continue
        after = rewrite_text(before)
        if after == before:
            continue
        if not dry_run:
            path.write_text(after, encoding="utf-8")
        report.updated_files.append(path)


def migrate(root: Path, dry_run: bool = False) -> MigrationReport:
    root = root.resolve()
    if not root.is_dir():
        raise MigrationError(f"Root directory does not exist: {root}")

    report = MigrationReport()
    rename_legacy_dir(root, LEGACY_TODO_DIRNAMES, TODO_DIRNAME, report, dry_run)
    rename_legacy_dir(root, LEGACY_HOW_DIRNAMES, HOW_DIRNAME, report, dry_run)
    update_internal_references(root, report, dry_run)
    return report


def print_report(report: MigrationReport, root: Path, dry_run: bool) -> None:
    prefix = "Would rename" if dry_run else "Renamed"
    if report.renamed:
        for old, new in report.renamed:
            print(f"{prefix} {old}/ -> {new}/")
    else:
        print("No legacy folders found")

    update_prefix = "Would update" if dry_run else "Updated"
    if report.updated_files:
        for path in report.updated_files:
            print(f"{update_prefix} path references in {path.relative_to(root)}")
    else:
        print("No stale path references found")

    if report.skipped_files:
        for path in report.skipped_files:
            print(f"Skipped non-UTF-8 file {path.relative_to(root)}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rename requirements/ or requirments/ to todo/, rename principles/ "
            "to how/, and update path references inside todo/ and how/."
        )
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Project root to migrate. Defaults to the current directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned changes without renaming folders or writing files.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = Path(args.root).resolve()
    try:
        report = migrate(root, dry_run=args.dry_run)
    except MigrationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print_report(report, root, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
