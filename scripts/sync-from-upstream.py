#!/usr/bin/env python3
"""
Sync files and directories from an upstream git repository into the current repo.

Usage:
    python3 sync-from-upstream.py [options]

See --help for details.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd, cwd = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)


def clone_and_checkout(repo_url: str, branch: str, dest: Path) -> None:
    print(f"Cloning {repo_url} @ {branch} ...")
    run(["git", "clone", "--depth=1", "--branch", branch, repo_url, str(dest)])


def copy_paths(source_root: Path, dest_root: Path, paths: list[str]) -> list[Path]:
    """Copy each path from source_root into dest_root, returning copied dest paths."""
    copied = []
    for rel in paths:
        src = source_root / rel
        dst = dest_root / rel

        if not src.exists():
            print(f"Warning: {rel!r} not found in upstream repo, skipping.", file=sys.stderr)
            continue

        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        copied.append(Path(rel))
        print(f"  Copied: {rel}")

    return copied


def git_add_and_commit(repo_root: Path, paths: list[Path], message: str) -> None:
    add_args = ["git", "add"] + [str(p) for p in paths]
    run(add_args, cwd=repo_root)

    result = run(["git", "diff", "--cached", "--quiet"], cwd=repo_root, check=False)
    if result.returncode == 0:
        print("Nothing changed — no commit created.")
        return

    run(["git", "commit", "-m", message], cwd=repo_root)
    result = run(["git", "log", "-1", "--oneline"], cwd=repo_root)
    print(f"Committed: {result.stdout.strip()}")


def current_repo_root() -> Path:
    result = run(["git", "rev-parse", "--show-toplevel"])
    return Path(result.stdout.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync files/directories from an upstream git repo into this repo."
    )
    parser.add_argument("--repo", required=True, help="URL of the upstream git repository")
    parser.add_argument("--branch", default="main", help="Branch to check out (default: main)")
    parser.add_argument(
        "--path",
        dest="paths",
        action="append",
        required=True,
        metavar="REL_PATH",
        help="Relative path (file or directory) to copy; may be specified multiple times",
    )
    parser.add_argument(
        "--message",
        "-m",
        default=None,
        help="Commit message (default: auto-generated)",
    )
    parser.add_argument(
        "--dest-root",
        default=None,
        help="Root of the destination repo (default: git root of the current working directory)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    dest_root = Path(args.dest_root) if args.dest_root else current_repo_root()
    commit_message = args.message or (
        f"Sync {', '.join(args.paths)} from {args.repo} @ {args.branch}"
    )

    with tempfile.TemporaryDirectory(prefix="sync-upstream-") as tmpdir:
        upstream = Path(tmpdir) / "upstream"
        clone_and_checkout(args.repo, args.branch, upstream)

        copied = copy_paths(upstream, dest_root, args.paths)

    if not copied:
        print("No files were copied.", file=sys.stderr)
        sys.exit(1)

    git_add_and_commit(dest_root, copied, commit_message)


if __name__ == "__main__":
    main()
