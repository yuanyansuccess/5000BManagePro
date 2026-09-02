# -*- coding: utf-8 -*-
"""
迁移脚本（一次性）：SDP 占位符数据落地（项目维度）。
作者：袁燕
功能：
  1) projects 表新增签署角色 / 硬件 / 软件 / 引用文档字段（覆盖 {{role.*}}/{{hw.*}}/{{sw.*}}/{{ref.*}}）。
  2) schedule_phases / stakeholders 由"全局共享"改为"按项目维度"（新增 project_id 列，
     旧数据归属默认项目 R105，符合项目方"基于项目维度"铁律）。
  3) 新建 hw_res / sw_res / doc_scale 三张业务表（项目维度），供 SDP 表格占位符聚合。
执行：python backend/db/_migrate_proj_signoff.py
安全：幂等（列/表存在则跳过），不丢旧数据。
"""
import sys
sys.path.insert(0, '.')
from sqlalchemy import text
from backend.db.session import SessionLocal, Engine
from backend.db.models import Base, HwRes, SwRes, DocScale, CodeScale


def _has_column(db, table, col):
    sql = text(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_schema = DATABASE() AND table_name = :t AND column_name = :c"
    )
    return db.execute(sql, {"t": table, "c": col}).scalar() > 0


def _add_column(db, table, col, dtype):
    if _has_column(db, table, col):
        print("  [skip] %s.%s 已存在" % (table, col))
        return
    db.execute(text("ALTER TABLE %s ADD COLUMN %s %s" % (table, col, dtype)))
    print("  [add] %s.%s (%s)" % (table, col, dtype))


def _rebuild_with_project(db, table, cols_def, cols_select):
    """重建表：加 id 自增主键 + project_id（默认 R105），旧数据迁移。
    用于旧表以业务列作主键、无法直接加自增列的场景。"""
    new = table + "_new"
    db.execute(text("DROP TABLE IF EXISTS %s" % new))
    db.execute(text(
        "CREATE TABLE %s (id INT AUTO_INCREMENT PRIMARY KEY, project_id VARCHAR(32) NOT NULL DEFAULT 'R105', %s)"
        % (new, cols_def)))
    db.execute(text(
        "INSERT INTO %s (project_id, %s) SELECT 'R105', %s FROM %s"
        % (new, cols_select, cols_select, table)))
    db.execute(text("DROP TABLE %s" % table))
    db.execute(text("RENAME TABLE %s TO %s" % (new, table)))
    print("  [rebuild] %s 已重建（id+project_id）" % table)


def main():
    db = SessionLocal()
    try:
        print("[1] projects 表新增标量字段（签署角色/硬件/软件/引用）")
        cols = [
            ("ccb", "VARCHAR(128)"), ("designer", "VARCHAR(64)"),
            ("reviewer", "VARCHAR(64)"), ("reviewer2", "VARCHAR(64)"),
            ("reviewer3", "VARCHAR(64)"), ("tester", "VARCHAR(64)"),
            ("qa", "VARCHAR(64)"), ("config_manager", "VARCHAR(64)"),
            ("org_config_manager", "VARCHAR(64)"),
            ("hw_ide_name", "VARCHAR(64)"), ("hw_mcu_model", "VARCHAR(64)"),
            ("sw_name_host", "VARCHAR(128)"), ("sw_name_iap", "VARCHAR(128)"),
            ("ref_sdtd_doc_number", "VARCHAR(64)"), ("ref_sqap_doc_number", "VARCHAR(64)"),
        ]
        for c, t in cols:
            _add_column(db, "projects", c, t)

        print("[2] schedule_phases / stakeholders 重建为 id 自增主键 + project_id（旧数据归属 R105）")
        # 幂等保护（修复：此前每次启动无条件重建导致数据清零）：表已有 project_id 列即视为已迁移，跳过
        for table, cols_def, cols_select in [
            ("schedule_phases",
             "phase_no INT NOT NULL, phase_name VARCHAR(32) NOT NULL, ratio VARCHAR(16), "
             "eng_md FLOAT, mgr_md FLOAT, start_date VARCHAR(16), end_date VARCHAR(16), milestone VARCHAR(255)",
             "phase_no, phase_name, ratio, eng_md, mgr_md, start_date, end_date, milestone"),
            ("stakeholders",
             "role VARCHAR(64) NOT NULL, name VARCHAR(64) NOT NULL, responsibility TEXT, join_phase VARCHAR(32)",
             "role, name, responsibility, join_phase"),
        ]:
            if _has_column(db, table, "project_id"):
                print("  [skip] %s 已含 project_id（迁移过），跳过重建" % table)
            else:
                _rebuild_with_project(db, table, cols_def, cols_select)

        print("[3] 新建 hw_res / sw_res / doc_scale / code_scale 表")
        Base.metadata.create_all(Engine, tables=[HwRes.__table__, SwRes.__table__,
                                                  DocScale.__table__, CodeScale.__table__])
        print("  [ok] 业务表已确保存在")

        db.commit()
        print("[done] 迁移完成")
    except Exception as e:
        db.rollback()
        print("[ERROR]", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
