# -*- coding: utf-8 -*-
"""
相关方路由（API 层）
作者：袁燕
功能：相关方增删查（PP A14）。不含 SQL（P18），无效参数 400（P10）。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.schemas import StakeholderCreate, StakeholderOut, ApiResp
from backend.services import data_service
from backend.db.models import Stakeholder

router = APIRouter(prefix="/api/stakeholders", tags=["stakeholders"])


@router.get("", response_model=ApiResp)
def list_stakeholders(db: Session = Depends(get_db)):
    rows = data_service.DataService.list_stakeholders(db)
    return ApiResp(data=[StakeholderOut.model_validate(r) for r in rows])


@router.post("", response_model=ApiResp)
def create_stakeholder(payload: StakeholderCreate, db: Session = Depends(get_db)):
    if not payload.role or not payload.name:
        raise HTTPException(status_code=400, detail="role 与 name 必填")
    obj = Stakeholder(
        role=payload.role, name=payload.name,
        responsibility=payload.responsibility, join_phase=payload.joinPhase,
    )
    data_service.DataService.create_stakeholder(db, obj)
    return ApiResp(data=StakeholderOut.model_validate(obj))


@router.delete("/{role}", response_model=ApiResp)
def delete_stakeholder(role: str, db: Session = Depends(get_db)):
    ok = data_service.DataService.delete_stakeholder(db, role)
    if not ok:
        raise HTTPException(status_code=404, detail="相关方不存在")
    return ApiResp(message="已删除")
