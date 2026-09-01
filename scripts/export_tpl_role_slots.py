# -*- coding: utf-8 -*-
"""导出模板 SDP_占位符版.docx 中所有 {{role.*}} 占位符及其所在表格行，用于角色统一核对。作者：袁燕"""
import io
import zipfile
from xml.etree import ElementTree as ET

PATH = r'D:\5000\5000BManagePro\templates\sdp\SDP_占位符版.docx'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def cell_text(tc):
    return ''.join(t.text or '' for t in tc.iter(f'{W}t')).strip()


def main():
    z = zipfile.ZipFile(PATH)
    root = ET.fromstring(z.read('word/document.xml').decode('utf-8'))
    body = root.find(f'{W}body')
    tables = list(body.iter(f'{W}tbl'))
    out = []
    out.append(f'表格数: {len(tables)}')
    for ti, tbl in enumerate(tables):
        trs = tbl.findall(f'{W}tr')
        rows = [[cell_text(tc) for tc in tr.findall(f'{W}tc')] for tr in trs]
        joined = '|'.join('|'.join(r) for r in rows)
        if '{{role.' not in joined and '李维' not in joined:
            continue
        out.append('=' * 100)
        out.append(f'[表{ti}] 行数{len(rows)}  <== 含角色占位符')
        for ri, r in enumerate(rows):
            out.append(f'  行{ri}: {r}')
    out.append('=' * 100)
    out.append('[段落中的角色占位符]')
    for p in body.iter(f'{W}p'):
        t = ''.join(x.text or '' for x in p.iter(f'{W}t'))
        if '{{role.' in t or '李维' in t:
            out.append('  ' + t[:160])
    io.open('temp/tpl_role_slots.txt', 'w', encoding='utf-8').write('\n'.join(out))
    print('\n'.join(out))


if __name__ == '__main__':
    main()
