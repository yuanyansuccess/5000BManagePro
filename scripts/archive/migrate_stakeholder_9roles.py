# -*- coding: utf-8 -*-
"""利益相关方参与计划：角色精简为 R121 附录B 的 9 个 + 清洗○标记。作者：袁燕

袁总要求：
  1) 利益相关方仅保留：顾客代表、项目经理、部门领导、项目负责人、系统工程组、EPG、QAG、CMG、OTG
  2) 其余角色（软件负责人/需求人员/设计人员/实现人员/测试人员/测量分析/SCM/质量保证）删除，
     数据库相关数据同步删除
  3) 不再出现 ○ 圆圈标记（只保留 √=计划参与，空=不参与）

变更：
  - 新增列 pm（项目经理）
  - 删除列 sw_owner / req_p / des_p / imp_p / test_p / measure / scm / qa
  - 保留列 customer_rep / dept_lead / proj_lead / sys_eng / epg / qag / cmg / otg
  - 所有保留列中的 "○" -> ""（空）
幂等：列存在则跳过新增，列不存在则跳过删除。
"""
import sys

sys.path.insert(0, 'd:/5000/5000BManagePro')

from sqlalchemy import text  # noqa: E402
from backend.db.session import Engine, SessionLocal  # noqa: E402

# R121 附录B 角色列顺序（9 个）
KEEP_COLS = ['customer_rep', 'pm', 'dept_lead', 'proj_lead', 'sys_eng',
             'epg', 'qag', 'cmg', 'otg']
DROP_COLS = ['sw_owner', 'req_p', 'des_p', 'imp_p', 'test_p', 'measure', 'scm', 'qa']


def has_column(db, table, col):
    return db.execute(text(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_schema = DATABASE() AND table_name = :t AND column_name = :c"
    ), {"t": table, "c": col}).scalar() > 0


def main():
    db = SessionLocal()
    try:
        print('[1] 清洗 ○ 标记（保留列中的 ○ -> 空）')
        total = 0
        for c in ['customer_rep', 'dept_lead', 'proj_lead', 'sys_eng', 'epg', 'qag', 'cmg', 'otg']:
            if not has_column(db, 'stakeholder_plan', c):
                continue
            n = db.execute(text(
                "UPDATE stakeholder_plan SET `%s` = '' WHERE `%s` = '○'" % (c, c))).rowcount
            if n:
                print(f'    清洗 {c}: {n} 处')
            total += n
        db.commit()
        print(f'    合计清洗 ○ {total} 处')

        print('[2] 新增列 pm（项目经理）')
        if has_column(db, 'stakeholder_plan', 'pm'):
            print('    已存在，跳过')
        else:
            # 放在 customer_rep 之后，保持 R121 顺序
            db.execute(text(
                "ALTER TABLE stakeholder_plan ADD COLUMN pm VARCHAR(4) DEFAULT '' "
                "AFTER customer_rep"))
            db.commit()
            print('    已新增')

        print('[3] 删除多余角色列')
        for c in DROP_COLS:
            if has_column(db, 'stakeholder_plan', c):
                db.execute(text("ALTER TABLE stakeholder_plan DROP COLUMN `%s`" % c))
                db.commit()
                print(f'    已删除 {c}')
            else:
                print(f'    不存在，跳过 {c}')

        print('[4] 复核最终列顺序')
        cols = [r[0] for r in db.execute(
            text("SHOW COLUMNS FROM stakeholder_plan")).fetchall()]
        print('   ', cols)

        print('[5] 数据行数与残留 ○ 检查')
        n = db.execute(text("SELECT COUNT(*) FROM stakeholder_plan")).scalar()
        print('    行数:', n)
        residual = 0
        for c in KEEP_COLS:
            if has_column(db, 'stakeholder_plan', c):
                residual += db.execute(text(
                    "SELECT COUNT(*) FROM stakeholder_plan WHERE `%s` = '○'" % c)).scalar()
        print('    残留 ○ :', residual)
        rows = db.execute(text(
            "SELECT seq, phase, activity, customer_rep, pm, dept_lead, proj_lead, "
            "sys_eng, epg, qag, cmg, otg FROM stakeholder_plan ORDER BY seq"
        )).fetchall()
        for r in rows:
            print('   ', r)
    finally:
        db.close()


if __name__ == '__main__':
    main()
