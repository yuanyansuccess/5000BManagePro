# -*- coding: utf-8 -*-
"""把 MS Project 导出的进度表 XML 1:1 写入后台数据库（schedule_tasks 表）。
作者：袁燕
背景：袁总要求「进度表页面元素删除，但后台要把 mpp 生成的进度表写入后台」。
数据源：R105软件进度表 .mpp -> MS Project 另存为 XML（MS Project XML 架构）。
导入字段（模型 ScheduleTask）：
  阶段归属 phase_name / 任务序号 task_no / 层级 outline_level / 摘要标记 is_summary /
  任务名 task_name / 计划开始 plan_start / 计划完成 plan_finish / 工期 duration_days(小时) /
  工时 work_hours(小时) / 负责人 owner(资源) / 完成百分比 percent /
  任务标识 wbs / 大纲编号 outline_number / 前置任务 predecessor / 里程碑 milestone
单位换算：XML 的 Duration/Work 为 ISO8601 时长（PT8H0M0S）；DurationFormat=7 表示按小时，
  PT160H0M0S = 160 小时；Work 同理（PT312H19M0S = 312.32 小时）。
幂等：按 project_id 先清后插。
用法：python scripts/import_mpp_xml_r105.py [xml路径] [项目代号]
"""
import sys
import re
import xml.etree.ElementTree as ET

sys.path.insert(0, 'd:/5000/5000BManagePro')

from backend.db.session import SessionLocal, Engine
from backend.db.models import Base, ScheduleTask

NS = '{http://schemas.microsoft.com/project}'

DEFAULT_XML = (r'E:\360MoveData\Users\25007\Desktop'
               r'\R105软件进度表V2.00(只含项目启动和策划阶段).xml')
PID_DEFAULT = 'R105'

# XML 中的根项目摘要任务名（不入库，作为整体容器）
SKIP_ROOT_NAMES = {'MSProj11'}


def _hours(iso):
    """PT160H0M0S / PT8H20M0S -> 160.0 / 8.33（保留 2 位）"""
    if not iso:
        return 0.0
    m = re.match(r'PT(?:(\d+(?:\.\d+)?)H)?(?:(\d+(?:\.\d+)?)M)?(?:(\d+(?:\.\d+)?)S)?', iso)
    if not m:
        return 0.0
    h = float(m.group(1) or 0)
    mi = float(m.group(2) or 0)
    s = float(m.group(3) or 0)
    return round(h + mi / 60 + s / 3600, 2)


def _date(iso):
    """2024-04-05T08:00:00 -> 2024-04-05"""
    return (iso or '')[:10]


def _text(el, tag):
    node = el.find(f'{NS}{tag}')
    return (node.text or '').strip() if node is not None and node.text else ''


def parse(xml_path):
    root = ET.parse(xml_path).getroot()
    tasks_el = root.find(f'{NS}Tasks')
    if tasks_el is None:
        raise RuntimeError('XML 中未找到 Tasks 节点')

    # 资源 UID -> 名称（用于负责人）
    res_map = {}
    res_el = root.find(f'{NS}Resources')
    if res_el is not None:
        for r in res_el:
            uid = _text(r, 'UID')
            nm = _text(r, 'Name')
            if uid and nm:
                res_map[uid] = nm

    # 任务 UID -> 资源名列表（经 Assignments 关联）
    task_res = {}
    assn_el = root.find(f'{NS}Assignments')
    if assn_el is not None:
        for a in assn_el:
            tuid = _text(a, 'TaskUID')
            ruid = _text(a, 'ResourceUID')
            if tuid and ruid and ruid in res_map:
                task_res.setdefault(tuid, [])
                nm = res_map[ruid]
                if nm not in task_res[tuid]:
                    task_res[tuid].append(nm)

    rows = []
    for t in tasks_el:
        name = _text(t, 'Name')
        if not name or name in SKIP_ROOT_NAMES:
            continue
        level = int(_text(t, 'OutlineLevel') or 1)
        outline = _text(t, 'OutlineNumber')
        summary = 1 if _text(t, 'Summary') == '1' else 0
        uid = _text(t, 'UID')
        owners = task_res.get(uid, [])
        rows.append(dict(
            outline=outline, level=level, summary=summary, name=name,
            start=_date(_text(t, 'Start')), finish=_date(_text(t, 'Finish')),
            dur=_hours(_text(t, 'Duration')), work=_hours(_text(t, 'Work')),
            owner='、'.join(owners),
            percent=int(float(_text(t, 'PercentComplete') or 0)),
            wbs=_text(t, 'WBS'), uid=uid,
            milestone=1 if _text(t, 'Milestone') == '1' else 0,
        ))
    # 按大纲编号排序：1 / 1.1 / 1.1.1 / 1.2 ...（逐级数值比较）
    def key(r):
        parts = [int(x) for x in (r['outline'] or '0').split('.') if x.isdigit()]
        return parts or [999]
    rows.sort(key=key)
    return rows


def resolve_phase(rows, i):
    """阶段归属：
    - 摘要行（阶段行/根）归属自身（阶段名即自己）
    - 具体任务向上找最近的摘要任务（level 更小且 summary=1）
    """
    r = rows[i]
    if r['summary'] == 1:
        return r['name'], r['outline']
    lv = r['level']
    for j in range(i - 1, -1, -1):
        if rows[j]['level'] < lv and rows[j]['summary'] == 1:
            return rows[j]['name'], rows[j]['outline']
    return r['name'], r['outline']


def main(xml_path=None, pid=None):
    xml_path = xml_path or DEFAULT_XML
    pid = pid or PID_DEFAULT
    rows = parse(xml_path)
    if not rows:
        print('[FAIL] 未解析到任务')
        return

    Base.metadata.create_all(Engine, tables=[ScheduleTask.__table__])
    db = SessionLocal()
    try:
        old = db.query(ScheduleTask).filter(ScheduleTask.project_id == pid).delete(
            synchronize_session=False)
        db.commit()
        for i, r in enumerate(rows, start=1):
            phase, _ = resolve_phase(rows, i - 1)
            db.add(ScheduleTask(
                project_id=pid,
                phase_name=phase,
                task_no=i,
                outline_level=r['level'],
                is_summary=r['summary'],
                task_name=r['name'],
                plan_start=r['start'],
                plan_finish=r['finish'],
                duration_days=r['dur'],
                work_hours=r['work'],
                owner=r['owner'] or '',
                percent=r['percent'],
                wbs=r['wbs'] or '',
                outline_number=r['outline'],
                predecessor='',
                milestone='是' if r['milestone'] else '',
                seq=i,
            ))
        db.commit()
        n = db.query(ScheduleTask).filter(ScheduleTask.project_id == pid).count()
        summ = db.query(ScheduleTask).filter(ScheduleTask.project_id == pid,
                                             ScheduleTask.is_summary == 1).count()
        phases = sorted({t.phase_name for t in db.query(ScheduleTask).filter(
            ScheduleTask.project_id == pid).all()})
        print(f'[OK] 清除 {old} 条，写入 {n} 条（摘要/阶段 {summ} 条，具体任务 {n - summ} 条）')
        print('阶段:', ' / '.join(phases))
        for t in db.query(ScheduleTask).filter(ScheduleTask.project_id == pid
                                               ).order_by(ScheduleTask.seq).all():
            mark = '*' if t.is_summary else ' '
            print(f"  {mark} {t.outline_number:>7} {t.phase_name:8} {t.task_name[:34]:34} "
                  f"{t.plan_start}~{t.plan_finish} 工期{t.duration_days}h 工时{t.work_hours}h "
                  f"负责人={t.owner}")
    finally:
        db.close()


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else None,
         sys.argv[2] if len(sys.argv) > 2 else None)
