# -*- coding: utf-8 -*-
"""打印生成文档中 shd 标签的原文样本，定位着色未生效原因。作者：袁燕"""
import io
import re
import sys
import zipfile

sys.path.insert(0, 'd:/5000/5000BManagePro')


def main():
    from backend.services import doc_service
    data = doc_service.generate_doc_bytes('R105', 'SDP', module=None)
    z = zipfile.ZipFile(io.BytesIO(data))
    xml = z.read('word/document.xml').decode('utf-8')
    out = []
    ms = list(re.finditer(r'<w:shd[^>]*>', xml))
    out.append(f'shd 标签总数: {len(ms)}')
    for m in ms[:6]:
        out.append(f'  [{m.start()}] {m.group(0)}')
    ys = [m for m in ms if 'FFFF00' in m.group(0)]
    out.append(f'黄色 shd 数: {len(ys)}')
    for m in ys[:3]:
        out.append(f'  [{m.start()}] {m.group(0)}')
    ws = [m for m in ms if 'FFFFFF' in m.group(0)]
    out.append(f'白色 shd 数: {len(ws)}')
    for m in ws[:3]:
        s = max(0, m.start() - 150)
        out.append(f'  上下文: ...{xml[s:m.end()]}')
    io.open('temp/shd_samples.txt', 'w', encoding='utf-8').write('\n'.join(out))
    print('\n'.join(out))


if __name__ == '__main__':
    main()
