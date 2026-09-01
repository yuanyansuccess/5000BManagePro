# -*- coding: utf-8 -*-
"""诊断：1) 模板锚点出现次数；2) 生成文档规模类表全量清点。作者：袁燕"""
import io
import sys
import zipfile
from xml.etree import ElementTree as ET

sys.path.insert(0, 'd:/5000/5000BManagePro')
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

z = zipfile.ZipFile('templates/sdp/SDP_占位符版.docx')
xml = z.read('word/document.xml').decode('utf-8')
print('===== 模板锚点出现次数 =====')
for a in ['{{table.doc_scale_est}}', '{{table.doc_scale_reuse}}',
          '{{table.code_scale_est}}', '{{table.code_scale_reuse}}',
          '{{table.schedule}}', '{{table.stakeholders}}',
          '{{table.hw_env_res}}', '{{table.sw_env_res}}',
          '{{table.meeting_plan}}', '{{table.risks}}',
          '{{table.stakeholder_plan}}', '{{table.data_mgmt}}']:
    print(f'  {a:34} x{xml.count(a)}')

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from backend.services import doc_service
data = doc_service.generate_doc_bytes('R105', 'SDP', module=None)
z2 = zipfile.ZipFile(io.BytesIO(data))
root = ET.fromstring(z2.read('word/document.xml').decode('utf-8'))
body = root.find(f'{W}body')
print('\n===== 生成文档：规模类表全量清点 =====')
last = ''
i = 0
for child in body:
    tag = child.tag.replace(W, '')
    if tag == 'p':
        t = ''.join(x.text or '' for x in child.iter(f'{W}t')).strip()
        if t:
            last = t
    elif tag == 'tbl':
        i += 1
        trs = child.findall(f'{W}tr')
        rows = [[''.join(x.text or '' for x in tc.iter(f'{W}t')).strip()
                 for tc in tr.findall(f'{W}tc')] for tr in trs]
        head = '|'.join(rows[0]) if rows else ''
        if ('规模' in head or '规模' in last or '构件' in head or '部件' in head
                or 'Loc' in head):
            grid = [int(g.get(f'{W}w') or 0) for g in child.iter(f'{W}gridCol')]
            print(f'表{i:02} 列{len(grid)} 行{len(rows)} 宽{sum(grid)}')
            print(f'   上文: {last[:52]}')
            print(f'   表头: {str(rows[0])[:86]}')
            if len(rows) > 1:
                print(f'   行2 : {str(rows[1])[:86]}')
            print()
