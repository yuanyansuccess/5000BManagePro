@echo off
chcp 65001 >nul
cd /d "%~dp0..\.."
set MYSQL=C:\Program Files\MySQL\MySQL Server 5.7\bin\mysql.exe
set DBUSER=root
set DBPWD=root
set DBNAME=gjb5000b

echo ============================================
echo  5000B 管理系统 - 初始化数据库
echo ============================================
echo.

if not exist "%MYSQL%" (
  echo [失败] 未找到 mysql.exe：%MYSQL%
  echo 请修改本脚本第 4 行 set MYSQL= 为你本机的 mysql.exe 实际路径
  pause
  exit /b 1
)

echo [1/3] 创建数据库 %DBNAME%（如已存在则跳过）...
"%MYSQL%" --user=%DBUSER% --password=%DBPWD% --host=127.0.0.1 --port=3306 --default-character-set=utf8mb4 -e "CREATE DATABASE IF NOT EXISTS %DBNAME% DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"
if errorlevel 1 goto fail

echo [2/3] 导入初始数据 database\%DBNAME%.sql（约 800KB，请稍候）...
"%MYSQL%" --user=%DBUSER% --password=%DBPWD% --host=127.0.0.1 --port=3306 --default-character-set=utf8mb4 %DBNAME% < database\%DBNAME%.sql
if errorlevel 1 goto fail

echo [3/3] 校验：列出导入的表...
"%MYSQL%" --user=%DBUSER% --password=%DBPWD% --host=127.0.0.1 --port=3306 --default-character-set=utf8mb4 %DBNAME% -e "SHOW TABLES;"

echo.
echo ============================================
echo  数据库初始化完成！
echo  下一步：运行项目根 start.bat 启动系统
echo ============================================
pause
exit /b 0

:fail
echo.
echo [失败] 数据库操作出错，请检查：
echo   1) MySQL 服务是否已启动（任务管理器-服务 或 net start MySQL5）
echo   2) 本脚本中的账号密码（默认 root/root）是否与你的 MySQL 一致
echo   3) database\%DBNAME%.sql 文件是否存在
pause
exit /b 1
