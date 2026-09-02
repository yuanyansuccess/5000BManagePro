# -*- coding: utf-8 -*-
"""代码规模估算 DAO（PP A.3.1 代码规模估计）作者：袁燕
按 project_id 维度隔离（项目方铁律）。不含 SQL（P18）。
"""
from backend.db.base import BaseDao
from backend.db.models import CodeScale


class CodeScaleDao(BaseDao):
    model = CodeScale
    pk_field = "id"

    @staticmethod
    def list_by_project(db, project_id: str):
        return db.query(CodeScale).filter(CodeScale.project_id == project_id).order_by(CodeScale.id).all()

    @staticmethod
    def delete_by_project(db, project_id: str):
        db.query(CodeScale).filter(CodeScale.project_id == project_id).delete()
        db.commit()
