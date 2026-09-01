# -*- coding: utf-8 -*-
"""
风险路由（API 层）
作者：袁燕
功能：风险增删查。字段对齐 R121（量化）。按当前项目读写（不硬编码代号）。
      不含 SQL（继承 P18），无效参数返回明确 400（P10）。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.schemas import RiskCreate, RiskOut, ApiResp
from backend.services import data_service
from backend.db.models import Risk, RISK_STATUS

router = APIRouter(prefix="/api/risks", tags=["risks"])

RISK_PROB_LEVELS = ["很低", "比较低", "中等", "比较高", "高"]
RISK_SOURCES = ["公司内部", "公司外部", "客户", "供应商", "其他"]
RISK_CATEGORIES = ["人员", "技术", "需求", "计划编制风险", "测试", "进度", "质量"]


@router.get("", response_model=ApiResp)
def list_risks(db: Session = Depends(get_db)):
    """列出当前项目的风险（R121 附录A 14 列对齐）。"""
    cur = data_service.DataService.get_current_project(db)
    rows = data_service.DataService.list_risks(db, project_id=cur.project_id)
    out = [RiskOut.model_validate(r).model_dump() for r in rows]
    return ApiResp(data=out)


@router.post("", response_model=ApiResp)
def create_risk(payload: RiskCreate, db: Session = Depends(get_db)):
    if not payload.riskId or not payload.description:
        raise HTTPException(status_code=400, detail="riskId 与 description 必填")
    if payload.status not in RISK_STATUS:
        raise HTTPException(status_code=400, detail="status 取值非法")
    if payload.probability and payload.probability not in RISK_PROB_LEVELS:
        raise HTTPException(status_code=400, detail="probability 取值非法")
    if payload.impactLevel and payload.impactLevel not in RISK_PROB_LEVELS:
        raise HTTPException(status_code=400, detail="impactLevel 取值非法")
    if payload.source and payload.source not in RISK_SOURCES:
        raise HTTPException(status_code=400, detail="source 取值非法")
    cur = data_service.DataService.get_current_project(db)
    obj = Risk(
        risk_id=payload.riskId, project_id=cur.project_id,
        identified_date=payload.identifiedDate, source=payload.source,
        category=payload.category, description=payload.description,
        probability=payload.probability, impact_level=payload.impactLevel,
        level=payload.level, priority=payload.priority,
        prevention=payload.prevention, owner=payload.owner,
        mitigation=payload.mitigation, status=payload.status,
        closed_date=payload.closedDate,
    )
    try:
        data_service.DataService.create_risk(db, obj)
    except Exception as e:
        # 回滚可能再次抛错，单独保护，避免掩盖原错误
        try:
            db.rollback()
        except Exception:
            pass
        # 主键冲突/字段超长等落到明确 400，避免裸 500 崩成 "Failed to fetch"
        err = str(e)
        if "Duplicate" in err or "PRIMARY" in err or "1062" in err:
            raise HTTPException(status_code=400, detail="风险编号已存在，请更换编号")
        raise HTTPException(status_code=400, detail="保存失败：" + err)
    return ApiResp(data=RiskOut.model_validate(obj).model_dump())


@router.put("/{risk_id}", response_model=ApiResp)
def update_risk(risk_id: str, payload: dict, db: Session = Depends(get_db)):
    """编辑风险（行内/弹窗修改）。只更新传入字段，驼峰键映射蛇形列。"""
    field_map = {
        "identifiedDate": "identified_date", "source": "source", "category": "category",
        "description": "description", "probability": "probability", "impactLevel": "impact_level",
        "riskCoef": "risk_coef", "level": "level", "priority": "priority",
        "prevention": "prevention", "owner": "owner", "mitigation": "mitigation",
        "status": "status", "closedDate": "closed_date",
    }
    mapped = {field_map[k]: v for k, v in payload.items() if k in field_map}
    if not mapped:
        raise HTTPException(status_code=400, detail="没有需要更新的字段")
    ok = data_service.DataService.update_risk(db, risk_id, mapped)
    if not ok:
        raise HTTPException(status_code=404, detail="风险不存在")
    return ApiResp(message="已更新")


@router.delete("/{risk_id}", response_model=ApiResp)
def delete_risk(risk_id: str, db: Session = Depends(get_db)):
    ok = data_service.DataService.delete_risk(db, risk_id)
    if not ok:
        raise HTTPException(status_code=404, detail="风险不存在")
    return ApiResp(message="已删除")
