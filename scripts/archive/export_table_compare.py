# -*- coding: utf-8 -*-
"""导出两份文档（R121 参考 / 当前生成的 R105 SDP）的表格结构清单，用于逐表比对格式差异。
作者：袁燕
输出：temp/table_compare.txt
"""
import io
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

sys.path.insert(0, 'd:/5000/5000BManagePro')

R121 = (r'C:\Users\25007\AppData\Local\Temp\codebuddy-dropped-files'
        r'\13ed8ea7-5867-4338-9d1a-29566d8b03bf\R121_SDP_V1.02.docx')
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
OUT = 'temp/table_compare.txt'


def cell_text(tc):
    return ''.join(t.text or '' for t in tc.iter(f'{W}t')).strip()


def table_seq(body):
    """按文档顺序返回 (序号, 表标题, 表格元素)。"""
    res = []
    cur_title = ''
    idx = 0
    for child in body:
        tag = child.tag.replace(W, '')
        if tag == 'p':
            t = ''.join(x.text or '' for x in child.iter(f'{W}t')).strip()
            if re.match(r'^表\s*(\d+)\s*(.*)$', t):
                cur_title = t
        elif tag == 'tbl':
            idx += 1
            res.append((idx, cur_title, child))
            cur_title = ''
    return res


def dump(name, path=None, data=None):
    lines = ['#' * 110, f'===== {name} =====']
    if data is None:
        z = zipfile.ZipFile(path)
        xml = z.read('word/document.xml').decode('utf-8')
    else:
        z = zipfile.ZipFile(io.BytesIO(data))
        xml = z.read('word/document.xml').decode('utf-8')
    root = ET.fromstring(xml)
    body = root.find(f'{W}body')
    seq = table_seq(body)
    lines.append(f'表格总数: {len(seq)}')
    for i, title, tbl in seq:
        trs = tbl.findall(f'{W}tr')
        grid = [g.get(f'{W}w') for g in tbl.iter(f'{W}gridCol')]
        rows = [[cell_text(tc) for tc in tr.findall(f'{W}tc')] for tr in trs]
        head = rows[0] if rows else []
        r2 = rows[1] if len(rows) > 1 else []
        lines.append('-' * 100)
        lines.append(f'[表{i:02}] 标题: {title or "(无)"}')
        lines.append(f'   列数={len(grid)} 行数={len(rows)}')
        lines.append(f'   列宽={grid}')
        lines.append(f'   表头={head}')
        lines.append(f'   行2  ={r2}')
    lines.append('')
    return lines


def main():
    out = dump('R121 参考文档（袁总提供）', path=R121)
    from backend.services import doc_service
    data = doc_service.generate_doc_bytes('R105', 'SDP', module=None)
    out += dump('当前生成的 R105 SDP', data=data)
    io.open(OUT, 'w', encoding='utf-8').write('\n'.join(out))
    print('已导出:', OUT, '行数:', len(out))


if __name__ == '__main__':
    main()
