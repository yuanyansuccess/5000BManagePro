@echo off
chcp 65001 >nul
cd /d "%~dp0..\.."
echo ============================================
echo  5000B 管理系统 - 安装后端 Python 依赖
echo ============================================
echo.
echo [1/2] 升级 pip（使用清华镜像加速）...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 goto fail
echo.
echo [2/2] 安装 requirements.txt 中的依赖...
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 goto fail
echo.
echo ============================================
echo  依赖安装完成！
echo  下一步：运行 build\env\02_init_db.bat 初始化数据库
echo  或运行 python build\env\check_env.py 自检
echo ============================================
pause
exit /b 0

:fail
echo.
echo [失败] 依赖安装出错，请检查：
echo   1) Python 是否已安装并勾选 Add to PATH
echo   2) 网络是否可访问（可换手机热点或公司网络重试）
echo   3) 是否以管理员身份运行（一般不需要）
pause
exit /b 1
