# -*- coding: utf-8 -*-
"""校验 pp.js：子页签列表与估算面板结构（袁总要求：隐藏进度表 + 删除 Delphi 估算收敛表）。作者：袁燕"""
import re

src = open('frontend/js/pages/pp.js', encoding='utf-8').read()

print('--- PP_TABS（未注释）---')
for m in re.finditer(r"\{\s*key:\s*'(\w+)',\s*label:\s*'([^']+)'", src):
    print(' ', m.group(1), m.group(2))

print()
print('sched 是否已被注释:', "// { key: 'sched'" in src or "//{ key: 'sched'" in src)
print('是否残留 Delphi 标题:', '软件估算与收敛（Delphi 法' in src)
print('是否残留 rt-tabs 轮次切换:', 'ppEstSwitchRound' in src or "class=\"rt-tabs\"" in src)
print('是否残留 est-tbody:', 'est-tbody' in src)
print('是否残留 PP_EST_ROUND:', 'PP_EST_ROUND' in src)
print('ppSchedTab 是否仍定义（隐藏但保留代码）:', 'function ppSchedTab' in src)
print('ppCodeScaleLoad 仍存在:', 'function ppCodeScaleLoad' in src)

i = src.find('function ppEstPanel')
print()
print('--- ppEstPanel 代码块 ---')
print(src[i:i + 320])
