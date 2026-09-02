# -*- coding: utf-8 -*-
"""利益相关方参与计划 DAO（R121 附录B 矩阵）。作者：袁燕
按 project_id 维度隔离（项目方铁律）。不含 SQL（P18）。
"""
from backend.db.base import BaseDao
from backend.db.models import StakeholderPlan


class StakeholderPlanDao(BaseDao):
    model = StakeholderPlan
    pk_field = "id"

    @staticmethod
    def list_by_project(db, project_id: str):
        return db.query(StakeholderPlan).filter(
            StakeholderPlan.project_id == project_id
        ).order_by(StakeholderPlan.seq).all()
