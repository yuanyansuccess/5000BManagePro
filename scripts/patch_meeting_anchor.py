# -*- coding: utf-8 -*-
"""把模板中写死的"会议计划"表替换为 {{table.meeting_plan}} 占位符段落。作者：袁燕

背景：会议计划表原本 7 行硬编码在模板里（日期 2025 年，与 R105 项目不符），
      袁总要求改为从数据库（meeting_plan 表）动态读取。

实现：纯字符串处理（此前 ElementTree 重写模板曾导致 w:shd 底纹丢失，故禁用）。
"""
import os
import re
import shutil
import zipfile

PATH = r'D:\5000\5000BManagePro\templates\sdp\SDP_占位符版.docx'
BAK = PATH + '.meeting.bak'

PH_PARA = ('<w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
           '<w:r><w:t>{{table.meeting_plan}}</w:t></w:r></w:p>')


def find_tbl_span(doc, anchor_text):
    i = doc.find(anchor_text)
    if i < 0:
        return None
    start = max(doc.rfind('<w:tbl>', 0, i), doc.rfind('<w:tbl ', 0, i))
    if start < 0:
        return None
    depth = 0
    pos = start
    while True:
        cands = [x for x in (doc.find('<w:tbl>', pos), doc.find('<w:tbl ', pos)) if x >= 0]
        nxt_open = min(cands) if cands else -1
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
                return (start, pos)


def main():
    if not os.path.exists(BAK):
        shutil.copy(PATH, BAK)
        print('已备份:', BAK)

    z = zipfile.ZipFile(PATH)
    names = z.namelist()
    data = {n: z.read(n) for n in names}
    z.close()

    doc = data['word/document.xml'].decode('utf-8')
    if '{{table.meeting_plan}}' in doc:
        print('  [--] 模板已含会议计划锚点，跳过')
        return

    span = find_tbl_span(doc, '会议类型')
    if not span:
        print('  [--] 未定位到会议计划表')
        return
    a, b = span
    old_len = b - a
    doc = doc[:a] + PH_PARA + doc[b:]
    data['word/document.xml'] = doc.encode('utf-8')

    with zipfile.ZipFile(PATH, 'w', zipfile.ZIP_DEFLATED) as zo:
        for n in names:
            zo.writestr(n, data[n])

    z = zipfile.ZipFile(PATH)
    xml = z.read('word/document.xml').decode('utf-8')
    print(f'  [OK] 会议计划表已替换为锚点（原表 {old_len} 字符）')
    print('  锚点数:', xml.count('{{table.meeting_plan}}'))
    print('  shd 数:', len(re.findall(r'<w:shd', xml)))
    print('  文档长度:', len(xml))


if __name__ == '__main__':
    main()
