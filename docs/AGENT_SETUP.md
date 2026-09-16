# Install Agent Voice Kit with an AI agent

Send the repository link to an agent together with this request:

> Install Agent Voice Kit from https://github.com/AlekseiUL/agent-voice-kit. Follow the repository's `INSTALL_FOR_AGENTS.md`. Do not use sudo, restart services, edit my agent profile or send external messages without approval. Run the offline doctor and one short live synthesis, then report the version, checks, output format and remaining risk. If this is Hermes Agent, install the provided Hermes skill into the active profile after the CLI passes.

## Expected result

A correct installation ends with:

```bash
agent-voice --version
agent-voice --doctor --json
```

The doctor should return `"ready": true`. It deliberately does not contact Microsoft. The agent then runs one short live synthesis to verify network access.

## What the installed agent should do later

- “Answer by voice” → prepare the complete answer, generate `.ogg`, verify the receipt, deliver one voice message.
- “Voice this document” → pass the exact regular UTF-8 text-file path to `agent-voice`, then deliver the generated file. Markdown cleanup is automatic only for Markdown extensions.
- Long recording interrupted → repeat the same text and settings so verified chunks resume.
- Sensitive document → stop and explain that its text would be sent to the selected external TTS provider.

## Generic agents

Any agent that can run commands and attach files can use the CLI. The delivery step belongs to that agent's platform; this repository intentionally stores no bot token or chat ID.

## Hermes Agent

Install the CLI first, then the skill:

```bash
uv tool install "git+https://github.com/AlekseiUL/agent-voice-kit.git@v0.3.0"
hermes skills install \
  https://raw.githubusercontent.com/AlekseiUL/agent-voice-kit/v0.3.0/integrations/hermes/SKILL.md \
  --name agent-voice --yes
```

Start a new session or use `/reset`; tool and skill visibility is session-scoped. The skill tells Hermes how to preserve the full text, generate verified Ogg/Opus and return a native Telegram voice attachment.
