# -*- coding: utf-8 -*-
"""校验生成文档：全篇只读（无可编辑区间）+ 整篇黄色底纹 + 自动更新域。作者：袁燕"""
import collections
import io
import re
import sys
import zipfile

sys.path.insert(0, 'd:/5000/5000BManagePro')

SHD = re.compile(r'<w:shd[^>]*w:fill="([0-9A-Fa-f]{6})"')


def main():
    from backend.services import doc_service
    data = doc_service.generate_doc_bytes('R105', 'SDP', module=None)
    z = zipfile.ZipFile(io.BytesIO(data))
    xml = z.read('word/document.xml').decode('utf-8')
    st = z.read('word/settings.xml').decode('utf-8')

    fills = collections.Counter(SHD.findall(xml))
    print('底纹统计:', dict(fills))
    print('permStart 残留:', xml.count('permStart'))
    print('permEnd   残留:', xml.count('permEnd'))
    print('只读保护(Enforcement=1):', 'w:enforcement="1"' in st)
    print('打开自动更新域:', 'updateFields' in st)
    ok = (xml.count('permStart') == 0 and xml.count('permEnd') == 0
          and 'w:enforcement="1"' in st)
    print()
    print('结论:', 'PASS 全篇只读' if ok else 'FAIL 仍存在可编辑区间')


if __name__ == '__main__':
    main()
