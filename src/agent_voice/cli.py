"""Command-line interface for Agent Voice Kit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .cache import prune_cache
from .diagnostics import doctor
from .engine import synthesize


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        prog="agent-voice",
        description="Create resumable, verified speech from UTF-8 text files through Edge, Azure or OpenAI.",
    )
    value.add_argument("input", nargs="?", help="Any UTF-8 text file; omit when using --text")
    value.add_argument("--text", help="Text to speak instead of reading a file")
    value.add_argument("-o", "--output", default="voice.ogg", help="Output .ogg or .mp3 file (default: voice.ogg)")
    value.add_argument("--provider", choices=("edge", "azure", "openai"), default="edge")
    value.add_argument("--voice", help="Provider voice; defaults to DmitryNeural (Edge/Azure) or alloy (OpenAI)")
    value.add_argument("--model", help="Provider model, for example gpt-4o-mini-tts")
    value.add_argument("--rate", default="+0%", help="Edge/Azure prosody rate, for example +20%% or -10%%")
    value.add_argument("--volume", default="+0%")
    value.add_argument("--pitch", default="+0Hz")
    value.add_argument("--chunk-chars", type=int, default=500)
    value.add_argument("--timeout", type=float, default=90.0, help="Per-attempt timeout in seconds")
    markup = value.add_mutually_exclusive_group()
    markup.add_argument("--plain-text", action="store_true", help="Treat input as plain text")
    markup.add_argument("--markdown", action="store_true", help="Normalize Markdown even for a non-.md file")
    value.add_argument("--no-resume", action="store_true", help="Disable checkpoint reuse and the one transient retry")
    value.add_argument("--force", action="store_true", help="Replace only the named output file")
    value.add_argument("--cache-dir", help="Checkpoint directory (default: user cache directory)")
    value.add_argument("--doctor", action="store_true", help="Check local prerequisites without contacting TTS")
    value.add_argument("--prune-cache", action="store_true", help="Preview expired cache jobs; add --apply to remove")
    value.add_argument("--apply", action="store_true", help="Apply --prune-cache removal")
    value.add_argument("--json", action="store_true", help="Print a machine-readable receipt")
    value.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.doctor and args.prune_cache:
        parser().error("choose only one of --doctor or --prune-cache")
    if args.apply and not args.prune_cache:
        parser().error("--apply requires --prune-cache")
    if args.prune_cache:
        if args.input or args.text:
            parser().error("--prune-cache does not accept an input file or --text")
        try:
            report = prune_cache(args.cache_dir, apply=args.apply)
            if args.json:
                print(json.dumps(report, ensure_ascii=False, sort_keys=True))
            else:
                verb = "Removed" if args.apply else "Found"
                count = report["removed_count"] if args.apply else report["candidate_count"]
                print(f"{verb} {count} expired cache job(s).")
                if not args.apply and count:
                    print("Run again with --apply to remove only these validated expired jobs.")
            return 0
        except Exception as exc:
            if args.json:
                print(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False, sort_keys=True))
            else:
                print(f"agent-voice prune: {exc}", file=sys.stderr)
            return 1
    if args.doctor:
        if args.input or args.text:
            parser().error("--doctor does not accept an input file or --text")
        try:
            report = doctor(args.cache_dir, provider=args.provider)
            if args.json:
                print(json.dumps(report, ensure_ascii=False, sort_keys=True))
            else:
                state = "ready" if report["ready"] else "not ready"
                print(f"Agent Voice Kit doctor: {state}")
                for name, passed in report["checks"].items():
                    print(f"  {'PASS' if passed else 'FAIL'} {name}")
                print(report["next_step"])
            return 0 if report["ready"] else 1
        except Exception as exc:
            if args.json:
                print(json.dumps({"ready": False, "error": str(exc)}, ensure_ascii=False, sort_keys=True))
            else:
                print(f"agent-voice doctor: {exc}", file=sys.stderr)
            return 1
    if bool(args.input) == bool(args.text):
        parser().error("provide exactly one input file or --text")
    try:
        source = Path(args.input).expanduser() if args.input else None
        if source is not None and (source.is_symlink() or not source.is_file()):
            raise ValueError("input must be a regular, non-symlink UTF-8 text file")
        if args.text is not None:
            text = args.text
        else:
            assert source is not None
            text = source.read_text(encoding="utf-8")
        if "\x00" in text:
            raise ValueError("input contains NUL bytes and does not look like a text file")
        markdown = args.markdown or (
            not args.plain_text and source is not None
            and source.suffix.lower() in {".md", ".markdown", ".mdown", ".mkd"}
        )
        result = synthesize(
            text, args.output, voice=args.voice, provider_name=args.provider, model=args.model,
            rate=args.rate, volume=args.volume, pitch=args.pitch,
            chunk_chars=args.chunk_chars, timeout=args.timeout, markdown=markdown,
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
