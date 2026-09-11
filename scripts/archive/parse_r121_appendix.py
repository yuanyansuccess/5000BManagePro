# -*- coding: utf-8 -*-
"""解析 R121 参考开发计划（R121_SDP_V1.02.docx）的附录 A/B/C 三张表结构，
用于校准 table_builder 生成的表格格式。作者：袁燕
输出：每张表的 表头文字 / 列数 / 行数 / 前若干行内容 / 列宽（gridCol）
"""
import re
import sys
import zipfile

PATH = r'D:\5000\R121\项目管理\项目策划\项目计划\R121_SDP_V1.02.docx'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def cell_text(tc):
    return ''.join(t.text or '' for t in tc.iter(f'{W}t')).strip()


def row_cells(tr):
    return [cell_text(tc) for tc in tr.findall(f'{W}tc')]


def grid(tbl):
    return [g.get(f'{W}w') for g in tbl.iter(f'{W}gridCol')]


def main():
    z = zipfile.ZipFile(PATH)
    xml = z.read('word/document.xml').decode('utf-8')
    # 定位附录标题附近文字
    text = re.sub(r'<[^>]+>', '', xml)
    for kw in ['附录A', '附录B', '附录C', '风险管理表', '利益相关方参与计划', '数据管理表']:
        i = text.find(kw)
        print(f'{kw}: 位置 {i}' + (f'  上下文: ...{text[i:i+60]}...' if i >= 0 else '（未找到）'))
    print()

    from xml.etree import ElementTree as ET
    root = ET.fromstring(xml)
    body = root.find(f'{W}body')
    tables = list(body.iter(f'{W}tbl'))
    print(f'文档表格总数: {len(tables)}\n')

    for idx, tbl in enumerate(tables):
        trs = tbl.findall(f'{W}tr')
        if not trs:
            continue
        head = row_cells(trs[0])
        head_s = '|'.join(head)
        # 只关心三张附录表
        is_a = ('风险' in head_s and '概率' in head_s) or '风险类别' in head_s
        is_b = '顾客代表' in head_s or ('活动' in head_s and 'EPG' in head_s)
        is_c = '数据类别' in head_s or ('存储' in head_s and '管理' in head_s)
        if not (is_a or is_b or is_c):
            continue
        tag = '附录A 风险管理表' if is_a else ('附录B 利益相关方参与计划表' if is_b else '附录C 数据管理表')
        print('=' * 100)
        print(f'[表{idx}] {tag}')
        print(f'  列数(gridCol): {len(grid(tbl))}  列宽: {grid(tbl)}')
        print(f'  行数: {len(trs)}')
        print(f'  表头: {head}')
        for r in trs[1:4]:
            print(f'    行: {row_cells(r)}')
        if len(trs) > 4:
            print(f'    末行: {row_cells(trs[-1])}')
        # 表头样式：加粗/字号/底纹
        first_tr = trs[0]
        for tc in first_tr.findall(f'{W}tc')[:1]:
            tcpr = tc.find(f'{W}tcPr')
            if tcpr is not None:
                shd = tcpr.find(f'{W}shd')
                if shd is not None:
                    print('  表头底纹:', shd.attrib)
        print()


if __name__ == '__main__':
    main()
