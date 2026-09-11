# -*- coding: utf-8 -*-
"""利益相关方参与计划 DAO（R121 附录B 矩阵）。作者：袁燕
按 project_id 维度隔离（项目方铁律）。通用 CRUD/list_by_project 全在 BaseDao，此处仅声明模型与排序。
"""
from backend.db.base import BaseDao
from backend.db.models import StakeholderPlan


class StakeholderPlanDao(BaseDao):
    model = StakeholderPlan
    pk_field = "id"
    order_fields = (StakeholderPlan.seq,)
