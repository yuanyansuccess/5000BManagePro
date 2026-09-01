# -*- coding: utf-8 -*-
"""表22「测量分析」行姓名单元格补 {{role.measure}}（纯字符串处理，不重建 XML）。
作者：袁燕
背景：此前用 ElementTree 重写模板导致 w:shd 底纹丢失、XML 膨胀，已回滚；
      本脚本只在目标单元格内插入一个 <w:r>，不触碰其余内容。
定位：先找角色列文本"测量分析"，再往前找紧邻的空 <w:tc>（姓名列），在其中插入 run。
"""
import os
import re
import shutil
import zipfile

PATH = r'D:\5000\5000BManagePro\templates\sdp\SDP_占位符版.docx'
BAK = PATH + '.measure2.bak'

RUN = ('<w:r><w:rPr><w:rFonts w:ascii="宋体" w:hAnsi="宋体"/>'
       '<w:sz w:val="21"/></w:rPr><w:t>{{role.measure}}</w:t></w:r>')


def cell_span(doc, start):
    b = doc.find('</w:tc>', start)
    return (start, b + len('</w:tc>')) if b > 0 else (start, start)


def cell_text(doc, a, b):
    seg = doc[a:b]
    # 注意：必须精确匹配 <w:t> 或 <w:t ...>；否则 <w:t[^>]*> 会误匹配 <w:tcPr>
    return ''.join(re.findall(r'<w:t(?:\s[^>]*)?>(.*?)</w:t>', seg, flags=re.S))


def main():
    if not os.path.exists(BAK):
        shutil.copy(PATH, BAK)
        print('已备份:', BAK)

    z = zipfile.ZipFile(PATH)
    names = z.namelist()
    data = {n: z.read(n) for n in names}
    z.close()

    doc = data['word/document.xml'].decode('utf-8')
    if '{{role.measure}}' in doc:
        print('  [--] 已存在 measure 占位符，跳过')
        return

    spans = []
    pos = 0
    while True:
        a1 = doc.find('<w:tc>', pos)
        a2 = doc.find('<w:tc ', pos)
        cands = [x for x in (a1, a2) if x >= 0]
        if not cands:
            break
        a = min(cands)
        spans.append(cell_span(doc, a))
        pos = spans[-1][1]

    # 精确定位人力资源表（7.2.1）的"测量分析"行：
    # 行结构 = 序号 | 姓名(空) | 角色"测量分析" | 要求"熟悉GJB5000B测量分析工作"
    # （数据管理表中也有"测量分析"，用后一格特征区分，避免误改）
    target = None
    for i, (a, b) in enumerate(spans):
        if cell_text(doc, a, b).strip() != '测量分析' or i + 1 >= len(spans) or i < 2:
            continue
        nx_a, nx_b = spans[i + 1]
        nxt = cell_text(doc, nx_a, nx_b)
        if '测量分析工作' not in nxt:
            continue
        na, nb = spans[i - 1]
        if not cell_text(doc, na, nb).strip():
            target = (na, nb)
            break
    if not target:
        print('  [--] 未定位到空的测量分析姓名单元格')
        return

    na, nb = target
    cell = doc[na:nb]
    m = re.search(r'<w:p(?:\s[^>]*)?>', cell)
    if not m:
        print('  [--] 单元格内无段落标签')
        return
    ins = m.end()
    new_cell = cell[:ins] + RUN + cell[ins:]
    doc = doc[:na] + new_cell + doc[nb:]
    data['word/document.xml'] = doc.encode('utf-8')

    with zipfile.ZipFile(PATH, 'w', zipfile.ZIP_DEFLATED) as zo:
        for n in names:
            zo.writestr(n, data[n])

    z = zipfile.ZipFile(PATH)
    xml = z.read('word/document.xml').decode('utf-8')
    print('  长度:', len(xml))
    print('  shd 数:', len(re.findall(r'<w:shd', xml)))
    print('  {{role.measure}}:', xml.count('{{role.measure}}'))
    print('  {{role.coder}}:', xml.count('{{role.coder}}'))
    print('  李维:', '李维' in xml)


if __name__ == '__main__':
    main()
