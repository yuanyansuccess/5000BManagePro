# -*- coding: utf-8 -*-
"""
文档生成服务（Service 层）。
作者：袁燕
功能：从 template_anchors 读取锚点数据，调用 doc_engine 灌装占位符模板，
      再经 doc_postprocess 后处理流水线，产出正式 docx 字节流。
      模板文件在 templates/ 目录（平台外，不提交 SVN）。
设计：高内聚（本模块只做编排与数据聚合）、低耦合（docx 细节全在
      doc_engine 灌装 + doc_postprocess 后处理 + table_builder 表格构建）。
"""
import os
import re

from sqlalchemy.orm import Session

from backend import config
from backend.db.models import TemplateAnchor, Project
from backend.doc_engine import SdpFiller
from backend.services.table_builder import build_risks_tbl, build_schedule_tbl, \
    build_stakeholders_tbl, build_stakeholder_plan_tbl, build_hw_env_tbl, \
    build_sw_env_tbl, build_doc_scale_tbl, build_code_scale_tbl, \
    build_data_mgmt_tbl, build_meeting_plan_tbl, build_schedule_phases_tbl, \
    build_baselines_tbl, build_human_resource_tbl, build_org_chart_tbl
from backend.services.doc_postprocess import (
    _estimate_pages,
    _apply_doc_fields,
    _apply_sdt_readonly,
    _apply_header_protection,
    _center_index_columns,
    _compact_table_headers,
    _clean_all_table_spaces,
    _strip_breaks_between_caption_and_table,
    _strip_cover_to_toc_blanks,
    _add_caption_keepnext,
    _trim_trailing_empty_paragraphs,
    _finalize_placeholders,
    _fit_tables_to_page,
    _separate_adjacent_tables,
    _remove_redundant_text,
    _tighten_appendix_captions,
    _unify_appendix_pages,
    _fix_11b_cfg_items,
    _ensure_signature_page,
    _auto_size_all_tables,
    _adjust_appendix_pgnumtype,
    _update_fields_with_word,
)

# 模板根目录：项目根/templates/sdp/<template_name>_占位符版.docx
TEMPLATES_DIR = os.path.join(config.BASE_DIR, "templates", "sdp")


def _tpl_path(template_name: str) -> str:
    """按模板名定位占位符版 docx。约定：<name>_占位符版.docx。"""
    return os.path.join(TEMPLATES_DIR, f"{template_name}_占位符版.docx")


def _parse_cfg_items(raw) -> list:
    """袁总 2026-09-03：解析 Project.cfg_items（JSON 数组）为配置项列表。
    入参：JSON 字符串，如 '[{"name":"…","code":"R105_0201"}]'。
    返回：list[dict]，解析失败/为空时回退为单个"主软件"配置项（保证文档不空）。
    """
    import json
    if not raw:
        return [{"name": "终点/轮载开关模拟器驱动软件", "code": project_id_default()}]
    try:
        items = json.loads(raw)
    except Exception:
        return [{"name": raw, "code": ""}] if isinstance(raw, str) else []
    if isinstance(items, dict):
        items = [items]
    if not isinstance(items, list) or not items:
        return [{"name": "终点/轮载开关模拟器驱动软件", "code": ""}]
    out = []
    for it in items:
        if isinstance(it, dict) and it.get("name"):
            out.append(it)
        elif isinstance(it, str) and it:
            out.append({"name": it, "code": ""})
    return out or [{"name": "终点/轮载开关模拟器驱动软件", "code": ""}]


def project_id_default() -> str:
    """占位符兜底用的默认项目号（cfg_items 为空时）。"""
    return "R105"


def _meta_ph_map(db: Session, project_id: str) -> dict:
    """
    按当前项目动态构造标量占位符映射（取代 doc_engine 里写死的 R121 反向回填）。
    字段与 SDP_占位符版.docx 的 {{meta.*}}/{{sys.*}}/{{org.*}}/{{role.*}} 锚点一一对应，
    确保"新建/修改项目弹窗收集的关键字"能注入到生成的开发计划里。
    """
    proj = db.query(Project).filter(Project.project_id == project_id).first()
    pid = project_id
    name = (proj.project_name if proj else '') or '飞管软件'
    model = (proj.aircraft_model if proj else '') or ''
    owner = (proj.owner if proj else '') or ''
    org = (proj.org if proj else '') or ''
    customer = (proj.customer_dept if proj else '') or ''
    approve_date = (proj.approve_date if proj else '') or ''
    # 项目方 2026-09-02：签字页日期统一 8 位紧凑格式(20250315)，去掉横杠/斜杠
    approve_date = str(approve_date).replace('-', '').replace('/', '')
    ide_version = (proj.ide_version if proj else '') or ''
    sw_version = (proj.sw_version if proj else '') or ''
    doc_no = (proj.doc_number if proj else '') or f'{pid}_SDP_V1.00'
    # 袁总 2026-09-03 需求2：封面编号仅前缀不可编辑，版本号可编辑
    _m_doc = re.match(r'^(.*_)(V[\d.]+)$', doc_no)
    doc_prefix = _m_doc.group(1) if _m_doc else doc_no
    doc_ver_edit = _m_doc.group(2) if _m_doc else "V1.00"
    # SDP 签署角色 / 开发环境 / 引用文档（设置页可编辑，按项目维度）
    ccb = (proj.ccb if proj else '') or ''
    designer = (proj.designer if proj else '') or ''
    reviewer = (proj.reviewer if proj else '') or ''
    reviewer2 = (proj.reviewer2 if proj else '') or ''
    reviewer3 = (proj.reviewer3 if proj else '') or ''
    tester = (proj.tester if proj else '') or ''
    qa = (proj.qa if proj else '') or ''
    config_manager = (proj.config_manager if proj else '') or ''
    org_config_manager = (proj.org_config_manager if proj else '') or ''
    # 项目组织角色（7.2.1 人力资源 / 相关方清单）：三处一致（前端录入=数据库=生成文档）
    requirement = (proj.requirement if proj else '') or owner   # 需求分析人员（未录入回退软件负责人）
    coder = (proj.coder if proj else '') or ''
    measure = (proj.measure if proj else '') or ''
    proj_lead = (proj.proj_lead if proj else '') or ''
    sys_eng = (proj.sys_eng if proj else '') or ''
    hw_ide_name = (proj.hw_ide_name if proj else '') or ''
    hw_mcu_model = (proj.hw_mcu_model if proj else '') or ''
    sw_name_host = (proj.sw_name_host if proj else '') or ''
    sw_name_iap = (proj.sw_name_iap if proj else '') or ''
    ref_sdtd = (proj.ref_sdtd_doc_number if proj else '') or ''
    ref_sqap = (proj.ref_sqap_doc_number if proj else '') or ''
    # 袁总 2026-09-03：软件配置项清单（1.1 标识章节 b）动态化）
    # 从 Project.cfg_items（JSON 数组）解析出配置项名称与数量；
    # 无数据时回退为 1 个"主软件"配置项，保证文档不出现空占位。
    cfg_items = _parse_cfg_items(proj.cfg_items if proj else None)
    cfg_count = str(len(cfg_items))
    # 袁总 2026-09-03（第四十一轮）：1.1 标识 b) 软件名称需【逐个列出配置项
    # 名称 + 配置项标识】（如"终点/轮载开关模拟器驱动软件（R105_0201）"），
    # 此前只输出名称、标识丢失，袁总反复反馈"两个配置项没体现"。
    cfg_names = "、".join(
        (("%s（%s）" % (it.get("name", ""), it.get("code", "")))
         if it.get("code") else str(it.get("name", "")))
        for it in cfg_items if it.get("name"))
    # 袁总 2026-09-03：表 11 软件配置管理库三库地址改为
    # https://192.168.5.160:444/svn/configurationLib/software/{trunk|tags|branches}/R105
    _svn_root = "https://192.168.5.160:444/svn/configurationLib/software"
    return {
        # meta 类（模板 {{meta.*}}）
        "{{meta.project_id}}": pid,
        # 袁总 2026-09-03（页眉丢失根因之一）：页眉 header4/5 的"配置项标识"列
        # 用的是 {{meta.doc_number}}，此前 ph_map 缺此键 → 页眉占位符替换不生效。
        "{{meta.doc_number}}": doc_no,
        # 袁总 2026-09-03 需求2：封面编号拆前缀(锁)+版本(可编辑)
        "{{meta.doc_prefix}}": doc_prefix,
        "{{meta.doc_ver_edit}}": doc_ver_edit,
        "{{meta.doc_version}}": sw_version or "V1.00",
        "{{meta.doc_ver_tag}}": "D",   # 项目方要求：页眉版本标识永远写死 D 版
        "{{meta.approve_date}}": approve_date,
        "{{meta.ide_version}}": ide_version,
        "{{meta.sw_version_example}}": sw_version,
        "{{meta.total_pages}}": "%TP%",   # 占位，fill 后由 generate_doc_bytes 统计段落数回填（封面用 NUMPAGES 域时此映射不再使用）
        "{{header.form_no}}": "CEC 设表022c",   # 项目方要求：页眉表单号永远写死 CEC 设表022c（无占位符）
        # sys 类（系统/软件名称）
        "{{sys.software_full}}": name,
        "{{sys.name}}": name,
        "{{sys.short}}": model,
        # 袁总 2026-09-03：引用文件表"《软件名》软件研制任务书"整句锁定用
        # （模板已把"{{sys.software_full}}软件研制任务书"合并为该占位符）
        "{{sys.taskbook}}": (name + "软件研制任务书") if name else "",
        # 袁总 2026-09-03：1.1 标识章节 b）软件配置项数量与名称清单
        "{{sys.cfg_count}}": cfg_count,
        "{{sys.cfg_items}}": cfg_names,
        # org 类（部门/单位）：封面公司名写死（项目方 2026-08-28 指示，对标 R105 封面"成都成飞电子科技有限公司"）
        "{{org.dev_dept}}": org,
        "{{org.customer_dept}}": customer,
        "{{org.user_dept}}": customer,   # 项目用户（同项目需方一致，新增占位符对接 Project.customer_dept）
        "{{org.developer}}": "成都成飞电子科技有限公司",
        "{{org.maintainer}}": org,       # 项目保障机构 = 承研单位（同一开发部）
        "{{org.site}}": model,           # 项目当前运行现场 = 项目型号（CB-B/DSQ-1AG）
        "{{org.plan_site}}": model,      # 项目计划运行现场 = 项目型号（同上）
        # cm 类（SVN 路径）—— 袁总 2026-09-03：表 11 软件配置管理库三库地址
        "{{cm.svn_trunk}}": f"{_svn_root}/trunk/{project_id}",
        "{{cm.svn_branches}}": f"{_svn_root}/branches/{project_id}",
        "{{cm.svn_tags}}": f"{_svn_root}/tags/{project_id}",
        # role 类（签署角色：编制/开发方=项目负责人；其余来自设置页签署角色字段）
        "{{role.author}}": owner,
        "{{role.ccb}}": ccb,
        "{{role.designer}}": designer,
        "{{role.reviewer}}": reviewer,
        "{{role.reviewer_2}}": reviewer2,
        "{{role.reviewer_3}}": reviewer3,
        "{{role.tester}}": tester,
        "{{role.qa}}": qa,
        "{{role.config_manager}}": config_manager,
        "{{role.org_config_manager}}": org_config_manager,
        # 项目组织角色（项目方要求：前端录入=数据库=生成文档，三处一致，不再写死/错位）
        "{{role.requirement}}": requirement,
        "{{role.coder}}": coder,
        "{{role.measure}}": measure,
        "{{role.proj_lead}}": proj_lead,
        "{{role.sys_eng}}": sys_eng,
        # hw / sw 类（开发环境，A.4.1）
        "{{hw.ide_name}}": hw_ide_name,
        "{{hw.mcu_model}}": hw_mcu_model,
        "{{sw.name_host}}": sw_name_host,
        "{{sw.name_iap}}": sw_name_iap,
        # ref 类（引用文档，A.2.1）
        "{{ref.sdtd_doc_number}}": ref_sdtd,
        "{{ref.sqap_doc_number}}": ref_sqap,
    }


def load_anchors(db: Session, project_id: str, template_name: str, module=None):
    """
    读取某项目某模板的全部锚点，分拣为标量映射与整表映射。
    返回 (ph_map, table_map)。标量占位符会用当前项目元信息覆盖（避免写死 R121）。
    module: None=全部用库最新；est/risk/stake=只更新该类，其余用快照（保持文档原样）。
    """
    rows = (
        db.query(TemplateAnchor)
        .filter(
            TemplateAnchor.project_id == project_id,
            TemplateAnchor.template_name == template_name,
        )
        .all()
    )
    ph_map, table_map = {}, {}
    for r in rows:
        if r.anchor_key.startswith("{{table."):
            table_map[r.anchor_key] = r.anchor_value or ""
        else:
            ph_map[r.anchor_key] = r.anchor_value or ""
    # 当前项目元信息覆盖标量占位符（R121 不再硬编码）
    ph_map.update(_meta_ph_map(db, project_id))
    # C1：风险整表强制从业务表动态生成（不依赖 template_anchors 是否有此锚点行，
    #     模板 SDP_占位符版.docx 内已含 {{table.risks}} 锚点，这里直接覆盖）
    table_map["{{table.risks}}"] = build_risks_tbl(project_id)
    # C2：其余 8 个表格占位符统一从业务表聚合（杜绝空值占位符残留）。
    #     数据均按 project_id 维度，来自平台真实业务库（最终随 SVN 受控）。
    from backend.services import data_service
    table_map["{{table.schedule}}"] = build_schedule_tbl(
        data_service.DataService.list_schedule_phases(db, project_id))
    table_map["{{table.stakeholders}}"] = build_stakeholders_tbl(
        data_service.DataService.list_stakeholders(db, project_id))
    table_map["{{table.stakeholder_plan}}"] = build_stakeholder_plan_tbl(
        data_service.DataService.list_stakeholder_plan(db, project_id))
    table_map["{{table.hw_env_res}}"] = build_hw_env_tbl(
        data_service.DataService.list_hw_res(db, project_id))
    table_map["{{table.sw_env_res}}"] = build_sw_env_tbl(
        data_service.DataService.list_sw_res(db, project_id))
    # 项目方 2026-09-02 恢复：文档规模【估计表(4列)】与【复用表(5列)】两张并存（对标 R121）
    table_map["{{table.doc_scale_est}}"] = build_doc_scale_tbl(
        data_service.DataService.list_doc_scale(db, project_id), kind="est")
    table_map["{{table.doc_scale_reuse}}"] = build_doc_scale_tbl(
        data_service.DataService.list_doc_scale(db, project_id), kind="reuse")
    # 进度阶段表（对标 R121：阶段名称|计划开始时间|计划结束时间|备注）
    table_map["{{table.schedule_phases}}"] = build_schedule_phases_tbl(
        data_service.DataService.list_schedule_phases(db, project_id))
    table_map["{{table.code_scale_est}}"] = build_code_scale_tbl(project_id)
    # 会议计划（项目方要求：从 meeting_plan 表读取，不再写死在模板中）
    table_map["{{table.meeting_plan}}"] = build_meeting_plan_tbl(project_id)
    # 基线列表（项目方 2026-09-02：从 config_items 表按 baseline 分组聚合，
    # 多配置项用中文顿号"、"连接——不再写死在模板中）
    from backend.dao import config_item_dao as _ci_dao
    table_map["{{table.baselines}}"] = build_baselines_tbl(
        _ci_dao.ConfigItemDao.list_baselines(db, project_id))
    # 人力资源表（项目方 2026-09-02：从 project_members 表读，所有"姓名"在文档中 sdt 锁定）
    from backend.dao import project_member_dao as _pm_dao
    table_map["{{table.human_resource}}"] = build_human_resource_tbl(
        _pm_dao.ProjectMemberDao.list_by_project(db, project_id))
    # 组织机构表（项目方 2026-09-02：对标 R121 表29，从 org_chart 表读，sdt 锁定）
    from backend.dao import org_chart_dao as _oc_dao
    table_map["{{table.org_chart}}"] = build_org_chart_tbl(
        _oc_dao.OrgChartDao.list_by_project(db, project_id))
    proj = db.query(Project).filter(Project.project_id == project_id).first()
    table_map["{{table.data_mgmt}}"] = build_data_mgmt_tbl(proj)
    # ---- 分类同步（项目方口径）：整篇文档提交，但只更新所选类数据，其余章节用快照 ----
    apply_module_snapshot(db, project_id, module, table_map)
    return ph_map, table_map


# 分类同步：模块 -> 该模块包含的表格锚点
MODULE_TABLES = {
    "est": ["{{table.schedule}}", "{{table.code_scale_est}}", "{{table.code_scale_reuse}}"],
    "risk": ["{{table.risks}}", "{{table.hw_env_res}}", "{{table.sw_env_res}}"],
    "stake": ["{{table.stakeholder_plan}}", "{{table.stakeholders}}"],
}


def apply_module_snapshot(db: Session, project_id: str, module, table_map):
    """按模块冻结/更新表格 XML：
    - module=None（整篇提交）：全部用数据库最新，并刷新 est/risk/stake 三类快照
    - module='est'：只重新渲染 est 类表格并更新其快照；risk/stake 用上次快照 XML（保持原样）
    - 快照缺失时回退为库值（并补写快照）。"""
    import json
    import datetime
    from backend.db.models import SvnModuleSnapshot
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for mod, anchors in MODULE_TABLES.items():
        update_this = (module is None) or (module == mod)
        if update_this:
            # 用库值并写快照
            snap = json.dumps({a: table_map.get(a, "") for a in anchors},
                              ensure_ascii=False)
            row = db.query(SvnModuleSnapshot).filter(
                SvnModuleSnapshot.project_id == project_id,
                SvnModuleSnapshot.module == mod).first()
            if row:
                row.content = snap
                row.updated_at = now
            else:
                db.add(SvnModuleSnapshot(project_id=project_id, module=mod,
                                         content=snap, updated_at=now))
            db.commit()
        else:
            # 用快照（保持文档原样）
            row = db.query(SvnModuleSnapshot).filter(
                SvnModuleSnapshot.project_id == project_id,
                SvnModuleSnapshot.module == mod).first()
            if row and row.content:
                try:
                    data = json.loads(row.content)
                    for a, xml in data.items():
                        if xml:
                            table_map[a] = xml
                except Exception:
                    pass  # 快照损坏则保持库值
            else:
                # 无快照：用库值并补写
                snap = json.dumps({a: table_map.get(a, "") for a in anchors},
                                  ensure_ascii=False)
                db.add(SvnModuleSnapshot(project_id=project_id, module=mod,
                                         content=snap, updated_at=now))
                db.commit()


def upsert_anchors(db: Session, project_id: str, template_name: str,
                   scalars: dict, tables: dict) -> int:
    """
    批量写入/更新锚点。返回写入条数。
    幂等：按 (project_id, template_name, anchor_key) 唯一键 upsert。
    """
    cnt = 0
    for k, v in {**scalars, **tables}.items():
        exist = (
            db.query(TemplateAnchor)
            .filter(
                TemplateAnchor.project_id == project_id,
                TemplateAnchor.template_name == template_name,
                TemplateAnchor.anchor_key == k,
            )
            .first()
        )
        if exist:
            exist.anchor_value = v
        else:
            db.add(TemplateAnchor(
                project_id=project_id, template_name=template_name,
                anchor_key=k, anchor_value=v,
            ))
        cnt += 1
    db.commit()
    return cnt

def generate_doc_bytes(project_id: str, template_name: str,
                       ph_override: dict = None, module=None) -> bytes:
    """
    生成文档字节流（不落库、不落盘，直接返回 bytes 供 StreamingResponse）。
    ph_override: 测试/特定场景覆盖标量（如配置项标识注入）。
    module: None=全部用库最新；est/risk/stake=只更新该类数据，其余章节用快照保持原样。
    """
    from backend.db.session import SessionLocal
    db = SessionLocal()
    try:
        # 必填校验：关键项目字段未填写则报错，强制前端录入真实数据（项目方 2026-09-02 口径）
        validate_project_for_sdp(db, project_id)
        ph_map, table_map = load_anchors(db, project_id, template_name, module=module)
        # 取项目所选阶段（页眉阶段勾选联动用：F方案/C初样/S正样/D定型/P批产）
        _proj = db.query(Project).filter(Project.project_id == project_id).first()
        phase_val = (_proj.phase if _proj else "") or ""
    finally:
        db.close()

    if ph_override:
        ph_map.update(ph_override)

    tpl = _tpl_path(template_name)
    if not os.path.exists(tpl):
        raise FileNotFoundError(f"模板不存在: {tpl}")

    # 临时文件灌装（复用 SdpFiller，不动 doc_engine 内部）
    import tempfile
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    tmp_path = tmp.name
    tmp.close()
    try:
        SdpFiller(tpl, tmp_path).fill_from_data(ph_map, table_map,
                                                lock_keys=LOCKED_PLACEHOLDER_KEYS)
        # 回填总页数：统计 document.xml 段落数（近似每页段落），写回 zip
        total_pages = _estimate_pages(tmp_path)
        # 项目方 2026-09-02：封面页数改为 NUMPAGES 域 + 打开自动刷新（不再写死估算数字）
        _apply_doc_fields(tmp_path, total_pages)
        # 平台数据只读保护（项目方 2026-09-02）：用 Content Control(sdt) 包裹 10 张
        # 平台表，内容锁定(sdtContentLocked)，其余正文/手写表默认可编辑。
        # 不依赖整文档 documentProtection，规避此前 perm 注入 body 级导致 Word 空白。
        _apply_sdt_readonly(tmp_path, project_id,
                            ph_map.get("{{meta.doc_version}}", "V1.00"))
        # 页眉：阶段勾选按平台所选阶段联动 + 阶段表/配置项标识锁定不可编辑
        _apply_header_protection(tmp_path, phase_val)
        # 项目方 2026-09-02：所有表格"序号"列统一居中（水平+垂直），
        # 覆盖模板静态表与动态生成表（在 sdt 包裹后执行，含 sdtContent 内的表）。
        _center_index_columns(tmp_path)
        # 袁总 2026-09-03（第三十九轮）：表头紧凑化对标 R121（序\xa0号→序号、
        # 型号 / 图号→型号/图号）——袁总反复点名的"表格里的空格"根因。
        _compact_table_headers(tmp_path)
        # 袁总 2026-09-04（反复反馈"所有表格里的空格始终没解决"）：
        # 上面两个函数只做 strip()/表头紧凑化，不动单元格【中间】的空格，
        # 导致封面签署页"审  定"、文件分发表"文  件  分  发/纸    质"等
        # 27 处字间距空格长期残留。本函数对全部表格单元格做强制清理。
        _clean_all_table_spaces(tmp_path)
        # 袁总 2026-09-03：先删表标题与表格之间的硬分页符（否则会产生整页
        # 空白，且 keepNext 失效）→ 再给表标题加 keepNext 绑定表格。
        _strip_breaks_between_caption_and_table(tmp_path)
        # 袁总 2026-09-04（正文前空白页 P3）：删封面签署区之后、目录之前的纯空段
        _strip_cover_to_toc_blanks(tmp_path)
        _add_caption_keepnext(tmp_path)
        # 袁总 2026-09-03：删除文末多余空段落，消除末页空白页
        _trim_trailing_empty_paragraphs(tmp_path)
        # 袁总 2026-09-03（第四十二轮）：兜底替换文档内残留的 {{...}}}} 占位符
        # ——跨 run 拆分或 ph_map 缺键的场景，确保生成文件无任何占位符
        # （空值统一替换为 V1.00，对应袁总"默认写成 v1.00"指示）
        _finalize_placeholders(tmp_path, ph_map)
        # 袁总 2026-09-03：全文档表格宽度适配页面 + 整表居中。
        # 诊断发现纵向页可用宽仅 9468 dxa，而模板/生成的表大量超宽
        # （附录B 15083、附录A 14425、表24 硬件 10508、表19 10260…），
        # 导致"超出页边"。本函数统一等比缩到可用宽内并加 tblPr/jc=center。
        _fit_tables_to_page(tmp_path)
        # 袁总 2026-09-03：相邻两张表之间无段落时 Word 会合并渲染为一张表
        # （表22/23"和到一起"根因），统一插入空段落强制分隔。
        _separate_adjacent_tables(tmp_path)
        # 袁总 2026-09-03：删除正文中的冗余残句（"CB-B/DSQ-1AGIAP下位机软件 下位机软件"）
        _remove_redundant_text(tmp_path)
        # 袁总 2026-09-04（"48页那根横线把它放在47页"）：文档末尾残留 8 个空段落，
        # Word 会多渲染出一个近乎空白的末页（第48页），只剩一根横线。
        # 上次清理调用得太早——后续的 _separate_adjacent_tables 等步骤又会补回
        # 空段落，故在【所有结构处理完成后、统计页数前】再清一次，
        # 让末页内容收回上一页（48 页 → 47 页）。
        _trim_trailing_empty_paragraphs(tmp_path)
        # 袁总 2026-09-04（"附录 C/A 标题上下多余空白"）：删掉附录标题上下多余空段
        _tighten_appendix_captions(tmp_path)
        # 袁总 2026-09-04（"附录A/B 要和下面表格挨着、48页去掉"）：
        # 删附录A/B 标题前的 pageBreakBefore，让 A/B 紧贴前一节末；附录B 不再
        # 独立成页；保留附录C 的 pageBreakBefore（横版分节）。
        _unify_appendix_pages(tmp_path)
        # 袁总 2026-09-04（"1.1 b 应该是两条但只显示一条"）根因：
        # 模板 1.1 b 章节只画了 R105_0201 一行，第二行根本没有占位符挂载点。
        # 后处理在第一行后追加 N-1 个配置项行。
        _fix_11b_cfg_items(tmp_path, project_id)
        # 袁总 2026-09-04（新增签字页）：独立"签字页"，单页布局，参考 R121 封面签署区做法，
        # 角色姓名取自 Project 签署字段（与封面同源，数据单一源头）。
        _ensure_signature_page(tmp_path, project_id)
        # 袁总 2026-09-04（"表 5/7/19/23/24/25 看不全"）：模板静态表（如表 19）
        # 没有走 _simple_tbl 自适应字号分支，默认继承 docDefaults=24（小四）撑不下
        # 911 dxa 这样的窄列，逐字竖排"开/发/阶/段"。本函数对【全文档所有表格】
        # （含 sdt 内的动态表与模板静态表）按列宽强制设字号（21/22/24）。
        _auto_size_all_tables(tmp_path)
        # 袁总 2026-09-03：上述后处理（表格宽度适配、删除段落）会改变实际页数，
        # 必须【最后】重新统计页数并刷新封面 NUMPAGES 域结果，
        # 否则封面"（共 N 页）"是过期数字（原流程在改页数前统计，导致与实际不符）。
        _apply_doc_fields(tmp_path)
        # 袁总 2026-09-04（"目录页码与实际不一致"）：
        # R121 模板 final sectPr pgNumType.start=34，但 R105 正文短，
        # 项目组织视觉页就到 34-37，导致附录 A/B/C 视觉页与正文重号。
        # 改为附录 A 的全局页号（让附录 C 节从附录 A 全局页重新编号）。
        _adjust_appendix_pgnumtype(tmp_path)
        # 袁总 2026-09-03：NUMPAGES 域真实页数只有 Word 分页引擎知道，
        # 用 COM 实打开更新全部域并保存（封面总页码与实际一致）。
        _update_fields_with_word(tmp_path)
        with open(tmp_path, "rb") as f:
            data = f.read()
    finally:
        # Windows 上 docx 句柄可能延迟释放，删除失败忽略即可（临时文件）
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass
    return data

SDP_REQUIRED_PROJECT_FIELDS = {
    "project_name": "软件名称",
    "owner": "软件负责人(编制人)",
    "customer_dept": "顾客代表单位",
    "approve_date": "批准日期",
    "org": "承研单位",
}


def validate_project_for_sdp(db: Session, project_id: str):
    """生成《软件开发计划》前必填校验：关键项目字段未填写则报错，强制前端录入真实数据。"""
    proj = db.query(Project).filter(Project.project_id == project_id).first()
    missing = [label for f, label in SDP_REQUIRED_PROJECT_FIELDS.items()
               if not (proj and getattr(proj, f))]
    if missing:
        raise ValueError(
            "生成《软件开发计划》失败：以下关键字段未填写，请先在「项目信息」中补全 —— "
            + "、".join(missing))

# 只读锁定白名单（项目方 2026-09-02 口径）：
# 只有这些占位符填入的值不可编辑（封面编号/型号/软件名称/版本/单位/表单号/
# 配置项标识/签署日期/引用文件编号/SVN 地址等核心字段）；
# 其余由数据库读入的描述性正文（系统概述、IAP 概述、资源描述等）保持可编辑。
# 说明：sys.short(型号)、org.*(单位)、ref.*(引用文件)、cm.svn_*(SVN 地址) 等
# 在正文段落中大量出现，若锁定会让"系统概述/资源描述"等正文不可编辑，
# 与"描述性正文可编辑"的要求冲突，故【不列入】锁定白名单。
LOCKED_PLACEHOLDER_KEYS = (
    "{{meta.project_id}}",
    "{{meta.doc_version}}",
    "{{meta.doc_ver_tag}}",
    # 袁总 2026-09-03：签字页日期 {{meta.approve_date}}（20250315）改为【可编辑】
    # （签署日期需打印后手签/盖章前按实际日期调整，属人工填写项，不再锁定）。
    "{{meta.total_pages}}",
    "{{sys.software_full}}",
    "{{sys.name}}",
    # 袁总 2026-09-03（第三十九轮）：文档中所有 CB-B/DSQ-1AG/R105/软件名+
    # 软件研制任务书 均不可编辑——sys.short(型号) 加回锁定（此前第三十七轮
    # 因"正文大量出现锁太多"移除，袁总本轮明确要求全部锁定，以袁总最新指令为准）。
    "{{sys.short}}",
    # 袁总 2026-09-03：1.1 b) 配置项数量与清单（从 Project.cfg_items 读）锁定
    "{{sys.cfg_count}}",
    "{{sys.cfg_items}}",
    # 袁总 2026-09-03：引用文件表中"《软件名》软件研制任务书"整句锁定
    # （模板已合并为单占位符 {{sys.taskbook}}，值=软件名+软件研制任务书）
    "{{sys.taskbook}}",
    "{{header.form_no}}",
    # 项目方 2026-09-02：检视小组（5.7.2.5 代码审查人员安排）两人来自平台
    # projects 表签署角色字段（role.author=编制人、role.requirement=需求人员），
    # 替换后 sdt 锁定不可编辑。人名属签署类字段，锁定符合"签署信息不可编辑"口径。
    "{{role.author}}",
    "{{role.requirement}}",
    # 项目方 2026-09-02：所有"与人相关"的占位符从 Project.* 读，替换后 sdt 锁定，
    # 文档中不可手改（测试人员/评审/QA/CM 等角色姓名 = 签署类，锁定语义）。
    "{{role.ccb}}",
    "{{role.designer}}",
    "{{role.reviewer}}",
    "{{role.reviewer_2}}",
    "{{role.reviewer_3}}",
    "{{role.tester}}",
    "{{role.qa}}",
    "{{role.config_manager}}",
    "{{role.org_config_manager}}",
    "{{role.coder}}",
    "{{role.measure}}",
    "{{role.proj_lead}}",
    "{{role.sys_eng}}",
    # 项目方 2026-09-02：项目相关方（1.2.3 章节）6 行 org.* 从 Project.* 读，
    # 替换后 sdt 锁定——单位/现场/部门名均属元数据，应由平台统管。
    "{{org.dev_dept}}",
    "{{org.customer_dept}}",
    "{{org.user_dept}}",
    "{{org.maintainer}}",
    "{{org.site}}",
    "{{org.plan_site}}",
    # 袁总 2026-09-03：表 11 软件配置管理库三库地址——SVN URL 由平台统管。
    # 注：{{meta.project_id}} 不在此处锁定（封面/页眉/签署页均用，全锁会破坏太多区域），
    # 通过 READONLY_TABLE_KEYS ["配置库路径"] 让表 11 整表 sdt 锁定即可。
    "{{cm.svn_trunk}}",
    "{{cm.svn_branches}}",
    "{{cm.svn_tags}}",
    # 袁总 2026-09-03：{{sys.short}}(型号 CB-B/DSQ-1AG) 按本文件 700-702 行口径
    # 【不列入】锁定白名单——型号在正文(1.1/系统概述/项目概述等)大量出现，
    # 全锁会让正文不可编辑；项目相关方(1.2.3)那一处由 org.* 单独锁负责。
)
