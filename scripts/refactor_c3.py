# -*- coding: utf-8 -*-
"""代码整改 C 组（3/3）：C7~C11 注释与一致性优化。作者：袁燕"""
import io
import os
import re

BASE = r'D:\5000\5000BManagePro'
n = 0


def patch(rel, old, new, desc):
    global n
    p = os.path.join(BASE, rel)
    src = io.open(p, encoding='utf-8').read()
    if old not in src:
        print('  [跳过]', desc)
        return
    io.open(p, 'w', encoding='utf-8').write(src.replace(old, new, 1))
    print('  [OK]', desc)
    n += 1


# C7 api.js request() 函数注释增强
patch('frontend/js/api.js',
      'function request(method, url, opts) {',
      '// 平台统一请求入口：所有前端数据一律走 /api/*（绝不直连数据库）。\n'
      '// method=GET/POST/PUT/DELETE；opts 可携带 body、docNumber、docVersion 等查询参数。\n'
      '// 统一错误出口：非 2xx 时抛出后端 detail（前端各调用点 catch 后 toast 提示）。\n'
      'function request(method, url, opts) {',
      'C7 api.js request 注释增强')

# C8 shellSwitchTo：alert -> toast（统一提示风格）
patch('frontend/js/shell.js',
      "alert('已切换到 ' + pid);",
      "toast('已切换到 ' + pid);",
      'C8 切换项目 alert 改 toast')

# C9 resources.py ensure_tables 调用处补注释
patch('backend/api/resources.py',
      'def list_sched(project_id: str, db=Depends(get_db)):\n    ensure_tables(SchedulePhase)',
      'def list_sched(project_id: str, db=Depends(get_db)):\n'
      '    # 幂等兜底：防迁移半途导致表缺失时接口 500（与 session.ensure_tables 策略一致）\n'
      '    ensure_tables(SchedulePhase)',
      'C9 resources.py ensure_tables 注释')

# C10 doc.py commit_svn docstring 补返回说明
patch('backend/api/doc.py',
      '    module: est/risk/stake —— 分类同步（只更新该类数据，其余章节用快照保持原样）。\n    """',
      '    module: est/risk/stake —— 分类同步（只更新该类数据，其余章节用快照保持原样）。\n'
      '    返回：revision（SVN 修订号）与受控库文档路径；失败抛 404/500。\n    """',
      'C10 doc.py docstring 补齐')

# C11 session.py init_db 注释补齐
patch('backend/db/session.py',
      '    """启动建表/补列（继承智能柜 P22 schema 自检思路）。"""',
      '    """启动建表/补列（继承智能柜 P22 schema 自检思路）。\n'
      '    注意：此处执行的迁移均已做幂等保护（列存在即跳过），可随每次启动安全执行。\n    """',
      'C11 session.py init_db 注释')
print(f'C 组（3/3）完成: {n} 条')
