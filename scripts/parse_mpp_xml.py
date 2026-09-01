# -*- coding: utf-8 -*-
"""解析 R105 进度表 XML（MS Project 导出）。作者：袁燕"""
import xml.etree.ElementTree as ET
ns = '{http://schemas.microsoft.com/project}'
p = r'E:\360MoveData\Users\25007\Desktop\R105软件进度表V2.00(只含项目启动和策划阶段).xml'
root = ET.parse(p).getroot()
tasks = root.find(f'{ns}Tasks')
print('Tasks 总数:', len(tasks))
rows = []
for t in tasks:
    g = lambda k: (t.find(f'{ns}{k}').text if t.find(f'{ns}{k}') is not None else '')
    rows.append(dict(
        uid=g('UID'), name=g('Name'), level=g('OutlineLevel'), summary=g('Summary'),
        outline=g('OutlineNumber'), start=g('Start'), finish=g('Finish'),
        dur=g('Duration'), work=g('Work'), milestone=g('Milestone')))
rows.sort(key=lambda r: (r['outline'] or 'zz'))
print('--- 任务列表(按大纲) ---')
for r in rows:
    star = '*' if r['summary'] == '1' else ('-' if r['milestone'] == '1' else ' ')
    nm = (r['name'] or '')[:40]
    out = (r['outline'] or '').rjust(6)
    lv = (r['level'] or '').rjust(1)
    uid = (r['uid'] or '').rjust(4)
    st = (r['start'] or '')[:10]
    fn = (r['finish'] or '')[:10]
    du = (r['dur'] or '')[:10]
    wk = (r['work'] or '')[:8]
    print(f"{star} {out} L{lv} {uid} {nm:40} {st}~{fn} dur={du} work={wk}")
