# -*- coding: utf-8 -*-
"""告警日志 DAO 作者：袁燕"""
from backend.db.base import BaseDao
from backend.db.models import AlertLog


class AlertDao(BaseDao):
    model = AlertLog
    pk_field = "id"

    @classmethod
    def get_all(cls, db, status=None, category=None):
        """按状态/类别筛选（告警页筛选用）。SQL 内聚本层。"""
        q = db.query(cls.model)
        if status:
            q = q.filter(cls.model.status == status)
        if category:
            q = q.filter(cls.model.category == category)
        return q.order_by(cls.model.created_at.desc()).all()
