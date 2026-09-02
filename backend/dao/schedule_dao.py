# -*- coding: utf-8 -*-
"""进度阶段 DAO（PP/PMC 进度计划表）作者：袁燕
按 project_id 维度隔离（项目方铁律）。不含 SQL（P18）。
"""
from backend.db.base import BaseDao
from backend.db.models import SchedulePhase


class ScheduleDao(BaseDao):
    model = SchedulePhase
    pk_field = "id"

    @staticmethod
    def list_by_project(db, project_id: str):
        return db.query(SchedulePhase).filter(
            SchedulePhase.project_id == project_id
        ).order_by(SchedulePhase.phase_no).all()

    @staticmethod
    def delete_by_project(db, project_id: str):
        db.query(SchedulePhase).filter(SchedulePhase.project_id == project_id).delete()
        db.commit()
