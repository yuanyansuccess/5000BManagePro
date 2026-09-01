# -*- coding: utf-8 -*-
"""从 R105 原始开发计划（软件开发计划V3.01.docx）提取"会议计划"表真实数据。作者：袁燕"""
import io
import zipfile
from xml.etree import ElementTree as ET

PATH = (r'C:\Users\25007\AppData\Local\Temp\codebuddy-dropped-files'
        r'\f0874145-a36b-4547-9abe-7e700a56cafe\软件开发计划V3.01.docx')
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
OUT = 'temp/r105_meeting_plan.txt'


def cell_text(tc):
    return ''.join(t.text or '' for t in tc.iter(f'{W}t')).strip()


def main():
    z = zipfile.ZipFile(PATH)
    root = ET.fromstring(z.read('word/document.xml').decode('utf-8'))
    body = root.find(f'{W}body')
    tables = [t for t in body if t.tag.replace(W, '') == 'tbl']
    out = []
    for i, tbl in enumerate(tables, 1):
        trs = tbl.findall(f'{W}tr')
        rows = [[cell_text(tc) for tc in tr.findall(f'{W}tc')] for tr in trs]
        head = rows[0] if rows else []
        if '会议类型' in '|'.join(head) or '会议组织者' in '|'.join(head):
            out.append(f'[表{i}] 列{len(head)} 行{len(rows)}')
            for r in rows:
                out.append('   ' + ' || '.join(r))
    io.open(OUT, 'w', encoding='utf-8').write('\n'.join(out))
    print('\n'.join(out))


if __name__ == '__main__':
    main()
