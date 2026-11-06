#!/usr/bin/env python3
"""Report publication inventory without restricting file types or binary data.

Every file deliberately tracked in OpenD578 is publishable by this project
check. GitHub's own upload limits and repository permissions still apply.
"""

from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    process = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=False
    )
    if process.returncode != 0:
        print("Publication check: unable to list tracked files with git")
        return 1

    entries = [p for p in process.stdout.split(b"\0") if p]
    total_size = 0
    missing = 0
    for raw in entries:
        rel = raw.decode("utf-8", errors="surrogateescape")
        path = ROOT / rel
        try:
            if path.is_file():
                total_size += path.stat().st_size
            else:
                missing += 1
        except OSError:
            missing += 1

    print(
        f"Publication check: {len(entries)} tracked entries, "
        f"{total_size:,} bytes, {missing} absent or non-regular entries"
    )
    print("Publication policy: any file format and binary content allowed")
    if missing:
        print("Note: files absent from the worktree were not measured (non-blocking)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
