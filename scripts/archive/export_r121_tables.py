# -*- coding: utf-8 -*-
"""把 R121 参考文档表格结构导出为 UTF-8 文本（PowerShell 控制台中文会乱码）。作者：袁燕
重点：附录A 风险管理表 / 附录B 利益相关方参与计划表 / 附录C 数据管理表
"""
import io
import zipfile
from xml.etree import ElementTree as ET

PATH = r'D:\5000\R121\项目管理\项目策划\项目计划\R121_SDP_V1.02.docx'
OUT = r'D:\5000\5000BManagePro\temp\r121_tables.txt'
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
    lines = []
    lines.append(f'表格总数: {len(tables)}\n')

    for idx, tbl in enumerate(tables):
        trs = tbl.findall(f'{W}tr')
        if not trs:
            continue
        grid = [g.get(f'{W}w') for g in tbl.iter(f'{W}gridCol')]
        rows = [row_cells(tr) for tr in trs]
        joined = '|'.join('|'.join(r) for r in rows[:3])
        mark = ''
        if any(k in joined for k in ['概率', '风险系数', '风险等级', '风险描述']):
            mark = '  <<<<<< 附录A 风险管理表'
        elif any(k in joined for k in ['顾客代表', 'EPG', 'QAG', 'CMG', 'OTG']):
            mark = '  <<<<<< 附录B 利益相关方参与计划表'
        elif '数据类别' in joined:
            mark = '  <<<<<< 附录C 数据管理表'
        lines.append('=' * 110)
        lines.append(f'[表{idx}] 行数{len(trs)} 列数{len(grid)}{mark}')
        lines.append(f'  列宽: {grid}')
        for i, r in enumerate(rows):
            tag = '表头' if i == 0 else f' 行{i}'
            lines.append(f'  {tag}: {r}')
        lines.append('')

    io.open(OUT, 'w', encoding='utf-8').write('\n'.join(lines))
    print('已导出:', OUT)


if __name__ == '__main__':
    main()
