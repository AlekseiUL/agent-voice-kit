# Offline verification boundary

Locked CI/release synchronization and an opt-in dependency-update artifact job.

## Reproduce

`uv sync --locked --extra dev; uv run --locked pytest`

Mock synthesis does not prove TTS delivery; no live provider call is part of this gate.

## Rollback

Review the commit diff and use a new checkout of the pre-change commit for source rollback. Keep user data and live installations untouched. A source rollback is not permission to restore unsafe network exposure or bypass approval.
