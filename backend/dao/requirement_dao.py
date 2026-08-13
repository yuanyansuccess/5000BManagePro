# -*- coding: utf-8 -*-
"""需求 DAO（RDM）作者：袁燕"""
from backend.db.base import BaseDao
from backend.db.models import Requirement


class RequirementDao(BaseDao):
    model = Requirement
    pk_field = "req_id"  # 标识符主外键（OR/SR/DR/CT）
