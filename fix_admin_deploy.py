#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""上传 admin 修复文件到远程服务器（读取本地 deploy.config.json）"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "deploy.config.json"

if not CONFIG_PATH.exists():
    print("请先创建 deploy.config.json（参考 deploy.config.json.example）")
    sys.exit(1)

config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
REMOTE = f"{config['user']}@{config['server']}"
RP = config["remote_path"]

FILES = [
    ("backend/app/schemas/admin.py", f"{RP}/backend/app/schemas/"),
    ("backend/app/services/admin_service.py", f"{RP}/backend/app/services/"),
]


def run_cmd(cmd, check=True):
    print(f">>> {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}")
    return result


def main():
    for local, remote_dir in FILES:
        run_cmd(f'scp "{ROOT / local}" {REMOTE}:{remote_dir}')

    run_cmd(f'ssh {REMOTE} "cd {RP} && docker compose --env-file .env.deploy restart backend"')
    print("\n完成。请刷新管理后台页面验证。")


if __name__ == "__main__":
    main()
