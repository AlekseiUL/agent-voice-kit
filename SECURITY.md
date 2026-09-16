# Security policy

## Supported version

Security fixes are provided for the latest tagged release.

## Boundaries

- The tool needs network access to Microsoft Edge Read Aloud through `edge-tts`.
- Input text is sent to that external service for synthesis. Do not submit secrets, credentials, health records or other sensitive text unless that transfer is acceptable to you.
- The tool does not require or store API keys.
- Checkpoints contain generated audio and hashes, not the original text. They expire logically after seven days; automatic physical cleanup is not yet included in v0.2.1.
- `--force` can replace only the exact output file supplied by the user. The tool refuses to write through an output symlink.

## Reporting a vulnerability

Please report security issues privately through GitHub Security Advisories:

https://github.com/AlekseiUL/agent-voice-kit/security/advisories/new

Do not open a public issue containing credentials, private text or exploit details.
