# -*- coding: utf-8 -*-
"""按表头关键词在 R121 参考文档中精确定位各表，输出列宽与表头作为格式对标基准。作者：袁燕"""
import zipfile
from xml.etree import ElementTree as ET

R121 = (r'C:\Users\25007\AppData\Local\Temp\codebuddy-dropped-files'
        r'\13ed8ea7-5867-4338-9d1a-29566d8b03bf\R121_SDP_V1.02.docx')
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

TARGETS = {
    '进度表（工作量估算）': ['调整后总工作量', '工程类工作量'],
    '相关方清单（A14）': ['人员（代表）', '组织机构'],
    '基线列表': ['基线'],
    '会议计划': ['会议类型', '会议时机'],
    '硬件环境资源表': ['资源名称', '跟踪情况'],
    '软件环境资源表': ['软件名称'],
    '文档规模估计': ['规模估计'],
    '人力资源投入': ['投入精力'],
    '配置项清单': ['配置项名称'],
}


def cell_text(tc):
    return ''.join(t.text or '' for t in tc.iter(f'{W}t')).strip()


def main():
    z = zipfile.ZipFile(R121)
    root = ET.fromstring(z.read('word/document.xml').decode('utf-8'))
    body = root.find(f'{W}body')
    tables = [t for t in body if t.tag.replace(W, '') == 'tbl']
    print(f'顶层表格数: {len(tables)}')
    for label, kws in TARGETS.items():
        print('=' * 96)
        print(f'【{label}】')
        found = False
        for i, tbl in enumerate(tables, 1):
            trs = tbl.findall(f'{W}tr')
            if not trs:
                continue
            rows = [[cell_text(tc) for tc in tr.findall(f'{W}tc')] for tr in trs]
            joined = '|'.join('|'.join(r) for r in rows[:2])
            if not all(k in joined for k in kws):
                continue
            grid = [g.get(f'{W}w') for g in tbl.iter(f'{W}gridCol')]
            total = sum(int(x) for x in grid if x) if grid else 0
            print(f'  表序号={i}  列数={len(grid)} 行数={len(rows)}')
            print(f'  列宽={grid}  合计={total}')
            print(f'  表头={rows[0]}')
            if len(rows) > 1:
                print(f'  行2  ={rows[1]}')
            found = True
            break
        if not found:
            print('  （未匹配到）')


if __name__ == '__main__':
    main()
