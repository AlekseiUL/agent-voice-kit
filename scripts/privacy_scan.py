#!/usr/bin/env python3
"""Fail CI on common credential material, private keys and absolute home paths."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", ".venv", "dist", "build", "__pycache__", ".pytest_cache"}
TEXT_SUFFIXES = {".py", ".md", ".toml", ".yaml", ".yml", ".json", ".txt"}
PATTERNS = {
    "absolute macOS home path": re.compile(r"/Users/[A-Za-z0-9._-]+/"),
    "absolute Linux home path": re.compile(r"/home/[A-Za-z0-9._-]+/"),
    "private key header": re.compile("BEGIN " + "(?:RSA |EC |OPENSSH )?PRIVATE KEY"),
    "GitHub token": re.compile("gh" + r"[opsu]_[A-Za-z0-9]{20,}"),
    "generic secret assignment": re.compile(r"(?i)(?:api[_-]?key|secret|password|token)\s*[=:]\s*['\"][^'\"]{8,}['\"]"),
}


def main() -> int:
    findings = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES or any(part in SKIP for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                findings.append(f"{path.relative_to(ROOT)}:{text.count(chr(10), 0, match.start()) + 1}: {label}")
    if findings:
        print("\n".join(findings))
        return 1
    print("privacy scan: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
