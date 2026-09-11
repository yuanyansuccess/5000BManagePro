# -*- coding: utf-8 -*-
"""设置接口（API 层）。
作者：袁燕
功能：SVN 配置（仓库/文档路径映射/本机本地路径）的 CRUD，统一存库，设置页可配。
设计：路由仅做校验与转换（P10），数据操作全部走 settings_dao（P18 不含 SQL）。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.schemas import ApiResp
from backend.dao import settings_dao

router = APIRouter(prefix="/api/settings", tags=["settings"])


# ===== SVN 仓库配置 =====
@router.get("/svn-repos", response_model=ApiResp)
def list_svn_repos(db: Session = Depends(get_db)):
    rows = settings_dao.SvnRepoConfigDao.get_all(db)
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
    settings_dao.SvnRepoConfigDao.upsert(
        db, pid, body["repoUrl"],
        body.get("username", "admin"), body.get("password", "123456"),
        body.get("baseRelPath", "trunk/develop"))
    return ApiResp(message="已保存仓库配置 " + pid)


# ===== 文档路径映射（全局 GLOBAL：所有项目 SVN 相对路径几乎一致）=====
@router.get("/svn-doc-paths", response_model=ApiResp)
def list_svn_doc_paths(db: Session = Depends(get_db)):
    rows = settings_dao.SvnDocPathMapDao.get_all_global(db)
    return ApiResp(data=[{
        "projectId": r.project_id, "templateName": r.template_name,
        "relPath": r.rel_path,
    } for r in rows])


@router.post("/svn-doc-paths", response_model=ApiResp)
def upsert_svn_doc_path(body: dict, db: Session = Depends(get_db)):
    tpl = body.get("templateName")
    rel = body.get("relPath")
    if not tpl or not rel:
        raise HTTPException(status_code=400, detail="templateName/relPath 必填")
    settings_dao.SvnDocPathMapDao.upsert(db, tpl, rel)
    return ApiResp(message="已保存文档路径映射(全局) " + tpl)


# ===== 本机本地路径 =====
@router.get("/local-paths", response_model=ApiResp)
def list_local_paths(db: Session = Depends(get_db)):
    rows = settings_dao.LocalSvnPathDao.get_all(db)
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
        raise HTTPException(status_code=400, detail="machineId/userId/projectId/localPath 必填")
    settings_dao.LocalSvnPathDao.upsert(db, mid, uid, pid, lp)
    return ApiResp(message="已保存本地路径 " + pid)
