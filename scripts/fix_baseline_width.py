# -*- coding: utf-8 -*-
"""修正模板中"基线列表"表的列宽：9806 -> R121 原文 [763,2551,4204,1895]（合计 9413）。
作者：袁燕
说明：基线列表为模板静态表，当前列宽 9806 超出纵向页可用宽（约 9468），
      且与 R121 参考文档（9413）不一致；纯字符串方式替换其 tblGrid。
"""
import os
import re
import shutil
import zipfile

PATH = r'D:\5000\5000BManagePro\templates\sdp\SDP_占位符版.docx'
BAK = PATH + '.baseline.bak'
KW = ['基线名称', '基线标识', '基线包含的配置项', '基线发布时机']
NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NEW_GRID = ('<w:tblGrid xmlns:w="%s">'
            '<w:gridCol w:w="763"/><w:gridCol w:w="2551"/>'
            '<w:gridCol w:w="4204"/><w:gridCol w:w="1895"/></w:tblGrid>' % NS)


def find_tbl_span(doc, kws):
    pos = 0
    while True:
        s1 = doc.find('<w:tbl>', pos)
        s2 = doc.find('<w:tbl ', pos)
        cands = [x for x in (s1, s2) if x >= 0]
        if not cands:
            return None
        start = min(cands)
        depth, p, end = 0, start, None
        while True:
            c2 = [x for x in (doc.find('<w:tbl>', p), doc.find('<w:tbl ', p)) if x >= 0]
            nxt_open = min(c2) if c2 else -1
            nxt_close = doc.find('</w:tbl>', p)
            if nxt_close < 0:
                return None
            if 0 <= nxt_open < nxt_close:
                depth += 1
                p = nxt_open + 7
            else:
                depth -= 1
                p = nxt_close + 8
                if depth == 0:
                    end = p
                    break
        texts = ''.join(re.findall(r'<w:t(?:\s[^>]*)?>(.*?)</w:t>', doc[start:end], flags=re.S))
        if all(k in texts for k in kws):
            return (start, end)
        pos = end


def main():
    if not os.path.exists(BAK):
        shutil.copy(PATH, BAK)
        print('已备份:', BAK)

    z = zipfile.ZipFile(PATH)
    names = z.namelist()
    data = {n: z.read(n) for n in names}
    z.close()

    doc = data['word/document.xml'].decode('utf-8')
    span = find_tbl_span(doc, KW)
    if not span:
        print('  [--] 未找到基线列表表')
        return
    a, b = span
    seg = doc[a:b]
    old_grid = re.search(r'<w:tblGrid.*?</w:tblGrid>', seg, flags=re.S)
    print('  原列宽:', re.findall(r'w:w="(\d+)"', old_grid.group(0)) if old_grid else '无')
    new_seg = re.sub(r'<w:tblGrid.*?</w:tblGrid>', NEW_GRID, seg, count=1, flags=re.S)
    new_seg = re.sub(r'(<w:tblW w:w=")\d+(")', r'\g<1>9413\g<2>', new_seg, count=1)
    doc = doc[:a] + new_seg + doc[b:]

    data['word/document.xml'] = doc.encode('utf-8')
    with zipfile.ZipFile(PATH, 'w', zipfile.ZIP_DEFLATED) as zo:
        for n in names:
            zo.writestr(n, data[n])

    z = zipfile.ZipFile(PATH)
    xml = z.read('word/document.xml').decode('utf-8')
    print('  [OK] 基线列表列宽已改为 R121 [763,2551,4204,1895]（合计 9413）')
    print('  shd 数:', len(re.findall(r'<w:shd', xml)))


if __name__ == '__main__':
    main()
