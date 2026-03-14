#!/usr/bin/env python3

import argparse
import subprocess
import sys


def configure_hooks_path(hooks_path: str) -> int:
    result = subprocess.run(["git", "config", "core.hooksPath", hooks_path], check=False)
    if result.returncode != 0:
        return result.returncode

    result = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return result.returncode

    print(f"Configured git hooks path: {result.stdout.strip()}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Configure repository git hooks path")
    parser.add_argument("--hooks-path", default=".githooks", help="Git hooks path to configure")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return configure_hooks_path(args.hooks_path)


if __name__ == "__main__":
    raise SystemExit(main())
