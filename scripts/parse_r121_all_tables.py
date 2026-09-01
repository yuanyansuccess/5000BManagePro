# -*- coding: utf-8 -*-
"""列出 R121_SDP_V1.02.docx 全部表格索引/行数/列数/前两行，用于定位附录A/B。作者：袁燕"""
import zipfile
from xml.etree import ElementTree as ET

PATH = r'D:\5000\R121\项目管理\项目策划\项目计划\R121_SDP_V1.02.docx'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def cell_text(tc):
    return ''.join(t.text or '' for t in tc.iter(f'{W}t')).strip()


def row_cells(tr):
    return [cell_text(tc) for tc in tr.findall(f'{W}tc')]


def main():
    z = zipfile.ZipFile(PATH)
    root = ET.fromstring(z.read('word/document.xml').decode('utf-8'))
    body = root.find(f'{W}body')
    tables = list(body.iter(f'{W}tbl'))
    print('表格总数:', len(tables))
    for idx, tbl in enumerate(tables):
        trs = tbl.findall(f'{W}tr')
        if not trs:
            continue
        grid = [g.get(f'{W}w') for g in tbl.iter(f'{W}gridCol')]
        r1 = row_cells(trs[0])
        r2 = row_cells(trs[1]) if len(trs) > 1 else []
        s1 = '|'.join(r1)[:70]
        s2 = '|'.join(r2)[:70]
        print(f'[表{idx:2}] 行{len(trs):2} 列{len(grid):2} | R1: {s1}')
        if s2:
            print(f'{"":9}            | R2: {s2}')


if __name__ == '__main__':
    main()
