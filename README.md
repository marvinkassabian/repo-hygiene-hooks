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

## Recommended usage (download from GitHub URL)

From a target repository root:

python3 /path/to/repo-hygiene-hooks/scripts/configure-git-hooks-path.py --mode github

In github mode, the script downloads hook files from:

- https://raw.githubusercontent.com/<owner>/<repo>/<ref>/.githooks/

It stores them in the target repository .git cache and sets core.hooksPath to
that cached location with a repo-relative path. The selected ref must already
contain the .githooks files on GitHub.

## Other modes

Shared checkout mode:

python3 /path/to/repo-hygiene-hooks/scripts/configure-git-hooks-path.py --mode shared

Local mirror mode:

python3 /path/to/repo-hygiene-hooks/scripts/configure-git-hooks-path.py --mode local
