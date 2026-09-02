@echo off
chcp 65001 >nul
cd /d "%~dp0..\.."
echo ============================================
echo  5000B 管理系统 - 一键启动（后端+前端）
echo ============================================
echo.
echo 即将调用项目根 start.bat 启动：
echo   后端 http://127.0.0.1:8000  （接口文档 /docs）
echo   前端 http://127.0.0.1:8080
echo.
call start.bat
pause
