# -*- coding: utf-8 -*-
"""代码整改 C 组（2/2）：C4 角色常量提取；C5 死函数删除；C6 魔法import改正。作者：袁燕"""
import io
import os
import re

BASE = r'D:\5000\5000BManagePro'
n = 0

# C4 pp.js：两处重复的 9 角色数组 -> 模块级常量
p = os.path.join(BASE, 'frontend/js/pages/pp.js')
src = io.open(p, encoding='utf-8').read()
const = ('// 利益相关方参与计划：9 角色列（对标 R121 附录B，与数据库 stakeholder_plan 列一致）\n'
         'var PP_STAKE_ROLES = ["customer_rep", "pm", "dept_lead", "proj_lead", "sys_eng",'
         ' "epg", "qag", "cmg", "otg"];\n'
         'var PP_STAKE_LABELS = ["顾客代表", "项目经理", "部门领导", "项目负责人", "系统工程组",'
         ' "EPG", "QAG", "CMG", "OTG"];\n')
if 'PP_STAKE_ROLES' not in src:
    src = src.replace('var PP_CUR_TAB = ', const + '\nvar PP_CUR_TAB = ', 1)
    src, k = re.subn(
        r"  var roles = \['customer_rep', 'pm'[^\]]+\];\n"
        r"(  var roleLabels = \[[^\]]+\];\n)?",
        "  var roles = PP_STAKE_ROLES;\n  var roleLabels = PP_STAKE_LABELS;\n", src)
    io.open(p, 'w', encoding='utf-8').write(src)
    print('  [OK] C4 pp.js 角色常量提取（替换', k, '处）')
    n += 1

# C5 pp.js：删除死函数 ppSyncAll（仅定义无调用）
m = re.search(r'\nfunction ppSyncAll\(\)[\s\S]*?\n}\n', src)
if m and len(re.findall(r'\bppSyncAll\b', src)) == 1:
    src = src.replace(m.group(0), '\n')
    io.open(p, 'w', encoding='utf-8').write(src)
    print('  [OK] C5 pp.js 删除死函数 ppSyncAll')
    n += 1

# C6 data_service：魔法 __import__ 改正常 import
p = os.path.join(BASE, 'backend/services/data_service.py')
src = io.open(p, encoding='utf-8').read()
old = ('        return db.query(__import__("backend.db.models", '
       'fromlist=["SchedulePhase"]).SchedulePhase).all()')
if old in src:
    src = src.replace(old,
                      '        from backend.db.models import SchedulePhase\n'
                      '        return db.query(SchedulePhase).all()', 1)
    io.open(p, 'w', encoding='utf-8').write(src)
    print('  [OK] C6 data_service 魔法import改正')
    n += 1
print('C 组（2/2）完成:', n, '条')
