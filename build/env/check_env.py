# -*- coding: utf-8 -*-
"""
5000B 管理系统 —— 环境自检工具（新手第一步必跑）

用法（在【项目根目录】执行）：
    python build/env/check_env.py

逐项检查并给出修复建议：
  1. Python 版本（要求 >= 3.8）
  2. pip 是否可用
  3. 后端依赖包（fastapi / uvicorn / sqlalchemy / pymysql / python-docx）
  4. MySQL 服务是否安装
  5. MySQL 3306 端口是否通
  6. 数据库 gjb5000b 是否可连通
  7. 后端 8000 / 前端 8080 端口占用情况

全部 [OK] 后即可运行 start.bat 启动系统。
"""
import os
import socket
import subprocess
import sys

# MySQL 客户端默认安装路径（若你装在其他目录，请修改这里）
MYSQL_BIN = r"C:\Program Files\MySQL\MySQL Server 5.7\bin\mysql.exe"
CONN = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "root",
    "db": "gjb5000b",
}


def port_open(host, port, timeout=1.0):
    s = socket.socket()
    s.settimeout(timeout)
    try:
        return s.connect_ex((host, port)) == 0
    finally:
        s.close()


def main():
    print("=" * 62)
    print("5000B 管理系统 环境自检")
    print("=" * 62)

    # 1) Python 版本
    v = sys.version_info
    ok_py = (v.major, v.minor) >= (3, 8)
    print("[%s] Python 版本：%d.%d.%d（要求 >= 3.8）"
          % ("OK" if ok_py else "失败", v.major, v.minor, v.micro))

    # 2) pip
    try:
        r = subprocess.run([sys.executable, "-m", "pip", "--version"],
                           capture_output=True, text=True)
        ok_pip = r.returncode == 0
        out = (r.stdout or r.stderr or "").strip().splitlines()
        print("[%s] pip：%s" % ("OK" if ok_pip else "失败",
                                out[0] if out else "不可用"))
    except Exception as e:
        print("[失败] pip：%s" % e)

    # 3) 后端依赖
    for mod, tip in (("fastapi", "fastapi"), ("uvicorn", "uvicorn"),
                     ("sqlalchemy", "sqlalchemy"), ("pymysql", "pymysql"),
                     ("docx", "python-docx")):
        try:
            __import__(mod)
            print("[OK] 依赖 %s 已安装" % mod)
        except ImportError:
            print("[失败] 依赖 %s 未安装 -> 运行 build/env/01_install_deps.bat" % tip)

    # 4) MySQL 服务
    try:
        r = subprocess.run(["sc", "query", "type=", "service", "state=", "all"],
                           capture_output=True, text=True)
        names = [ln.split(":", 1)[1].strip()
                 for ln in (r.stdout or "").splitlines() if "SERVICE_NAME" in ln]
        mysql_svc = [n for n in names if n.lower().startswith("mysql")]
        print("[%s] MySQL 服务：%s" % ("OK" if mysql_svc else "失败",
                                     "、".join(mysql_svc) if mysql_svc else "未检测到，请先安装 MySQL 5.7"))
    except Exception as e:
        print("[失败] 检测 MySQL 服务出错：%s" % e)

    # 5) 3306 端口
    ok_3306 = port_open("127.0.0.1", 3306)
    print("[%s] MySQL 3306 端口：%s"
          % ("OK" if ok_3306 else "失败", "已监听" if ok_3306 else "未通，请启动 MySQL 服务"))

    # 6) 数据库连通
    if ok_3306 and os.path.exists(MYSQL_BIN):
        cmd = [MYSQL_BIN,
               "--user=%s" % CONN["user"], "--password=%s" % CONN["password"],
               "--host=%s" % CONN["host"], "--port=%s" % CONN["port"],
               "--default-character-set=utf8mb4", CONN["db"], "-e", "SELECT 1;"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        ok_db = r.returncode == 0
        print("[%s] 数据库 %s 连通：%s"
              % ("OK" if ok_db else "失败", CONN["db"],
                 "正常" if ok_db else (r.stderr or "").strip()[:150]))
        if not ok_db:
            print("       提示：若提示 Unknown database，先运行 build/env/02_init_db.bat 建库并导入数据")
    else:
        print("[跳过] 数据库连通检查（3306 未通，或 mysql.exe 不在：%s）" % MYSQL_BIN)

    # 7) 端口占用
    for p, name in ((8000, "后端"), (8080, "前端")):
        used = port_open("127.0.0.1", p)
        print("[%s] %s端口 %d：%s"
              % ("OK" if not used else "提示", name, p,
                 "空闲，可启动" if not used else "已被占用（若服务已启动属正常；否则需清理）"))

    print("=" * 62)
    print("自检完成。全部 [OK] 后，运行项目根 start.bat 即可启动系统。")
    print("=" * 62)


if __name__ == "__main__":
    main()
