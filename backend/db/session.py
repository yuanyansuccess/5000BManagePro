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
from sqlalchemy.orm import sessionmaker
from backend import config

Engine = create_engine(
    config.DATABASE_URL,
    pool_pre_ping=True,          # 连接存活检测，避免僵死连接（继承智能柜 P7 跨库兼容思路）
    pool_recycle=3600,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)


# 表存在性缓存：已确认存在的表不再重复检查（避免每次请求都 SHOW TABLES）
_ENSURED_TABLES = set()


def ensure_tables(*model_classes):
    """按需确保业务表存在（幂等，带缓存）。
    背景：历史上多次因迁移脚本半途失败/手工 DROP 导致表缺失，
          接口直接 500（前端显示"加载失败"）。本函数做最后一道兜底。"""
    from backend.db import models
    todo = []
    for m in model_classes:
        tname = getattr(m, "__tablename__", None)
        if tname and tname not in _ENSURED_TABLES:
            todo.append(m)
    if not todo:
        return
    models.Base.metadata.create_all(
        Engine, tables=[m.__table__ for m in todo])
    for m in todo:
        _ENSURED_TABLES.add(m.__tablename__)


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
    """启动建表/补列（继承智能柜 P22 schema 自检思路）。
    注意：此处执行的迁移均已做幂等保护（列存在即跳过），可随每次启动安全执行。
    """
    from backend.db import models  # 确保模型注册
    if config.AUTO_CREATE_TABLES:
        models.Base.metadata.create_all(bind=Engine)
        _migrate_risk_columns()
        # SDP 占位符数据按项目维度落地：签署角色/硬件/软件/引用文档等字段 + 资源表
        from backend.db import _migrate_proj_signoff
        try:
            _migrate_proj_signoff.main()
        except Exception as e:
            print("[migrate_proj_signoff] skip:", e)
        # 现有项目补预置：文档规模清单（相关方由 scripts/seed_r105_stake.py 专项管理）
        try:
            from backend.db._seed_doc_scale import seed_doc_scale
            from backend.services import data_service
            for p in data_service.DataService.list_projects(SessionLocal()):
                seed_doc_scale(SessionLocal(), p.project_id)
        except Exception as e:
            print("[seed] skip:", e)


def _migrate_risk_columns():
    """对已有的 risks 表补新列（category/likelihood/impact/risk_value），兼容旧数据。"""
    from sqlalchemy import text
    try:
        cols = [c[0] for c in Engine.connect().execute(text("SHOW COLUMNS FROM risks")).fetchall()]
    except Exception:
        return
    needed = {
        "category": "VARCHAR(32)",
        "likelihood": "INT DEFAULT 3",
        "impact": "INT DEFAULT 3",
        "risk_value": "INT DEFAULT 9",
    }
    with Engine.begin() as conn:
        for col, dtype in needed.items():
            if col not in cols:
                conn.execute(text("ALTER TABLE risks ADD COLUMN %s %s" % (col, dtype)))
