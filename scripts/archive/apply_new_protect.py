# -*- coding: utf-8 -*-
"""用 temp/new_protect.py 的新保护逻辑替换 doc_service 旧实现。作者：袁燕"""
import io

SRC = 'backend/services/doc_service.py'
NEW = 'temp/new_protect.py'

src = io.open(SRC, encoding='utf-8').read()
new_code = io.open(NEW, encoding='utf-8').read()

a = src.find('def _shade_readonly_yellow')
assert a > 0, 'old start not found'
tail = src[a:]
print('old len:', len(tail))
src = src[:a] + new_code
io.open(SRC, 'w', encoding='utf-8').write(src)
print('replaced ok')
