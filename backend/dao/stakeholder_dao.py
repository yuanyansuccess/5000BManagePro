# -*- coding: utf-8 -*-
"""相关方 DAO（PP A14）作者：袁燕
按 project_id 维度隔离（项目方铁律）。不含 SQL（P18）。
"""
from backend.db.base import BaseDao
from backend.db.models import Stakeholder


class StakeholderDao(BaseDao):
    model = Stakeholder
    pk_field = "id"

    @staticmethod
    def list_by_project(db, project_id: str):
        return db.query(Stakeholder).filter(
            Stakeholder.project_id == project_id
        ).order_by(Stakeholder.id).all()

    @staticmethod
    def delete_by_project(db, project_id: str):
        db.query(Stakeholder).filter(Stakeholder.project_id == project_id).delete()
        db.commit()
