# -*- coding: utf-8 -*-
"""R105 A14 利益相关方清单 seed（数据源：软件开发计划V3.01.docx 表29）。
作者：袁燕
说明：A14 原表为 3 列（组织机构/角色|人员（代表）|职责），职责统一"参见公司《军用软件管理体系文件》
总则（Q CEC R00.00-2025）"；平台第 4 列"参与阶段"按表34 参与矩阵归纳。幂等：先清后插。"""
import sys
sys.path.insert(0, 'd:/5000/5000BManagePro')

from backend.db.session import SessionLocal
from backend.db.models import Stakeholder

PID = "R105"
RESP = "参见公司《军用软件管理体系文件》的总则（Q CEC R00.00-2025）部分"

ROWS = [
    ("项目软件配置控制委员会", "许宏刚", "全部"),
    ("公司配置管理组", "廖建英", "按需"),
    ("软件负责人", "辛峥峰", "全部"),
    ("项目负责人/系统工程组", "孙超", "评审/阶段会议"),
    ("质量保证组", "张莉", "全部"),
    ("软件需求人员", "马慧芳", "需求"),
    ("软件设计人员", "吴明森、罗臻", "设计和实现"),
    ("软件实现人员", "吴明森、罗臻", "设计和实现"),
    ("软件测试人员", "谢柯薪", "测试"),
    ("软件配置管理人员", "张星竹", "全部"),
    ("软件测量与分析人员", "张星竹", "全部"),
    ("软件质量保证人员", "杜晟", "全部"),
]


def main():
    db = SessionLocal()
    try:
        old = db.query(Stakeholder).filter(Stakeholder.project_id == PID).delete(
            synchronize_session=False)
        for role, name, phase in ROWS:
            db.add(Stakeholder(project_id=PID, role=role, name=name,
                               responsibility=RESP, join_phase=phase))
        db.commit()
        n = db.query(Stakeholder).filter(Stakeholder.project_id == PID).count()
        print(f"[OK] 清除 {old} 条，写入 {n} 条 A14 相关方清单")
    finally:
        db.close()


if __name__ == "__main__":
    main()
