"""LocalStudio startup manager for ComfyUI Portable (Windows / NVIDIA)."""
from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORTABLE = ROOT / "runtime" / "ComfyUI_windows_portable"
PYTHON = PORTABLE / "python_embeded" / "python.exe"
COMFY_MAIN = PORTABLE / "ComfyUI" / "main.py"
COMFY_URL = "http://127.0.0.1:8190"
APP_URL = "http://127.0.0.1:7865"


def reachable(url, *, expect=None):
    try:
        with urllib.request.urlopen(url, timeout=1.5) as resp:
            data = resp.read(100)
            return resp.status == 200 and (expect is None or expect in data)
    except (urllib.error.URLError, TimeoutError, ValueError):
        return False


def main():
    if os.name != "nt":
        print("此启动器仅适用于 Windows。")
        return 1
    if not PYTHON.is_file() or not COMFY_MAIN.is_file():
        print("尚未安装运行环境。请先双击 01_安装.cmd。")
        return 2
    env = os.environ.copy()
    for name in ("cache", "temp", "output", "input"):
        (ROOT / name).mkdir(parents=True, exist_ok=True)
    dirs = {
        "TEMP": ROOT / "temp", "TMP": ROOT / "temp",
        "HF_HOME": ROOT / "cache" / "huggingface",
        "HUGGINGFACE_HUB_CACHE": ROOT / "cache" / "huggingface" / "hub",
        "TORCH_HOME": ROOT / "cache" / "torch",
        "PIP_CACHE_DIR": ROOT / "cache" / "pip",
        "UV_CACHE_DIR": ROOT / "cache" / "uv",
        "XDG_CACHE_HOME": ROOT / "cache" / "xdg",
    }
    for name, path in dirs.items():
        path.mkdir(parents=True, exist_ok=True)
        env[name] = str(path)
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["STUDIO_COMFY_URL"] = COMFY_URL
    env["STUDIO_PORT"] = "7865"

    if reachable(APP_URL + "/api/status"):
        print("本地画室界面已经启动：", APP_URL)
        webbrowser.open(APP_URL)
        return 0

    processes = []
    try:
        if not reachable(COMFY_URL + "/system_stats", expect=b"devices"):
            # Check that the port is not occupied by a non-Comfy process.
            import socket
            with socket.socket() as s:
                if s.connect_ex(("127.0.0.1", 8190)) == 0:
                    print("8190 端口已被其他程序占用。请关闭该程序后重试。")
                    return 3
            cmd = [
                str(PYTHON), "-s", str(COMFY_MAIN),
                "--windows-standalone-build", "--listen", "127.0.0.1",
                "--port", "8190", "--lowvram", "--disable-auto-launch",
                "--output-directory", str(ROOT / "output"),
                "--input-directory", str(ROOT / "input"),
                "--temp-directory", str(ROOT / "temp"),
            ]
            print("启动 ComfyUI GPU 后端（RTX 显卡 / lowvram）…")
            processes.append(subprocess.Popen(cmd, cwd=str(PORTABLE), env=env))
        print("启动简洁中文界面…")
        processes.append(subprocess.Popen([str(PYTHON), "-s", str(ROOT / "app" / "server.py")], cwd=str(ROOT), env=env))
        for _ in range(50):
            if reachable(APP_URL + "/api/status"):
                webbrowser.open(APP_URL)
                print("界面已打开：", APP_URL)
                print("后端服务：", COMFY_URL)
                print("保存目录：", ROOT / "output")
                print("保持此窗口运行；按 Ctrl+C 可以关闭。")
                break
            if processes[-1].poll() is not None:
                print("界面服务异常退出，检查上面的错误。")
                return 4
            time.sleep(.2)
        else:
            print("界面未能在 10 秒内启动，请检查端口是否被占用。")
            return 5
        while all(p.poll() is None for p in processes):
            time.sleep(.5)
        print("某个服务已退出。")
        return 0
    except KeyboardInterrupt:
        print("\n正在停止本地服务…")
        return 0
    finally:
        for p in reversed(processes):
            if p.poll() is None:
                p.terminate()
        for p in reversed(processes):
            try:
                p.wait(timeout=8)
            except subprocess.TimeoutExpired:
                p.kill()


if __name__ == "__main__":
    sys.exit(main())
