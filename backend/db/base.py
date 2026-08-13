# -*- coding: utf-8 -*-
"""
DAO 基类（通用 CRUD 内聚，SQLAlchemy 版）
作者：袁燕
功能：提供通用的 get/get_all/create/update/delete，子类只需声明 model 类。
      SQL 全部内聚在此层，Service/API 不感知（继承智能柜 P18 分层铁律）。
设计原则：高内聚（SQL 只在此层）、低耦合（子类零 SQL 即得 CRUD）。
"""
from typing import Type, List, Optional, Any
from sqlalchemy.orm import Session


class BaseDao:
    model = None  # 子类声明具体 ORM 模型

    @classmethod
    def get_by_pk(cls, db: Session, pk_value: Any) -> Optional[object]:
        """按主键查询，主键名由子类 pk_field 指定（高内聚：主键映射内聚在 DAO）"""
        pk_field = getattr(cls, "pk_field", "id")
        return db.query(cls.model).filter(
            getattr(cls.model, pk_field) == pk_value
        ).first()

    @classmethod
    def get_all(cls, db: Session) -> List[object]:
        return db.query(cls.model).all()

    @classmethod
    def create(cls, db: Session, obj: object) -> object:
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @classmethod
    def update(cls, db: Session, obj: object) -> object:
        db.merge(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @classmethod
    def delete(cls, db: Session, pk_value: Any) -> bool:
        obj = cls.get_by_pk(db, pk_value)
        if not obj:
            return False
        db.delete(obj)
        db.commit()
        return True
