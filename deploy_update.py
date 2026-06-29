#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Windows-friendly deploy script (UTF-8 paths)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARCHIVE = "badminton-deploy.tar"
EXCLUDES = [
    "./node_modules",
    "./frontend/node_modules",
    "./frontend/dist",
    "./backend/data",
    "./backups",
    "./.git",
    "./.env",
    "./.env.deploy",
    "./backend/.env",
    "./backend/.env.local.sqlite",
    "./backend/.env.production.local",
    "./frontend/.env.local",
    "./badminton-deploy.tar",
    "./__pycache__",
]


def load_config() -> dict:
    cfg_path = ROOT / "deploy.config.json"
    if not cfg_path.exists():
        raise SystemExit(f"Missing {cfg_path}")
    with cfg_path.open(encoding="utf-8") as f:
        return json.load(f)


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd or ROOT, check=True)


def pack() -> None:
    archive = ROOT / ARCHIVE
    if archive.exists():
        archive.unlink()
    cmd = ["tar", "-cf", ARCHIVE]
    for pattern in EXCLUDES:
        cmd.append(f"--exclude={pattern}")
    cmd.append(".")
    run(cmd)
    print(f"[OK] Pack done: {ARCHIVE} ({archive.stat().st_size} bytes)")


def main() -> int:
    upload_env = "--upload-env" in sys.argv
    pack_only = "--pack-only" in sys.argv

    cfg = load_config()
    server = cfg["server"]
    user = cfg["user"]
    remote_path = cfg["remote_path"]
    remote = f"{user}@{server}"
    remote_dir = f"{remote}:{remote_path}/"

    print("[1/4] Pack")
    pack()
    if pack_only:
        print(f"Next: scp {ARCHIVE} {remote_dir}")
        return 0

    print(f"[2/4] Upload -> {remote}:{remote_path}")
    run(["ssh", remote, f"mkdir -p {remote_path}"])
    run(["scp", ARCHIVE, remote_dir])
    run(["scp", "deploy-remote.sh", remote_dir])

    if upload_env:
        env_file = ROOT / ".env.deploy"
        if not env_file.exists():
            raise SystemExit("local .env.deploy not found")
        print("[INFO] Upload local .env.deploy (overwrite remote)")
        run(["scp", str(env_file), remote_dir])
    else:
        print("[INFO] Keep remote .env.deploy")
        check = subprocess.run(
            ["ssh", remote, f'bash -lc "test -f {remote_path}/.env.deploy"'],
            cwd=ROOT,
        )
        if check.returncode != 0:
            raise SystemExit(
                f"remote {remote_path}/.env.deploy not found; "
                "configure on server or run: python deploy_update.py --upload-env"
            )

    print("[3/4] Remote deploy")
    deploy_cmd = (
        f'bash -lc "chmod +x {remote_path}/deploy-remote.sh; '
        f'cd {remote_path}; ./deploy-remote.sh"'
    )
    run(["ssh", remote, deploy_cmd])

    print(f"\n[4/4] Done: http://{server}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] command failed (exit {e.returncode})", file=sys.stderr)
        raise SystemExit(e.returncode)
