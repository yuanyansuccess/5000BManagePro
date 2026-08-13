# -*- coding: utf-8 -*-
"""
风险路由（API 层）
作者：袁燕
功能：风险增删查。不含 SQL（继承 P18），无效参数返回明确 400（P10）。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.schemas import RiskCreate, RiskOut, ApiResp
from backend.services import data_service
from backend.db.models import Risk, RISK_STATUS

router = APIRouter(prefix="/api/risks", tags=["risks"])


@router.get("", response_model=ApiResp)
def list_risks(db: Session = Depends(get_db)):
    rows = data_service.DataService.list_risks(db)
    return ApiResp(data=[RiskOut.model_validate(r) for r in rows])


@router.post("", response_model=ApiResp)
def create_risk(payload: RiskCreate, db: Session = Depends(get_db)):
    if not payload.riskId or not payload.description:
        raise HTTPException(status_code=400, detail="riskId 与 description 必填")
    if payload.status not in RISK_STATUS:
        raise HTTPException(status_code=400, detail="status 取值非法")
    obj = Risk(
        risk_id=payload.riskId, description=payload.description,
        level=payload.level, owner=payload.owner,
        status=payload.status, mitigation=payload.mitigation,
    )
    data_service.DataService.create_risk(db, obj)
    return ApiResp(data=RiskOut.model_validate(obj))


@router.delete("/{risk_id}", response_model=ApiResp)
def delete_risk(risk_id: str, db: Session = Depends(get_db)):
    ok = data_service.DataService.delete_risk(db, risk_id)
    if not ok:
        raise HTTPException(status_code=404, detail="风险不存在")
    return ApiResp(message="已删除")
