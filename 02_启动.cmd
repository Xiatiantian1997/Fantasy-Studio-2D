@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONDONTWRITEBYTECODE=1"
if not exist "%~dp0runtime\ComfyUI_windows_portable\python_embeded\python.exe" (
  echo 请先运行 01_安装.cmd
  pause
  exit /b 1
)
"%~dp0runtime\ComfyUI_windows_portable\python_embeded\python.exe" -s "%~dp0launcher.py"
echo.
echo 启动器已退出。按任意键关闭。
pause >nul
