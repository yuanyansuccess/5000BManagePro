# -*- coding: utf-8 -*-
"""终审：生成文档全部表格 vs R121 参考文档，逐表对比 列数/总宽/一致性。作者：袁燕
判定：动态表总宽 <= 所在页可用宽（纵向 9468 / 横向 14406）；
      模板静态表与 R121 对应表总宽一致（±300 容差）即 PASS。
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
OUT = 'temp/table_final_audit.txt'
LIMIT_P, LIMIT_L = 9468, 14406

DYNAMIC = {
    '文档规模估计': ('规模估计', LIMIT_P),
    '进度表': ('调整后总工作量', LIMIT_P),
    '会议计划': ('会议类型', LIMIT_P),
    '配置项清单': ('受控时机', LIMIT_P),
    '基线列表': ('基线名称', LIMIT_P),
    '相关方清单': ('姓名/单位', LIMIT_P),
    '硬件环境': ('资源名称', LIMIT_L),
    '软件环境': ('软件名称', LIMIT_P),
    '风险表': ('风险通报方式及频率', LIMIT_L),
    '相关方参与计划': ('顾客代表', LIMIT_L),
    '数据管理表': ('收集时机', LIMIT_L),
}


def cell_text(tc):
    return ''.join(t.text or '' for t in tc.iter(f'{W}t')).strip()


def get_tables(path=None, data=None):
    z = zipfile.ZipFile(path) if data is None else zipfile.ZipFile(io.BytesIO(data))
    root = ET.fromstring(z.read('word/document.xml').decode('utf-8'))
    body = root.find(f'{W}body')
    res = []
    for t in [x for x in body if x.tag.replace(W, '') == 'tbl']:
        trs = t.findall(f'{W}tr')
        rows = [[cell_text(tc) for tc in tr.findall(f'{W}tc')] for tr in trs]
        grid = [int(g.get(f'{W}w') or 0) for g in t.iter(f'{W}gridCol')]
        res.append({'ncol': len(grid), 'total': sum(grid), 'rows': rows,
                    'head': rows[0] if rows else []})
    return res


def classify(tbl):
    head = '|'.join(tbl['head'])
    for label, (kw, limit) in DYNAMIC.items():
        if kw in head:
            return label, limit
    return '模板静态表', LIMIT_P


def main():
    out = []
    r121 = get_tables(path=R121)
    from backend.services import doc_service
    gen = get_tables(data=doc_service.generate_doc_bytes('R105', 'SDP', module=None))

    r121_width = {'|'.join(t['head'])[:30]: t['total'] for t in r121}
    out.append(f'R121 表格数={len(r121)}   生成文档表格数={len(gen)}')
    out.append('')
    problems = []
    for i, t in enumerate(gen, 1):
        label, limit = classify(t)
        total = t['total']
        if label == '模板静态表':
            k = '|'.join(t['head'])[:30]
            ref = r121_width.get(k)
            if ref is None:
                for k2, v2 in r121_width.items():
                    if k2[:12] == k[:12]:
                        ref = v2
                        break
            if ref is not None and abs(ref - total) <= 300:
                status = f'OK（与R121一致 宽{total}/参考{ref}）'
            elif ref is not None:
                status = f'注意（与R121不同 宽{total}/参考{ref}）'
                problems.append(f'表{i} {label}: 宽{total} vs R121 {ref}')
            else:
                status = f'OK（R121 无对应，宽{total}）'
        else:
            if total <= limit:
                status = f'OK（动态表 宽{total} <= 上限{limit}）'
            else:
                status = f'FAIL（动态表溢出 宽{total} > 上限{limit}）'
                problems.append(f'表{i} {label}: 宽{total} 溢出')
        out.append(f'表{i:02} [{label:10}] 列{t["ncol"]:2} 行{len(t["rows"]):2} '
                   f'宽{total:6}  {status}')

    out.append('')
    out.append('=' * 80)
    if problems:
        out.append(f'问题 {len(problems)} 项：')
        out += ['  - ' + p for p in problems]
    else:
        out.append('全部表格 PASS（动态表适配页面宽度；静态表与 R121 一致）')
    io.open(OUT, 'w', encoding='utf-8').write('\n'.join(out))
    print('\n'.join(out))


if __name__ == '__main__':
    main()
