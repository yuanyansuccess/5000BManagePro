# -*- coding: utf-8 -*-
"""列出当前生成文档前 20 张表的内容摘要（上文+表头+行2），用于定位袁总提到的表号。作者：袁燕"""
import io
import sys
import zipfile
from xml.etree import ElementTree as ET

sys.path.insert(0, 'd:/5000/5000BManagePro')
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def cell_text(tc):
    return ''.join(t.text or '' for t in tc.iter(f'{W}t')).strip()


def main():
    from backend.services import doc_service
    data = doc_service.generate_doc_bytes('R105', 'SDP', module=None)
    z = zipfile.ZipFile(io.BytesIO(data))
    root = ET.fromstring(z.read('word/document.xml').decode('utf-8'))
    body = root.find(f'{W}body')

    items = []
    last_text = ''
    for child in body:
        tag = child.tag.replace(W, '')
        if tag == 'p':
            t = ''.join(x.text or '' for x in child.iter(f'{W}t')).strip()
            if t:
                last_text = t
        elif tag == 'tbl':
            items.append((last_text, child))
            last_text = ''

    for i, (cap, tbl) in enumerate(items[:20], 1):
        trs = tbl.findall(f'{W}tr')
        rows = [[cell_text(tc) for tc in tr.findall(f'{W}tc')] for tr in trs]
        grid = [g.get(f'{W}w') for g in tbl.iter(f'{W}gridCol')]
        total = sum(int(x) for x in grid if x) if grid else 0
        print(f'表{i:02} 列{len(grid)} 行{len(rows)} 宽{total}')
        print(f'   上文: {cap[:56]}')
        print(f'   表头: {str(rows[0])[:100] if rows else []}')
        if len(rows) > 1:
            print(f'   行2 : {str(rows[1])[:100]}')
        print()


if __name__ == '__main__':
    main()
