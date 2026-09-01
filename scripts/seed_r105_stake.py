# -*- coding: utf-8 -*-
"""预置 stakeholder_plan 表（R105 项目）：R121 附录B 9 角色结构 + R105 原始 13 行。
作者：袁燕
变更（袁总要求）：
  1) 角色精简为 9 个（对标 R121 附录B）：
     顾客代表 | 项目经理 | 部门领导 | 项目负责人 | 系统工程组 | EPG | QAG | CMG | OTG
  2) 不再有 ○ 圆圈标记：√=计划参与，空=不参与（原 ○ 一律转为空）
数据来源：R105 软件开发计划V3.01 附录B TABLE 34，按 9 角色重新映射。
"""
import sys
sys.path.insert(0, 'd:/5000/5000BManagePro')

from backend.db.session import SessionLocal, Engine  # noqa: E402
from backend.db.models import Base, StakeholderPlan  # noqa: E402

PID = "R105"

# 9 个角色列（顺序与数据库列、R121 附录B 一致）
ROLE_COLS = ["customer_rep", "pm", "dept_lead", "proj_lead", "sys_eng",
             "epg", "qag", "cmg", "otg"]

# R105 附录B 13 行（原 16 角色 -> 9 角色映射；○ 已转为空）
# 映射说明：顾客代表=原顾客/代表（原为○者转空）；项目经理=新列（R105 原表无，留空）；
#           部门领导/项目负责人/系统工程组=原同名；EPG/QAG/CMG/OTG=原同名
ROWS = [
    ("项目策划", "软件项目计划评审", ["", "", "√", "√", "√", "√", "√", "√", ""]),
    ("需求", "需求分析",             ["", "", "", "", "√", "", "", "", ""]),
    ("需求", "软件需求评审",         ["", "", "", "", "√", "", "", "", ""]),
    ("需求", "需求阶段会议",         ["", "", "√", "", "", "", "", "", ""]),
    ("设计和实现", "软件设计评审",   ["", "", "", "", "", "", "", "", ""]),
    ("设计和实现", "测试用例评审",   ["", "", "", "", "", "", "", "", ""]),
    ("设计和实现", "设计和实现阶段会议", ["", "", "√", "", "", "", "", "", ""]),
    ("测试", "配置项测试",           ["", "", "", "", "√", "", "", "", ""]),
    ("测试", "测试报告评审",         ["", "", "", "", "√", "", "", "", ""]),
    ("测试", "测试阶段会议",         ["", "", "√", "", "", "", "", "", ""]),
    ("验收结项", "验收评审",         ["", "", "", "", "√", "", "", "", ""]),
    ("验收结项", "结项会议",         ["", "", "√", "√", "√", "", "", "", ""]),
    ("其它", "双周例会",             ["", "", "", "", "", "", "", "", ""]),
]


def main():
    Base.metadata.create_all(Engine, tables=[StakeholderPlan.__table__])
    db = SessionLocal()
    try:
        old = db.query(StakeholderPlan).filter(
            StakeholderPlan.project_id == PID).delete(synchronize_session=False)
        db.commit()
        for i, (phase, act, marks) in enumerate(ROWS, start=1):
            row = StakeholderPlan(project_id=PID, seq=i, phase=phase, activity=act)
            for col, v in zip(ROLE_COLS, marks):
                setattr(row, col, v)
            db.add(row)
        db.commit()
        n = db.query(StakeholderPlan).filter(StakeholderPlan.project_id == PID).count()
        print(f"[OK] stakeholder_plan 重建：清除 {old} 行，写入 {n} 行（9 角色，无 ○）")
        for r in db.query(StakeholderPlan).filter(
                StakeholderPlan.project_id == PID).order_by(StakeholderPlan.seq).all():
            print(f"  {r.seq:2} {r.phase:6} {r.activity:14} "
                  f"{[getattr(r, c) or '-' for c in ROLE_COLS]}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
