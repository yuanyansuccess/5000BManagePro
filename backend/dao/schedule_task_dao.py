# -*- coding: utf-8 -*-
"""进度任务项 DAO（R105 .mpp 导入，阶段+全部任务两维度）作者：袁燕
按 project_id 维度隔离（项目方铁律）。通用 CRUD/list_by_project 全在 BaseDao，此处仅声明模型与排序。
"""
from backend.db.base import BaseDao
from backend.db.models import ScheduleTask


class ScheduleTaskDao(BaseDao):
    model = ScheduleTask
    pk_field = "id"
    order_fields = (ScheduleTask.seq,)
