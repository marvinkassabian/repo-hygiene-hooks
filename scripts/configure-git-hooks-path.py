#!/usr/bin/env python3

import argparse
import os
import shutil
import stat
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Configure repository git hooks path")
    parser.add_argument(
        "--mode",
        choices=["github", "shared", "local"],
        default="github",
        help=(
            "github = sync hooks from remote into target repo .git cache, "
            "shared = point to an existing repo-hygiene-hooks checkout, "
            "local = copy hooks into target repo"
        ),
    )
    parser.add_argument(
        "--target-repo",
        default=".",
        help="Target repository where git config should be updated (default: current directory)",
    )
    parser.add_argument(
        "--hooks-path",
        default=".githooks",
        help="hooks path value for local mode (default: .githooks)",
    )
    parser.add_argument(
        "--shared-hooks-dir",
        default="",
        help="Override path to shared hooks directory for shared/local mode",
    )
    parser.add_argument(
        "--github-repo",
        default="https://github.com/marvinkassabian/repo-hygiene-hooks.git",
        help="GitHub repo URL used in github mode",
    )
    parser.add_argument(
        "--github-ref",
        default="main",
        help="Git ref used in github mode (branch, tag, or commit)",
    )
    return parser.parse_args()


def run(command: list[str], capture_output: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=False, text=True, capture_output=capture_output)


def repo_hygiene_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_shared_hooks_dir(override: str) -> Path:
    if override:
        hooks_dir = Path(override).expanduser().resolve()
    else:
        hooks_dir = repo_hygiene_root() / ".githooks"

    if not hooks_dir.is_dir():
        raise FileNotFoundError(f"Shared hooks directory not found: {hooks_dir}")

    return hooks_dir


def git_path(target_repo: Path, pathspec: str) -> Path:
    result = run(["git", "-C", str(target_repo), "rev-parse", "--git-path", pathspec], capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"Failed to resolve git path for {pathspec}")
    return Path(result.stdout.strip()).resolve()


def set_hooks_path(target_repo: Path, hooks_path_value: str) -> int:
    result = run(["git", "-C", str(target_repo), "config", "core.hooksPath", hooks_path_value])
    if result.returncode != 0:
        return result.returncode

    verify = run(["git", "-C", str(target_repo), "config", "--get", "core.hooksPath"], capture_output=True)
    if verify.returncode != 0:
        return verify.returncode

    print(f"Configured git hooks path: {verify.stdout.strip()}")
    return 0


def copy_hooks(shared_dir: Path, destination_dir: Path) -> None:
    destination_dir.mkdir(parents=True, exist_ok=True)

    for source in sorted(shared_dir.iterdir()):
        if not source.is_file():
            continue

        target = destination_dir / source.name
        shutil.copy2(source, target)

        mode = target.stat().st_mode
        target.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def ensure_github_cache(target_repo: Path, repo_url: str, ref: str) -> Path:
    cache_root = git_path(target_repo, "hook-sources/repo-hygiene-hooks")

    if not (cache_root / ".git").is_dir():
        cache_root.parent.mkdir(parents=True, exist_ok=True)
        clone_result = run(["git", "clone", repo_url, str(cache_root)])
        if clone_result.returncode != 0:
            raise RuntimeError(f"Failed to clone {repo_url} into {cache_root}")

    set_url_result = run(["git", "-C", str(cache_root), "remote", "set-url", "origin", repo_url])
    if set_url_result.returncode != 0:
        raise RuntimeError(f"Failed to set origin URL for {cache_root}")

    fetch_result = run(["git", "-C", str(cache_root), "fetch", "--all", "--tags"])
    if fetch_result.returncode != 0:
        raise RuntimeError(f"Failed to fetch updates for {cache_root}")

    checkout_result = run(["git", "-C", str(cache_root), "checkout", ref])
    if checkout_result.returncode != 0:
        raise RuntimeError(f"Failed to checkout ref {ref} in {cache_root}")

    pull_result = run(["git", "-C", str(cache_root), "pull", "--ff-only", "origin", ref])
    if pull_result.returncode != 0:
        # Non-branch refs (tag/SHA) do not need pull.
        pass

    hooks_dir = cache_root / ".githooks"
    if not hooks_dir.is_dir():
        raise FileNotFoundError(f"Missing .githooks in cached repo: {cache_root}. Push a commit containing .githooks to the remote, or use --mode shared temporarily.")

    return hooks_dir


def main() -> int:
    args = parse_args()
    target_repo = Path(args.target_repo).expanduser().resolve()

    if args.mode == "github":
        hooks_dir = ensure_github_cache(target_repo=target_repo, repo_url=args.github_repo, ref=args.github_ref)
        rel_path = os.path.relpath(hooks_dir, start=target_repo)
        return set_hooks_path(target_repo=target_repo, hooks_path_value=rel_path)

    shared_hooks_dir = resolve_shared_hooks_dir(args.shared_hooks_dir)

    if args.mode == "shared":
        return set_hooks_path(target_repo=target_repo, hooks_path_value=str(shared_hooks_dir))

    local_hooks_dir = (target_repo / args.hooks_path).resolve()
    copy_hooks(shared_dir=shared_hooks_dir, destination_dir=local_hooks_dir)
    rel_path = os.path.relpath(local_hooks_dir, start=target_repo)
    return set_hooks_path(target_repo=target_repo, hooks_path_value=rel_path)


if __name__ == "__main__":
    raise SystemExit(main())
