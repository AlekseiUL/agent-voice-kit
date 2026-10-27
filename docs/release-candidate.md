# Release candidate v0.4.0

Status: prepared, not published. Publish only after the exact PR head passes CI and the owner approves merge/release. Existing tags must not move.

Distribution: Python wheel and source archive. This candidate includes all changes on main since v0.3.2, plus pinned GitHub Actions and review-first dependency updates. This is not an npm/PyPI publication.

Compatibility: Python 3.11+ is now required because the fixed filelock 4.x does not support Python 3.10. The 0.4.0 version signals this compatibility change. Node or live TTS is not required for offline verification.

Install into a fresh temporary environment from the built archive, not an editable checkout. Run the documented offline core command/fixture before publishing; do not enable profiles, contact paid providers or start services. After release, download the exact public artifact and repeat this check.

Rollback: close the unmerged PR; after merge, submit a revert PR. Do not rewrite the release tag or delete old artifacts. A bad release must be superseded and clearly marked, with owner approval.
