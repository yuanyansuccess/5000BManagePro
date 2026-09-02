# -*- coding: utf-8 -*-
"""硬件资源 DAO（PP A.4.1 开发环境资源）作者：袁燕
按 project_id 维度隔离（项目方铁律）。不含 SQL（P18）。
"""
from backend.db.base import BaseDao
from backend.db.models import HwRes


class HwResDao(BaseDao):
    model = HwRes
    pk_field = "id"

    @staticmethod
    def list_by_project(db, project_id: str):
        return db.query(HwRes).filter(HwRes.project_id == project_id).order_by(HwRes.id).all()

    @staticmethod
    def delete_by_project(db, project_id: str):
        db.query(HwRes).filter(HwRes.project_id == project_id).delete()
        db.commit()
