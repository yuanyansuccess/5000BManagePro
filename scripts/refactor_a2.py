# -*- coding: utf-8 -*-
"""代码整改 A 组补充：A3~A13（按实际行精确处理）。作者：袁燕"""
import io
import os

BASE = r'D:\5000\5000BManagePro'


def patch(rel, old, new, desc):
    p = os.path.join(BASE, rel)
    src = io.open(p, encoding='utf-8').read()
    if old not in src:
        print(f'  [跳过] {desc}')
        return 0
    io.open(p, 'w', encoding='utf-8').write(src.replace(old, new, 1))
    print(f'  [OK] {desc}')
    return 1


n = 0
n += patch('backend/api/settings.py', 'from typing import List\n', '',
           'A3 settings.py 删未使用 List')
n += patch('backend/api/svn.py',
           'from fastapi import APIRouter, Depends, HTTPException, Header, Query',
           'from fastapi import APIRouter, Depends, HTTPException, Query',
           'A4 svn.py 删未使用 Header')
n += patch('backend/api/svn.py', 'from typing import List, Optional',
           'from typing import Optional', 'A5 svn.py 删未使用 List')
n += patch('backend/db/base.py', 'from typing import Type, List, Optional, Any',
           'from typing import List, Optional, Any', 'A6 base.py 删未使用 Type')
n += patch('backend/doc_engine/doc_engine.py', 'import shutil\n', '',
           'A8 doc_engine 删未使用 shutil')
n += patch('backend/services/data_service.py',
           '        from backend.dao import stakeholder_plan_dao as _spd\n', '',
           'A9 data_service 删未使用局部 import')
n += patch('backend/api/settings.py',
           'from fastapi import APIRouter, Depends',
           'from fastapi import APIRouter, Depends, HTTPException',
           'A13 settings.py HTTPException 提升至顶部')
n += patch('backend/api/settings.py', '        from fastapi import HTTPException\n', '',
           'A13b settings.py 删函数内重复 import')
print(f'A 组补充完成: {n} 条')
