# -*- coding: utf-8 -*-
"""定位每个 {{table.*}} 锚点在模板中所属的节（纵向/横向），决定表格宽度上限。作者：袁燕
纵向节可用宽：节1=9468，节2/3=9590；横向节（附录）可用宽=14406。
"""
import re
import zipfile

TPL = 'templates/sdp/SDP_占位符版.docx'


def main():
    z = zipfile.ZipFile(TPL)
    xml = z.read('word/document.xml').decode('utf-8')

    sects = []
    for m in re.finditer(r'<w:sectPr[ >].*?</w:sectPr>', xml, flags=re.S):
        seg = m.group(0)
        pg = re.search(r'<w:pgSz[^>]*w:w="(\d+)"', seg)
        orient = 'landscape' in seg
        mar = re.search(r'<w:pgMar[^>]*w:left="(\d+)"[^>]*w:right="(\d+)"', seg)
        if not pg:
            continue
        pw = int(pg.group(1))
        avail = pw - int(mar.group(1)) - int(mar.group(2)) if mar else pw
        sects.append((m.start(), '横向' if orient else '纵向', avail))

    print('节信息（按 XML 出现顺序）：')
    for i, (pos, o, a) in enumerate(sects, 1):
        print(f'  节{i}: {o}  可用宽={a}  @{pos}')

    anchors = ['{{table.risks}}', '{{table.schedule}}', '{{table.stakeholders}}',
               '{{table.stakeholder_plan}}', '{{table.hw_env_res}}',
               '{{table.sw_env_res}}', '{{table.doc_scale_est}}',
               '{{table.doc_scale_reuse}}', '{{table.code_scale_est}}',
               '{{table.code_scale_reuse}}', '{{table.data_mgmt}}']
    print('\n锚点定位（所属节 = 该锚点之前最近的 sectPr 序号）：')
    for a in anchors:
        i = xml.find(a)
        if i < 0:
            print(f'  {a:32} 未找到')
            continue
        sec_idx = 0
        for k, (pos, o, avail) in enumerate(sects, 1):
            if pos < i:
                sec_idx = k
        o, avail = (sects[sec_idx - 1][1], sects[sec_idx - 1][2]) if sec_idx else ('?', '?')
        print(f'  {a:32} 节{sec_idx}({o}) 可用宽={avail}  @{i}')


if __name__ == '__main__':
    main()
