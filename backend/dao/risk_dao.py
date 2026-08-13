# -*- coding: utf-8 -*-
"""风险 DAO（PP/PMC）作者：袁燕"""
from backend.db.base import BaseDao
from backend.db.models import Risk


class RiskDao(BaseDao):
    model = Risk
    pk_field = "risk_id"
