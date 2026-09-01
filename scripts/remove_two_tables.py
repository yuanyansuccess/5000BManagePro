# -*- coding: utf-8 -*-
"""袁总 2026-09-01：删除两张表的生成项（doc_scale_est / code_scale_reuse）。作者：袁燕"""
import io

p = 'backend/services/doc_service.py'
t = io.open(p, encoding='utf-8').read()
old1 = ('    table_map["{{table.doc_scale_est}}"] = build_doc_scale_tbl(\n'
        '        data_service.DataService.list_doc_scale(db, project_id), kind="est")\n')
old2 = ('    table_map["{{table.code_scale_reuse}}"] = '
        'build_code_scale_tbl(project_id, kind="reuse")\n')
c1, c2 = t.count(old1), t.count(old2)
t = t.replace(old1, '').replace(old2, '')
mark = ('    # 袁总 2026-09-01：删除"文档规模估计"与"IAP 代码规模估计"两张表，\n'
        '    # 仅保留"文档规模估计及复用情况"一张表承载规模数据。\n')
if c1:
    t = t.replace('    table_map["{{table.doc_scale_reuse}}"]',
                  mark + '    table_map["{{table.doc_scale_reuse}}"]', 1)
io.open(p, 'w', encoding='utf-8').write(t)
print('removed:', c1, c2)
