# Agent Voice Kit — «Голос агента»

[Русская версия](README.ru.md)

[![CI](https://github.com/AlekseiUL/agent-voice-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/AlekseiUL/agent-voice-kit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB.svg)

Turn an AI-agent reply or any regular UTF-8 text file into verified MP3 or Telegram-ready Ogg/Opus audio. The default route uses server-side Microsoft Edge Read Aloud through the independent [`edge-tts`](https://github.com/rany2/edge-tts) client, so speech generation does not run a neural model on your computer. Optional official Azure Speech and OpenAI Speech API routes are available when an SLA or supported API is required.

The project adds the reliability layer that a one-line TTS call does not provide: bounded retry, short chunks, checkpoint resume, full decode verification and atomic output publication.

## How it differs from `edge-tts`

[`edge-tts`](https://github.com/rany2/edge-tts) is the upstream client that talks to Microsoft Edge Read Aloud. It already provides direct synthesis, voice discovery, subtitles and prosody controls. Agent Voice Kit is **not a fork or replacement**: it installs `edge-tts` as a separate dependency and adds a workflow-oriented reliability layer for AI agents.

Agent Voice Kit adds Markdown cleanup, safe chunking, one bounded transient retry, verified checkpoint resume, complete-file decode validation, atomic publication, Telegram-ready Ogg/Opus and a JSON receipt. It deliberately does not duplicate upstream voice listing, subtitle or playback features; use `edge-tts` directly when those are what you need.

## What it does

- reads any regular UTF-8 text file or accepts text directly;
- removes common Markdown controls without discarding readable content;
- splits long text at sentence and word boundaries;
- retries a transient provider failure once;
- saves each verified chunk and resumes an identical request later;
- converts audio to MP3 or Telegram-compatible Ogg/Opus;
- validates duration and decodes the complete file with FFmpeg;
- writes the final file atomically and refuses accidental overwrite;
- prints a compact human result or a machine-readable JSON receipt.

## Important boundary

This project is not a hosted TTS service. Its default Edge route is not an official Microsoft SDK; the consumer Edge Read Aloud endpoint has no SLA for this project and can change or stop working. Azure and OpenAI routes use their official HTTP APIs but require separately managed paid accounts. Internet access is required. Do not send sensitive text unless transferring it to the selected external provider is acceptable.

For contractual availability or commercial support, select and configure an official provider. Agent Voice Kit deliberately does not fall back to another provider silently.

## Requirements

- Python 3.10 or newer;
- `ffmpeg` and `ffprobe` in `PATH`;
- internet access for live synthesis.

Install FFmpeg:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y ffmpeg

# Windows (administrator shell)
choco install ffmpeg -y
```

## Install

With `uv`:

```bash
uv tool install "git+https://github.com/AlekseiUL/agent-voice-kit.git@v0.3.1"
agent-voice --version
agent-voice --doctor --json
```

Or from a clone:

```bash
git clone https://github.com/AlekseiUL/agent-voice-kit.git
cd agent-voice-kit
uv sync
uv run agent-voice --help
```

`--doctor` is offline: it checks `edge-tts`, FFmpeg/ffprobe, required encoders and cache access without sending text to Microsoft. A short explicit synthesis is still required to prove network access.

## Install it with an AI agent

Send the repository link and this instruction:

> Install Agent Voice Kit and follow `INSTALL_FOR_AGENTS.md`. Do not use sudo, change my profile, restart services or send anything externally without approval. Run the offline doctor and one short live test, then report the evidence and remaining risk.

The complete copy/paste workflow is in [docs/AGENT_SETUP.md](docs/AGENT_SETUP.md). The pinned safety contract is [INSTALL_FOR_AGENTS.md](INSTALL_FOR_AGENTS.md). Any command-capable agent can use the CLI; native delivery remains platform-specific.

For Hermes Agent, install the maintained skill after the CLI passes:

```bash
hermes skills install \
  https://raw.githubusercontent.com/AlekseiUL/agent-voice-kit/v0.3.1/integrations/hermes/SKILL.md \
  --name agent-voice --yes
```

Start a new session or use `/reset`. The skill handles voice replies and complete Markdown narration, including the native Telegram voice attachment format.

## Text-file input

The positional input can be any regular UTF-8 text file: `.txt`, `.md`, `.rst`, `.csv`, `.json`, `.yaml`, logs, configuration or source files. Binary files, invalid UTF-8, NUL-containing files and input symlinks are rejected. Markdown cleanup is automatic only for `.md`, `.markdown`, `.mdown` and `.mkd`; use `--markdown` or `--plain-text` to override detection.

## Quick start

Voice a Markdown file as a Telegram-ready voice message:

```bash
agent-voice answer.md --output answer.ogg
```

Speak direct text:

```bash
agent-voice --text "The agent has finished the task." --voice en-US-GuyNeural --output answer.mp3
```

Russian voice with a slightly faster rate:

```bash
agent-voice answer.md \
  --voice ru-RU-DmitryNeural \
  --rate=+15% \
  --output answer.ogg
```

Machine-readable receipt:

```bash
agent-voice answer.md --output answer.ogg --json
```

Voice a plain log or another text file:

```bash
agent-voice service.log --output service-log.ogg --json
```

## Providers

- `edge` (default): no API key, server-side and light on the local machine, but the consumer endpoint has no project SLA.
- `azure`: official Azure Speech REST API. Configure `AZURE_SPEECH_KEY` plus `AZURE_SPEECH_REGION` or `AZURE_SPEECH_ENDPOINT`.
- `openai`: official OpenAI Speech REST API. Configure `OPENAI_API_KEY`; the default model is `gpt-4o-mini-tts` and default voice is `alloy`.

```bash
agent-voice report.txt --provider azure --voice ru-RU-DmitryNeural -o report.ogg
agent-voice report.txt --provider openai --model gpt-4o-mini-tts --voice alloy -o report.mp3
agent-voice --doctor --provider azure --json
```

Provider credentials are read from environment variables and are never included in receipts. Azure/OpenAI usage is paid according to the provider account. OpenAI prosody flags are intentionally rejected rather than silently ignored.

Example:

```json
{
  "success": true,
  "output": "answer.ogg",
  "provider": "edge",
  "chunks": 3,
  "resumed_chunks": 3,
  "duration_seconds": 72.4
}
```

The real receipt also contains the voice, format, byte size, SHA-256 digest and a content-derived job ID. It stores only the output filename, not an absolute local path.

## Failure and resume behavior

A new request gets at most two attempts per chunk: the initial request and one retry for timeouts, connection failures, HTTP 429/5xx, `NoAudioReceived` or `WebSocketError`. Configuration errors and HTTP 403 are not retried.

Completed chunks are verified before entering the checkpoint. Repeating the same text and settings reuses those chunks. The checkpoint manifest contains hashes and audio metadata, not the original text. The retention window is seven days. Cleanup is preview-first:

```bash
agent-voice --prune-cache --json
agent-voice --prune-cache --apply --json
```

Only validated, expired, unlocked 64-character job directories are removed. Unknown entries, malformed manifests, symlinks, current jobs and locked jobs are skipped.

Disable checkpoint reuse and the retry when exact-one behavior is required:

```bash
agent-voice answer.md --output answer.ogg --no-resume
```

## Using it from an agent

The CLI is intentionally platform-neutral. An agent can run it as a subprocess, inspect the exit code/JSON receipt and attach the resulting file through its own delivery layer:

```python
import subprocess

result = subprocess.run(
    ["agent-voice", "reply.md", "--output", "reply.ogg", "--json"],
    text=True,
    capture_output=True,
    check=True,
)
print(result.stdout)
```

Telegram bots should upload the generated `.ogg` through their voice-message method. Tokens, chat IDs and sending logic are intentionally outside this repository.

## Commands

```text
agent-voice INPUT [-o FILE]
agent-voice --text TEXT [-o FILE]
agent-voice --doctor [--json]
agent-voice --prune-cache [--apply] [--json]
```

Run `agent-voice --help` for the verified current flag list.

Safety defaults:

- output must end in `.ogg` or `.mp3`;
- an existing different output is not replaced without `--force`;
- `--force` affects only the explicitly named output file;
- output symlinks are rejected;
- concurrent identical jobs fail with a clear busy error instead of corrupting checkpoints.

## Development

```bash
uv sync --extra dev
uv run pytest
uv run python scripts/privacy_scan.py
uv build
```

Unit tests synthesize local test tones and do not contact Microsoft. A manual live smoke is explicit:

```bash
uv run agent-voice --text "Live synthesis check." --voice en-US-GuyNeural --output /tmp/agent-voice-live.ogg
```

## Attribution and licensing

Agent Voice Kit code is released under the [MIT License](LICENSE). It depends on `edge-tts`, which is a separate LGPL-3.0 project. FFmpeg is an external runtime dependency and is not bundled. See [NOTICE.md](NOTICE.md) for sources, licenses and the Microsoft-service boundary.

## Releases, SBOM and PyPI

Tagged GitHub releases are built in GitHub Actions, receive GitHub artifact provenance and SBOM attestations, and include a CycloneDX JSON inventory of the installed runtime dependency graph. Verify a downloaded artifact with `gh attestation verify FILE --repo AlekseiUL/agent-voice-kit`.

The repository contains a tokenless PyPI Trusted Publishing workflow. Until the owner-side PyPI publisher registration and first publication are complete, install the pinned GitHub tag shown above; do not assume the PyPI name is live merely because the workflow exists. The exact no-secret activation procedure is in [docs/PYPI_PUBLISHING.md](docs/PYPI_PUBLISHING.md).

## Creator links

- GitHub: https://github.com/AlekseiUL
- YouTube: https://youtube.com/@alekseiulianov
- Telegram — Sprut AI: https://t.me/Sprut_AI
- Telegram community: https://t.me/+eH-qNIDmud8zNDZi
- AI Операционка / support: https://t.me/tribute/app?startapp=sJyg

Created and maintained by [AlekseiUL](https://github.com/AlekseiUL) with community contributors.
