# -*- coding: utf-8 -*-
"""
用户 DAO（系统 RBAC + 登录校验）
作者：袁燕
功能：用户 CRUD + 按账号查询（登录用）。
     密码仅存 bcrypt hash，原始密码绝不落盘。
"""
from typing import Optional
from sqlalchemy.orm import Session
from backend.db.base import BaseDao
from backend.db.models import User


class UserDao(BaseDao):
    model = User
    pk_field = "user_id"

    @classmethod
    def get_by_account(cls, db: Session, account: str) -> Optional[User]:
        """按登录账号查询用户（登录校验专用）。返回 User 或 None。"""
        return db.query(User).filter(User.account == account).first()
