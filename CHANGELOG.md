# Changelog

All notable changes are documented here.

## 0.3.1

- Generate a complete CycloneDX runtime dependency SBOM from an isolated wheel installation.

## 0.3.0

- Added UTF-8 text-file input independent of filename extension, with Markdown auto-detection.
- Added official Azure Speech and OpenAI Speech API providers alongside the free Edge route.
- Added conservative expired-cache preview and explicit apply pruning.
- Added Windows CI for Python 3.10 and 3.12.
- Added signed GitHub release provenance and SPDX SBOM generation.
- Added a tokenless PyPI Trusted Publishing workflow, pending owner-side publisher registration.

## 0.2.1

- Made the documented Hermes skill installation non-interactive with `--yes`.

## 0.2.0

- Added an offline `--doctor` readiness check.
- Added a safe, pinned installation contract for command-capable AI agents.
- Added an installable Hermes Agent skill for voice replies and Markdown narration.
- Clarified the boundary between this reliability wrapper and upstream `edge-tts`.
- Clarified third-party licensing and platform-specific delivery responsibilities.

## 0.1.0

- Initial standalone release.
- Markdown and direct-text input.
- Microsoft Edge Read Aloud synthesis through `edge-tts` 7.2.8.
- Bounded transient retry and seven-day checkpoint validity.
- MP3 and Telegram-ready Ogg/Opus output.
- FFmpeg duration and full-decode verification.
- Atomic output publication and symlink protection.
- English and Russian documentation, offline tests and privacy scanning.
