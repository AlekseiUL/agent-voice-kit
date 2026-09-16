"""Offline installation and runtime diagnostics."""

from __future__ import annotations

import importlib.metadata
import json
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def doctor(cache_dir: str | Path | None = None) -> dict[str, Any]:
    """Check local prerequisites without sending text to an external service."""
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    encoders: set[str] = set()
    if ffmpeg:
        result = subprocess.run(
            [ffmpeg, "-nostdin", "-hide_banner", "-encoders"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            for name in ("libopus", "libmp3lame"):
                if name in result.stdout:
                    encoders.add(name)
    try:
        edge_version = importlib.metadata.version("edge-tts")
    except importlib.metadata.PackageNotFoundError:
        edge_version = None
    cache = Path(cache_dir).expanduser() if cache_dir else Path.home() / ".cache" / "agent-voice-kit"
    cache_writable = False
    try:
        cache.mkdir(parents=True, exist_ok=True, mode=0o700)
        with tempfile.NamedTemporaryFile(prefix=".doctor-", dir=cache):
            cache_writable = True
    except OSError:
        pass
    checks = {
        "edge_tts_installed": edge_version is not None,
        "ffmpeg_available": ffmpeg is not None,
        "ffprobe_available": ffprobe is not None,
        "libopus_available": "libopus" in encoders,
        "libmp3lame_available": "libmp3lame" in encoders,
        "cache_writable": cache_writable,
    }
    return {
        "ready": all(checks.values()),
        "network_checked": False,
        "python": platform.python_version(),
        "edge_tts": edge_version,
        "checks": checks,
        "next_step": (
            "Run a short explicit synthesis to verify network access."
            if all(checks.values()) else
            "Install the missing local prerequisites, then run doctor again."
        ),
    }


def doctor_json(cache_dir: str | Path | None = None) -> str:
    return json.dumps(doctor(cache_dir), ensure_ascii=False, sort_keys=True)
