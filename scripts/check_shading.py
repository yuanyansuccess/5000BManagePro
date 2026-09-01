# -*- coding: utf-8 -*-
"""检查模板与生成文档中的底纹（shd fill）与可编辑区间（permStart/permEnd）位置关系。
用于实现袁总要求：可编辑=白色，不可编辑=黄色，打印预览全灰。作者：袁燕"""
import collections
import glob
import io
import re
import sys
import zipfile

sys.path.insert(0, 'd:/5000/5000BManagePro')

SHD = re.compile(r'<w:shd[^>]*w:fill="([0-9A-Fa-f]{6})"')


def report(name, xml):
    fills = collections.Counter(SHD.findall(xml))
    i0 = xml.find('<w:permStart')
    i1 = xml.find('<w:permEnd')
    print(f'--- {name}')
    print('  底纹统计:', dict(fills))
    print(f'  permStart@{i0}  permEnd@{i1}')
    for m in list(SHD.finditer(xml))[:8]:
        pos, f = m.start(), m.group(1)
        zone = '可编辑区' if (i0 >= 0 and i1 > i0 and i0 < pos < i1) else '只读区'
        print(f'    shd {f} @ {pos} -> {zone}')
    print()


def main():
    print('===== 模板 =====')
    for p in glob.glob('templates/sdp/*.docx') + glob.glob('backend/templates/*.docx'):
        z = zipfile.ZipFile(p)
        report(p, z.read('word/document.xml').decode('utf-8'))

    print('===== 生成文档 =====')
    from backend.services import doc_service
    data = doc_service.generate_doc_bytes('R105', 'SDP', module=None)
    z = zipfile.ZipFile(io.BytesIO(data))
    report('R105_SDP (生成)', z.read('word/document.xml').decode('utf-8'))


if __name__ == '__main__':
    main()
