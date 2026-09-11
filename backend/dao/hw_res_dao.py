# -*- coding: utf-8 -*-
"""硬件资源 DAO（PP A.4.1 开发环境资源）作者：袁燕
按 project_id 维度隔离（项目方铁律）。通用 CRUD/list_by_project 全在 BaseDao，此处仅声明模型与排序。
"""
from backend.db.base import BaseDao
from backend.db.models import HwRes


class HwResDao(BaseDao):
    model = HwRes
    pk_field = "id"
    order_fields = (HwRes.id,)
