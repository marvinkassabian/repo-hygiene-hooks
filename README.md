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

## Recommended usage (no local .githooks copy)

From a target repository root:

python3 /path/to/repo-hygiene-hooks/scripts/configure-git-hooks-path.py --mode shared

This sets core.hooksPath to the shared hooks directory inside repo-hygiene-hooks.

## Optional local mirror mode

python3 /path/to/repo-hygiene-hooks/scripts/configure-git-hooks-path.py --mode local

This copies hooks into the target repository and points core.hooksPath to that local path.
