# -*- coding: utf-8 -*-
"""projects 表新增 5 个角色字段，打通"前端录入 -> 数据库 -> 生成文档"三处一致。作者：袁燕

背景（袁总反馈）：
  - 模板把"软件实现人员"位置填成了 reviewer2/reviewer3（钱七、孙八），角色错位；
  - "项目负责人""系统工程组"位置分别误用了 reviewer / designer；
  - 模板硬编码"李维"（需求分析行），"测量分析"行为空；
  - 前端缺"需求分析人员"等输入框，导致这些人员无法在平台录入。
新增字段（按 R105 真实组织角色）：
  requirement  需求分析人员
  coder        软件实现人员
  measure      测量分析人员
  proj_lead    项目负责人
  sys_eng      系统工程组
幂等：列已存在则跳过。
"""
import sys

sys.path.insert(0, 'd:/5000/5000BManagePro')

from sqlalchemy import text  # noqa: E402
from backend.db.session import SessionLocal  # noqa: E402

NEW_COLS = [
    ("requirement", "需求分析人员"),
    ("coder", "软件实现人员"),
    ("measure", "测量分析人员"),
    ("proj_lead", "项目负责人"),
    ("sys_eng", "系统工程组"),
]

ROLE_COLS = ('owner', 'ccb', 'org_config_manager', 'designer', 'reviewer',
             'reviewer2', 'reviewer3', 'tester', 'qa', 'config_manager',
             'requirement', 'coder', 'measure', 'proj_lead', 'sys_eng')


def has_column(db, table, col):
    return db.execute(text(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_schema = DATABASE() AND table_name = :t AND column_name = :c"
    ), {"t": table, "c": col}).scalar() > 0


def main():
    db = SessionLocal()
    try:
        for col, label in NEW_COLS:
            if has_column(db, "projects", col):
                print(f'  [skip] projects.{col} 已存在（{label}）')
                continue
            db.execute(text(
                "ALTER TABLE projects ADD COLUMN `%s` VARCHAR(64) DEFAULT ''" % col))
            db.commit()
            print(f'  [add]  projects.{col}（{label}）')
        cols = [r[0] for r in db.execute(
            text("SHOW COLUMNS FROM projects")).fetchall()]
        print('\nprojects 角色相关列:')
        for c in cols:
            if c in ROLE_COLS:
                print('   -', c)
    finally:
        db.close()


if __name__ == "__main__":
    main()
