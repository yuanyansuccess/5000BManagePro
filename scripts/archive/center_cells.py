# -*- coding: utf-8 -*-
"""动态表单元格段落统一居中（对标 R121 原文 w:jc=center）。作者：袁燕"""
import io

p = 'backend/services/table_builder.py'
t = io.open(p, encoding='utf-8').read()
old = '<w:p><w:r><w:t xml:space='
new = '<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:t xml:space='
print('hit:', t.count(old))
io.open(p, 'w', encoding='utf-8').write(t.replace(old, new))
print('done')
