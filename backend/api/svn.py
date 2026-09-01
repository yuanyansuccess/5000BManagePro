# -*- coding: utf-8 -*-
"""
SVN 集成接口（API 层）
作者：袁燕
功能：接收 SVN 钩子提交记录、客户端关注路径管理、更新指令下发与回报。
      不含 SQL（P18），逻辑走 Service。
设计：钩子只负责抓取+POST，匹配逻辑在服务端；客户端轮询拿待更新指令。
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from backend.db.session import get_db
from backend.schemas import (
    ApiResp, SvnCommitIn, SvnCommitOut,
    ClientWatchIn, ClientWatchOut, ClientUpdateQuery, ClientUpdateItem, ClientReportIn,
)
from backend import config
from backend.services import data_service

router = APIRouter(prefix="/api/svn", tags=["svn"])


def _check_secret(secret: Optional[str]):
    """钩子鉴权：secret 不匹配拒绝。"""
    if not config.SVN_HOOK_SECRET:
        return
    if secret != config.SVN_HOOK_SECRET:
        raise HTTPException(status_code=403, detail="secret 不匹配")


@router.post("/commit", response_model=ApiResp)
def svn_commit(payload: SvnCommitIn, db: Session = Depends(get_db)):
    """SVN 钩子调用：记录提交 + 标记受影响关注路径为 pending。"""
    _check_secret(payload.secret)
    obj = data_service.DataService.save_svn_commit(db, payload)
    affected = data_service.DataService.mark_affected_watches(db, obj)
    return ApiResp(
        data={"commitId": obj.id, "affectedWatches": affected},
        message="提交已记录，影响 %d 个客户端关注" % affected,
    )


@router.get("/commits", response_model=ApiResp)
def list_commits(repo: Optional[str] = None, db: Session = Depends(get_db)):
    """列出提交记录（前端查看）。"""
    rows = data_service.DataService.list_svn_commits(db, repo)
    return ApiResp(data=[SvnCommitOut.model_validate(r) for r in rows])


@router.post("/watch", response_model=ApiResp)
def add_watch(payload: ClientWatchIn, db: Session = Depends(get_db)):
    """用户配置关注路径。"""
    if not payload.machineId or not payload.watchPath:
        raise HTTPException(status_code=400, detail="machineId/watchPath 必填")
    obj = data_service.DataService.upsert_client_watch(db, payload)
    return ApiResp(data=ClientWatchOut.model_validate(obj), message="关注已保存")


@router.get("/watch", response_model=ApiResp)
def list_watch(machine: Optional[str] = None, db: Session = Depends(get_db)):
    """列出关注路径（前端/客户端查看）。"""
    rows = data_service.DataService.list_client_watches(db, machine)
    return ApiResp(data=[ClientWatchOut.model_validate(r) for r in rows])


@router.get("/client/updates", response_model=ApiResp)
def client_updates(machineId: str = Query(..., description="客户端机器标识"), db: Session = Depends(get_db)):
    """客户端轮询：返回本机待更新的关注路径及目标版本。"""
    if not config.SVN_CLIENT_WATCH_ENABLED:
        return ApiResp(data=[])
    items = data_service.DataService.get_pending_updates(db, machineId)
    return ApiResp(data=[ClientUpdateItem.model_validate(i) for i in items])


@router.post("/client/report", response_model=ApiResp)
def client_report(payload: ClientReportIn, db: Session = Depends(get_db)):
    """客户端回报更新结果。"""
    ok = data_service.DataService.report_client_update(db, payload)
    if not ok:
        raise HTTPException(status_code=404, detail="关注记录不存在")
    return ApiResp(message="已记录更新结果")
