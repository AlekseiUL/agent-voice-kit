"""Resumable TTS engine with bounded retry and independent audio verification."""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from filelock import FileLock, Timeout as LockTimeout

from .provider import EdgeProvider, SpeechProvider, retryable_edge_error
from .text import markdown_to_text, split_text


@dataclass(frozen=True)
class SynthesisResult:
    output: Path
    provider: str
    voice: str
    format: str
    chunks: int
    resumed_chunks: int
    duration_seconds: float
    bytes: int
    sha256: str
    job_id: str

    def receipt(self) -> dict[str, Any]:
        data = asdict(self)
        data["output"] = self.output.name
        data["duration_seconds"] = round(self.duration_seconds, 3)
        return data


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _tools() -> tuple[str, str]:
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("ffmpeg and ffprobe are required and must be available in PATH")
    return ffmpeg, ffprobe


def _probe(path: Path) -> float:
    _, ffprobe = _tools()
    result = subprocess.run(
        [ffprobe, "-v", "error", "-select_streams", "a:0", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, timeout=30, check=True,
    )
    duration = float(result.stdout.strip())
    if not math.isfinite(duration) or duration <= 0 or path.stat().st_size <= 0:
        raise RuntimeError("audio verification failed: no positive duration or empty file")
    return duration


def _decode(path: Path, duration: float) -> None:
    ffmpeg, _ = _tools()
    subprocess.run(
        [ffmpeg, "-nostdin", "-v", "error", "-xerror", "-i", str(path), "-map", "0:a:0", "-f", "null", "-"],
        capture_output=True, timeout=max(60, int(duration * 0.3)), check=True,
    )


def _verified_metadata(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("audio verification failed: output is not a regular file")
    duration = _probe(path)
    _decode(path, duration)
    return {"file": path.name, "bytes": path.stat().st_size, "duration": duration, "sha256": _sha256(path)}


def _convert(source: Path, target: Path, output_format: str) -> None:
    ffmpeg, _ = _tools()
    if output_format == "ogg":
        args = ["-c:a", "libopus", "-ac", "1", "-b:a", "48k", "-vbr", "on", "-application", "voip"]
    else:
        args = ["-c:a", "libmp3lame", "-b:a", "96k"]
    subprocess.run(
        [ffmpeg, "-nostdin", "-v", "error", "-xerror", "-y", "-i", str(source), *args, str(target)],
        capture_output=True, timeout=120, check=True,
    )


def _concat(job: Path, chunk_paths: list[Path], output_format: str) -> Path:
    ffmpeg, _ = _tools()
    final = job / f"final.{output_format}"
    if len(chunk_paths) == 1:
        shutil.copyfile(chunk_paths[0], final)
        return final
    listing = job / "concat.txt"
    listing.write_text("".join(f"file '{item.name}'\n" for item in chunk_paths), encoding="utf-8")
    if output_format == "ogg":
        codec = ["-c:a", "libopus", "-ac", "1", "-b:a", "64k", "-vbr", "off"]
    else:
        codec = ["-c:a", "libmp3lame", "-b:a", "96k"]
    subprocess.run(
        [ffmpeg, "-nostdin", "-v", "error", "-xerror", "-y", "-f", "concat", "-safe", "1",
         "-i", str(listing), "-vn", *codec, str(final)],
        cwd=job, capture_output=True, timeout=180, check=True,
    )
    return final


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    fd, temp = tempfile.mkstemp(prefix=".manifest-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=True, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        Path(temp).unlink(missing_ok=True)


def _publish(source: Path, destination: Path, *, force: bool) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink():
        raise RuntimeError("refusing to write through an output symlink")
    if destination.exists() and not force:
        if destination.is_file() and _sha256(destination) == _sha256(source):
            return
        raise FileExistsError(f"output already exists: {destination}; pass --force to replace only this file")
    fd, temp_name = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        shutil.copyfile(source, temp)
        if force:
            os.replace(temp, destination)
        else:
            os.link(temp, destination)
    finally:
        temp.unlink(missing_ok=True)


def _default_cache() -> Path:
    base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return base / "agent-voice-kit"


def _load_manifest(path: Path, job_id: str, count: int) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        expires_at = value.get("expires_at") if isinstance(value, dict) else None
        if (isinstance(value, dict) and value.get("version") == 1
                and value.get("job_id") == job_id and value.get("chunk_count") == count
                and isinstance(value.get("chunks"), dict)
                and isinstance(expires_at, (int, float)) and expires_at >= time.time()):
            return value
    except (OSError, ValueError, AttributeError):
        pass
    return {"version": 1, "job_id": job_id, "chunk_count": count, "chunks": {}}


def _valid_cached(path: Path, recorded: dict[str, Any]) -> bool:
    try:
        if path.name != recorded.get("file") or _sha256(path) != recorded.get("sha256"):
            return False
        actual = _verified_metadata(path)
        recorded_duration = recorded.get("duration")
        if not isinstance(recorded_duration, (int, float)):
            return False
        return actual["bytes"] == recorded.get("bytes") and abs(actual["duration"] - float(recorded_duration)) < 0.02
    except (OSError, ValueError, TypeError, RuntimeError, subprocess.SubprocessError):
        return False


def synthesize(
    text: str,
    output: str | Path,
    *,
    voice: str = "ru-RU-DmitryNeural",
    rate: str = "+0%",
    volume: str = "+0%",
    pitch: str = "+0Hz",
    chunk_chars: int = 500,
    timeout: float = 90.0,
    markdown: bool = True,
    resume: bool = True,
    force: bool = False,
    cache_dir: str | Path | None = None,
    provider: SpeechProvider | None = None,
) -> SynthesisResult:
    """Create verified MP3 or Ogg/Opus audio and preserve complete chunks for seven days."""
    destination = Path(output).expanduser()
    output_format = destination.suffix.lower().lstrip(".")
    if output_format not in {"ogg", "mp3"}:
        raise ValueError("output must end in .ogg or .mp3")
    spoken = markdown_to_text(text) if markdown else " ".join(text.split())
    chunks = split_text(spoken, chunk_chars)
    if not chunks:
        raise ValueError("text is empty after normalization")
    identity = {
        "version": 1, "provider": "edge", "voice": voice, "rate": rate, "volume": volume,
        "pitch": pitch, "format": output_format, "chunks": chunks,
    }
    job_id = hashlib.sha256(json.dumps(identity, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    root = Path(cache_dir).expanduser() if cache_dir else _default_cache()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    root.chmod(0o700)
    provider = provider or EdgeProvider()

    def execute(job: Path) -> SynthesisResult:
        manifest_path = job / "manifest.json"
        manifest = _load_manifest(manifest_path, job_id, len(chunks)) if resume else {
            "version": 1, "job_id": job_id, "chunk_count": len(chunks), "chunks": {}}
        resumed = 0
        paths: list[Path] = []
        for index, chunk in enumerate(chunks, 1):
            key = str(index)
            target = job / f"chunk-{index:05d}.{output_format}"
            recorded = manifest["chunks"].get(key)
            if resume and isinstance(recorded, dict) and _valid_cached(target, recorded):
                resumed += 1
                paths.append(target)
                continue
            target.unlink(missing_ok=True)
            last_error: BaseException | None = None
            attempts = (1, 2) if resume else (1,)
            for attempt in attempts:
                with tempfile.TemporaryDirectory(prefix=".attempt-", dir=job) as temporary:
                    raw = Path(temporary) / "edge.mp3"
                    try:
                        provider.save(chunk, raw, voice=voice, rate=rate, volume=volume, pitch=pitch, timeout=timeout)
                        converted = Path(temporary) / f"verified.{output_format}"
                        _convert(raw, converted, output_format)
                        metadata = _verified_metadata(converted)
                        os.replace(converted, target)
                        metadata["file"] = target.name
                        manifest["chunks"][key] = metadata
                        manifest["updated_at"] = int(time.time())
                        manifest["expires_at"] = int(time.time() + 7 * 24 * 60 * 60)
                        _atomic_json(manifest_path, manifest)
                        last_error = None
                        break
                    except Exception as exc:
                        last_error = exc
                        if attempt == attempts[-1] or not retryable_edge_error(exc):
                            break
                        time.sleep(1.0)
            if last_error is not None:
                raise RuntimeError(f"chunk {index}/{len(chunks)} failed after bounded retry: {last_error}") from last_error
            paths.append(target)
        cached_final = manifest.get("final")
        final_path = job / f"final.{output_format}"
        if resumed == len(chunks) and isinstance(cached_final, dict) and _valid_cached(final_path, cached_final):
            final = final_path
        else:
            final = _concat(job, paths, output_format)
            final_metadata = _verified_metadata(final)
            manifest["final"] = final_metadata
            _atomic_json(manifest_path, manifest)
        _publish(final, destination, force=force)
        published = _verified_metadata(destination)
        return SynthesisResult(
            output=destination, provider="edge", voice=voice, format=output_format,
            chunks=len(chunks), resumed_chunks=resumed, duration_seconds=published["duration"],
            bytes=published["bytes"], sha256=published["sha256"], job_id=job_id,
        )

    if not resume:
        with tempfile.TemporaryDirectory(prefix="agent-voice-") as directory:
            return execute(Path(directory))
    job = root / job_id
    job.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        with FileLock(str(job / ".lock"), timeout=0):
            return execute(job)
    except LockTimeout as exc:
        raise RuntimeError("the same recording is already running; wait and repeat the request") from exc
