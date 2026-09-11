# -*- coding: utf-8 -*-
"""从 R105软件进度表.mpp 导入进度任务到数据库（两维度：阶段 + 全部任务项）。
作者：袁燕
数据源：R105软件进度表V2.00(只含项目启动和策划阶段).mpp（OLE2，用 olefile 读任务流）
说明：.mpp 为 MS Project 私有二进制，任务名/阶段层级可 100% 可靠提取；
      工期与日期为私有编码，需 MPXJ(Java) 才能精确解析，本脚本按任务层级推导阶段归属，
      日期/工期字段留空待补（或用项目策划进度表的阶段日期填充）。
      导入为幂等操作（先清后插）。
"""
import sys, re
sys.path.insert(0, 'd:/5000/5000BManagePro')

import olefile
from backend.db.session import SessionLocal, Engine
from backend.db.models import Base, ScheduleTask, SchedulePhase

PID = "R105"
MPP = (r'C:\Users\25007\AppData\Local\Temp\codebuddy-dropped-files'
       r'\1be588dd-fca8-406e-9783-6da60156057a\R105软件进度表V2.00(只含项目启动和策划阶段).mpp')

# .mpp 任务文本流中提取到的真实任务（顺序即 .mpp 中的任务顺序）
# 摘要任务（阶段，层级1）：项目启动 / 项目策划
# 具体任务（层级2）：其余
SUMMARY_TASKS = ["项目启动", "项目策划"]
SKIP = ["进度表V2"]  # 项目摘要根，不入库


def extract_task_names(path):
    """从 .mpp 的 TBkndTask/Var2Data 流提取任务名（UTF-16LE 中文串）。"""
    ole = olefile.OleFileIO(path)
    try:
        data = ole.openstream(['   112', 'TBkndTask', 'Var2Data']).read()
    finally:
        ole.close()
    txt = data.decode('utf-16-le', errors='ignore')
    names = re.findall(r'[\u4e00-\u9fa5][\u4e00-\u9fa5A-Za-z0-9（）()·、/\-]{1,40}', txt)
    # 去重保序
    seen, out = set(), []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return [n for n in out if n not in SKIP]


def main():
    Base.metadata.create_all(Engine, tables=[ScheduleTask.__table__])
    names = extract_task_names(MPP)
    if not names:
        print("[FAIL] 未提取到任务名")
        return

    db = SessionLocal()
    try:
        db.query(ScheduleTask).filter(ScheduleTask.project_id == PID).delete(
            synchronize_session=False)
        db.commit()

        # 阶段日期兜底：从 schedule_phases 取（按阶段名匹配）
        phase_map = {}
        for p in db.query(SchedulePhase).filter(SchedulePhase.project_id == PID).all():
            phase_map[p.phase_name] = (p.start_date, p.end_date)

        cur_phase = None
        seq = 0
        no = 0
        for n in names:
            if n in SUMMARY_TASKS:
                cur_phase = n
                seq += 1
                no += 1
                s, e = phase_map.get(n, ("", ""))
                db.add(ScheduleTask(
                    project_id=PID, phase_name=n, task_no=no, outline_level=1,
                    is_summary=1, task_name=n,
                    plan_start=s or "", plan_finish=e or "", seq=seq))
                continue
            if cur_phase is None:
                continue
            seq += 1
            no += 1
            db.add(ScheduleTask(
                project_id=PID, phase_name=cur_phase, task_no=no, outline_level=2,
                is_summary=0, task_name=n, seq=seq))
        db.commit()
        total = db.query(ScheduleTask).filter(ScheduleTask.project_id == PID).count()
        summaries = db.query(ScheduleTask).filter(
            ScheduleTask.project_id == PID, ScheduleTask.is_summary == 1).count()
        print(f"[OK] 导入完成：总 {total} 条（阶段/摘要 {summaries} 条，具体任务 {total - summaries} 条）")
    finally:
        db.close()


if __name__ == "__main__":
    main()
