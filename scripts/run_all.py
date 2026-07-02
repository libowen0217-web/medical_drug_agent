from __future__ import annotations

import argparse
import ipaddress
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
NODE_MODULES_DIR = FRONTEND_DIR / "node_modules"

BACKEND_PORT = 8000
FRONTEND_PORT = 5173
BACKEND_BIND_URL = f"http://0.0.0.0:{BACKEND_PORT}"
BACKEND_LOCAL_URL = f"http://127.0.0.1:{BACKEND_PORT}"
FRONTEND_BIND_URL = f"http://0.0.0.0:{FRONTEND_PORT}"
FRONTEND_LOCAL_URL = f"http://localhost:{FRONTEND_PORT}/drug-safety"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="同时启动 FastAPI 后端和 Vue 前端。")
    parser.add_argument(
        "--open",
        action="store_true",
        help="启动完成后自动打开一次本机前端页面。默认只打印访问地址。",
    )
    return parser.parse_args()


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def is_backend_healthy(timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(f"{BACKEND_LOCAL_URL}/health", timeout=timeout) as response:
            return response.status == 200
    except (OSError, urllib.error.URLError):
        return False


def wait_for_backend_health(timeout_seconds: int = 30) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if is_backend_healthy(timeout=2.0):
            return True
        time.sleep(1)
    return False


def _private_ipv4_score(ip: str) -> int:
    if ip.startswith("192.168."):
        return 0
    if ip.startswith("10."):
        return 1
    if ip.startswith("172."):
        second = int(ip.split(".")[1])
        if 16 <= second <= 31:
            return 2
    return 9


def _looks_like_virtual_adapter_name(name: str) -> bool:
    lowered = name.lower()
    virtual_keywords = [
        "virtual",
        "vmware",
        "hyper-v",
        "wsl",
        "docker",
        "loopback",
        "vethernet",
        "bluetooth",
    ]
    return any(keyword in lowered for keyword in virtual_keywords)


def _collect_lan_ips_from_ps() -> list[str]:
    if os.name != "nt":
        return []

    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        (
            "Get-NetIPAddress -AddressFamily IPv4 | "
            "Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } | "
            "ForEach-Object { \"$($_.IPAddress)|$($_.InterfaceAlias)\" }"
        ),
    ]
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return []

    candidates: list[tuple[int, str]] = []
    for line in result.stdout.splitlines():
        if "|" not in line:
            continue
        ip, adapter_name = line.split("|", 1)
        ip = ip.strip()
        adapter_name = adapter_name.strip()
        try:
            address = ipaddress.ip_address(ip)
        except ValueError:
            continue
        if not isinstance(address, ipaddress.IPv4Address) or not address.is_private:
            continue
        virtual_penalty = 10 if _looks_like_virtual_adapter_name(adapter_name) else 0
        candidates.append((_private_ipv4_score(ip) + virtual_penalty, ip))

    return [ip for _, ip in sorted(candidates, key=lambda item: (item[0], item[1]))]


def get_lan_ips() -> list[str]:
    ips: list[str] = []

    for ip in _collect_lan_ips_from_ps():
        if ip not in ips:
            ips.append(ip)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            ip = sock.getsockname()[0]
            if ip and ip not in ips:
                address = ipaddress.ip_address(ip)
                if isinstance(address, ipaddress.IPv4Address) and address.is_private:
                    ips.append(ip)
    except (OSError, ValueError):
        pass

    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if ip in ips:
                continue
            try:
                address = ipaddress.ip_address(ip)
            except ValueError:
                continue
            if isinstance(address, ipaddress.IPv4Address) and address.is_private:
                ips.append(ip)
    except OSError:
        pass

    return sorted(ips, key=lambda item: (_private_ipv4_score(item), item))


def _print(message: str) -> None:
    print(message, flush=True)


def _start_backend() -> tuple[subprocess.Popen[str] | None, bool]:
    _print(f"[后端] FastAPI: {BACKEND_BIND_URL}")
    _print(f"[后端] 文档地址: {BACKEND_LOCAL_URL}/docs")

    if is_port_in_use(BACKEND_PORT):
        if is_backend_healthy():
            _print("[后端] 8000 端口已被占用，/health 正常，判断后端已运行。")
            return None, True
        _print("[错误] 8000 端口已被占用，但 /health 不正常。")
        _print("[错误] 请确认占用 8000 的是否为当前项目后端，或释放该端口后重试。")
        return None, False

    _print("[后端] 正在启动 FastAPI...")
    proc = subprocess.Popen(
        [sys.executable, "scripts/run_api.py"],
        cwd=str(PROJECT_ROOT),
        text=True,
    )

    if wait_for_backend_health(timeout_seconds=30):
        _print("[后端] /health 已就绪。")
        return proc, True

    _print("[错误] 后端 30 秒内未通过 /health 检查，已停止继续启动前端。")
    _terminate_process(proc)
    return None, False


def _find_npm_executable() -> str | None:
    return shutil.which("npm.cmd") or shutil.which("npm")


def _start_frontend() -> tuple[subprocess.Popen[str] | None, bool]:
    _print(f"[前端] Vue: {FRONTEND_BIND_URL}")

    if is_port_in_use(FRONTEND_PORT):
        _print("[提示] 5173 端口已被占用，可能前端已经启动。")
        return None, False

    if not NODE_MODULES_DIR.exists():
        _print("[前端] 未检测到 node_modules，请先运行：")
        _print("cd frontend")
        _print("npm install")
        return None, False

    npm_executable = _find_npm_executable()
    if not npm_executable:
        _print("[前端] 未检测到 npm，请先安装 Node.js。")
        return None, False

    _print("[前端] 正在启动 Vue/Vite...")
    proc = subprocess.Popen(
        [npm_executable, "run", "dev"],
        cwd=str(FRONTEND_DIR),
        text=True,
        shell=False,
    )
    return proc, True


def _terminate_process(proc: subprocess.Popen[str] | None) -> None:
    if proc is None or proc.poll() is not None:
        return

    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            proc.terminate()
            proc.wait(timeout=5)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def _print_access_urls(lan_ips: list[str]) -> None:
    _print("[系统] 本机访问:")
    _print(f"  - {FRONTEND_LOCAL_URL}")

    if lan_ips:
        if len(lan_ips) > 1:
            _print("[系统] 检测到多个局域网地址，请优先尝试 192.168 开头的地址：")
        else:
            _print("[系统] 局域网访问:")
        for ip in lan_ips:
            _print(f"  - http://{ip}:{FRONTEND_PORT}/drug-safety")
    else:
        _print("[系统] 未识别到局域网 IP，请使用 ipconfig 手动查看本机 IPv4 地址。")

    _print("[提示] 默认不自动打开浏览器，如需自动打开请使用: python scripts/run_all.py --open")


def main() -> int:
    args = parse_args()
    lan_ips = get_lan_ips()

    backend_proc, backend_ready = _start_backend()
    if not backend_ready:
        return 1

    frontend_proc, frontend_started = _start_frontend()
    _print_access_urls(lan_ips)

    if args.open and frontend_started:
        time.sleep(3)
        webbrowser.open(FRONTEND_LOCAL_URL, new=2)
    elif args.open:
        _print("[提示] 前端端口已占用或未启动，本次不再自动打开新页面。")

    try:
        while True:
            if backend_proc is not None and backend_proc.poll() is not None:
                _print("[后端] 进程已退出。")
                backend_proc = None
            if frontend_proc is not None and frontend_proc.poll() is not None:
                _print("[前端] 进程已退出。")
                frontend_proc = None
            time.sleep(1)
    except KeyboardInterrupt:
        _print("\n[系统] 正在关闭由 run_all.py 启动的子进程，请稍等...")
    finally:
        _terminate_process(frontend_proc)
        _terminate_process(backend_proc)
        _print("[系统] 已停止统一启动脚本。")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
