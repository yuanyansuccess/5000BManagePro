# -*- coding: utf-8 -*-
"""列出文档所有节的页面设置（sectPr）与正文中的"表 N"题注。作者：袁燕
用途：确认是否存在"正文纵向 + 附录横向"分节，避免把横向页的表格宽度标准误用于正文表格。
"""
import io
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

sys.path.insert(0, 'd:/5000/5000BManagePro')

R121 = (r'C:\Users\25007\AppData\Local\Temp\codebuddy-dropped-files'
        r'\13ed8ea7-5867-4338-9d1a-29566d8b03bf\R121_SDP_V1.02.docx')
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def show(name, path=None, data=None):
    z = zipfile.ZipFile(path) if data is None else zipfile.ZipFile(io.BytesIO(data))
    root = ET.fromstring(z.read('word/document.xml').decode('utf-8'))
    body = root.find(f'{W}body')
    print('=' * 100)
    print(f'===== {name} =====')
    idx = 0
    for sect in root.iter(f'{W}sectPr'):
        idx += 1
        pg = sect.find(f'{W}pgSz')
        mar = sect.find(f'{W}pgMar')
        if pg is None:
            continue
        pw = pg.get(f'{W}w')
        ph = pg.get(f'{W}h')
        orient = pg.get(f'{W}orient') or '（默认）'
        if mar is None:
            print(f'  节{idx}: 宽{pw} 高{ph} 方向={orient} 无页边距')
            continue
        l = int(mar.get(f'{W}left'))
        r = int(mar.get(f'{W}right'))
        print(f'  节{idx}: 宽{pw} 高{ph} 方向={orient} 边距L/R={l}/{r} -> 可用宽={int(pw) - l - r}')
    caps = []
    for p in body.iter(f'{W}p'):
        t = ''.join(x.text or '' for x in p.iter(f'{W}t')).strip()
        if re.match(r'^表\s*\d+', t) and len(t) < 60:
            caps.append(t)
    print(f'\n  表题注数量: {len(caps)}')
    for c in caps:
        print('   ', c)


def main():
    show('R121 参考文档', path=R121)
    from backend.services import doc_service
    data = doc_service.generate_doc_bytes('R105', 'SDP', module=None)
    show('当前生成的 R105 SDP', data=data)


if __name__ == '__main__':
    main()
