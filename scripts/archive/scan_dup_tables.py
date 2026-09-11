# -*- coding: utf-8 -*-
"""检查生成文档中各类表格是否重复出现（模板静态残留 + 动态生成）。作者：袁燕"""
import io
import sys
import zipfile
from xml.etree import ElementTree as ET

sys.path.insert(0, 'd:/5000/5000BManagePro')
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def cell_text(tc):
    return ''.join(t.text or '' for t in tc.iter(f'{W}t')).strip()


def scan(name, path=None, data=None):
    z = zipfile.ZipFile(path) if data is None else zipfile.ZipFile(io.BytesIO(data))
    root = ET.fromstring(z.read('word/document.xml').decode('utf-8'))
    body = root.find(f'{W}body')
    tbls = [t for t in body if t.tag.replace(W, '') == 'tbl']
    print('=' * 100)
    print(f'===== {name}  表格总数={len(tbls)} =====')
    keys = {
        '数据管理表': ['数据类别', '收集时机'],
        '配置项清单': ['配置项名称', '受控时机'],
        '基线列表': ['基线名称', '基线标识'],
        '会议计划': ['会议类型', '会议组织者'],
        '文档规模估计': ['规模估计'],
        '进度表': ['调整后总工作量'],
        '相关方清单': ['人员（代表）'],
        '风险表': ['风险通报方式及频率'],
        '相关方参与计划': ['顾客代表', 'EPG'],
        '硬件环境': ['资源名称', '跟踪情况'],
        '软件环境': ['软件名称', '跟踪情况'],
    }
    for label, kws in keys.items():
        hits = []
        for i, t in enumerate(tbls, 1):
            trs = t.findall(f'{W}tr')
            rows = [[cell_text(tc) for tc in tr.findall(f'{W}tc')] for tr in trs]
            joined = '|'.join('|'.join(r) for r in rows[:2])
            if all(k in joined for k in kws):
                grid = [int(g.get(f'{W}w') or 0) for g in t.iter(f'{W}gridCol')]
                hits.append((i, len(grid), sum(grid), len(rows)))
        if hits:
            mark = '  <== 重复' if len(hits) > 1 else ''
            print(f'  {label:14} 命中 {len(hits)} 次: {hits}{mark}')
        else:
            print(f'  {label:14} 未命中')


def main():
    scan('模板', path='templates/sdp/SDP_占位符版.docx')
    from backend.services import doc_service
    data = doc_service.generate_doc_bytes('R105', 'SDP', module=None)
    scan('生成文档', data=data)


if __name__ == '__main__':
    main()
