# -*- coding: utf-8 -*-
"""项目人员 DAO（PP 7.2.1 人力资源）作者：袁燕
按 project_id 维度隔离（项目方铁律）。通用 CRUD/list_by_project 全在 BaseDao，此处仅声明模型与排序。
人力资源表（{{table.human_resource}}）：按 seq 排序输出姓名+角色。
"""
from backend.db.base import BaseDao
from backend.db.models import ProjectMember


class ProjectMemberDao(BaseDao):
    model = ProjectMember
    pk_field = "id"
    order_fields = (ProjectMember.seq, ProjectMember.id)
