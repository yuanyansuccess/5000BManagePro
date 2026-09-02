# -*- coding: utf-8 -*-
"""
文档生成路由（API 层）。
作者：袁燕
功能：读锚点 / 写锚点 / 生成并下载文档。
设计：不含 SQL（P18），逻辑走 doc_service；前后端 JSON 通讯用 ApiResp。
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import io
import os

from backend.db.session import get_db
from backend.schemas import ApiResp
from backend.services import doc_service
from backend.services import svn_service

router = APIRouter(prefix="/api/doc", tags=["doc"])


@router.get("/{project_id}/{template_name}/anchors", response_model=ApiResp)
def get_anchors(project_id: str, template_name: str, db: Session = Depends(get_db)):
    """读取某项目某模板的全部锚点（标量 + 整表清单）。"""
    ph_map, table_map = doc_service.load_anchors(db, project_id, template_name)
    return ApiResp(data={
        "projectId": project_id,
        "templateName": template_name,
        "scalars": ph_map,
        "tables": list(table_map.keys()),
    })


@router.post("/{project_id}/{template_name}/anchors", response_model=ApiResp)
def post_anchors(project_id: str, template_name: str, body: dict,
                 db: Session = Depends(get_db)):
    """批量写入/更新锚点。body: {"scalars": {...}, "tables": {...}}。"""
    scalars = body.get("scalars", {})
    tables = body.get("tables", {})
    if not isinstance(scalars, dict) or not isinstance(tables, dict):
        raise HTTPException(status_code=400, detail="scalars/tables 必须为 dict")
    cnt = doc_service.upsert_anchors(db, project_id, template_name, scalars, tables)
    return ApiResp(message=f"已写入 {cnt} 条锚点")


@router.post("/{project_id}/{template_name}/generate")
def generate(project_id: str, template_name: str,
             doc_number: Optional[str] = None, doc_version: Optional[str] = None):
    """
    生成文档并返回 docx 下载流。
    doc_number/doc_version 可选：覆盖配置项标识（测试注入用）。
    """
    override = {}
    if doc_number:
        override["{{meta.doc_number}}"] = doc_number
    if doc_version:
        override["{{meta.doc_version}}"] = doc_version
    try:
        data = doc_service.generate_doc_bytes(project_id, template_name, override or None)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={project_id}_{template_name}.docx"},
    )


@router.post("/{project_id}/{template_name}/save-to-local")
def save_to_local(project_id: str, template_name: str,
                  body: dict = Body(...)):
    """
    生成文档并保存到用户指定的本机本地路径（方式1）。
    body: {"local_path": "D:/5000/R121", "filename": "可选.docx（可含子目录如 uploads/x.docx，会自动创建）"}
    """
    local_path = (body.get("local_path") or "").strip()
    if not local_path:
        raise HTTPException(status_code=400, detail="local_path 必填")
    if not os.path.isdir(local_path):
        raise HTTPException(status_code=400, detail="本地路径不存在: " + local_path)
    filename = body.get("filename") or f"{project_id}_{template_name}.docx"
    # 安全：禁止 filename 含盘符或 .. 等危险片段（仅允许相对子目录）
    safe_name = filename.replace("\\", "/")
    if ".." in safe_name.split("/") or (len(safe_name) >= 2 and safe_name[1] == ":"):
        raise HTTPException(status_code=400, detail="filename 非法，请使用纯文件名或 uploads/xxx.docx 形式")
    try:
        data = doc_service.generate_doc_bytes(project_id, template_name)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    full = os.path.join(local_path, safe_name)
    # 自动创建子目录（如 filename 含 uploads/xxx.docx → 创建 uploads/）
    parent = os.path.dirname(full)
    if parent and parent != local_path:
        try:
            os.makedirs(parent, exist_ok=True)
        except Exception as e:
            raise HTTPException(status_code=500, detail="创建子目录失败: " + str(e))
    try:
        with open(full, "wb") as f:
            f.write(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail="写盘失败: " + str(e))
    return ApiResp(data={"path": full, "size": len(data)},
                   message="已保存到 " + full)


@router.post("/{project_id}/{template_name}/commit-svn")
def commit_svn(project_id: str, template_name: str,
               doc_number: Optional[str] = None, doc_version: Optional[str] = None,
               module: Optional[str] = None,
               db: Session = Depends(get_db)):
    """
    生成文档并提交到 VisualSVN 仓库（方式2）。
    仓库 URL/账号 + 文档相对路径取自 svn_repo_config / svn_doc_path_map（设置页可配）。
    module: est/risk/stake —— 分类同步（只更新该类数据，其余章节用快照保持原样）。
    返回：revision（SVN 修订号）与受控库文档路径；失败抛 404/500。
    """
    from backend.db.models import SvnRepoConfig, SvnDocPathMap
    repo = db.query(SvnRepoConfig).filter(SvnRepoConfig.project_id == project_id).first()
    if not repo:
        raise HTTPException(status_code=400, detail="未配置项目 %s 的 SVN 仓库" % project_id)
    path_map = db.query(SvnDocPathMap).filter(
        SvnDocPathMap.project_id == "GLOBAL",
        SvnDocPathMap.template_name == template_name,
    ).first()
    if not path_map:
        raise HTTPException(status_code=400, detail="未配置全局 %s 的 SVN 文档路径" % template_name)

    override = {}
    if doc_number:
        override["{{meta.doc_number}}"] = doc_number
    if doc_version:
        override["{{meta.doc_version}}"] = doc_version
    try:
        data = doc_service.generate_doc_bytes(project_id, template_name,
                                              override or None, module=module)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    filename = f"{project_id}_{template_name}.docx"
    rev, info = svn_service.commit_docx(
        repo.repo_url, repo.username, repo.password,
        path_map.rel_path, filename, data,
        commit_msg=f"平台生成 {template_name} 文档（项目 {project_id}）",
    )
    if rev is None:
        raise HTTPException(status_code=500, detail=info)
    # 记录提交日志
    try:
        from backend.db.models import SvnCommitLog
        db.add(SvnCommitLog(repo_name=project_id, commit_user=repo.username,
                            revision=rev, changed_files=f"{path_map.rel_path}/{filename}",
                            project_name=project_id, raw_log=info))
        db.commit()
    except Exception:
        # 静默安全：SVN 提交本身已成功，告警日志记录失败仅影响审计完整性，
        # 不应让前端收到 500（提交结果以 revision 为准）。
        pass
    return ApiResp(data={"revision": rev, "url": info}, message="已提交 SVN，修订号 r%d" % rev)
