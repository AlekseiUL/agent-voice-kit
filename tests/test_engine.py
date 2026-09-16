from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from agent_voice.engine import synthesize


class ToneProvider:
    def __init__(self, failures: list[BaseException] | None = None):
        self.calls = 0
        self.failures = list(failures or [])

    def save(self, text, output, **kwargs):
        self.calls += 1
        if self.failures:
            raise self.failures.pop(0)
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is None:
            raise RuntimeError("ffmpeg is required for tests")
        subprocess.run([
            ffmpeg, "-nostdin", "-v", "error", "-y", "-f", "lavfi", "-i",
            "sine=frequency=440:duration=0.12", "-c:a", "libmp3lame", str(output),
        ], check=True, capture_output=True)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_checkpoint_resume_produces_identical_audio(tmp_path):
    text = "Первое предложение достаточно длинное. " * 12
    first_provider = ToneProvider()
    first = synthesize(text, tmp_path / "first.ogg", chunk_chars=100, cache_dir=tmp_path / "cache", provider=first_provider)
    second_provider = ToneProvider()
    second = synthesize(text, tmp_path / "second.ogg", chunk_chars=100, cache_dir=tmp_path / "cache", provider=second_provider)

    assert first.chunks >= 2
    assert first_provider.calls == first.chunks
    assert second_provider.calls == 0
    assert second.resumed_chunks == second.chunks
    assert digest(first.output) == digest(second.output)
    assert first.receipt()["output"] == "first.ogg"
    assert "/" not in first.receipt()["output"]


def test_one_retry_for_transient_failure(tmp_path):
    provider = ToneProvider([TimeoutError("temporary")])
    result = synthesize("Проверка временной ошибки.", tmp_path / "voice.mp3", cache_dir=tmp_path / "cache", provider=provider)
    assert result.bytes > 0
    assert provider.calls == 2


def test_expired_checkpoint_is_not_reused(tmp_path):
    cache = tmp_path / "cache"
    text = "Проверка срока хранения checkpoint."
    first_provider = ToneProvider()
    first = synthesize(text, tmp_path / "first.ogg", cache_dir=cache, provider=first_provider)
    manifest_path = cache / first.job_id / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["expires_at"] = 0
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    second_provider = ToneProvider()
    second = synthesize(text, tmp_path / "second.ogg", cache_dir=cache, provider=second_provider)
    assert second.resumed_chunks == 0
    assert second_provider.calls == second.chunks


def test_no_retry_for_non_transient_failure(tmp_path):
    provider = ToneProvider([ValueError("bad voice")])
    with pytest.raises(RuntimeError, match="bounded retry"):
        synthesize("Проверка ошибки конфигурации.", tmp_path / "voice.ogg", cache_dir=tmp_path / "cache", provider=provider)
    assert provider.calls == 1


def test_no_resume_disables_retry(tmp_path):
    provider = ToneProvider([TimeoutError("temporary")])
    with pytest.raises(RuntimeError, match="bounded retry"):
        synthesize("Проверка режима без восстановления.", tmp_path / "voice.ogg", resume=False, provider=provider)
    assert provider.calls == 1


def test_refuses_output_symlink(tmp_path):
    target = tmp_path / "target.ogg"
    target.write_bytes(b"not audio")
    link = tmp_path / "voice.ogg"
    link.symlink_to(target)
    with pytest.raises(RuntimeError, match="symlink"):
        synthesize("Проверка безопасного пути.", link, cache_dir=tmp_path / "cache", provider=ToneProvider(), force=True)
