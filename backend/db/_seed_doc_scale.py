# -*- coding: utf-8 -*-
"""
文档规模预置数据（对标 R121 TABLE 6 文档规模估计）。作者：袁燕
功能：新建项目时预置 R121 真实文档清单（11 类文档，单位 A4 页）。
"""
from backend.db.models import DocScale

# (code, name, pages_new)，pages_reuse 默认 0（新建项目尚未复用）
R121_DOC_SCALE = [
    ("SDP", "软件开发计划", 40),
    ("SQAP", "软件质量保证计划", 8),
    ("SRS", "软件需求规格说明", 20),
    ("SDD", "软件设计说明", 40),
    ("SCIP", "软件配置项测试计划", 15),
    ("SCITP", "软件配置项测试说明", 20),
    ("SCITR", "软件配置项测试报告", 24),
    ("SPS", "软件产品规格说明", 4),
    ("SVER", "软件版本说明", 7),
    ("SUM", "软件用户手册", 10),
    ("SWORK", "软件研制工作总结", 15),
]


def seed_doc_scale(db, project_id: str):
    """新建项目预置 R121 标准文档规模清单。已存在则跳过。"""
    from backend.dao import doc_scale_dao
    exists = doc_scale_dao.DocScaleDao.list_by_project(db, project_id)
    if exists:
        return
    for code, name, pages in R121_DOC_SCALE:
        obj = DocScale(project_id=project_id, code=code, name=name,
                       pages_new=pages, pages_reuse=0)
        db.add(obj)
    db.commit()
