# -*- coding: utf-8 -*-
"""代码整改 A 组：删除未使用的 import（A1~A12，逐条核实）。作者：袁燕"""
import io
import os

BASE = r'D:\5000\5000BManagePro'


def patch(rel, old, new, desc, must=True):
    p = os.path.join(BASE, rel)
    src = io.open(p, encoding='utf-8').read()
    if old not in src:
        print(f'  [跳过] {desc}')
        return 0
    io.open(p, 'w', encoding='utf-8').write(src.replace(old, new, 1))
    print(f'  [OK] {desc}')
    return 1


n = 0
n += patch('backend/api/resources.py',
           'from typing import List, Optional', 'from typing import Optional',
           'A1 resources.py 删 List')
n += patch('backend/api/resources.py',
           'from backend.db.session import get_db, SessionLocal',
           'from backend.db.session import get_db', 'A2 resources.py 删 SessionLocal')
n += patch('backend/api/settings.py',
           'from typing import List, Optional', 'from typing import Optional',
           'A3 settings.py 删 List')
n += patch('backend/api/svn.py',
           'from fastapi import APIRouter, Depends, Header, HTTPException',
           'from fastapi import APIRouter, Depends, HTTPException', 'A4 svn.py 删 Header')
n += patch('backend/db/session.py',
           'from sqlalchemy.orm import sessionmaker, scoped_session',
           'from sqlalchemy.orm import sessionmaker', 'A7 session.py 删 scoped_session')
n += patch('backend/services/data_service.py',
           'from backend.dao import stakeholder_plan_dao\n', '', 'A9 data_service 删冗余dao')
n += patch('backend/services/doc_service.py', 'import io\n', '', 'A10 doc_service 删 io')
n += patch('backend/services/table_builder.py', 'from lxml import etree\n', '',
           'A11 table_builder 删 etree')
n += patch('backend/services/table_builder.py',
           'from backend.db.models import Risk, Project',
           'from backend.db.models import Project, Risk',
           'A12 table_builder import 排序规范化')
print(f'A 组完成: {n} 条')
