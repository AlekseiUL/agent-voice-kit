# PyPI Trusted Publishing activation

The repository is prepared for tokenless publishing, but PyPI must first trust the GitHub workflow. This owner-side account step cannot be completed from repository code.

## One-time PyPI setup

While signed in to the intended PyPI account, add a pending Trusted Publisher for a new project with exactly:

- PyPI project name: `agent-voice-kit`
- GitHub owner: `AlekseiUL`
- Repository: `agent-voice-kit`
- Workflow: `publish-pypi.yml`
- Environment: `pypi`

Do not paste a PyPI password or API token into an issue, chat, repository file or workflow. Trusted Publishing uses a short-lived GitHub OIDC identity.

## First publication

After the publisher exists and the signed `v0.3.0` release is complete, run the GitHub workflow **Publish to PyPI** with input `v0.3.0`. The workflow checks that the package version matches the selected tag, builds in a separate low-privilege job, and gives `id-token: write` only to the publication job.

## Verification

A successful workflow is not sufficient by itself. Read back:

```bash
python -m pip index versions agent-voice-kit
uv tool install agent-voice-kit==0.3.0
agent-voice --version
```

Also verify `https://pypi.org/project/agent-voice-kit/` shows version `0.3.0` and the expected project links. If publication fails, do not reuse or expose tokens; inspect the Trusted Publisher tuple above first.
