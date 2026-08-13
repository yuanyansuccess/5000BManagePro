# -*- coding: utf-8 -*-
"""
告警路由（API 层）
作者：袁燕
功能：告警日志查询/新增/状态更新。不含 SQL（P18），无效参数 400（P10）。
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.schemas import AlertCreate, AlertOut, ApiResp
from backend.services import data_service
from backend.db.models import AlertLog, ALERT_STATUS, ALERT_LEVEL

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=ApiResp)
def list_alerts(
    status: str = Query(None), category: str = Query(None),
    db: Session = Depends(get_db),
):
    rows = data_service.DataService.list_alerts(db, status=status, category=category)
    return ApiResp(data=[AlertOut.model_validate(r) for r in rows])


@router.post("", response_model=ApiResp)
def create_alert(payload: AlertCreate, db: Session = Depends(get_db)):
    if not payload.title:
        raise HTTPException(status_code=400, detail="title 必填")
    if payload.level not in ALERT_LEVEL:
        raise HTTPException(status_code=400, detail="level 取值非法")
    if payload.status not in ALERT_STATUS:
        raise HTTPException(status_code=400, detail="status 取值非法")
    obj = AlertLog(
        level=payload.level, category=payload.category, title=payload.title,
        detail=payload.detail, source=payload.source, status=payload.status,
    )
    data_service.DataService.create_alert(db, obj)
    return ApiResp(data=AlertOut.model_validate(obj))


@router.patch("/{alert_id}/status", response_model=ApiResp)
def update_status(alert_id: int, body: dict, db: Session = Depends(get_db)):
    status = (body or {}).get("status")
    if status not in ALERT_STATUS:
        raise HTTPException(status_code=400, detail="status 取值非法")
    obj = data_service.DataService.update_alert_status(db, alert_id, status)
    if not obj:
        raise HTTPException(status_code=404, detail="告警不存在")
    return ApiResp(data=AlertOut.model_validate(obj))
