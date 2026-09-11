# -*- coding: utf-8 -*-
"""代码整改 C 组（3/3 补）：C7/C8/C9 按实际格式处理。作者：袁燕"""
import io
import os
import re

BASE = r'D:\5000\5000BManagePro'
n = 0

# C7 api.js：request 实际签名 async (method, path, body)
p = os.path.join(BASE, 'frontend/js/api.js')
src = io.open(p, encoding='utf-8').read()
if '平台统一请求入口' not in src:
    old = 'async function request(method, path, body) {'
    new = ('// 平台统一请求入口：所有前端数据一律走 /api/*（绝不直连数据库）。\n'
           '// method=GET/POST/PUT/DELETE；body 为 JSON 载荷（GET 可忽略）。\n'
           '// 统一错误出口：非 2xx 抛出后端 detail，由各调用点 catch 后 toast 提示。\n'
           'async function request(method, path, body) {')
    src = src.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8').write(src)
    print('  [OK] C7 api.js request 注释增强')
    n += 1

# C8 切换项目提示实际在 settings.js 的 settingsSetCurProj
p = os.path.join(BASE, 'frontend/js/pages/settings.js')
src = io.open(p, encoding='utf-8').read()
old = "settingsLoadProjects(); alert('已切换到 ' + pid);"
if old in src:
    src = src.replace(old, "settingsLoadProjects(); toast('已切换到 ' + pid);", 1)
    io.open(p, 'w', encoding='utf-8').write(src)
    print('  [OK] C8 切换项目 alert 改 toast')
    n += 1

# C9 resources.py：11 处函数内重复局部 import ensure_tables -> 模块顶部一次
p = os.path.join(BASE, 'backend/api/resources.py')
src = io.open(p, encoding='utf-8').read()
cnt = src.count('    from backend.db.session import ensure_tables\n')
if cnt:
    src = src.replace('    from backend.db.session import ensure_tables\n', '')
    anchor = ('from backend.dao import hw_res_dao, sw_res_dao, doc_scale_dao, '
              'code_scale_dao, schedule_dao')
    src = src.replace(anchor,
                      anchor + '\n'
                      'from backend.db.session import ensure_tables  '
                      '# 幂等兜底：防表缺失时接口 500')
    io.open(p, 'w', encoding='utf-8').write(src)
    print(f'  [OK] C9 resources.py 局部import提升（清理 {cnt} 处重复）')
    n += 1
print(f'C 组（3/3 补）完成: {n} 条')
