# Installation contract for AI agents

This file is the safe, reproducible installation path for an AI agent.

## Goal

Install Agent Voice Kit, verify its local prerequisites, run one explicit live smoke test, and report what changed. The tool must be able to voice a complete response or any regular UTF-8 text file. Long identical jobs should resume from verified chunks.

## Safety boundary

1. Read `README.md`, `SECURITY.md`, and `NOTICE.md` first.
2. Inspect the current OS, Python version, `uv`, `ffmpeg`, and `ffprobe` before changing anything.
3. Do not use `sudo`, install a system package, edit shell/profile configuration, restart a service, or send a message/file externally without the user's approval.
4. Do not synthesize private or sensitive text without confirming that transfer to Microsoft Edge Read Aloud is acceptable.
5. Do not add provider credentials: the default Edge route does not use an API key.

## Install

Use the pinned release:

```bash
uv tool install "git+https://github.com/AlekseiUL/agent-voice-kit.git@v0.3.2"
agent-voice --version
agent-voice --doctor --json
```

If `uv`, FFmpeg, or an encoder is missing, report the exact missing prerequisite. Ask before installing system software. Typical FFmpeg commands, after approval, are:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y ffmpeg
```

## Verify network synthesis

The doctor is offline. After it reports `"ready": true`, run one short, non-sensitive live test:

```bash
agent-voice \
  --text "Agent Voice Kit is ready." \
  --output /tmp/agent-voice-kit-smoke.ogg \
  --no-resume \
  --json
```

Require exit code `0`, `"success": true`, a non-empty `.ogg`, and a positive duration in the JSON receipt. Do not claim success from file existence alone.

## Hermes Agent integration

After the CLI passes, install the maintained skill into the active Hermes profile:

```bash
hermes skills install \
  https://raw.githubusercontent.com/AlekseiUL/agent-voice-kit/v0.3.2/integrations/hermes/SKILL.md \
  --name agent-voice --yes
```

Start a new session or use `/reset` so the skill becomes visible. Do not modify another Hermes profile.

## Completion receipt

Report:

- installed `agent-voice` version;
- offline doctor result;
- live smoke output format and duration;
- whether the Hermes skill was installed;
- privacy boundary: synthesis sends text to Microsoft;
- remaining limitation: the consumer endpoint has no project SLA.

For an official paid route, select `--provider azure` or `--provider openai` and configure that provider's environment variables. Never request or print credentials in chat. Preview expired generated-audio cache with `agent-voice --prune-cache --json`; deletion requires the separate explicit `--apply` flag.
