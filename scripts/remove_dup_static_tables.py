# -*- coding: utf-8 -*-
"""删除模板中与动态表重复的静态残留表（数据管理表 3 张 + 相关方清单 1 张）。作者：袁燕

原因：这些静态表是写死的 R121 数据，在生成文档中与动态表重复出现，
      且列宽 14613 超出页面可用宽导致"表格显示不完整"；
      动态表（{{table.data_mgmt}} / {{table.stakeholders}}）已覆盖其内容。

实现：纯字符串处理（ElementTree 重写曾导致 w:shd 底纹丢失，故禁用）。
"""
import os
import re
import shutil
import zipfile

PATH = r'D:\5000\5000BManagePro\templates\sdp\SDP_占位符版.docx'
BAK = PATH + '.rmdup.bak'

TARGETS = [
    ('数据管理表（静态残留）', ['序号', '数据类别', '收集时机']),
    ('相关方清单 A14（静态残留）', ['组织机构/角色', '人员（代表）', '职责']),
]


def cell_texts(seg):
    return re.findall(r'<w:t(?:\s[^>]*)?>(.*?)</w:t>', seg, flags=re.S)


def find_tbl_span(doc, from_pos, kws):
    i = from_pos
    while True:
        s1 = doc.find('<w:tbl>', i)
        s2 = doc.find('<w:tbl ', i)
        cands = [x for x in (s1, s2) if x >= 0]
        if not cands:
            return None
        start = min(cands)
        depth, pos, end = 0, start, None
        while True:
            c2 = [x for x in (doc.find('<w:tbl>', pos), doc.find('<w:tbl ', pos)) if x >= 0]
            nxt_open = min(c2) if c2 else -1
            nxt_close = doc.find('</w:tbl>', pos)
            if nxt_close < 0:
                return None
            if 0 <= nxt_open < nxt_close:
                depth += 1
                pos = nxt_open + 7
            else:
                depth -= 1
                pos = nxt_close + 8
                if depth == 0:
                    end = pos
                    break
        texts = ''.join(cell_texts(doc[start:end]))
        if all(k in texts for k in kws):
            return (start, end)
        i = end


def main():
    if not os.path.exists(BAK):
        shutil.copy(PATH, BAK)
        print('已备份:', BAK)

    z = zipfile.ZipFile(PATH)
    names = z.namelist()
    data = {n: z.read(n) for n in names}
    z.close()

    doc = data['word/document.xml'].decode('utf-8')
    for label, kws in TARGETS:
        cnt, pos = 0, 0
        while True:
            span = find_tbl_span(doc, pos, kws)
            if not span:
                break
            a, b = span
            doc = doc[:a] + doc[b:]
            cnt += 1
            pos = a
        print(f'  [{label}] 删除 {cnt} 张')

    data['word/document.xml'] = doc.encode('utf-8')
    with zipfile.ZipFile(PATH, 'w', zipfile.ZIP_DEFLATED) as zo:
        for n in names:
            zo.writestr(n, data[n])

    z = zipfile.ZipFile(PATH)
    xml = z.read('word/document.xml').decode('utf-8')
    print('  shd 数:', len(re.findall(r'<w:shd', xml)))
    print('  文档长度:', len(xml))


if __name__ == '__main__':
    main()
