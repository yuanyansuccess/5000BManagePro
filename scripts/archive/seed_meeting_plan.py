# -*- coding: utf-8 -*-
"""建 meeting_plan 表 + 预置 R105 真实会议计划（7 行）。作者：袁燕

袁总要求："表 9 会议计划的会议时机请读取项目策划中 R105 进度表中的会议时间，
         从数据库里面读取是最优解"。

数据来源：R105 软件开发计划V3.01 的"会议计划"表（真实值），
         并与 schedule_tasks（进度表）中的会议任务日期一致。
幂等：先清后插。
"""
import sys

sys.path.insert(0, 'd:/5000/5000BManagePro')

from backend.db.session import SessionLocal, Engine  # noqa: E402
from backend.db.models import Base, MeetingPlan  # noqa: E402

PID = "R105"

ROWS = [
    (1, "双周例会", "软件负责人",
     "项目策划阶段最后一天召开第一次双周例会，此后间隔10个工作日召开一次，"
     "如遇法定假日顺延，如与阶段会议相差两天以内，则与阶段会议合并召开。"
     "根据进度表首次双周例会确定时间为2024年4月30日"),
    (2, "需求规格说明评审", "软件负责人", "2024年5月15日"),
    (3, "需求阶段会议（与双周例会合并）", "软件负责人", "阶段结束当天，2024年5月16日"),
    (4, "设计实现阶段会议（与双周例会合并）", "软件负责人", "阶段结束当天，2024年6月14日"),
    (5, "软件测试评审", "软件负责人", "2024年6月27日"),
    (6, "测试阶段会议（与双周例会合并）", "软件负责人", "阶段结束当天，2024年6月28日"),
    (7, "验收阶段会议（与项目结项会议一起）", "软件负责人", "阶段结束当天，2024年7月5日"),
]


def main():
    Base.metadata.create_all(Engine, tables=[MeetingPlan.__table__])
    db = SessionLocal()
    try:
        old = db.query(MeetingPlan).filter(
            MeetingPlan.project_id == PID).delete(synchronize_session=False)
        db.commit()
        for seq, mtype, org, timing in ROWS:
            db.add(MeetingPlan(project_id=PID, seq=seq, meeting_type=mtype,
                               organizer=org, timing=timing))
        db.commit()
        n = db.query(MeetingPlan).filter(MeetingPlan.project_id == PID).count()
        print(f"[OK] meeting_plan：清除 {old} 行，写入 {n} 行")
        for r in db.query(MeetingPlan).filter(
                MeetingPlan.project_id == PID).order_by(MeetingPlan.seq).all():
            print(f"  {r.seq}. {r.meeting_type} | {r.organizer} | {r.timing}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
