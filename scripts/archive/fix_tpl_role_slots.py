# -*- coding: utf-8 -*-
"""修正 SDP 模板（SDP_占位符版.docx）中的角色占位符错位与硬编码人名。作者：袁燕

袁总反馈的问题与修正：
  1) 表22 人力资源投入表
     - 行2 姓名：{{role.requirement}}、李维   ->  {{role.requirement}}（删硬编码"李维"）
     - 行3 姓名：{{role.reviewer_2}}、{{role.reviewer_3}}  ->  {{role.coder}}
       （原把"评审副审"填到"软件实现"行，角色错位）
     - 行6 姓名：（空）                        ->  {{role.measure}}（测量分析人员）
  2) 表21 相关方组织机构
     - 行3 项目负责人：{{role.reviewer}}      ->  {{role.proj_lead}}
     - 行4 系统工程组：{{role.designer}}      ->  {{role.sys_eng}}
  3) 正文段落
     - 检视小组：{{role.author}}、{{role.requirement}}、李维。
       ->  检视小组：{{role.author}}、{{role.requirement}}。

安全：改前自动备份为 .rolefix.bak（仅首次）。
"""
import os
import re
import shutil
import zipfile

PATH = r'D:\5000\5000BManagePro\templates\sdp\SDP_占位符版.docx'
BAK = PATH + '.rolefix.bak'

# (旧串, 新串, 说明)
REPLACEMENTS = [
    ('{{role.reviewer_2}}、{{role.reviewer_3}}', '{{role.coder}}',
     '表22 软件实现行：评审副审 -> 软件实现人员'),
    ('{{role.requirement}}、李维', '{{role.requirement}}',
     '表22 软件需求分析行：去掉硬编码"李维"'),
    ('{{role.reviewer}}', '{{role.proj_lead}}',
     '表21 项目负责人行：reviewer -> 项目负责人'),
    ('{{role.designer}}', '{{role.sys_eng}}',
     '表21 系统工程组行：designer -> 系统工程组'),
    ('{{role.author}}、{{role.requirement}}、李维',
     '{{role.author}}、{{role.requirement}}',
     '正文检视小组：去掉硬编码"李维"'),
]

# 表22 行6（测量分析人员）为空单元格，需按上下文补占位符：
# 定位 '测量分析' 所在行前一格的姓名单元格，写入 {{role.measure}}
MEASURE_ANCHOR = '熟悉GJB5000B测量分析工作'


def patch_measure(doc: str) -> str:
    """表22 中'测量分析'行姓名为空 -> 填 {{role.measure}}。"""
    i = doc.find(MEASURE_ANCHOR)
    if i < 0:
        print('  [--] 未找到测量分析行锚点')
        return doc
    # 往前找该行第一个 <w:tc> ... </w:tc>（序号），第二个即姓名单元格
    seg = doc[:i]
    tcs = []
    pos = 0
    while True:
        a = seg.find('<w:tc>', pos)
        if a < 0:
            a = seg.find('<w:tc ', pos)
        if a < 0:
            break
        b = seg.find('</w:tc>', a)
        if b < 0:
            break
        tcs.append((a, b + len('</w:tc>')))
        pos = b + len('</w:tc>')
    if len(tcs) < 2:
        print('  [--] 测量分析行单元格不足')
        return doc
    # 取该行最后两个单元格：倒数第二个=姓名（在"测量分析"之前）
    name_a, name_b = tcs[-2]
    cell = seg[name_a:name_b]
    if '{{role.measure}}' in cell:
        print('  [--] 测量分析人员已填')
        return doc
    # 在单元格的段落 <w:p ...> 内插入文本 run
    p_open_end = cell.find('>', cell.find('<w:p'))
    if p_open_end < 0:
        print('  [--] 未找到段落标签')
        return doc
    run = ('<w:r><w:rPr><w:rFonts w:ascii="宋体" w:hAnsi="宋体"/>'
           '<w:sz w:val="21"/></w:rPr><w:t>{{role.measure}}</w:t></w:r>')
    new_cell = cell[:p_open_end + 1] + run + cell[p_open_end + 1:]
    doc = doc[:name_a] + new_cell + doc[name_b:]
    print('  [OK] 表22 测量分析行：填入 {{role.measure}}')
    return doc


def main():
    if not os.path.exists(BAK):
        shutil.copy(PATH, BAK)
        print('已备份:', BAK)

    z = zipfile.ZipFile(PATH)
    names = z.namelist()
    data = {n: z.read(n) for n in names}
    z.close()

    doc = data['word/document.xml'].decode('utf-8')
    for old, new, desc in REPLACEMENTS:
        cnt = doc.count(old)
        if cnt:
            doc = doc.replace(old, new)
            print(f'  [OK] {desc}（{cnt} 处）')
        else:
            print(f'  [--] 未命中：{desc}')
    doc = patch_measure(doc)
    data['word/document.xml'] = doc.encode('utf-8')

    with zipfile.ZipFile(PATH, 'w', zipfile.ZIP_DEFLATED) as zo:
        for n in names:
            zo.writestr(n, data[n])

    z = zipfile.ZipFile(PATH)
    doc2 = z.read('word/document.xml').decode('utf-8')
    txt = re.sub(r'<[^>]+>', '|', doc2)
    txt = re.sub(r'\|+', '|', txt)
    print()
    print('复核：模板中仍含"李维":', '李维' in txt)
    for ph in ['{{role.coder}}', '{{role.measure}}', '{{role.proj_lead}}',
               '{{role.sys_eng}}', '{{role.requirement}}']:
        print(f'  {ph}: {doc2.count(ph)} 处')


if __name__ == '__main__':
    main()
