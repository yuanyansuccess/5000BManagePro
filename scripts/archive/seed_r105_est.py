# -*- coding: utf-8 -*-
"""重建 est_items 表（加软件配置项列+收敛状态）+ 预置 R105 三轮估算数据。
作者：袁燕
数据来源：R105代码个人估算汇总表.xlsx（估算人：辛峥峰/罗臻/马慧芳；单位 Loc）。
计算规则：偏差 = Max-Min；平均值 = 三人合计/3；相对偏差 = 偏差/平均值；
          收敛判定：相对偏差 <= 20% 为"已收敛"，否则"需再估"（继续下一轮）。
"""
import sys
sys.path.insert(0, 'd:/5000/5000BManagePro')

from sqlalchemy import text
from backend.db.session import SessionLocal, Engine
from backend.db.models import Base, EstItem

PID = "R105"
CONVERGE_THRESHOLD = 20.0  # 相对偏差阈值(%)，<= 阈值判定收敛


def calc(a, b, c):
    """返回 (偏差, 平均值, 相对偏差%, 收敛状态)"""
    vals = [float(a), float(b), float(c)]
    dev = max(vals) - min(vals)
    avg = sum(vals) / 3.0
    rel = (dev / avg * 100) if avg else 0
    state = "已收敛" if rel <= CONVERGE_THRESHOLD else "需再估"
    return f"{dev:g}", f"{avg:.2f}", f"{rel:.1f}%", state


# (轮次, 软件配置项, 部件/功能点, 辛峥峰, 罗臻, 马慧芳)
RAW = [
    # ---- 第 1 轮（R105-PP-GH-01）----
    (1, "触摸屏控制软件", "初始化模块", 60, 55, 70),
    (1, "触摸屏控制软件", "看门狗模块", 80, 75, 80),
    (1, "触摸屏控制软件", "RS232通讯功能模块", 110, 80, 85),
    (1, "触摸屏控制软件", "温度数据处理模块", 260, 280, 280),
    (1, "主控板控制软件", "初始化模块", 80, 110, 90),
    (1, "主控板控制软件", "RS232通讯功能模块", 100, 90, 95),
    (1, "主控板控制软件", "数据处理模块", 40, 40, 45),
    (1, "主控板控制软件", "IO信号处理模块", 300, 260, 320),
    # ---- 第 2 轮（R105-PP-GH-02）----
    (2, "触摸屏控制软件", "初始化模块", 60, 60, 65),
    (2, "触摸屏控制软件", "看门狗模块", 80, 75, 80),
    (2, "触摸屏控制软件", "RS232通讯功能模块", 100, 85, 90),
    (2, "触摸屏控制软件", "温度数据处理模块", 260, 280, 280),
    (2, "主控板控制软件", "初始化模块", 85, 100, 90),
    (2, "主控板控制软件", "RS232通讯功能模块", 100, 90, 95),
    (2, "主控板控制软件", "数据处理模块", 40, 40, 45),
    (2, "主控板控制软件", "IO信号处理模块", 290, 270, 300),
]


def main():
    with Engine.begin() as c:
        c.execute(text("DROP TABLE IF EXISTS est_items"))
    Base.metadata.create_all(Engine, tables=[EstItem.__table__])
    db = SessionLocal()
    try:
        seq = 0
        for rd in (1, 2):
            rows = [x for x in RAW if x[0] == rd]
            for _, cfg, part, a, b, cc in rows:
                dev, avg, rel, state = calc(a, b, cc)
                seq += 1
                db.add(EstItem(project_id=PID, round_no=rd, cfg_item=cfg, wbs2=part,
                               est1=str(a), est2=str(b), est3=str(cc),
                               deviation=dev, avg_val=avg, rel_dev=rel,
                               converge=state, is_total=0, seq=seq))
            # 每轮合计行
            ta = sum(x[3] for x in rows)
            tb = sum(x[4] for x in rows)
            tc = sum(x[5] for x in rows)
            dev, avg, rel, state = calc(ta, tb, tc)
            seq += 1
            db.add(EstItem(project_id=PID, round_no=rd, cfg_item="合计", wbs2="—",
                           est1=str(ta), est2=str(tb), est3=str(tc),
                           deviation=dev, avg_val=avg, rel_dev=rel,
                           converge=state, is_total=1, seq=seq))
        db.commit()
        total = db.query(EstItem).filter(EstItem.project_id == PID).count()
        print(f"[OK] est_items 重建：{total} 行（2 轮 × (8 部件 + 1 合计)），收敛阈值 {CONVERGE_THRESHOLD}%")
        for rd in (1, 2):
            n = db.query(EstItem).filter(EstItem.project_id == PID,
                                         EstItem.round_no == rd,
                                         EstItem.converge == "需再估").count()
            print(f"  第{rd}轮：需再估 {n} 项")
    finally:
        db.close()


if __name__ == "__main__":
    main()
