@echo off
chcp 65001 >nul
rem ============================================================
rem  5000B 管理系统 - 一键下载环境安装包
rem  说明：安装包体积大（MySQL 约 300MB、Python 约 25MB），
rem        不适合放进 Git 仓库（会拖慢 clone/推送，且 GitHub 单文件限 100MB）。
rem        因此本脚本负责【自动下载】，下载目录 build\tools\installers\ 已加入
rem        .gitignore（不入库），需要时随时可重新下载。
rem ============================================================
cd /d "%~dp0"
set DL=%~dp0installers
if not exist "%DL%" mkdir "%DL%"

echo ============================================
echo  开始下载环境安装包到：%DL%
echo  若下载慢，可换网络或用手机热点重试
echo ============================================
echo.

echo [1/3] 下载 Python 3.9.13 (64位)...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.9.13/python-3.9.13-amd64.exe' -OutFile '%DL%\python-3.9.13-amd64.exe'"
if errorlevel 1 echo   [警告] Python 下载失败，请手动下载或重试

echo [2/3] 下载 MySQL 5.7.44 (MSI 64位)...
powershell -Command "Invoke-WebRequest -Uri 'https://cdn.mysql.com/Downloads/MySQLInstaller/mysql-installer-community-5.7.44.0.msi' -OutFile '%DL%\mysql-installer-5.7.44.msi'"
if errorlevel 1 echo   [警告] MySQL 下载失败（若官网改版，请从 https://dev.mysql.com/downloads/mysql/5.7.html 手动下载后放入本目录）

echo [3/3] 下载 Git (64位)...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/git-for-windows/git/releases/download/v2.45.2.windows.1/Git-2.45.2-64-bit.exe' -OutFile '%DL%\Git-2.45.2-64-bit.exe'"
if errorlevel 1 echo   [警告] Git 下载失败，请手动下载或重试

echo.
echo ============================================
echo  下载完成，目录内容：
dir "%DL%"
echo.
echo  接下来请按《环境搭建手册》第 2~4 章依次安装。
echo ============================================
pause
