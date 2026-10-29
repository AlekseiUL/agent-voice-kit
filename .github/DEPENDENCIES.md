# Dependency maintenance

Dependabot opens weekly review-first pull requests for the applicable manifests and GitHub Actions. There is no auto-merge. Keep existing SHA pins and review upstream changes before accepting updates.

The weekly dependency-audit workflow blocks every advisory in `requirements-audit.txt`, a complete pinned dependency snapshot (Python 3.12). It uses `pip-audit --strict --disable-pip --no-deps`; no target package is installed or executed by this audit. Runtime, optional and build/test dependencies are included where declared. This snapshot is not a claim about arbitrary caller-installed packages or optional external services.

Regenerate the snapshot when a dependency manifest changes. Review the diff, run the audit and the full regression/install gate before merging. Keep the snapshot aligned with the existing uv.lock/requirements-ci.lock when present. Do not suppress advisories to obtain green CI.

Build/test input: `requirements-build.in`; compile it with `pyproject.toml --all-extras` using uv pip compile. Existing uv projects must export their frozen lock as constraints first.

Dependabot uses the native `uv` ecosystem so each proposal updates the manifest
and `uv.lock` together. Minor/patch TTS transport updates share one proposal;
Actions minor/patch updates share a separate proposal. Major upgrades stay
individual. No grouping rule grants merge permission.

After a dependency proposal, regenerate the Python 3.12/Linux audit snapshot:

```sh
uv lock
uv export --locked --all-extras --no-emit-project --no-hashes --output-file audit-constraints.txt
uv pip compile pyproject.toml requirements-build.in --all-extras --python-version 3.12 --python-platform linux --constraint audit-constraints.txt --no-header --no-annotate --output-file requirements-audit.txt
uv run --no-project --with packaging==26.3 python scripts/check_dependency_consistency.py
uv sync --locked --extra dev
uv run --locked pytest
```

`audit-constraints.txt` is a temporary resolver input, not a committed manifest.
The early consistency check and negative regression fixtures reject drift; they
do not replace `--locked`, advisory audit, offline tests or installed-wheel smoke.
CI runs pull requests once per matrix entry and still runs main and all tags;
release, publication, audit schedules and manual workflows retain their triggers.
