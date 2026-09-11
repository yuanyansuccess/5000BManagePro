# -*- coding: utf-8 -*-
"""检查 table_builder.py 中 OOXML 属性是否缺 w: 命名空间前缀。作者：袁燕"""
import re

P = 'backend/services/table_builder.py'
src = open(P, encoding='utf-8').read()

bad = {}
for m in re.finditer(r'<w:([A-Za-z]+)((?:\s+[A-Za-z:]+="[^"]*")*)\s*/?>', src):
    tag, attrs = m.group(1), m.group(2)
    for a in re.finditer(r'\s+([A-Za-z:]+)=', attrs):
        n = a.group(1)
        if not n.startswith('w:') and n != 'xmlns:w':
            bad.setdefault((tag, n), 0)
            bad[(tag, n)] += 1

print('缺 w: 前缀的属性（元素 -> 属性）：')
for (tag, attr), cnt in sorted(bad.items()):
    print(f'  <w:{tag}> 属性 "{attr}"  x{cnt}')
print(f'\n合计 {len(bad)} 类、{sum(bad.values())} 处')
