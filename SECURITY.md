# Security policy

## Supported version

Security fixes are provided for the latest tagged release.

## Boundaries

- The tool needs network access to the selected Edge, Azure or OpenAI service.
- Input text is sent to that external provider for synthesis. Do not submit secrets, credentials, health records or other sensitive text unless that transfer is acceptable to you.
- The default Edge route needs no API key. Official Azure/OpenAI routes read their credentials from environment variables and do not store them or include them in receipts.
- Checkpoints contain generated audio and hashes, not the original text. They expire logically after seven days. `--prune-cache` previews conservatively; only `--prune-cache --apply` removes validated, expired, unlocked job directories.
- `--force` can replace only the exact output file supplied by the user. The tool refuses to write through an output symlink.

## Reporting a vulnerability

Please report security issues privately through GitHub Security Advisories:

https://github.com/AlekseiUL/agent-voice-kit/security/advisories/new

Do not open a public issue containing credentials, private text or exploit details.
