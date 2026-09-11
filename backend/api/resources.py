# -*- coding: utf-8 -*-
"""资源类业务 API（PP 开发环境/规模估算，按项目维度）。
作者：袁燕
功能：暴露 hw_res / sw_res / doc_scale / code_scale / schedule 的 CRUD，
     供前端项目策划页编辑；这些数据最终随 SDP 生成并受控于 SVN。
设计：路由仅做校验与转换（P10），业务聚合交由 data_service / DAO（P18 不含 SQL）。
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from backend.db.session import get_db
from backend.schemas import ApiResp
from backend.db.models import HwRes, SwRes, DocScale, CodeScale, SchedulePhase
from backend.dao import hw_res_dao, sw_res_dao, doc_scale_dao, code_scale_dao, schedule_dao
from backend.dao import est_item_dao, schedule_task_dao, project_member_dao
from backend.db.session import ensure_tables  # 幂等兜底：防表缺失时接口 500

router = APIRouter(prefix="/api/pp", tags=["pp-resources"])

# ---------- 相关方（按项目维度，对应 {{table.stakeholders}}/{{table.stakeholder_plan}}）----------
from backend.dao import stakeholder_dao
from backend.db.models import Stakeholder


class StakeholderIn(BaseModel):
    role: str
    name: str
    responsibility: Optional[str] = None
    join_phase: Optional[str] = None


@router.get("/{project_id}/stakeholders")
def list_stk(project_id: str, db=Depends(get_db)):
    ensure_tables(Stakeholder)
    return ApiResp(data=[{"id": r.id, "role": r.role, "name": r.name,
             "responsibility": r.responsibility, "join_phase": r.join_phase}
            for r in stakeholder_dao.StakeholderDao.list_by_project(db, project_id)])


@router.post("/{project_id}/stakeholders")
def create_stk(project_id: str, body: StakeholderIn, db=Depends(get_db)):
    obj = Stakeholder(project_id=project_id, **body.dict())
    return stakeholder_dao.StakeholderDao.create(db, obj).id


@router.put("/{project_id}/stakeholders/{rid}")
def update_stk(project_id: str, rid: int, body: StakeholderIn, db=Depends(get_db)):
    stakeholder_dao.StakeholderDao.update_fields(db, rid, body.dict())
    return {"ok": True}


@router.delete("/{project_id}/stakeholders/{rid}")
def delete_stk(project_id: str, rid: int, db=Depends(get_db)):
    stakeholder_dao.StakeholderDao.delete(db, rid)
    return {"ok": True}


# ---------- 利益相关方参与计划（对标 R121 附录B：阶段×活动×角色打勾矩阵）----------
from backend.dao import stakeholder_plan_dao
from backend.db.models import StakeholderPlan

ROLE_FIELDS = ["customer_rep", "proj_mgr", "dept_lead", "proj_lead", "sys_eng", "epg", "qag", "cmg", "otg"]


class StakeholderPlanIn(BaseModel):
    """对标 R121 附录B：9 个角色列（项目方确认，已删除软件负责人/需求/设计/实现/测试/
    测量分析/SCM/质量保证 8 列）。标记仅 √=计划参与，空=不参与（无 ○）。"""
    seq: Optional[int] = None
    phase: Optional[str] = None
    activity: Optional[str] = None
    customer_rep: Optional[str] = None   # 顾客代表
    pm: Optional[str] = None             # 项目经理
    dept_lead: Optional[str] = None      # 部门领导
    proj_lead: Optional[str] = None      # 项目负责人
    sys_eng: Optional[str] = None        # 系统工程组
    epg: Optional[str] = None            # EPG
    qag: Optional[str] = None            # QAG
    cmg: Optional[str] = None            # CMG
    otg: Optional[str] = None            # OTG


@router.get("/{project_id}/stakeholder_plan")
def list_plan(project_id: str, db=Depends(get_db)):
    ensure_tables(StakeholderPlan)
    rows = stakeholder_plan_dao.StakeholderPlanDao.list_by_project(db, project_id)
    data = [{
        "id": r.id, "seq": r.seq, "phase": r.phase, "activity": r.activity,
        "customer_rep": r.customer_rep, "pm": r.pm, "dept_lead": r.dept_lead,
        "proj_lead": r.proj_lead, "sys_eng": r.sys_eng,
        "epg": r.epg, "qag": r.qag, "cmg": r.cmg, "otg": r.otg,
    } for r in rows]
    return ApiResp(data=data)


@router.put("/{project_id}/stakeholder_plan/{rid}")
def update_plan(project_id: str, rid: int, body: StakeholderPlanIn, db=Depends(get_db)):
    payload = {k: v for k, v in body.dict().items() if v is not None}
    stakeholder_plan_dao.StakeholderPlanDao.update_fields(db, rid, payload)
    return {"ok": True}


# ---------- 请求体 ----------
class HwResIn(BaseModel):
    name: str
    spec: Optional[str] = None
    usage: Optional[str] = None
    owner: Optional[str] = None


class SwResIn(BaseModel):
    name: str
    spec: Optional[str] = None
    usage: Optional[str] = None
    owner: Optional[str] = None


class DocScaleIn(BaseModel):
    code: str
    name: str
    pages_new: int = 0
    pages_reuse: int = 0


class CodeScaleIn(BaseModel):
    comp: str
    est_loc: int = 0
    reuse_loc: int = 0


class SchedulePhaseIn(BaseModel):
    phase_no: int
    phase_name: str
    ratio: Optional[str] = None
    eng_md: Optional[float] = None
    mgr_md: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    milestone: Optional[str] = None


def _proj(db, pid):
    return pid


# ---------- HW 资源 ----------
@router.get("/{project_id}/hw-res")
def list_hw(project_id: str, db=Depends(get_db)):
    ensure_tables(HwRes)
    return ApiResp(data=[{"id": r.id, "name": r.name, "spec": r.spec, "usage": r.usage, "owner": r.owner}
            for r in hw_res_dao.HwResDao.list_by_project(db, project_id)])


@router.post("/{project_id}/hw-res")
def create_hw(project_id: str, body: HwResIn, db=Depends(get_db)):
    obj = HwRes(project_id=project_id, **body.dict())
    return hw_res_dao.HwResDao.create(db, obj).id


@router.put("/{project_id}/hw-res/{rid}")
def update_hw(project_id: str, rid: int, body: HwResIn, db=Depends(get_db)):
    hw_res_dao.HwResDao.update_fields(db, rid, body.dict())
    return {"ok": True}


@router.delete("/{project_id}/hw-res/{rid}")
def delete_hw(project_id: str, rid: int, db=Depends(get_db)):
    hw_res_dao.HwResDao.delete(db, rid)
    return {"ok": True}


# ---------- SW 资源 ----------
@router.get("/{project_id}/sw-res")
def list_sw(project_id: str, db=Depends(get_db)):
    ensure_tables(SwRes)
    return ApiResp(data=[{"id": r.id, "name": r.name, "spec": r.spec, "usage": r.usage, "owner": r.owner}
            for r in sw_res_dao.SwResDao.list_by_project(db, project_id)])


@router.post("/{project_id}/sw-res")
def create_sw(project_id: str, body: SwResIn, db=Depends(get_db)):
    obj = SwRes(project_id=project_id, **body.dict())
    return sw_res_dao.SwResDao.create(db, obj).id


@router.put("/{project_id}/sw-res/{rid}")
def update_sw(project_id: str, rid: int, body: SwResIn, db=Depends(get_db)):
    sw_res_dao.SwResDao.update_fields(db, rid, body.dict())
    return {"ok": True}


@router.delete("/{project_id}/sw-res/{rid}")
def delete_sw(project_id: str, rid: int, db=Depends(get_db)):
    sw_res_dao.SwResDao.delete(db, rid)
    return {"ok": True}


# ---------- 文档规模 ----------
@router.get("/{project_id}/doc-scale")
def list_ds(project_id: str, db=Depends(get_db)):
    ensure_tables(DocScale)
    return ApiResp(data=[{"id": r.id, "code": r.code, "name": r.name,
             "pages_new": r.pages_new, "pages_reuse": r.pages_reuse}
            for r in doc_scale_dao.DocScaleDao.list_by_project(db, project_id)])


@router.post("/{project_id}/doc-scale")
def create_ds(project_id: str, body: DocScaleIn, db=Depends(get_db)):
    obj = DocScale(project_id=project_id, **body.dict())
    return doc_scale_dao.DocScaleDao.create(db, obj).id


@router.put("/{project_id}/doc-scale/{rid}")
def update_ds(project_id: str, rid: int, body: DocScaleIn, db=Depends(get_db)):
    doc_scale_dao.DocScaleDao.update_fields(db, rid, body.dict())
    return {"ok": True}


@router.delete("/{project_id}/doc-scale/{rid}")
def delete_ds(project_id: str, rid: int, db=Depends(get_db)):
    doc_scale_dao.DocScaleDao.delete(db, rid)
    return {"ok": True}


# ---------- 代码规模 ----------
@router.get("/{project_id}/code-scale")
def list_cs(project_id: str, db=Depends(get_db)):
    ensure_tables(CodeScale)
    return ApiResp(data=[{"id": r.id, "comp": r.comp, "est_loc": r.est_loc, "reuse_loc": r.reuse_loc}
            for r in code_scale_dao.CodeScaleDao.list_by_project(db, project_id)])


@router.post("/{project_id}/code-scale")
def create_cs(project_id: str, body: CodeScaleIn, db=Depends(get_db)):
    obj = CodeScale(project_id=project_id, **body.dict())
    return code_scale_dao.CodeScaleDao.create(db, obj).id


@router.put("/{project_id}/code-scale/{rid}")
def update_cs(project_id: str, rid: int, body: CodeScaleIn, db=Depends(get_db)):
    code_scale_dao.CodeScaleDao.update_fields(db, rid, body.dict())
    return {"ok": True}


@router.delete("/{project_id}/code-scale/{rid}")
def delete_cs(project_id: str, rid: int, db=Depends(get_db)):
    code_scale_dao.CodeScaleDao.delete(db, rid)
    return {"ok": True}


# ---------- 进度阶段 ----------
@router.get("/{project_id}/schedule")
def list_sched(project_id: str, db=Depends(get_db)):
    ensure_tables(SchedulePhase)
    return ApiResp(data=[{"id": r.id, "phase_no": r.phase_no, "phase_name": r.phase_name, "ratio": r.ratio,
             "eng_md": r.eng_md, "mgr_md": r.mgr_md, "start_date": r.start_date,
             "end_date": r.end_date, "milestone": r.milestone}
            for r in schedule_dao.ScheduleDao.list_by_project(db, project_id)])


@router.post("/{project_id}/schedule")
def create_sched(project_id: str, body: SchedulePhaseIn, db=Depends(get_db)):
    obj = SchedulePhase(project_id=project_id, **body.dict())
    return schedule_dao.ScheduleDao.create(db, obj).id


@router.put("/{project_id}/schedule/{rid}")
def update_sched(project_id: str, rid: int, body: SchedulePhaseIn, db=Depends(get_db)):
    schedule_dao.ScheduleDao.update_fields(db, rid, body.dict())
    return {"ok": True}


@router.delete("/{project_id}/schedule/{rid}")
def delete_sched(project_id: str, rid: int, db=Depends(get_db)):
    schedule_dao.ScheduleDao.delete(db, rid)
    return {"ok": True}


# ---------- 软件估算收敛项（Delphi 3 轮，按项目维度，前端可编辑）----------


class EstItemIn(BaseModel):
    round_no: Optional[int] = None
    cfg_item: Optional[str] = None
    wbs2: Optional[str] = None
    est1: Optional[str] = None
    est2: Optional[str] = None
    est3: Optional[str] = None
    deviation: Optional[str] = None
    avg_val: Optional[str] = None
    rel_dev: Optional[str] = None
    is_total: Optional[int] = None
    seq: Optional[int] = None


@router.get("/{project_id}/est-items")
def list_est(project_id: str, round_no: int = 1, db=Depends(get_db)):
    """估算收敛项列表，按轮次过滤（对标 R105-PP-GH-01/02）。"""
    ensure_tables(est_item_dao.EstItemDao.model)
    rows = est_item_dao.EstItemDao.list_by_round(db, project_id, round_no)
    return ApiResp(data=[{
        "id": r.id, "roundNo": r.round_no, "cfg_item": r.cfg_item, "wbs2": r.wbs2,
        "est1": r.est1, "est2": r.est2, "est3": r.est3,
        "deviation": r.deviation, "avg_val": r.avg_val, "rel_dev": r.rel_dev,
        "converge": r.converge, "isTotal": r.is_total, "seq": r.seq,
    } for r in rows])


@router.post("/{project_id}/est-items")
def create_est(project_id: str, body: EstItemIn, db=Depends(get_db)):
    payload = {k: v for k, v in body.dict().items() if v is not None}
    obj = est_item_dao.EstItemDao.create(db, est_item_dao.EstItemDao.model(project_id=project_id, **payload))
    return obj.id


@router.put("/{project_id}/est-items/{rid}")
def update_est(project_id: str, rid: int, body: EstItemIn, db=Depends(get_db)):
    payload = {k: v for k, v in body.dict().items() if v is not None}
    obj = est_item_dao.EstItemDao.get_in_project(db, rid, project_id)
    if not obj:
        raise HTTPException(status_code=404, detail="估算项不存在")
    est_item_dao.EstItemDao.update_fields(db, rid, payload)
    return {"ok": True}


@router.delete("/{project_id}/est-items/{rid}")
def delete_est(project_id: str, rid: int, db=Depends(get_db)):
    obj = est_item_dao.EstItemDao.get_in_project(db, rid, project_id)
    if obj:
        est_item_dao.EstItemDao.delete(db, rid)
    return {"ok": True}


# ---------- 进度任务项（R105 .mpp 导入，两维度：阶段 + 全部任务，为双周任务表储备）----------


class ScheduleTaskIn(BaseModel):
    phase_name: Optional[str] = None
    task_no: Optional[int] = None
    outline_level: Optional[int] = None
    is_summary: Optional[int] = None
    task_name: Optional[str] = None
    plan_start: Optional[str] = None
    plan_finish: Optional[str] = None
    duration_days: Optional[float] = None
    owner: Optional[str] = None
    percent: Optional[int] = None
    predecessor: Optional[str] = None
    milestone: Optional[str] = None
    seq: Optional[int] = None


@router.get("/{project_id}/schedule-tasks")
def list_schedule_tasks(project_id: str, db=Depends(get_db)):
    ensure_tables(schedule_task_dao.ScheduleTaskDao.model)
    rows = schedule_task_dao.ScheduleTaskDao.list_by_project(db, project_id)
    return ApiResp(data=[{
        "id": r.id, "phaseName": r.phase_name, "taskNo": r.task_no,
        "outlineLevel": r.outline_level, "isSummary": r.is_summary,
        "taskName": r.task_name, "planStart": r.plan_start,
        "planFinish": r.plan_finish, "durationDays": r.duration_days,
        "workHours": r.work_hours, "owner": r.owner, "percent": r.percent,
        "wbs": r.wbs, "outlineNumber": r.outline_number,
        "predecessor": r.predecessor, "milestone": r.milestone, "seq": r.seq,
    } for r in rows])


@router.post("/{project_id}/schedule-tasks")
def create_schedule_task(project_id: str, body: ScheduleTaskIn, db=Depends(get_db)):
    payload = {k: v for k, v in body.dict().items() if v is not None}
    obj = schedule_task_dao.ScheduleTaskDao.create(
        db, schedule_task_dao.ScheduleTaskDao.model(project_id=project_id, **payload))
    return obj.id


@router.put("/{project_id}/schedule-tasks/{rid}")
def update_schedule_task(project_id: str, rid: int, body: ScheduleTaskIn, db=Depends(get_db)):
    payload = {k: v for k, v in body.dict().items() if v is not None}
    obj = schedule_task_dao.ScheduleTaskDao.get_in_project(db, rid, project_id)
    if not obj:
        raise HTTPException(status_code=404, detail="任务不存在")
    schedule_task_dao.ScheduleTaskDao.update_fields(db, rid, payload)
    return {"ok": True}


@router.delete("/{project_id}/schedule-tasks/{rid}")
def delete_schedule_task(project_id: str, rid: int, db=Depends(get_db)):
    obj = schedule_task_dao.ScheduleTaskDao.get_in_project(db, rid, project_id)
    if obj:
        schedule_task_dao.ScheduleTaskDao.delete(db, rid)
    return {"ok": True}


# ---------- 项目人员（用户管理「项目人员」，文档签署角色基础，按项目维度）----------


class ProjectMemberIn(BaseModel):
    # 项目方铁律：字段命名全链路统一。前端 JS 用 camelCase，DB/后端用 snake_case，
    # 故多词字段统一加 camelCase 别名（populate_by_name 允许两种写法都接受），
    # 避免"前端传 skillReq、后端期望 skill_req"导致该字段被静默丢弃（2026-09-02 教训）。
    model_config = ConfigDict(populate_by_name=True)
    name: Optional[str] = None
    role: Optional[str] = None
    team: Optional[str] = None
    no: Optional[str] = None
    svn: Optional[str] = None
    auth: Optional[str] = None
    # 表23 人力资源表扩展列（项目方 2026-09-02，对标 R121 表30）
    skill_req: Optional[str] = Field(default=None, alias="skillReq")
    join_project: Optional[str] = Field(default=None, alias="joinProject")
    period: Optional[str] = None
    effort_pct: Optional[str] = Field(default=None, alias="effortPct")
    seq: Optional[int] = None


@router.get("/{project_id}/members")
def list_members(project_id: str, db=Depends(get_db)):
    ensure_tables(project_member_dao.ProjectMemberDao.model)
    rows = project_member_dao.ProjectMemberDao.list_by_project(db, project_id)
    return ApiResp(data=[{
        "id": r.id, "name": r.name, "role": r.role, "team": r.team,
        "no": r.no, "svn": r.svn, "auth": r.auth, "seq": r.seq,
        "skillReq": r.skill_req, "joinProject": r.join_project,
        "period": r.period, "effortPct": r.effort_pct,
    } for r in rows])


@router.post("/{project_id}/members")
def create_member(project_id: str, body: ProjectMemberIn, db=Depends(get_db)):
    payload = {k: v for k, v in body.dict().items() if v is not None}
    obj = project_member_dao.ProjectMemberDao.create(
        db, project_member_dao.ProjectMemberDao.model(project_id=project_id, **payload))
    return obj.id


@router.put("/{project_id}/members/{rid}")
def update_member(project_id: str, rid: int, body: ProjectMemberIn, db=Depends(get_db)):
    payload = {k: v for k, v in body.dict().items() if v is not None}
    obj = project_member_dao.ProjectMemberDao.get_in_project(db, rid, project_id)
    if not obj:
        raise HTTPException(status_code=404, detail="项目人员不存在")
    project_member_dao.ProjectMemberDao.update_fields(db, rid, payload)
    return {"ok": True}


@router.delete("/{project_id}/members/{rid}")
def delete_member(project_id: str, rid: int, db=Depends(get_db)):
    obj = project_member_dao.ProjectMemberDao.get_in_project(db, rid, project_id)
    if obj:
        project_member_dao.ProjectMemberDao.delete(db, rid)
    return {"ok": True}


# ---------- 组织机构表（表22，对标 R121 表29；文档生成角色/代表来源）----------
from backend.dao import org_chart_dao as _org_dao


class OrgChartIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    org_role: Optional[str] = Field(default=None, alias="orgRole")
    representative: Optional[str] = None
    duty: Optional[str] = None
    seq: Optional[int] = None


@router.get("/{project_id}/org-chart")
def list_org_chart(project_id: str, db=Depends(get_db)):
    ensure_tables(_org_dao.OrgChartDao.model)
    rows = _org_dao.OrgChartDao.list_by_project(db, project_id)
    return ApiResp(data=[{
        "id": r.id, "orgRole": r.org_role, "representative": r.representative,
        "duty": r.duty, "seq": r.seq,
    } for r in rows])


@router.post("/{project_id}/org-chart")
def create_org_chart(project_id: str, body: OrgChartIn, db=Depends(get_db)):
    ensure_tables(_org_dao.OrgChartDao.model)
    payload = {k: v for k, v in body.dict().items() if v is not None}
    if not payload.get("org_role"):
        raise HTTPException(status_code=400, detail="组织机构/角色必填")
    obj = _org_dao.OrgChartDao.create(db, _org_dao.OrgChartDao.model(project_id=project_id, **payload))
    return {"ok": True, "id": obj.id}


@router.put("/{project_id}/org-chart/{rid}")
def update_org_chart(project_id: str, rid: int, body: OrgChartIn, db=Depends(get_db)):
    payload = {k: v for k, v in body.dict().items() if v is not None}
    obj = _org_dao.OrgChartDao.get_in_project(db, rid, project_id)
    if not obj:
        raise HTTPException(status_code=404, detail="组织机构项不存在")
    _org_dao.OrgChartDao.update_fields(db, rid, payload)
    return {"ok": True}


@router.delete("/{project_id}/org-chart/{rid}")
def delete_org_chart(project_id: str, rid: int, db=Depends(get_db)):
    obj = _org_dao.OrgChartDao.get_in_project(db, rid, project_id)
    if obj:
        _org_dao.OrgChartDao.delete(db, rid)
    return {"ok": True}


# ---------- 配置项与基线（表13 基线列表 / 表19 配置项，CM）----------
from backend.dao import config_item_dao as _ci_dao


class ConfigItemIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    ci_id: Optional[str] = Field(default=None, alias="ciId")
    name: Optional[str] = None
    baseline: Optional[str] = None          # 功能基线/分配基线/产品基线
    baseline_name: Optional[str] = Field(default=None, alias="baselineName")     # R105 / R105_0201 / R105_0202
    baseline_id: Optional[str] = Field(default=None, alias="baselineId")         # R105_JG_V1.00 等
    status: Optional[str] = None
    path: Optional[str] = None


@router.get("/{project_id}/config-items")
def list_config_items(project_id: str, db=Depends(get_db)):
    ensure_tables(_ci_dao.ConfigItemDao.model)
    rows = _ci_dao.ConfigItemDao.list_by_project(db, project_id)
    return ApiResp(data=[{
        "id": r.id, "ciId": r.ci_id, "name": r.name, "baseline": r.baseline,
        "baselineName": r.baseline_name, "baselineId": r.baseline_id,
        "status": r.status, "path": r.path,
    } for r in rows])


@router.get("/{project_id}/baselines")
def list_baselines(project_id: str, db=Depends(get_db)):
    """基线聚合视图（多配置项用顿号连接），供前端预览与文档生成同源。"""
    ensure_tables(_ci_dao.ConfigItemDao.model)
    return ApiResp(data=_ci_dao.ConfigItemDao.list_baselines(db, project_id))


@router.post("/{project_id}/config-items")
def create_config_item(project_id: str, body: ConfigItemIn, db=Depends(get_db)):
    ensure_tables(_ci_dao.ConfigItemDao.model)
    payload = {k: v for k, v in body.dict().items() if v is not None}
    if not payload.get("ci_id"):
        raise HTTPException(status_code=400, detail="配置项标识必填")
    obj = _ci_dao.ConfigItemDao.create(db, _ci_dao.ConfigItemDao.model(project_id=project_id, **payload))
    return {"ok": True, "id": obj.id}


@router.put("/{project_id}/config-items/{rid}")
def update_config_item(project_id: str, rid: int, body: ConfigItemIn, db=Depends(get_db)):
    payload = {k: v for k, v in body.dict().items() if v is not None}
    obj = _ci_dao.ConfigItemDao.get_in_project(db, rid, project_id)
    if not obj:
        raise HTTPException(status_code=404, detail="配置项不存在")
    _ci_dao.ConfigItemDao.update_fields(db, rid, payload)
    return {"ok": True}


@router.delete("/{project_id}/config-items/{rid}")
def delete_config_item(project_id: str, rid: int, db=Depends(get_db)):
    obj = _ci_dao.ConfigItemDao.get_in_project(db, rid, project_id)
    if obj:
        _ci_dao.ConfigItemDao.delete(db, rid)
    return {"ok": True}
