# -*- coding: utf-8 -*-
"""终验：只读岛布局 + 无底纹 + perm 区间数。作者：袁燕"""
import collections
import io
import re
import sys
import zipfile

sys.path.insert(0, 'd:/5000/5000BManagePro')

from backend.services import doc_service
from backend.services.doc_service import READONLY_TABLE_KEYS

data = doc_service.generate_doc_bytes('R105', 'SDP', module=None)
z = zipfile.ZipFile(io.BytesIO(data))
xml = z.read('word/document.xml').decode('utf-8')
st = z.read('word/settings.xml').decode('utf-8')

print('1) 只读保护 enforcement=1:', 'w:enforcement="1"' in st)
fills = collections.Counter(re.findall(r'<w:shd[^>]*w:fill="([0-9A-Fa-f]{6})"', xml))
print('2) 底纹统计（应无 FFFF00）:', dict(fills))
ns, ne = xml.count('<w:permStart'), xml.count('<w:permEnd')
print(f'3) perm: start={ns} end={ne}（应相等；岛数={ns - 1}）')
print('4) 只读表关键词组数:', len(READONLY_TABLE_KEYS))

# 逐岛验证：每个 permEnd 后紧跟的表格表头是否为只读表
zones = [(m.start(), m.group(0)) for m in
         re.finditer(r'<w:perm(?:Start|End)[^>]*/>', xml)]
ro_tables = 0
for idx in range(len(zones) - 1):
    pos, tag = zones[idx]
    if 'permEnd' in tag:
        seg = xml[pos:zones[idx + 1][0]]
        if '<w:tbl>' in seg or '<w:tbl ' in seg:
            ro_tables += 1
print('5) permEnd 后紧跟表格（只读岛）:', ro_tables)

ok = ('w:enforcement="1"' in st and 'FFFF00' not in str(fills)
      and ns == ne and ro_tables == len(READONLY_TABLE_KEYS))
print()
print('结论:', 'PASS' if ok else 'FAIL')
