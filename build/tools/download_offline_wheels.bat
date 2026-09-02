@echo off
chcp 65001 >nul
rem ============================================================
rem  5000B 管理系统 - 下载后端依赖离线包（内网/断网部署用）
rem  在有网的机器上运行，把依赖下载成 wheel 包到 build\tools\offline_wheels\
rem  再把整个 offline_wheels 目录拷到目标机器，执行：
rem    python -m pip install --no-index --find-links=build\tools\offline_wheels -r requirements.txt
rem ============================================================
cd /d "%~dp0..\.."
set OL=%~dp0offline_wheels
if not exist "%OL%" mkdir "%OL%"

echo 正在下载后端依赖离线包到：%OL%
echo （首次运行可能需要几分钟，请耐心等待）
echo.
python -m pip download -r requirements.txt -d "%OL%" -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
  echo.
  echo [失败] 下载出错。请确认已安装 Python 且网络可用后重试。
  pause
  exit /b 1
)

echo.
echo ============================================
echo  离线包下载完成，文件数：
dir "%OL%" | findstr /c:".whl" /c:".tar.gz" | find /c ":"
echo.
echo  部署到目标机器后执行：
echo  python -m pip install --no-index --find-links=build\tools\offline_wheels -r requirements.txt
echo ============================================
pause
