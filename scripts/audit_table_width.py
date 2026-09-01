# -*- coding: utf-8 -*-
"""诊断：计算页面可用宽度，逐表检查列宽总和是否溢出（袁总反馈"表格没有显示完整"）。
作者：袁燕
页面可用宽度 = 页面宽(pgSz.w) - 左边距(pgMar.left) - 右边距(pgMar.right)
表格总宽（tblW 或 gridCol 之和）超过可用宽度 -> 右侧被截，显示不完整。
"""
import io
import sys
import zipfile
from xml.etree import ElementTree as ET

sys.path.insert(0, 'd:/5000/5000BManagePro')

R121 = (r'C:\Users\25007\AppData\Local\Temp\codebuddy-dropped-files'
        r'\13ed8ea7-5867-4338-9d1a-29566d8b03bf\R121_SDP_V1.02.docx')
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
OUT = 'temp/table_width_audit.txt'


def page_width(root):
    sect = root.find(f'.//{W}sectPr')
    if sect is None:
        return None, None
    pg = sect.find(f'{W}pgSz')
    mar = sect.find(f'{W}pgMar')
    if pg is None or mar is None:
        return None, None
    pw = int(pg.get(f'{W}w'))
    left = int(mar.get(f'{W}left'))
    right = int(mar.get(f'{W}right'))
    return pw, pw - left - right


def table_seq(body):
    res, idx = [], 0
    for child in body:
        if child.tag.replace(W, '') == 'tbl':
            idx += 1
            res.append((idx, child))
    return res


def tbl_width(tbl):
    pr = tbl.find(f'{W}tblPr')
    w = None
    if pr is not None:
        tw = pr.find(f'{W}tblW')
        if tw is not None and tw.get(f'{W}w'):
            w = int(tw.get(f'{W}w'))
    grid = [int(g.get(f'{W}w')) for g in tbl.iter(f'{W}gridCol') if g.get(f'{W}w')]
    return w, (sum(grid) if grid else 0), len(grid)


def cell_text(tc):
    return ''.join(t.text or '' for t in tc.iter(f'{W}t')).strip()


def audit(name, path=None, data=None):
    z = zipfile.ZipFile(path) if data is None else zipfile.ZipFile(io.BytesIO(data))
    root = ET.fromstring(z.read('word/document.xml').decode('utf-8'))
    body = root.find(f'{W}body')
    pw, avail = page_width(root)
    lines = ['#' * 100, f'===== {name} =====']
    lines.append(f'页面宽={pw}  可用宽={avail} dxa')
    lines.append(f'{"表":>4} {"列":>4} {"tblW":>7} {"grid和":>7} {"判定":>10}  首行文本')
    over = []
    for i, tbl in table_seq(body):
        w, gsum, ncol = tbl_width(tbl)
        eff = w if w else gsum
        trs = tbl.findall(f'{W}tr')
        first = [cell_text(tc) for tc in trs[0].findall(f'{W}tc')] if trs else []
        ok = eff <= avail if avail else True
        flag = 'OK' if ok else f'溢出+{eff - avail}'
        if not ok:
            over.append((i, eff, ncol, first))
        lines.append(f'{i:>4} {ncol:>4} {str(w or "-"):>7} {gsum:>7} {flag:>10}  {str(first)[:56]}')
    lines.append('')
    lines.append(f'溢出表格数: {len(over)}')
    for i, eff, ncol, first in over:
        lines.append(f'  - 表{i}: 宽{eff} 列{ncol} | {str(first)[:58]}')
    lines.append('')
    return lines


def main():
    out = audit('R121 参考文档', path=R121)
    from backend.services import doc_service
    data = doc_service.generate_doc_bytes('R105', 'SDP', module=None)
    out += audit('当前生成的 R105 SDP', data=data)
    io.open(OUT, 'w', encoding='utf-8').write('\n'.join(out))
    print('\n'.join(l for l in out if ('溢出' in l or '=====' in l or '可用宽' in l)))


if __name__ == '__main__':
    main()
