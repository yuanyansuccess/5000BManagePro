# -*- coding: utf-8 -*-
"""后端启动自检（作者：袁燕）：验证建表 + 需求 CRUD 闭环，不常驻。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db.session import init_db, Engine
from backend.db.models import Base
from sqlalchemy import inspect


def main():
    init_db()
    insp = inspect(Engine)
    tables = insp.get_table_names()
    print("已建表数量:", len(tables))
    for t in ["requirements", "risks", "users", "template_anchors", "audit_logs"]:
        print("  -", t, "存在" if t in tables else "缺失!")

    # CRUD 闭环验证
    from backend.db.session import SessionLocal
    from backend.db.models import Requirement
    from backend.dao import requirement_dao
    db = SessionLocal()
    try:
        # 清旧
        db.query(Requirement).filter(Requirement.req_id == "OR-01").delete()
        db.commit()
        # 增
        obj = Requirement(req_id="OR-01", req_type="OR", req_name="触摸屏控制软件初始化", status="草稿")
        requirement_dao.RequirementDao.create(db, obj)
        got = requirement_dao.RequirementDao.get_by_pk(db, "OR-01")
        print("增+查:", got.req_id, got.req_name, got.status)
        # 删
        requirement_dao.RequirementDao.delete(db, "OR-01")
        print("删后存在:", requirement_dao.RequirementDao.get_by_pk(db, "OR-01") is not None)
    finally:
        db.close()
    print("后端自检通过。")


if __name__ == "__main__":
    main()
