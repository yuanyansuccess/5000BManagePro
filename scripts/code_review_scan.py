# -*- coding: utf-8 -*-
"""代码审查扫描器：backend / frontend 静态检查，输出问题清单。作者：袁燕
维度：P1 未使用import P2 空except P3 print残留 P4 旧端口硬编码
      P7 console.log P8 过长函数 P9 temp临时脚本
输出：temp/code_review_report.txt
"""
import io
import os
import re

BASE = r'D:\5000\5000BManagePro'
issues = []


def iter_files(ext, base_rel):
    d = os.path.join(BASE, base_rel)
    for root, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x not in ('__pycache__', 'node_modules')]
        for f in files:
            if f.endswith(ext):
                yield os.path.join(root, f)


def check_py(path):
    rel = os.path.relpath(path, BASE)
    src = io.open(path, encoding='utf-8', errors='ignore').read()
    lines = src.split('\n')
    for i, line in enumerate(lines, 1):
        m = re.match(r'^(?:from\s+[\w.]+\s+import\s+|import\s+)(.+)$', line.strip())
        if m and '#' not in line:
            for name in re.split(r'[,\s]+', m.group(1)):
                name = name.strip().split(' as ')[-1].split('.')[0]
                if name and len(re.findall(r'\b' + re.escape(name) + r'\b', src)) <= 1:
                    issues.append(('P1', rel, i, '未使用 import: ' + name))
        if re.match(r'\s*except\s+Exception:\s*$', line):
            nxt = lines[i] if i < len(lines) else ''
            if re.match(r'\s*pass\s*$', nxt):
                issues.append(('P2', rel, i, '空 except Exception: pass'))
        if re.search(r'backend[/\\](api|services|dao)', rel) and re.match(r'\s*print\(', line):
            issues.append(('P3', rel, i, 'print 调试残留'))
        m2 = re.search(r'http://127\.0\.0\.1:(\d+)', line)
        if m2 and m2.group(1) not in ('8000', '5500'):
            issues.append(('P4', rel, i, '硬编码旧端口 ' + m2.group(1)))


def check_js(path):
    rel = os.path.relpath(path, BASE)
    src = io.open(path, encoding='utf-8', errors='ignore').read()
    lines = src.split('\n')
    for i, line in enumerate(lines, 1):
        if 'console.log' in line:
            issues.append(('P7', rel, i, 'console.log'))
    fns = [(m.start(), m.group(1)) for m in re.finditer(r'function\s+(\w+)\s*\(', src)]
    for idx, (start, name) in enumerate(fns):
        end = fns[idx + 1][0] if idx + 1 < len(fns) else len(src)
        n = src[start:end].count('\n')
        if n > 150:
            issues.append(('P8', rel, src[:start].count('\n') + 1,
                           '过长函数 ' + name + '（约' + str(n) + '行）'))


def main():
    for p in iter_files('.py', 'backend'):
        check_py(p)
    for p in iter_files('.js', 'frontend'):
        check_js(p)
    temp = os.path.join(BASE, 'temp')
    temp_scripts = [f for f in (os.listdir(temp) if os.path.isdir(temp) else [])
                    if f.endswith('.py')]

    buf = [f'代码审查报告  代码问题={len(issues)} 处  temp临时脚本={len(temp_scripts)} 个', '']
    by = {}
    for code, rel, ln, desc in issues:
        by.setdefault(code, []).append((rel, ln, desc))
    order = [('P1', '未使用 import'), ('P2', '空 except'), ('P3', 'print 调试残留'),
             ('P4', '旧端口硬编码'), ('P7', 'console.log'), ('P8', '过长函数')]
    for code, label in order:
        items = by.get(code, [])
        buf.append(f'[{code}] {label}: {len(items)} 处')
        for rel, ln, desc in items:
            buf.append(f'  {rel}:{ln}  {desc}')
        buf.append('')
    buf.append(f'[P9] temp 临时脚本: {len(temp_scripts)} 个（建议清理）')
    buf.extend('  ' + f for f in sorted(temp_scripts))
    io.open(os.path.join(temp, 'code_review_report.txt'), 'w', encoding='utf-8').write(
        '\n'.join(buf))
    print(f'代码问题: {len(issues)} 处  temp临时脚本: {len(temp_scripts)} 个')
    for code, label in order:
        print(f'  [{code}] {label}: {len(by.get(code, []))}')


if __name__ == '__main__':
    main()
