# -*- coding: utf-8 -*-
"""
需求路由（API 层）
作者：袁燕
功能：HTTP 路由 + 参数校验 + 调 Service + 返回 JSON。
      不含业务规则、不含 SQL（继承智能柜 P18：路由不直连 DAO）。
      无效参数返回明确错误，不降级到错误 Service（继承 P10 路由不降级铁律）。
设计原则：高内聚（路由与协议处理内聚）、低耦合（只依赖 services + schemas）。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.schemas import RequirementCreate, RequirementOut, ApiResp
from backend.services import data_service
from backend.db.models import Requirement

router = APIRouter(prefix="/api/requirements", tags=["requirements"])


@router.get("", response_model=ApiResp)
def list_requirements(db: Session = Depends(get_db)):
    rows = data_service.DataService.list_requirements(db)
    return ApiResp(data=[RequirementOut.model_validate(r) for r in rows])


@router.post("", response_model=ApiResp)
def create_requirement(payload: RequirementCreate, db: Session = Depends(get_db)):
    # 参数校验：reqId 必填，状态值对齐枚举
    if not payload.reqId or not payload.reqName:
        raise HTTPException(status_code=400, detail="reqId 与 reqName 必填")
    if payload.status not in ["草稿", "评审中", "已基线", "实施中", "已关闭"]:
        raise HTTPException(status_code=400, detail="status 取值非法")
    obj = Requirement(
        req_id=payload.reqId, req_type=payload.reqType, req_name=payload.reqName,
        status=payload.status, source=payload.source, baseline=payload.baseline,
    )
    data_service.DataService.create_requirement(db, obj)
    return ApiResp(data=RequirementOut.model_validate(obj))


@router.delete("/{req_id}", response_model=ApiResp)
def delete_requirement(req_id: str, db: Session = Depends(get_db)):
    ok = data_service.DataService.delete_requirement(db, req_id)
    if not ok:
        raise HTTPException(status_code=404, detail="需求不存在")
    return ApiResp(message="已删除")
