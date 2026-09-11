# -*- coding: utf-8 -*-
"""代码整改 D 组：清理 temp 目录一次性调试/补丁脚本及临时产物。作者：袁燕
保留：final_template_backup/（模板兜底）、code_review_report.txt（审查报告）
"""
import os

TEMP = r'D:\5000\5000BManagePro\temp'
KEEP = {'final_template_backup', 'code_review_report.txt'}


def main():
    removed, kept = [], []
    for fn in sorted(os.listdir(TEMP)):
        p = os.path.join(TEMP, fn)
        if fn in KEEP:
            kept.append(fn)
            continue
        if os.path.isfile(p):
            os.remove(p)
            removed.append(fn)
        else:
            kept.append(fn + '/')
    print(f'已删除 {len(removed)} 个临时文件')
    print(f'保留 {len(kept)} 项: ' + ', '.join(kept))


if __name__ == '__main__':
    main()
