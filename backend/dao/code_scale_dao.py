# -*- coding: utf-8 -*-
"""代码规模估算 DAO（PP A.3.1 代码规模估计）作者：袁燕
按 project_id 维度隔离（项目方铁律）。通用 CRUD/list_by_project 全在 BaseDao，此处仅声明模型与排序。
"""
from backend.db.base import BaseDao
from backend.db.models import CodeScale


class CodeScaleDao(BaseDao):
    model = CodeScale
    pk_field = "id"
    order_fields = (CodeScale.id,)
