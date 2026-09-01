# -*- coding: utf-8 -*-
"""模板：删除 doc_scale_est / code_scale_reuse 两个锚点段落（袁总：这两张表去掉）。作者：袁燕"""
import os
import re
import shutil
import zipfile

PATH = r'D:\5000\5000BManagePro\templates\sdp\SDP_占位符版.docx'
BAK = PATH + '.rmtbl.bak'


def para_span(doc, anchor):
    i = doc.find(anchor)
    if i < 0:
        return None
    a = max(doc.rfind('<w:p>', 0, i), doc.rfind('<w:p ', 0, i))
    b = doc.find('</w:p>', i)
    if a < 0 or b < 0:
        return None
    return (a, b + len('</w:p>'))


def main():
    if not os.path.exists(BAK):
        shutil.copy(PATH, BAK)
        print('backup:', BAK)

    z = zipfile.ZipFile(PATH)
    names = z.namelist()
    data = {n: z.read(n) for n in names}
    z.close()

    doc = data['word/document.xml'].decode('utf-8')
    for anchor in ['{{table.doc_scale_est}}', '{{table.code_scale_reuse}}']:
        span = para_span(doc, anchor)
        if not span:
            print('  [skip]', anchor)
            continue
        a, b = span
        doc = doc[:a] + doc[b:]
        print('  [OK] removed', anchor)

    data['word/document.xml'] = doc.encode('utf-8')
    with zipfile.ZipFile(PATH, 'w', zipfile.ZIP_DEFLATED) as zo:
        for n in names:
            zo.writestr(n, data[n])

    z = zipfile.ZipFile(PATH)
    xml = z.read('word/document.xml').decode('utf-8')
    print('  shd:', len(re.findall(r'<w:shd', xml)))
    for a in ['{{table.doc_scale_est}}', '{{table.code_scale_reuse}}']:
        print(f'  {a}: {xml.count(a)}')


if __name__ == '__main__':
    main()
