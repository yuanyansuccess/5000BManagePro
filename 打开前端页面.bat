@echo off
chcp 65001 >nul
REM 作者：袁燕
REM 功能：启动前端服务并打开浏览器页面（后端未启动时仅前端可看，数据需后端）。

setlocal
set ROOT=%~dp0
set URL=http://127.0.0.1:8080/

REM 端口 8080 已监听则不再重复启动前端服务
netstat -ano | findstr "LISTENING" | findstr ":8080 " >nul 2>&1
if %errorlevel%==0 goto open

echo 正在启动前端服务(8080) ...
start "GJB5000B-Frontend" /min cmd /c "cd /d %ROOT% && python scripts/frontend_server.py 8080 frontend"

REM 等待前端端口就绪，最多约 15 秒
set TRY=0
:wait
ping -n 2 127.0.0.1 >nul 2>&1
netstat -ano | findstr "LISTENING" | findstr ":8080 " >nul 2>&1
if %errorlevel%==0 goto open
set /a TRY+=1
if %TRY% lss 15 goto wait

echo 前端服务启动失败，请查看 logs\frontend.log 或先用 start.bat 启动整个系统。
pause
goto :eof

:open
echo 前端页面: %URL%
start "" %URL%
ping -n 3 127.0.0.1 >nul 2>&1
goto :eof
