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

# SVN 客户端（svn_service 提交文档用）
SVN_EXE = r"D:\Program Files\VisualSVN Server\bin\svn.exe"

# ===== SVN 集成（提交钩子 + 客户端服务）=====
# 钩子调用平台接口时的鉴权密钥（防止外部伪造提交记录）
SVN_HOOK_SECRET = os.getenv("SVN_HOOK_SECRET", "gjb5000b-hook-2026")
# 是否开启客户端更新下发
SVN_CLIENT_WATCH_ENABLED = True
