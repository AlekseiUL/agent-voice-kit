---
name: agent-voice
description: "Use when an agent must answer by voice or voice a text/Markdown document. Generate verified audio with Agent Voice Kit and deliver it through the active platform."
version: 0.3.2
license: MIT
metadata:
  hermes:
    tags: [tts, voice, markdown, telegram, edge-tts]
---

# Agent Voice

Use the installed `agent-voice` CLI for explicit requests such as “answer by voice”, “record this”, or “voice this text file”. UTF-8 Markdown, TXT, RST, CSV, JSON, YAML, logs and source files are accepted; Markdown cleanup is automatic only for Markdown extensions.

## Preconditions

1. Run `agent-voice --doctor --json` when readiness is unknown.
2. `ready: true` proves local dependencies only. A short synthesis proves network access.
3. Text is sent to the selected external TTS provider. The default is Microsoft Edge Read Aloud through `edge-tts`; Azure/OpenAI are explicit alternatives. Do not send secrets, credentials, health records or other sensitive text without confirming that this external transfer is acceptable.

## Voice an answer

Preserve the full answer unless the user asks to shorten it. Write the final response to a temporary UTF-8 `.md` file so shell quoting cannot alter the text, then run:

```bash
agent-voice /path/to/response.md --output /path/to/response.ogg --json
```

## Voice a text file

For any user-provided UTF-8 text file:

```bash
agent-voice /path/to/document.md --output /path/to/document.ogg --json
```

Use `--markdown` to normalize Markdown stored under another extension, or `--plain-text` to preserve Markdown control characters literally.

Do not voice a different local file merely because its name is similar. Respect the active agent's normal file-access and privacy boundaries.

## Verification and delivery

- Treat exit code zero plus `"success": true` as synthesis evidence.
- The tool already checks positive duration and full FFmpeg decode. Confirm the returned output exists before delivery.
- For Hermes on Telegram, return exactly one native voice attachment:

```text
[[audio_as_voice]]
MEDIA:/absolute/path/to/result.ogg
```

- On platforms without native voice bubbles, attach the generated audio file normally.
- Do not send duplicate audio after a successful platform delivery.
- If generation fails, report the concrete error. The tool already performs one bounded retry for transient Edge failures; do not loop whole requests indefinitely.

## Long recordings

The default checkpoint reuses verified chunks for seven days. Repeat the same text and settings to resume. Use `--no-resume` only when the task explicitly forbids retry or reuse.
