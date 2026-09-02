# -*- coding: utf-8 -*-
"""
全局配置
作者：袁燕
功能：集中管理数据库连接、SVN、密钥等配置，避免散落各处。
      切换 MySQL/SQLite 只改此处 DATABASE_URL，业务与 DAO 零改动（高内聚低耦合）。
"""
import os

# 项目根目录（backend 的上一级）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 数据库：默认 MySQL（项目方确认）。如需本地轻量可改为 sqlite:///data/platform.db
DATABASE_URL = os.getenv(
    "GJB5000B_DB_URL",
    "mysql+pymysql://root:root@127.0.0.1:3306/gjb5000b?charset=utf8mb4"
)

# 自动建表开关（开发期 True，生产可关）
AUTO_CREATE_TABLES = True

# SVN 三库路径（开发库/受控库/产品库），沿用现有配置管理
SVN_EXE = r"D:\Program Files\VisualSVN Server\bin\svn.exe"
SVN_DEV_REPO = ""
SVN_CTRL_REPO = ""
SVN_PROD_REPO = ""

# ===== SVN 集成（提交钩子 + 客户端服务）=====
# 钩子调用平台接口时的鉴权密钥（防止外部伪造提交记录）
SVN_HOOK_SECRET = os.getenv("SVN_HOOK_SECRET", "gjb5000b-hook-2026")
# 客户端服务轮询间隔（秒），可配置
SVN_POLL_INTERVAL = int(os.getenv("SVN_POLL_INTERVAL", "10"))
# 是否开启客户端更新下发
SVN_CLIENT_WATCH_ENABLED = True
# 平台对外地址（钩子/客户端回连用，可配置）
SVN_PLATFORM_BASE = os.getenv("SVN_PLATFORM_BASE", "http://127.0.0.1:8000")

# RBAC：角色与权限（与前端权限位对齐）
ROLE_ADMIN = "admin"
ROLE_USER = "user"
AUTH_ITEMS = {
    "user_manage": "用户管理",
    "alert_view": "告警查看",
    "tpl_config": "模板配置",
    "base_edit": "基础编辑",
    "sys_config": "系统配置",
}
