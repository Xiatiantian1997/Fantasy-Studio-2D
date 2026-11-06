@echo off
chcp 65001 >nul
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp001_安装.ps1"
if errorlevel 1 (
  echo.
  echo 安装未完成。请查看上面的错误信息，再尝试安装。
)
pause
