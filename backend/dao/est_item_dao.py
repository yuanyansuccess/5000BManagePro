# -*- coding: utf-8 -*-
"""软件估算收敛项 DAO（PP Delphi 估算，按项目维度+轮次）作者：袁燕
按 project_id 维度隔离（项目方铁律）。通用 CRUD 全在 BaseDao，此处仅声明模型与排序、轮次过滤。
"""
from backend.db.base import BaseDao
from backend.db.models import EstItem


class EstItemDao(BaseDao):
    model = EstItem
    pk_field = "id"
    order_fields = (EstItem.seq,)

    @staticmethod
    def list_by_round(db, project_id: str, round_no: int):
        """按项目+轮次查询估算收敛项（对标 R105-PP-GH-01/02）。"""
        return db.query(EstItem).filter(
            EstItem.project_id == project_id, EstItem.round_no == round_no
        ).order_by(EstItem.seq).all()
