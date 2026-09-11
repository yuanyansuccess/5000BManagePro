# -*- coding: utf-8 -*-
"""解析 R121 附录A 风险管理表（表32）每行的单元格数与 gridSpan，得到精确列合并结构。作者：袁燕"""
import io
import zipfile
from xml.etree import ElementTree as ET

PATH = r'D:\5000\R121\项目管理\项目策划\项目计划\R121_SDP_V1.02.docx'
OUT = r'D:\5000\5000BManagePro\temp\r121_risktbl_span.txt'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

TARGET = 32  # 附录A 风险管理表


def cell_text(tc):
    return ''.join(t.text or '' for t in tc.iter(f'{W}t')).strip()


def cell_span(tc):
    tcpr = tc.find(f'{W}tcPr')
    if tcpr is None:
        return 1
    gs = tcpr.find(f'{W}gridSpan')
    return int(gs.get(f'{W}val')) if gs is not None and gs.get(f'{W}val') else 1


def main():
    z = zipfile.ZipFile(PATH)
    root = ET.fromstring(z.read('word/document.xml').decode('utf-8'))
    body = root.find(f'{W}body')
    tables = list(body.iter(f'{W}tbl'))
    tbl = tables[TARGET]
    trs = tbl.findall(f'{W}tr')
    grid = [g.get(f'{W}w') for g in tbl.iter(f'{W}gridCol')]

    lines = []
    lines.append(f'表{TARGET} 行数={len(trs)} 列数={len(grid)}')
    lines.append(f'列宽: {grid}')
    lines.append('')
    for i, tr in enumerate(trs):
        tcs = tr.findall(f'{W}tc')
        spans = [cell_span(tc) for tc in tcs]
        texts = [cell_text(tc)[:26] for tc in tcs]
        lines.append(f'行{i}: span合计={sum(spans)} cell数={len(tcs)}')
        lines.append(f'   spans: {spans}')
        lines.append(f'   文本: {texts}')
    io.open(OUT, 'w', encoding='utf-8').write('\n'.join(lines))
    print('已导出:', OUT)
    print('\n'.join(lines[:40]))


if __name__ == '__main__':
    main()
