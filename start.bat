@echo off
chcp 65001 >nul
REM 作者：袁燕
REM 功能：一键启动 GJB5000B 管理平台前后端。
REM   后端 FastAPI -> http://127.0.0.1:8000
REM   前端静态服务 -> http://127.0.0.1:8080
REM 设计：先检测端口占用，已占用则跳过；日志写入项目根 logs/ 目录。

setlocal
set ROOT=%~dp0
set LOGS=%ROOT%logs
if not exist "%LOGS%" mkdir "%LOGS%"

echo ============================================
echo  GJB5000B 管理平台启动器
echo  后端: 127.0.0.1:8000  前端: 127.0.0.1:8080
echo ============================================

REM ---- 启动后端（uvicorn）----
set /a BACKEND_PORT=8000
netstat -ano | findstr ":%BACKEND_PORT%" >nul
if %errorlevel%==0 (
  echo [后端] 端口 %BACKEND_PORT% 已被占用，跳过启动（可能已在运行）
) else (
  echo [后端] 正在启动 uvicorn ...
  start "GJB5000B-Backend" cmd /c "cd /d %ROOT% && set PYTHONPATH=%ROOT% && python run_backend.py > %LOGS%\backend.log 2>&1"
)

REM ---- 启动前端静态服务 ----
set /a FRONTEND_PORT=8080
netstat -ano | findstr ":%FRONTEND_PORT%" >nul
if %errorlevel%==0 (
  echo [前端] 端口 %FRONTEND_PORT% 已被占用，跳过启动（可能已在运行）
) else (
  echo [前端] 正在启动静态服务 ...
  start "GJB5000B-Frontend" cmd /c "cd /d %ROOT%frontend && python -m http.server %FRONTEND_PORT% > %LOGS%\frontend.log 2>&1"
)

echo.
echo 启动完成。浏览器打开: http://127.0.0.1:8080/
echo 日志目录: %LOGS%
echo 按任意键退出本窗口（前后端仍在后台运行）...
pause >nul
endlocal
