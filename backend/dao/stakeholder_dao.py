# -*- coding: utf-8 -*-
"""相关方 DAO（PP A14）作者：袁燕"""
from backend.db.base import BaseDao
from backend.db.models import Stakeholder


class StakeholderDao(BaseDao):
    model = Stakeholder
    pk_field = "role"
