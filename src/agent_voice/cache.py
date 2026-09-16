"""Conservative cache inspection and pruning."""

from __future__ import annotations

import json
import re
import shutil
import time
from pathlib import Path
from typing import Any

from filelock import FileLock, Timeout as LockTimeout

_JOB_ID = re.compile(r"^[0-9a-f]{64}$")


def default_cache() -> Path:
    import os

    base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return base / "agent-voice-kit"


def prune_cache(cache_dir: str | Path | None = None, *, apply: bool = False,
                now: float | None = None) -> dict[str, Any]:
    """Preview or remove only expired, valid, unlocked job directories."""
    root = Path(cache_dir).expanduser() if cache_dir else default_cache()
    timestamp = time.time() if now is None else now
    report: dict[str, Any] = {
        "cache": str(root),
        "apply": apply,
        "candidates": [],
        "removed": [],
        "skipped": [],
    }
    if root.is_symlink():
        raise RuntimeError("refusing to prune a cache root symlink")
    if not root.exists():
        report["success"] = True
        return report
    if not root.is_dir():
        raise RuntimeError("cache path is not a directory")

    for job in sorted(root.iterdir(), key=lambda item: item.name):
        if job.name == ".locks" and job.is_dir() and not job.is_symlink():
            continue
        if job.is_symlink() or not job.is_dir() or not _JOB_ID.fullmatch(job.name):
            report["skipped"].append({"name": job.name, "reason": "unrecognized entry"})
            continue
        manifest_path = job / "manifest.json"
        if manifest_path.is_symlink() or not manifest_path.is_file():
            report["skipped"].append({"name": job.name, "reason": "missing regular manifest"})
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            expires_at = manifest.get("expires_at")
            valid = (
                isinstance(manifest, dict)
                and manifest.get("version") == 1
                and manifest.get("job_id") == job.name
                and isinstance(expires_at, (int, float))
            )
        except (OSError, ValueError, AttributeError):
            valid = False
            expires_at = None
        if not valid:
            report["skipped"].append({"name": job.name, "reason": "invalid manifest"})
            continue
        assert isinstance(expires_at, (int, float))
        if expires_at >= timestamp:
            report["skipped"].append({"name": job.name, "reason": "not expired"})
            continue
        report["candidates"].append(job.name)
        if not apply:
            continue
        try:
            lock_root = root / ".locks"
            lock_root.mkdir(parents=True, exist_ok=True, mode=0o700)
            with FileLock(str(lock_root / f"{job.name}.lock"), timeout=0):
                shutil.rmtree(job)
            report["removed"].append(job.name)
        except LockTimeout:
            report["skipped"].append({"name": job.name, "reason": "active lock"})
        except OSError as exc:
            report["skipped"].append({"name": job.name, "reason": f"remove failed: {exc}"})

    report["success"] = True
    report["candidate_count"] = len(report["candidates"])
    report["removed_count"] = len(report["removed"])
    return report
