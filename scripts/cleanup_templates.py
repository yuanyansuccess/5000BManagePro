# -*- coding: utf-8 -*-
"""清理模板目录中多余的开发计划模板及历史备份，仅保留一份最终模板。作者：袁燕

保留：templates/sdp/SDP_占位符版.docx（唯一在用主模板，doc_service 引用）
删除：
  templates/sdp/R121_SDP_验证版.docx    旧验证产物，无任何代码引用
  templates/sdp/sdp__tbl_*.xml (10)     旧 doc_engine.fill() 专用表格片段；
                                        当前生成走 doc_service + table_builder
  templates/sdp/SDP_占位符版.docx.*.bak 历史备份
安全：删除前把最终模板另存一份到 temp/final_template_backup/ 兜底。
"""
import os
import shutil

BASE = r'D:\5000\5000BManagePro'
TPL_DIR = os.path.join(BASE, 'templates', 'sdp')
KEEP = 'SDP_占位符版.docx'
SAFE_DIR = os.path.join(BASE, 'temp', 'final_template_backup')


def main():
    os.makedirs(SAFE_DIR, exist_ok=True)
    final = os.path.join(TPL_DIR, KEEP)
    dst = os.path.join(SAFE_DIR, KEEP)
    if not os.path.exists(dst):
        shutil.copy(final, dst)
        print('最终模板已另存兜底:', dst)

    removed = []
    for fn in sorted(os.listdir(TPL_DIR)):
        p = os.path.join(TPL_DIR, fn)
        if not os.path.isfile(p):
            continue
        if fn == KEEP:
            continue
        if (fn == 'R121_SDP_验证版.docx'
                or (fn.startswith('sdp__tbl_') and fn.endswith('.xml'))
                or (fn.startswith(KEEP + '.') and fn.endswith('.bak'))):
            os.remove(p)
            removed.append(fn)
        else:
            print('  [保留]', fn)

    print(f'\n已删除 {len(removed)} 个文件：')
    for r in removed:
        print('   -', r)
    print('\n模板目录剩余：')
    for fn in sorted(os.listdir(TPL_DIR)):
        fp = os.path.join(TPL_DIR, fn)
        kind = '目录' if os.path.isdir(fp) else f'{os.path.getsize(fp)} 字节'
        print(f'   {fn}  ({kind})')


if __name__ == '__main__':
    main()
