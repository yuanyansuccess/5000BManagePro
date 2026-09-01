# -*- coding: utf-8 -*-
"""查看生成文档中"会议计划"表的结构与占位符情况（袁总：会议时机动态取自进度表）。作者：袁燕"""
import io
import sys
import zipfile
from xml.etree import ElementTree as ET

sys.path.insert(0, 'd:/5000/5000BManagePro')
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def cell_text(tc):
    return ''.join(t.text or '' for t in tc.iter(f'{W}t')).strip()


def find_meeting_tbl(body, label):
    print(f'===== {label} =====')
    for i, tbl in enumerate([t for t in body if t.tag.replace(W, '') == 'tbl'], 1):
        trs = tbl.findall(f'{W}tr')
        rows = [[cell_text(tc) for tc in tr.findall(f'{W}tc')] for tr in trs]
        joined = '|'.join('|'.join(r) for r in rows[:3])
        if '会议' in joined and ('时机' in joined or '组织者' in joined):
            grid = [g.get(f'{W}w') for g in tbl.iter(f'{W}gridCol')]
            print(f'  表序号={i} 列{len(grid)} 行{len(rows)} 列宽={grid}')
            for r in rows:
                print(f'    {r}')
            return
    print('  （未找到会议计划表）')


def main():
    z = zipfile.ZipFile('templates/sdp/SDP_占位符版.docx')
    root = ET.fromstring(z.read('word/document.xml').decode('utf-8'))
    find_meeting_tbl(root.find(f'{W}body'), '模板中的会议计划表')

    from backend.services import doc_service
    data = doc_service.generate_doc_bytes('R105', 'SDP', module=None)
    z2 = zipfile.ZipFile(io.BytesIO(data))
    root2 = ET.fromstring(z2.read('word/document.xml').decode('utf-8'))
    find_meeting_tbl(root2.find(f'{W}body'), '\n生成文档中的会议计划表')

    print('\n===== R105 进度表中含"会议/例会"的任务 =====')
    from backend.db.session import SessionLocal
    from backend.db.models import ScheduleTask
    db = SessionLocal()
    try:
        for t in db.query(ScheduleTask).filter(
                ScheduleTask.project_id == 'R105').order_by(ScheduleTask.seq).all():
            if ('会议' in (t.task_name or '')) or ('例会' in (t.task_name or '')):
                print(f'  seq={t.seq} {t.outline_number} {t.task_name} '
                      f'{t.plan_start}~{t.plan_finish} 负责人={t.owner}')
    finally:
        db.close()


if __name__ == '__main__':
    main()
