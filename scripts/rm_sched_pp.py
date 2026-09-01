# -*- coding: utf-8 -*-
"""删除 pp.js 中「进度表」全部前端元素（袁总要求：页面彻底删除，后台数据保留）。
作者：袁燕
范围：PP 页 PP_TABS 的 sched 注释行 + ppSchedTab/ppSchedLoad/ppSchedSave/ppSchedAdd/
     ppSchedSaveNew/ppSchedDel/ppSchedTaskLoad/ppSchedTaskSave/ppSchedTaskDel/
     ppSchedTaskAdd/ppSchedTaskSaveNew 全部函数块（672~803 行区间）。
后端接口与 schedule_tasks/schedule_phases 数据均保留（仍作为生成 SDP 的数据源）。
"""
import io

P = 'frontend/js/pages/pp.js'
src = io.open(P, encoding='utf-8').read()

# 1) 删除 PP_TABS 中的 sched 注释行
lines = src.split('\n')
out = [l for l in lines if "key: 'sched'" not in l]
removed_tabs = len(lines) - len(out)
src = '\n'.join(out)

# 2) 删除进度表函数块：从 "// 进度表（按项目维度" 到 "// 利益相关方（按项目维度" 之前
marker_start = '// 进度表（按项目维度'
marker_end = '// 利益相关方（按项目维度'
i = src.find(marker_start)
j = src.find(marker_end)
if i < 0 or j < 0 or j <= i:
    print('[FAIL] 未定位到进度表函数块区间')
    raise SystemExit(1)
removed_chars = j - i
src = src[:i] + src[j:]

io.open(P, 'w', encoding='utf-8').write(src)
print(f'[OK] 删除 sched tab 行 {removed_tabs} 行，删除函数块 {removed_chars} 字符')
