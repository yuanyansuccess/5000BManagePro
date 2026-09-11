# -*- coding: utf-8 -*-
"""组织机构 DAO（PP 7.2 项目组织）作者：袁燕
按 project_id 维度隔离（项目方铁律）。通用 CRUD/list_by_project 全在 BaseDao，此处仅声明模型与排序。
对标 R121 表29：组织机构/角色 | 人员（代表） | 职责。
"""
from backend.db.base import BaseDao
from backend.db.models import OrgChart


class OrgChartDao(BaseDao):
    model = OrgChart
    pk_field = "id"
    order_fields = (OrgChart.seq, OrgChart.id)
