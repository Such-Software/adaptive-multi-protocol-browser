from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {".git", "__pycache__", "generated", "private"}
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def main() -> int:
    failures: list[str] = []
    for path in _markdown_files():
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT)
        if not _has_status_header(text):
            failures.append(f"{rel}: missing status header in first six lines")
        failures.extend(_broken_links(path, text))
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print("AMPBROWSER_DOCS_CHECK status=ok")
    return 0


def _markdown_files() -> list[Path]:
    paths: list[Path] = []
    for path in ROOT.rglob("*.md"):
        rel_parts = set(path.relative_to(ROOT).parts)
        if rel_parts & IGNORED_PARTS:
            continue
        paths.append(path)
    return sorted(paths)


def _has_status_header(text: str) -> bool:
    return any(line.startswith("> Status:") for line in text.splitlines()[:6])


def _broken_links(path: Path, text: str) -> list[str]:
    failures: list[str] = []
    for match in LINK_RE.finditer(text):
        target = match.group(1)
        if _is_external_or_anchor(target):
            continue
        target_path = (path.parent / target.split("#", 1)[0]).resolve()
        try:
            target_path.relative_to(ROOT)
        except ValueError:
            failures.append(f"{path.relative_to(ROOT)}: link escapes repo: {target}")
            continue
        if not target_path.exists():
            failures.append(f"{path.relative_to(ROOT)}: broken link: {target}")
    return failures


def _is_external_or_anchor(target: str) -> bool:
    return (
        target.startswith("#")
        or "://" in target
        or target.startswith("mailto:")
        or target.startswith("tel:")
    )


if __name__ == "__main__":
    raise SystemExit(main())
