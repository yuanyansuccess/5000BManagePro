# -*- coding: utf-8 -*-
"""C5 修正：恢复 ppSyncAll 函数（被误删——onclick 字符串引用未被正则计入）。作者：袁燕"""
import io
import os
import re

BASE = r'D:\5000\5000BManagePro'
p = os.path.join(BASE, 'frontend/js/pages/pp.js')
src = io.open(p, encoding='utf-8').read()

if 'function ppSyncAll' not in src:
    fn = ('// 一键提交：整篇生成并提交 SVN（module 为空 = 全部数据用库最新值，'
          '并刷新各分类快照）\n'
          'function ppSyncAll() {\n'
          '  ppCommitSvn();   // 复用分类提交通道：不传 module 即整篇提交\n'
          '}\n\n')
    i = src.find('function ppCommitSvn')
    src = src[:i] + fn + src[i:]
    io.open(p, 'w', encoding='utf-8').write(src)
    print('  [OK] ppSyncAll 已恢复')
else:
    print('  [--] ppSyncAll 已存在')
