# -*- coding: utf-8 -*-
"""软件资源 DAO（PP A.4.1 开发环境资源）作者：袁燕
按 project_id 维度隔离（项目方铁律）。不含 SQL（P18）。
"""
from backend.db.base import BaseDao
from backend.db.models import SwRes


class SwResDao(BaseDao):
    model = SwRes
    pk_field = "id"

    @staticmethod
    def list_by_project(db, project_id: str):
        return db.query(SwRes).filter(SwRes.project_id == project_id).order_by(SwRes.id).all()

    @staticmethod
    def delete_by_project(db, project_id: str):
        db.query(SwRes).filter(SwRes.project_id == project_id).delete()
        db.commit()
