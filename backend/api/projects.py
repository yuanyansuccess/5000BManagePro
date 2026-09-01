# -*- coding: utf-8 -*-
"""
项目配置路由（API 层）
作者：袁燕
功能：项目增删查改 + 当前项目获取/切换。
     平台所有代号（文件名/风险表/路径/SVN）统一读 current_project，杜绝硬编码 R121。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.schemas import ApiResp
from backend.services import data_service
from backend.db.models import Project

router = APIRouter(prefix="/api/projects", tags=["projects"])


# 前端驼峰字段 -> 模型蛇形字段（项目配置）
_PROJ_FIELD_MAP = {
    "projectId": "project_id", "projectName": "project_name",
    "aircraftModel": "aircraft_model", "owner": "owner", "org": "org",
    "customerDept": "customer_dept", "phase": "phase", "startDate": "start_date",
    "approveDate": "approve_date", "ideVersion": "ide_version", "swVersion": "sw_version",
    "docNumber": "doc_number",
    "localPath": "local_path", "svnBasePath": "svn_base_path",
    "isCurrent": "is_current",
    # ===== SDP 签署角色（设置页可编辑，-> {{role.*}}）=====
    "ccb": "ccb", "designer": "designer", "reviewer": "reviewer",
    "reviewer2": "reviewer2", "reviewer3": "reviewer3", "tester": "tester",
    "qa": "qa", "configManager": "config_manager", "orgConfigManager": "org_config_manager",
    # ===== 开发环境（-> {{hw.*}}/{{sw.*}}）=====
    "hwIdeName": "hw_ide_name", "hwMcuModel": "hw_mcu_model",
    "swNameHost": "sw_name_host", "swNameIap": "sw_name_iap",
    # ===== 引用文档（-> {{ref.*}}）=====
    "refSdtdDocNumber": "ref_sdtd_doc_number", "refSqapDocNumber": "ref_sqap_doc_number",
    # ===== 项目组织角色（7.2.1 人力资源 / 相关方清单，前端录入=数据库=生成文档）=====
    "requirement": "requirement", "coder": "coder", "measure": "measure",
    "projLead": "proj_lead", "sysEng": "sys_eng",
}


def _proj_out(p: Project) -> dict:
    return {
        "projectId": p.project_id, "projectName": p.project_name,
        "aircraftModel": p.aircraft_model, "owner": p.owner, "org": p.org,
        "customerDept": p.customer_dept, "phase": p.phase, "startDate": p.start_date,
        "approveDate": p.approve_date, "ideVersion": p.ide_version, "swVersion": p.sw_version,
        "docNumber": p.doc_number,
        "localPath": p.local_path, "svnBasePath": p.svn_base_path,
        "isCurrent": p.is_current == 1,
        # SDP 签署角色 / 开发环境 / 引用文档（原样回传前端）
        "ccb": p.ccb, "designer": p.designer, "reviewer": p.reviewer,
        "reviewer2": p.reviewer2, "reviewer3": p.reviewer3, "tester": p.tester,
        "qa": p.qa, "configManager": p.config_manager, "orgConfigManager": p.org_config_manager,
        "hwIdeName": p.hw_ide_name, "hwMcuModel": p.hw_mcu_model,
        "swNameHost": p.sw_name_host, "swNameIap": p.sw_name_iap,
        "refSdtdDocNumber": p.ref_sdtd_doc_number, "refSqapDocNumber": p.ref_sqap_doc_number,
        # 项目组织角色（回传前端用于"修改项目"预填）
        "requirement": p.requirement, "coder": p.coder, "measure": p.measure,
        "projLead": p.proj_lead, "sysEng": p.sys_eng,
    }


@router.get("/current", response_model=ApiResp)
def get_current_project(db: Session = Depends(get_db)):
    proj = data_service.DataService.get_current_project(db)
    return ApiResp(data=_proj_out(proj))


@router.get("/{project_id}", response_model=ApiResp)
def get_project(project_id: str, db: Session = Depends(get_db)):
    rows = data_service.DataService.list_projects(db)
    proj = next((p for p in rows if p.project_id == project_id), None)
    if not proj:
        raise HTTPException(status_code=404, detail="项目不存在")
    return ApiResp(data=_proj_out(proj))


@router.get("", response_model=ApiResp)
def list_projects(db: Session = Depends(get_db)):
    rows = data_service.DataService.list_projects(db)
    return ApiResp(data=[_proj_out(r) for r in rows])


@router.post("", response_model=ApiResp)
def create_project(payload: dict, db: Session = Depends(get_db)):
    pid = (payload.get("projectId") or "").strip()
    if not pid:
        raise HTTPException(status_code=400, detail="projectId 必填")
    if any(p.project_id == pid for p in data_service.DataService.list_projects(db)):
        raise HTTPException(status_code=400, detail="项目代号已存在")
    set_cur = bool(payload.get("setCurrent", False))
    proj = Project(
        project_id=pid,
        project_name=payload.get("projectName", pid),
        aircraft_model=payload.get("aircraftModel"),
        owner=payload.get("owner"),
        org=payload.get("org"),
        customer_dept=payload.get("customerDept"),
        phase=payload.get("phase"),
        start_date=payload.get("startDate"),
        approve_date=payload.get("approveDate"),
        ide_version=payload.get("ideVersion"),
        sw_version=payload.get("swVersion"),
        doc_number=payload.get("docNumber"),
        local_path=payload.get("localPath") or ("D:/5000/" + pid),
        svn_base_path=payload.get("svnBasePath") or (pid + "/trunk"),
        is_current=1 if set_cur else 0,
        # SDP 签署角色 / 开发环境 / 引用文档（新建即可填）
        ccb=payload.get("ccb"), designer=payload.get("designer"),
        reviewer=payload.get("reviewer"), reviewer2=payload.get("reviewer2"),
        reviewer3=payload.get("reviewer3"), tester=payload.get("tester"),
        qa=payload.get("qa"), config_manager=payload.get("configManager"),
        org_config_manager=payload.get("orgConfigManager"),
        hw_ide_name=payload.get("hwIdeName"), hw_mcu_model=payload.get("hwMcuModel"),
        sw_name_host=payload.get("swNameHost"), sw_name_iap=payload.get("swNameIap"),
        ref_sdtd_doc_number=payload.get("refSdtdDocNumber"),
        ref_sqap_doc_number=payload.get("refSqapDocNumber"),
    )
    # 若设为当前，先清其他
    if set_cur:
        for p in db.query(Project).all():
            p.is_current = 0
    data_service.DataService.create_project(db, proj)
    return ApiResp(data={"projectId": proj.project_id}, message="已创建项目")


@router.put("/{project_id}", response_model=ApiResp)
def update_project(project_id: str, payload: dict, db: Session = Depends(get_db)):
    # 驼峰 -> 蛇形，再交给 data_service 逐字段更新
    mapped = {_PROJ_FIELD_MAP.get(k, k): v for k, v in payload.items() if k in _PROJ_FIELD_MAP}
    if "is_current" in mapped:  # 不允许通过 update 改当前标记（用 /current 接口）
        mapped.pop("is_current")
    ok = data_service.DataService.update_project(db, project_id, mapped)
    if not ok:
        raise HTTPException(status_code=404, detail="项目不存在")
    return ApiResp(message="已更新项目信息")


@router.post("/{project_id}/current", response_model=ApiResp)
def set_current(project_id: str, db: Session = Depends(get_db)):
    proj = data_service.DataService.set_current_project(db, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="项目不存在")
    return ApiResp(data={"projectId": proj.project_id}, message="已切换当前项目")
