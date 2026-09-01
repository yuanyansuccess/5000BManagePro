# -*- coding: utf-8 -*-
"""
设置接口（API 层）。
作者：袁燕
功能：SVN 配置（仓库/文档路径映射/本机本地路径）的 CRUD，统一存库，设置页可配。
设计：不含 SQL（P18），逻辑走 Service；前后端 JSON 通讯用 ApiResp。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.schemas import ApiResp
from backend.db.models import SvnRepoConfig, SvnDocPathMap, LocalSvnPath

router = APIRouter(prefix="/api/settings", tags=["settings"])


# ===== SVN 仓库配置 =====
@router.get("/svn-repos", response_model=ApiResp)
def list_svn_repos(db: Session = Depends(get_db)):
    rows = db.query(SvnRepoConfig).all()
    return ApiResp(data=[{
        "projectId": r.project_id, "repoUrl": r.repo_url,
        "username": r.username, "password": r.password,
        "baseRelPath": r.base_rel_path,
    } for r in rows])


@router.post("/svn-repos", response_model=ApiResp)
def upsert_svn_repo(body: dict, db: Session = Depends(get_db)):
    pid = body.get("projectId")
    if not pid or not body.get("repoUrl"):
        raise HTTPException(status_code=400, detail="projectId/repoUrl 必填")
    obj = db.query(SvnRepoConfig).filter(SvnRepoConfig.project_id == pid).first()
    if not obj:
        obj = SvnRepoConfig(project_id=pid)
        db.add(obj)
    obj.repo_url = body["repoUrl"]
    obj.username = body.get("username", "admin")
    obj.password = body.get("password", "123456")
    obj.base_rel_path = body.get("baseRelPath", "trunk/develop")
    db.commit()
    return ApiResp(message="已保存仓库配置 " + pid)


# ===== 文档路径映射（不分项目，全局 GLOBAL：所有项目 SVN 相对路径几乎一致）=====
GLOBAL_PID = "GLOBAL"


@router.get("/svn-doc-paths", response_model=ApiResp)
def list_svn_doc_paths(db: Session = Depends(get_db)):
    rows = db.query(SvnDocPathMap).filter(SvnDocPathMap.project_id == GLOBAL_PID).all()
    return ApiResp(data=[{
        "projectId": r.project_id, "templateName": r.template_name,
        "relPath": r.rel_path,
    } for r in rows])


@router.post("/svn-doc-paths", response_model=ApiResp)
def upsert_svn_doc_path(body: dict, db: Session = Depends(get_db)):
    tpl = body.get("templateName")
    rel = body.get("relPath")
    if not tpl or not rel:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="templateName/relPath 必填")
    obj = db.query(SvnDocPathMap).filter(
        SvnDocPathMap.project_id == GLOBAL_PID, SvnDocPathMap.template_name == tpl).first()
    if not obj:
        obj = SvnDocPathMap(project_id=GLOBAL_PID, template_name=tpl)
        db.add(obj)
    obj.rel_path = rel
    db.commit()
    return ApiResp(message="已保存文档路径映射(全局) " + tpl)


# ===== 本机本地路径 =====
@router.get("/local-paths", response_model=ApiResp)
def list_local_paths(db: Session = Depends(get_db)):
    rows = db.query(LocalSvnPath).all()
    return ApiResp(data=[{
        "machineId": r.machine_id, "userId": r.user_id,
        "projectId": r.project_id, "localPath": r.local_path,
    } for r in rows])


@router.post("/local-paths", response_model=ApiResp)
def upsert_local_path(body: dict, db: Session = Depends(get_db)):
    mid = body.get("machineId")
    uid = body.get("userId")
    pid = body.get("projectId")
    lp = body.get("localPath")
    if not mid or not uid or not pid or not lp:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="machineId/userId/projectId/localPath 必填")
    obj = db.query(LocalSvnPath).filter(
        LocalSvnPath.machine_id == mid, LocalSvnPath.user_id == uid,
        LocalSvnPath.project_id == pid).first()
    if not obj:
        obj = LocalSvnPath(machine_id=mid, user_id=uid, project_id=pid)
        db.add(obj)
    obj.local_path = lp
    db.commit()
    return ApiResp(message="已保存本地路径 " + pid)
