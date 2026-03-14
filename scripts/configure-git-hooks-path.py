#!/usr/bin/env python3

import argparse
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Configure repository git hooks path")
    parser.add_argument(
        "--mode",
        choices=["shared", "local"],
        default="shared",
        help="shared = point to repo-hygiene-hooks/.githooks, local = copy hooks into target repo",
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
        help="Override path to shared hooks directory (default: <repo-hygiene-hooks>/.githooks)",
    )
    return parser.parse_args()


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


def set_hooks_path(target_repo: Path, hooks_path_value: str) -> int:
    result = subprocess.run(
        ["git", "-C", str(target_repo), "config", "core.hooksPath", hooks_path_value],
        check=False,
    )
    if result.returncode != 0:
        return result.returncode

    verify = subprocess.run(
        ["git", "-C", str(target_repo), "config", "--get", "core.hooksPath"],
        capture_output=True,
        text=True,
        check=False,
    )
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

        # Ensure copied hooks are executable.
        mode = target.stat().st_mode
        target.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def main() -> int:
    args = parse_args()

    target_repo = Path(args.target_repo).expanduser().resolve()
    shared_hooks_dir = resolve_shared_hooks_dir(args.shared_hooks_dir)

    if args.mode == "shared":
        return set_hooks_path(target_repo=target_repo, hooks_path_value=str(shared_hooks_dir))

    local_hooks_dir = (target_repo / args.hooks_path).resolve()
    copy_hooks(shared_dir=shared_hooks_dir, destination_dir=local_hooks_dir)
    rel_path = os.path.relpath(local_hooks_dir, start=target_repo)
    return set_hooks_path(target_repo=target_repo, hooks_path_value=rel_path)


if __name__ == "__main__":
    raise SystemExit(main())
