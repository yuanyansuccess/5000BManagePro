# -*- coding: utf-8 -*-
"""补齐全局 SVN 文档路径映射（GLOBAL 维度，袁总要求：所有项目共用）。作者：袁燕"""
import sys
sys.path.insert(0, 'd:/5000/5000BManagePro')
from backend.db.session import SessionLocal
from backend.db.models import SvnDocPathMap

# 文档类型 -> SVN 相对路径（对标 R105/R121 仓库结构）
PATHS = {
    "SDP": "trunk/项目管理/项目策划/项目计划",
    "SQAP": "trunk/项目管理/项目策划/质量保证计划",
    "SCM": "trunk/项目管理/项目策划/配置管理计划",
    "MA": "trunk/项目管理/项目策划/测量分析计划",
    "STP": "trunk/项目管理/项目策划/测试计划",
}

db = SessionLocal()
try:
    for tpl, rel in PATHS.items():
        obj = db.query(SvnDocPathMap).filter(
            SvnDocPathMap.project_id == "GLOBAL",
            SvnDocPathMap.template_name == tpl,
        ).first()
        if obj:
            obj.rel_path = rel
        else:
            db.add(SvnDocPathMap(project_id="GLOBAL", template_name=tpl, rel_path=rel))
    db.commit()
    print("[OK] 全局路径映射补齐：")
    for m in db.query(SvnDocPathMap).filter(SvnDocPathMap.project_id == "GLOBAL").all():
        print("  ", m.template_name, "->", m.rel_path)
finally:
    db.close()
