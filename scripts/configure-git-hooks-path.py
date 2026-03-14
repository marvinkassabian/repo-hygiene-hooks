#!/usr/bin/env python3

import argparse
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


DEFAULT_HOOK_FILES = ["commit-msg", "pre-push"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Configure repository git hooks path")
    parser.add_argument(
        "--mode",
        choices=["github", "shared", "local"],
        default="github",
        help=(
            "github = download hooks from GitHub into target repo .git cache, "
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
        help="GitHub repository URL used in github mode",
    )
    parser.add_argument(
        "--github-ref",
        default="main",
        help="GitHub ref used in github mode (branch, tag, or commit)",
    )
    parser.add_argument(
        "--hook-files",
        nargs="+",
        default=DEFAULT_HOOK_FILES,
        help="Hook filenames to download from .githooks (default: commit-msg pre-push)",
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


def parse_github_owner_repo(repo_url: str) -> tuple[str, str]:
    match = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?/?$", repo_url)
    if not match:
        raise ValueError(f"Unsupported GitHub repo URL: {repo_url}")
    return match.group("owner"), match.group("repo")


def safe_ref_fragment(ref: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", ref)


def download_text(url: str) -> str:
    try:
        with urlopen(url) as response:
            return response.read().decode("utf-8")
    except HTTPError as exc:
        raise FileNotFoundError(f"Failed to download {url} (HTTP {exc.code}). Ensure the remote ref contains .githooks files and has been pushed.") from exc
    except URLError as exc:
        raise RuntimeError(f"Network error while downloading {url}: {exc.reason}") from exc


def ensure_github_cache(target_repo: Path, repo_url: str, ref: str, hook_files: list[str]) -> Path:
    owner, repo = parse_github_owner_repo(repo_url)

    cache_dir = git_path(target_repo, f"hook-sources/{repo}/{safe_ref_fragment(ref)}/.githooks")
    cache_dir.mkdir(parents=True, exist_ok=True)

    for hook_name in hook_files:
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/.githooks/{hook_name}"
        content = download_text(raw_url)

        hook_path = cache_dir / hook_name
        hook_path.write_text(content, encoding="utf-8")

        mode = hook_path.stat().st_mode
        hook_path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    return cache_dir


def main() -> int:
    args = parse_args()
    target_repo = Path(args.target_repo).expanduser().resolve()

    if args.mode == "github":
        hooks_dir = ensure_github_cache(
            target_repo=target_repo,
            repo_url=args.github_repo,
            ref=args.github_ref,
            hook_files=args.hook_files,
        )
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
