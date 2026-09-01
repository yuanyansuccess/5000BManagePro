# -*- coding: utf-8 -*-
"""调试：列出模板中所有文本含"测量分析"的单元格与其前后相邻单元格。作者：袁燕"""
import re
import zipfile

PATH = r'D:\5000\5000BManagePro\templates\sdp\SDP_占位符版.docx'


def cell_text(seg):
    return ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', seg, flags=re.S))


def main():
    z = zipfile.ZipFile(PATH)
    doc = z.read('word/document.xml').decode('utf-8')

    spans = []
    pos = 0
    while True:
        a1 = doc.find('<w:tc>', pos)
        a2 = doc.find('<w:tc ', pos)
        cands = [x for x in (a1, a2) if x >= 0]
        if not cands:
            break
        a = min(cands)
        b = doc.find('</w:tc>', a)
        spans.append((a, b + len('</w:tc>')))
        pos = spans[-1][1]

    print(f'单元格总数: {len(spans)}')
    for i, (a, b) in enumerate(spans):
        t = cell_text(doc[a:b]).strip()
        if '测量分析' in t:
            prev = cell_text(doc[spans[i - 1][0]:spans[i - 1][1]]).strip() if i >= 1 else '<无>'
            nxt = cell_text(doc[spans[i + 1][0]:spans[i + 1][1]]).strip() if i + 1 < len(spans) else '<无>'
            print(f'  [{i}] 本格={t!r}')
            print(f'       前一格={prev!r}  后一格={nxt!r}')


if __name__ == '__main__':
    main()
