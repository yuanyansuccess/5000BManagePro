# -*- coding: utf-8 -*-
"""文档规模估算 DAO（PP A.3.1 文档规模估计）作者：袁燕
按 project_id 维度隔离（袁总铁律）。不含 SQL（P18）。
"""
from backend.db.base import BaseDao
from backend.db.models import DocScale


class DocScaleDao(BaseDao):
    model = DocScale
    pk_field = "id"

    @staticmethod
    def list_by_project(db, project_id: str):
        return db.query(DocScale).filter(DocScale.project_id == project_id).order_by(DocScale.id).all()

    @staticmethod
    def delete_by_project(db, project_id: str):
        db.query(DocScale).filter(DocScale.project_id == project_id).delete()
        db.commit()
