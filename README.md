# repo-hygiene-hooks

Reusable repository hygiene helpers.

## Canonical hooks

- .githooks/commit-msg
- .githooks/pre-push

These files are intended to be shared by multiple repositories.

## Tools

- scripts/configure-git-hooks-path.py

Backward-compatible alias during migration:

- scripts/setup-git-hooks.py

## Recommended usage (auto-fetch from GitHub)

From a target repository root:

python3 /path/to/repo-hygiene-hooks/scripts/configure-git-hooks-path.py --mode github

This clones or updates repo-hygiene-hooks inside the target repo .git cache and
sets core.hooksPath to that cached .githooks directory using a repo-relative path.

## Other modes

Shared checkout mode:

python3 /path/to/repo-hygiene-hooks/scripts/configure-git-hooks-path.py --mode shared

Local mirror mode:

python3 /path/to/repo-hygiene-hooks/scripts/configure-git-hooks-path.py --mode local
