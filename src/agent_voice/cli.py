"""Command-line interface for Agent Voice Kit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .engine import synthesize


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        prog="agent-voice",
        description="Create resumable, verified speech from text or Markdown through Edge Read Aloud.",
    )
    value.add_argument("input", nargs="?", help="UTF-8 text/Markdown file; omit when using --text")
    value.add_argument("--text", help="Text to speak instead of reading a file")
    value.add_argument("-o", "--output", default="voice.ogg", help="Output .ogg or .mp3 file (default: voice.ogg)")
    value.add_argument("--voice", default="ru-RU-DmitryNeural")
    value.add_argument("--rate", default="+0%", help="Edge prosody rate, for example +20%% or -10%%")
    value.add_argument("--volume", default="+0%")
    value.add_argument("--pitch", default="+0Hz")
    value.add_argument("--chunk-chars", type=int, default=500)
    value.add_argument("--timeout", type=float, default=90.0, help="Per-attempt timeout in seconds")
    value.add_argument("--plain-text", action="store_true", help="Do not normalize Markdown")
    value.add_argument("--no-resume", action="store_true", help="Disable checkpoint reuse and the one transient retry")
    value.add_argument("--force", action="store_true", help="Replace only the named output file")
    value.add_argument("--cache-dir", help="Checkpoint directory (default: user cache directory)")
    value.add_argument("--json", action="store_true", help="Print a machine-readable receipt")
    value.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if bool(args.input) == bool(args.text):
        parser().error("provide exactly one input file or --text")
    try:
        text = args.text if args.text is not None else Path(args.input).read_text(encoding="utf-8")
        result = synthesize(
            text, args.output, voice=args.voice, rate=args.rate, volume=args.volume, pitch=args.pitch,
            chunk_chars=args.chunk_chars, timeout=args.timeout, markdown=not args.plain_text,
            resume=not args.no_resume, force=args.force, cache_dir=args.cache_dir,
        )
        if args.json:
            print(json.dumps({"success": True, **result.receipt()}, ensure_ascii=False, sort_keys=True))
        else:
            print(f"Saved {result.output.name}: {result.duration_seconds:.1f}s, {result.chunks} chunk(s), "
                  f"{result.resumed_chunks} resumed")
        return 0
    except Exception as exc:
        if args.json:
            print(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        else:
            print(f"agent-voice: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
