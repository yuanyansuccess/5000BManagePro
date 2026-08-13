# -*- coding: utf-8 -*-
"""
数据库会话层（数据层最底层，唯一持有连接）
作者：袁燕
功能：SQLAlchemy 引擎 + Session 工厂，全局唯一入口。
      上层（DAO/Service）绝不直连 MySQL，只通过本模块取 session。
      换数据库只改 config.DATABASE_URL，其余层零改动（解耦驱动）。
设计原则：高内聚（连接管理内聚）、低耦合（上层不感知具体驱动）。
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from backend import config

Engine = create_engine(
    config.DATABASE_URL,
    pool_pre_ping=True,          # 连接存活检测，避免僵死连接（继承智能柜 P7 跨库兼容思路）
    pool_recycle=3600,
    echo=False,
)

SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=Engine)
)


def get_db():
    """
    依赖注入用：FastAPI 路由通过 Depends(get_db) 获取 session，请求结束自动关闭。
    返回：SQLAlchemy Session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """启动建表/补列（继承智能柜 P22 schema 自检思路）。"""
    from backend.db import models  # 确保模型注册
    if config.AUTO_CREATE_TABLES:
        models.Base.metadata.create_all(bind=Engine)
