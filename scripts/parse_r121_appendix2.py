# -*- coding: utf-8 -*-
"""列出 R121_SDP_V1.02.docx 中附录A/B/C 三张表结构。作者：袁燕"""
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
    for idx, tbl in enumerate(tables):
        trs = tbl.findall(f'{W}tr')
        if not trs:
            continue
        head = row_cells(trs[0])
        hs = '|'.join(head)
        grid = [g.get(f'{W}w') for g in tbl.iter(f'{W}gridCol')]
        mark = ''
        if any(k in hs for k in ['概率', '风险系数', '风险等级']):
            mark = ' <<< 附录A 风险管理表'
        elif any(k in hs for k in ['顾客代表', 'EPG', 'QAG']):
            mark = ' <<< 附录B 利益相关方参与计划表'
        elif '数据类别' in hs:
            mark = ' <<< 附录C 数据管理表'
        if mark:
            print(f'[表{idx}] 行数{len(trs)} 列数{len(grid)}{mark}')
            print(f'  表头: {head}')
            print(f'  列宽: {grid}')
            for r in trs[1:3]:
                print(f'    行: {row_cells(r)}')
            if len(trs) > 3:
                print(f'    末行: {row_cells(trs[-1])}')
            print()


if __name__ == '__main__':
    main()
