@echo off
chcp 65001 >nul
REM 作者：袁燕
REM 功能：一键启动 GJB5000B 管理平台（后端 8000、前端 8080）。

setlocal enabledelayedexpansion
set ROOT=%~dp0
set LOGS=%ROOT%\logs
if not exist "%LOGS%" mkdir "%LOGS%"

echo ============================================
echo  GJB5000B 管理平台启动器
echo  后端: 127.0.0.1:8000  前端: 127.0.0.1:8080
echo ============================================
echo.
echo [1/4] 正在停止旧服务 ...
call :stop_port 8000
call :stop_port 8080

echo [2/4] 正在启动后端 ...
start "GJB5000B-Backend" cmd /c "cd /d %ROOT% && set PYTHONPATH=%ROOT% && python run_backend.py ^> %LOGS%\backend.log 2^>^&1"

echo [3/4] 正在启动前端 ...
start "GJB5000B-Frontend" cmd /c "cd /d %ROOT% && set PYTHONPATH=%ROOT% && python scripts/frontend_server.py 8080 frontend ^> %LOGS%\frontend.log 2^>^&1"

echo [4/4] 正在等待服务就绪 ...
set TRY=0

:wait
ping -n 3 127.0.0.1 >nul 2>&1
set /a TRY+=1
set OK_B=0
set OK_F=0
netstat -ano | findstr "LISTENING" | findstr ":8000 " >nul 2>&1 && set OK_B=1
netstat -ano | findstr "LISTENING" | findstr ":8080 " >nul 2>&1 && set OK_F=1
if "%OK_B%"=="1" if "%OK_F%"=="1" goto ok
if %TRY% lss 10 goto wait

echo.
echo 启动失败：服务未能就绪。
echo 请查看日志：%LOGS%\backend.log
echo 处理方法：关掉本窗口，重新双击 start.bat 再试一次。
echo.
pause >nul
goto :eof

:ok
echo.
echo ============================================
echo  启动成功！
echo  请在浏览器打开: http://127.0.0.1:8080/
echo  关闭本窗口不影响系统运行。
echo ============================================
echo.
pause >nul
goto :eof

:stop_port
set PORT=%1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr "LISTENING" ^| findstr ":%PORT% "') do (
  taskkill /F /PID %%a /T >nul 2>&1
)
REM 兜底清理残留后端进程 防止孤儿worker占用端口
if "%PORT%"=="8000" powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object {$_.CommandLine -match 'run_backend|backend.main'} | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>&1
ping -n 6 127.0.0.1 >nul 2>&1
goto :eof
