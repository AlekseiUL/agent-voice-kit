from __future__ import annotations

import json
from pathlib import Path

from filelock import FileLock

from agent_voice.cache import prune_cache


def _job(root: Path, name: str, expires_at: float) -> Path:
    path = root / name
    path.mkdir(parents=True)
    (path / "manifest.json").write_text(json.dumps({
        "version": 1,
        "job_id": name,
        "chunk_count": 1,
        "chunks": {},
        "expires_at": expires_at,
    }), encoding="utf-8")
    (path / "audio.mp3").write_bytes(b"generated cache")
    return path


def test_prune_is_preview_by_default_and_apply_removes_only_expired(tmp_path):
    expired_name = "a" * 64
    current_name = "b" * 64
    expired = _job(tmp_path, expired_name, 10)
    current = _job(tmp_path, current_name, 1000)

    preview = prune_cache(tmp_path, now=100)
    assert preview["candidates"] == [expired_name]
    assert preview["removed"] == []
    assert expired.exists() and current.exists()

    applied = prune_cache(tmp_path, now=100, apply=True)
    assert applied["removed"] == [expired_name]
    assert not expired.exists()
    assert current.exists()


def test_prune_skips_unknown_invalid_and_locked_entries(tmp_path):
    (tmp_path / "notes").mkdir()
    invalid = tmp_path / ("c" * 64)
    invalid.mkdir()
    (invalid / "manifest.json").write_text("{}", encoding="utf-8")
    locked = _job(tmp_path, "d" * 64, 1)

    lock_root = tmp_path / ".locks"
    lock_root.mkdir()
    with FileLock(str(lock_root / f"{locked.name}.lock"), timeout=0):
        report = prune_cache(tmp_path, now=100, apply=True)

    reasons = {item["reason"] for item in report["skipped"]}
    assert "unrecognized entry" in reasons
    assert "invalid manifest" in reasons
    assert "active lock" in reasons
    assert locked.exists()
