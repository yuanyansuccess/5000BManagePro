# -*- coding: utf-8 -*-
"""进度阶段 DAO（PP/PMC 进度计划表）作者：袁燕
按 project_id 维度隔离（项目方铁律）。通用 CRUD/list_by_project 全在 BaseDao，此处仅声明模型与排序。
"""
from backend.db.base import BaseDao
from backend.db.models import SchedulePhase


class ScheduleDao(BaseDao):
    model = SchedulePhase
    pk_field = "id"
    order_fields = (SchedulePhase.phase_no,)
