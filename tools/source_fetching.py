from __future__ import annotations

import argparse
import hashlib
import subprocess
import urllib.request
from pathlib import Path


USER_AGENT = "ocaml-ecma-regex-source-fetch/0.0 (+test evidence)"


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def git_head(dest: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(dest), "rev-parse", "HEAD"], text=True
    ).strip()


def git_fetch_main(source_family: str, repo_url: str, default_dest: str) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-url", default=repo_url)
    parser.add_argument("--dest", default=default_dest)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    dest = Path(args.dest)
    git_dir = dest / ".git"
    checkout_exists = git_dir.is_dir()
    action = "fetch" if checkout_exists else "clone"

    print(f"source_family\t{source_family}")
    print(f"repo_url\t{args.repo_url}")
    print(f"destination\t{dest}")
    print(f"checkout_exists\t{bool_text(checkout_exists)}")
    print(f"planned_action\t{action}")
    print(f"dry_run\t{bool_text(args.dry_run)}")

    if args.dry_run:
        return

    dest.parent.mkdir(parents=True, exist_ok=True)
    if checkout_exists:
        subprocess.run(
            ["git", "-C", str(dest), "fetch", "--tags", "--prune"],
            check=True,
        )
    else:
        subprocess.run(["git", "clone", args.repo_url, str(dest)], check=True)

    print(f"revision\t{git_head(dest)}")


def fetch_url(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_with_checksum(target: Path, data: bytes) -> str:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    digest = sha256_bytes(data)
    target.with_suffix(target.suffix + ".sha256").write_text(
        f"{digest}  {target.name}\n", encoding="utf-8"
    )
    return digest
