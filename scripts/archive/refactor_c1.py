# -*- coding: utf-8 -*-
"""代码整改 C 组（1/2）：C1 doc_service re 提升模块级。作者：袁燕"""
import io
import os

BASE = r'D:\5000\5000BManagePro'
p = os.path.join(BASE, 'backend/services/doc_service.py')
src = io.open(p, encoding='utf-8').read()
n = 0
if '\nimport re\n' not in src:
    src = src.replace('import os\n', 'import os\nimport re\n', 1)
    n += 1
if 'import re as _re' in src:
    src = src.replace('    import re as _re\n', '')
    src = src.replace('_re.subn', 're.subn').replace('_re.sub', 're.sub')
    src = src.replace('_re.S', 're.S')
    n += 1
io.open(p, 'w', encoding='utf-8').write(src)
print('C1 完成:', n, '处')
