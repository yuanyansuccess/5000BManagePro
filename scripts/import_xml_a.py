# -*- coding: utf-8 -*-
"""XML 进度导入 part A。作者：袁燕"""
import sys
import xml.etree.ElementTree as ET
sys.path.insert(0, 'd:/5000/5000BManagePro')

from sqlalchemy import text
from backend.db.session import SessionLocal, Engine
from backend.db.models import Base, ScheduleTask

PID = "R105"
XML = r'E:\360MoveData\Users\25007\Desktop\R105软件进度表V2.00(只含项目启动和策划阶段).xml'


def strip(tag):
    return tag.split('}')[-1]


def parse_duration(s):
    import re
    if not s:
        return None
    m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?', s)
    if not m:
        return None
    return round(int(m.group(1) or 0) + int(m.group(2) or 0) / 60 + float(m.group(3) or 0) / 3600, 2)


def parse_dt(s):
    return (s or '')[:10]


def collect():
    tree = ET.parse(XML)
    root = tree.getroot()
    res_map = {}
    for child in root:
        if strip(child.tag) == 'Resources':
            for r in child:
                uid = name = None
                for f in r:
                    if strip(f.tag) == 'UID':
                        uid = (f.text or '').strip()
                    elif strip(f.tag) == 'Name':
                        name = (f.text or '').strip()
                if uid:
                    res_map[uid] = name
    tasks, assign = [], {}
    for child in root:
        if strip(child.tag) == 'Tasks':
            for t in child:
                d = {strip(f.tag): (f.text or '').strip() for f in t}
                tasks.append(d)
        if strip(child.tag) == 'Assignments':
            for a in child:
                d = {strip(f.tag): (f.text or '').strip() for f in a}
                tu, ru = d.get('TaskUID'), d.get('ResourceUID')
                if tu and ru and ru != '0' and res_map.get(ru):
                    assign.setdefault(tu, []).append(res_map[ru])
    return tasks, assign


def transform():
    """XML -> 行记录（1:1：WBS/层级/摘要/里程碑/起止/工期/工时/完成%/负责人）。"""
    tasks, assign = collect()
    out = []
    seq = 0
    for t in tasks:
        uid = t.get('UID')
        name = t.get('Name', '')
        if uid == '0' or name.startswith('MSProj'):
            continue
        seq += 1
        out.append(dict(
            uid=uid, task_no=t.get('ID') or seq, seq=seq,
            wbs=t.get('WBS', ''), ono=t.get('OutlineNumber', ''),
            lvl=int(t.get('OutlineLevel') or 1),
            is_sum=1 if t.get('Summary') == '1' else 0,
            ms=1 if t.get('Milestone') == '1' else 0,
            name=name, start=parse_dt(t.get('Start')),
            finish=parse_dt(t.get('Finish')),
            dur=parse_duration(t.get('Duration')),
            work=parse_duration(t.get('Work')),
            pct=int(float(t.get('PercentComplete') or 0)),
            owner='、'.join(assign.get(uid, [])),
        ))
    cur = None
    for rec in out:
        if rec['is_sum']:
            cur = rec['name']
        rec['phase'] = cur or ''
    return out


if __name__ == '__main__':
    rows = transform()
    with Engine.begin() as c:
        c.execute(text('DROP TABLE IF EXISTS schedule_tasks'))
    Base.metadata.create_all(Engine, tables=[ScheduleTask.__table__])
    db = SessionLocal()
    try:
        for rec in rows:
            db.add(ScheduleTask(
                project_id=PID, phase_name=rec['phase'], task_no=int(rec['task_no']),
                outline_level=rec['lvl'], is_summary=rec['is_sum'],
                task_name=rec['name'], plan_start=rec['start'], plan_finish=rec['finish'],
                duration_days=rec['dur'], work_hours=rec['work'],
                percent=rec['pct'], owner=rec['owner'], wbs=rec['wbs'],
                outline_number=rec['ono'], milestone=rec['ms'], seq=rec['seq']))
        db.commit()
        print('[OK] imported', len(rows))
        for rec in rows:
            print(rec['wbs'], rec['name'], rec['start'], rec['finish'], rec['dur'], rec['owner'])
    finally:
        db.close()
