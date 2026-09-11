# -*- coding: utf-8 -*-
"""对比当前模板与两份备份的完整性（shd 底纹/长度/占位符）。作者：袁燕"""
import collections
import re
import zipfile

FILES = [
    'templates/sdp/SDP_占位符版.docx',
    'templates/sdp/SDP_占位符版.docx.rolefix.bak',
    'templates/sdp/SDP_占位符版.docx.measure.bak',
]
SHD = re.compile(r'<w:shd[^>]*w:fill="([0-9A-Fa-f]{6})"')

for p in FILES:
    try:
        z = zipfile.ZipFile(p)
        xml = z.read('word/document.xml').decode('utf-8')
        f = collections.Counter(SHD.findall(xml))
        print(f'{p.split("/")[-1]:34} 长度={len(xml):7}  shd={dict(f)}  '
              f'李维={"李维" in xml}  '
              f'measure={xml.count("{{role.measure}}")}  '
              f'coder={xml.count("{{role.coder}}")}')
    except Exception as e:
        print(f'{p}: ERR {e}')
