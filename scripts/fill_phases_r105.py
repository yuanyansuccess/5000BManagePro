# -*- coding: utf-8 -*-
"""从 R105 原始开发计划（软件开发计划V3.01.docx 表8/表28）填充 schedule_phases。
作者：袁燕
数据（R105 真实值）：
  表8 工作量估算：需求19%/设计24%/实现29%/测试22%/验收6%，工程45.9人日+管理30.6人日=76.5→调整77
  表28 阶段日期：策划4-23~4-30 / 需求5-1~5-15 / 设计实现5-16~6-14 / 测试6-15~6-30 / 验收7-1~7-5
幂等：先清后插。"""
import sys
sys.path.insert(0, 'd:/5000/5000BManagePro')

from backend.db.session import SessionLocal
from backend.db.models import SchedulePhase

PID = "R105"

# 7 阶段：项目启动 + 项目策划（0 工作量，标识整体时间窗）+ 5 实施阶段（需求/设计/实现/测试/验收）
# 项目启动/策划 数据源：R105 软件进度表 .mpp 摘要任务（XML 导出）
# 5 实施阶段 数据源：原表8 工作量估算 + 表28 阶段日期
ROWS = [
    (1, "项目启动", "0%", 0.0, 0.0, "2024-04-05", "2024-04-22", "项目启动会议（2024-4-5）"),
    (2, "项目策划", "0%", 0.0, 0.0, "2024-04-23", "2024-04-30", "软件项目计划评审会议（2024-4-29）"),
    (3, "需求", "19%", 8.721, 5.814, "2024-05-01", "2024-05-15", "软件需求规格说明技术评审（2024-5-15）"),
    (4, "设计", "24%", 11.016, 7.344, "2024-05-16", "2024-06-14", "软件设计说明签字审批（2024-5-30）"),
    (5, "实现", "29%", 13.311, 8.874, "2024-05-16", "2024-06-14", "软件源代码签字审批（2024-6-14）"),
    (6, "测试", "22%", 10.098, 6.732, "2024-06-15", "2024-06-30", "软件测试报告技术评审（2024-6-30）"),
    (7, "验收", "6%", 2.754, 1.836, "2024-07-01", "2024-07-05", "项目结项（2024-7-5）"),
]


def main():
    db = SessionLocal()
    try:
        old = db.query(SchedulePhase).filter(SchedulePhase.project_id == PID).delete(
            synchronize_session=False)
        for r in ROWS:
            db.add(SchedulePhase(
                project_id=PID, phase_no=r[0], phase_name=r[1], ratio=r[2],
                eng_md=r[3], mgr_md=r[4], start_date=r[5], end_date=r[6],
                milestone=r[7]))
        db.commit()
        n = db.query(SchedulePhase).filter(SchedulePhase.project_id == PID).count()
        print(f"[OK] 清除 {old} 条，写入 {n} 条阶段工作量数据")
        for p in db.query(SchedulePhase).filter(SchedulePhase.project_id == PID).all():
            print(f"  {p.phase_no} {p.phase_name} {p.ratio} 工程{p.eng_md} 管理{p.mgr_md} "
                  f"{p.start_date}~{p.end_date}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
