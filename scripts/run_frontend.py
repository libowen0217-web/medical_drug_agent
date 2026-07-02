from __future__ import annotations

import subprocess
import shutil
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
NODE_MODULES_DIR = FRONTEND_DIR / "node_modules"


def main() -> int:
    if not FRONTEND_DIR.exists():
        print("frontend 目录不存在，请先确认前端文件已创建。")
        return 1

    if not NODE_MODULES_DIR.exists():
        print("未检测到 frontend/node_modules，请先运行：")
        print("cd frontend")
        print("npm install")
        return 1

    npm_executable = shutil.which("npm.cmd") or shutil.which("npm")
    if not npm_executable:
        print("未检测到 npm，请先安装 Node.js。")
        return 1

    command = [npm_executable, "run", "dev"]
    return subprocess.call(command, cwd=str(FRONTEND_DIR))


if __name__ == "__main__":
    raise SystemExit(main())
