# Contributing

Small, test-backed pull requests are welcome.

1. Fork the repository and create a focused branch.
2. Install development dependencies with `uv sync --extra dev`.
3. Run `uv run pytest`.
4. Verify `uv run agent-voice --help` and update both README files when CLI behavior changes.
5. Do not commit generated audio, caches, personal text, tokens or absolute local paths.

Provider additions must keep the base Edge path optional, preserve bounded retries and produce independently decodable audio. A new provider must not silently replace Edge after a failed request.
