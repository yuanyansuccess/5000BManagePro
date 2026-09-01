# -*- coding: utf-8 -*-
"""代码整改 C 组（2/2）：C2 页宽常量化；C3 会议计划生成器导入统一。作者：袁燕"""
import io
import os

BASE = r'D:\5000\5000BManagePro'
n = 0

# C2 页宽常量
p = os.path.join(BASE, 'backend/services/table_builder.py')
src = io.open(p, encoding='utf-8').read()
anchor = 'TEMPLATES_DIR = os.path.join(config.BASE_DIR, "templates", "sdp")'
if 'PAGE_W_PORTRAIT' not in src:
    add = (anchor + '\n\n'
           '# 页面可用宽度（dxa）：正文纵向约 9468，附录横向约 14406（由模板 sectPr 决定）。\n'
           '# 动态表格列宽总和不得超过所在节可用宽，否则右侧被截、显示不完整（袁总反馈根因）。\n'
           'PAGE_W_PORTRAIT = 9468\n'
           'PAGE_W_LANDSCAPE = 14406')
    src = src.replace(anchor, add)
    io.open(p, 'w', encoding='utf-8').write(src)
    print('  [OK] C2 页宽常量化')
    n += 1

# C3 会议计划生成器局部导入统一
old = ('    from backend.db.session import SessionLocal as _SL\n'
       '    from backend.db.models import MeetingPlan as _MP\n'
       '    db = _SL()\n'
       '    try:\n        q = db.query(_MP)\n'
       '        if project_id:\n            q = q.filter(_MP.project_id == project_id)\n'
       '        rows = q.order_by(_MP.seq).all()\n'
       '    finally:\n        db.close()\n')
new = ('    db = SessionLocal()\n'
       '    try:\n'
       '        q = db.query(MeetingPlan)\n'
       '        if project_id:\n'
       '            q = q.filter(MeetingPlan.project_id == project_id)\n'
       '        rows = q.order_by(MeetingPlan.seq).all()\n'
       '    finally:\n        db.close()\n')
if old in src:
    src = src.replace(old, new, 1)
    if 'from backend.db.models import MeetingPlan' not in src:
        src = src.replace('from backend.db.models import Project, Risk',
                          'from backend.db.models import MeetingPlan, Project, Risk')
    io.open(p, 'w', encoding='utf-8').write(src)
    print('  [OK] C3 导入统一')
    n += 1
print('C2/C3 完成:', n, '处')
