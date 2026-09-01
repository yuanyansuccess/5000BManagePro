# -*- coding: utf-8 -*-
"""补齐 table_builder.py 中 OOXML 属性缺失的 w: 命名空间前缀。作者：袁燕
问题：属性写作 w="900"（无前缀），Word 要求 w:w="900"，
      否则列宽/类型无效 -> 表格塌陷、显示不完整。
"""
import io

P = 'backend/services/table_builder.py'
src = io.open(P, encoding='utf-8').read()

PAIRS = [
    ('<w:gridCol w="%d"/>', '<w:gridCol w:w="%d"/>'),
    ('<w:tblW w="%d" type="dxa"/>', '<w:tblW w:w="%d" w:type="dxa"/>'),
    ('<w:tcW w="{width}" type="dxa"/>', '<w:tcW w:w="{width}" w:type="dxa"/>'),
]

for old, new in PAIRS:
    n = src.count(old)
    if n:
        src = src.replace(old, new)
        print(f'  替换 {n} 处: {old} -> {new}')

io.open(P, 'w', encoding='utf-8').write(src)
print('完成')
