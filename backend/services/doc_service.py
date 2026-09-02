# -*- coding: utf-8 -*-
"""
文档生成服务（Service 层）。
作者：袁燕
功能：从 template_anchors 读取锚点数据，调用 doc_engine 灌装占位符模板，
      产出正式 docx 字节流。模板文件在 templates/ 目录（平台外，不提交 SVN）。
设计：高内聚（文档拼装逻辑内聚）、低耦合（只依赖 doc_engine + DAO/ORM）。
"""
import os
import re
from lxml import etree

from sqlalchemy.orm import Session

# OOXML 命名空间（统计段落/打补丁占位符用，避免重复定义）
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

from backend import config
from backend.db.models import TemplateAnchor, Project
from backend.doc_engine import SdpFiller
from backend.services.table_builder import build_risks_tbl, build_schedule_tbl, \
    build_stakeholders_tbl, build_stakeholder_plan_tbl, build_hw_env_tbl, \
    build_sw_env_tbl, build_doc_scale_tbl, build_code_scale_tbl, \
    build_data_mgmt_tbl, build_meeting_plan_tbl

# 模板根目录：项目根/templates/sdp/<template_name>_占位符版.docx
TEMPLATES_DIR = os.path.join(config.BASE_DIR, "templates", "sdp")


def _tpl_path(template_name: str) -> str:
    """按模板名定位占位符版 docx。约定：<name>_占位符版.docx。"""
    return os.path.join(TEMPLATES_DIR, f"{template_name}_占位符版.docx")


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
    phase = (proj.phase if proj else '') or ''
    start_date = (proj.start_date if proj else '') or ''
    approve_date = (proj.approve_date if proj else '') or ''
    ide_version = (proj.ide_version if proj else '') or ''
    sw_version = (proj.sw_version if proj else '') or ''
    doc_no = (proj.doc_number if proj else '') or f'{pid}_SDP_V1.00'
    svn_base = (proj.svn_base_path if proj else '') or f'{pid}/trunk'
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
    return {
        # meta 类（模板 {{meta.*}}）
        "{{meta.project_id}}": pid,
        "{{meta.doc_number}}": doc_no,
        "{{meta.doc_version}}": sw_version or "V1.00",
        "{{meta.doc_ver_tag}}": "D",   # 袁总要求：页眉版本标识永远写死 D 版
        "{{meta.approve_date}}": approve_date,
        "{{meta.ide_version}}": ide_version,
        "{{meta.sw_version_example}}": sw_version,
        "{{meta.total_pages}}": "%TP%",   # 占位，fill 后由 generate_doc_bytes 统计段落数回填（封面用 NUMPAGES 域时此映射不再使用）
        "{{header.form_no}}": "CEC 设表022c",   # 袁总要求：页眉表单号永远写死 CEC 设表022c（无占位符）
        # sys 类（系统/软件名称）
        "{{sys.software_full}}": name,
        "{{sys.name}}": name,
        "{{sys.short}}": model,
        # org 类（部门/单位）：封面公司名写死（袁总 2026-08-28 指示，对标 R105 封面"成都成飞电子科技有限公司"）
        "{{org.dev_dept}}": org,
        "{{org.customer_dept}}": customer,
        "{{org.developer}}": "成都成飞电子科技有限公司",
        "{{org.maintainer}}": "成都成飞电子科技有限公司",
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
        # 项目组织角色（袁总要求：前端录入=数据库=生成文档，三处一致，不再写死/错位）
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
        # cm 类（SVN 路径）
        "{{cm.svn_trunk}}": f"https://yuanyan/svn/{svn_base}",
        "{{cm.svn_branches}}": f"https://yuanyan/svn/{svn_base.replace('/trunk', '/branches')}",
        "{{cm.svn_tags}}": f"https://yuanyan/svn/{svn_base.replace('/trunk', '/tags')}",
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
    # 袁总 2026-09-01：删除"文档规模估计"与"IAP 代码规模估计"两张表，
    # 仅保留"文档规模估计及复用情况"一张表承载规模数据。
    table_map["{{table.doc_scale_reuse}}"] = build_doc_scale_tbl(
        data_service.DataService.list_doc_scale(db, project_id), kind="reuse")
    table_map["{{table.code_scale_est}}"] = build_code_scale_tbl(project_id)
    # 会议计划（袁总要求：从 meeting_plan 表读取，不再写死在模板中）
    table_map["{{table.meeting_plan}}"] = build_meeting_plan_tbl(project_id)
    proj = db.query(Project).filter(Project.project_id == project_id).first()
    table_map["{{table.data_mgmt}}"] = build_data_mgmt_tbl(proj)
    # ---- 分类同步（袁总口径）：整篇文档提交，但只更新所选类数据，其余章节用快照 ----
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
        # 必填校验：关键项目字段未填写则报错，强制前端录入真实数据（袁总 2026-09-02 口径）
        validate_project_for_sdp(db, project_id)
        ph_map, table_map = load_anchors(db, project_id, template_name, module=module)
    finally:
        db.close()

    if ph_override:
        ph_map.update(ph_override)

    tpl = _tpl_path(template_name)
    if not os.path.exists(tpl):
        raise FileNotFoundError(f"模板不存在: {tpl}")

    # 临时文件灌装（复用 SdpFiller，不动 doc_engine 内部）
    import tempfile
    import zipfile
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    tmp_path = tmp.name
    tmp.close()
    try:
        SdpFiller(tpl, tmp_path).fill_from_data(ph_map, table_map)
        # 回填总页数：统计 document.xml 段落数（近似每页段落），写回 zip
        total_pages = _estimate_pages(tmp_path)
        _patch_placeholder_in_docx(tmp_path, "%TP%", str(total_pages))
        # 平台数据只读保护（袁总 2026-09-02）：用 Content Control(sdt) 包裹 10 张
        # 平台表，内容锁定(sdtContentLocked)，其余正文/手写表默认可编辑。
        # 不依赖整文档 documentProtection，规避此前 perm 注入 body 级导致 Word 空白。
        _apply_sdt_readonly(tmp_path)
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


# 平台 4 类录入内容对应的只读表（表头关键词须全部命中才判定）。
# 这些表的数据均来自"项目策划"页录入，生成文档后锁定为只读岛；
# 模板静态表（签署页/引用文件/评审计划/基线列表等）不在其中，保持可编辑。
READONLY_TABLE_KEYS = [
    ['规模估计', '复用页数'],
    ['规模估计（行）'],
    ['调整后总工作量'],
    ['会议类型', '会议组织者'],
    ['姓名/单位'],
    ['顾客代表'],
    ['资源名称', '跟踪情况'],
    ['软件名称'],
    ['风险通报方式及频率'],
    ['数据类别', '收集时机'],
]


def _tbl_span(doc, start, keys):
    """从 start 起找第一个表头同时含 keys 的最外层表格区间。"""
    pos = start
    while True:
        cands = [x for x in (doc.find('<w:tbl>', pos), doc.find('<w:tbl ', pos)) if x >= 0]
        if not cands:
            return None
        s = min(cands)
        depth, p2, end = 0, s, None
        while True:
            c2 = [x for x in (doc.find('<w:tbl>', p2), doc.find('<w:tbl ', p2)) if x >= 0]
            nxt_open = min(c2) if c2 else -1
            nxt_close = doc.find('</w:tbl>', p2)
            if nxt_close < 0:
                return None
            if 0 <= nxt_open < nxt_close:
                depth += 1
                p2 = nxt_open + 7
            else:
                depth -= 1
                p2 = nxt_close + 8
                if depth == 0:
                    end = p2
                    break
        texts = ''.join(re.findall(r'<w:t(?:\s[^>]*)?>(.*?)</w:t>', doc[s:end], flags=re.S))
        if all(k in texts for k in keys):
            return (s, end)
        pos = end


def _mark_readonly_tables(doc):
    """平台数据对应的动态表 = 真实只读岛（Word 文档保护 perm 多区间）；
    表之间的段落间隙 = 可编辑区间。perm 均插在段落内部（OOXML 规范）。
    袁总 2026-09-01 终审口径：平台录入数据真实不可编辑，其余正文均可编辑。"""
    spans, pos = [], 0
    for keys in READONLY_TABLE_KEYS:
        p2 = 0
        while True:
            r = _tbl_span(doc, p2, keys)
            if not r:
                break
            if not any(a < r[1] and r[0] < b for a, b in spans):
                spans.append(r)
            p2 = r[1]
    spans.sort()
    pid = 1000
    inserts = [(0, '<w:permStart w:id="%d" w:edGrp="everyone"/>' % pid)]
    pid += 1
    for a, b in spans:
        inserts.append((a, '<w:permEnd w:id="%d"/>' % pid))
        pid += 1
        inserts.append((b, '<w:permStart w:id="%d" w:edGrp="everyone"/>' % pid))
        pid += 1
    end_body = doc.rfind('</w:body>')
    inserts.append((end_body, '<w:permEnd w:id="%d"/>' % pid))
    for pos, txt in sorted(inserts, key=lambda x: -x[0]):
        doc = doc[:pos] + txt + doc[pos:]
    return doc


def _shade_readonly_tables(doc):
    """给平台数据对应的动态表（真实只读岛）所有单元格加黄色底纹(FFF2CC)，
    辅助标识'不可编辑'；其余正文/静态表保持白色(可编辑)。
    反向(从后往前)替换，避免字符串索引偏移。"""
    spans = []
    for keys in READONLY_TABLE_KEYS:
        p2 = 0
        while True:
            r = _tbl_span(doc, p2, keys)
            if not r:
                break
            if not any(a < r[1] and r[0] < b for a, b in spans):
                spans.append(r)
            p2 = r[1]
    spans.sort(reverse=True)
    for a, b in spans:
        seg = doc[a:b]

        def _shd(m):
            tcpr = m.group(0)
            if "<w:shd" in tcpr:
                return re.sub(r'w:fill="[^"]*"', 'w:fill="FFF2CC"', tcpr)
            return tcpr[:-len("</w:tcPr>")] + \
                '<w:shd w:val="clear" w:color="auto" w:fill="FFF2CC"/></w:tcPr>'
        seg = re.sub(r"<w:tcPr>.*?</w:tcPr>", _shd, seg, flags=re.S)
        doc = doc[:a] + seg + doc[b:]
    return doc


def _protect_readonly_zones(docx_path):
    """真实只读保护 + 只读区黄色底纹（袁总 2026-09-01 终审口径）：
    1) settings.xml 设文档只读保护(readOnly) + 打开自动更新域；
    2) 平台录入数据对应的动态表 = 真实只读岛(perm 多区间，不可编辑)，其余正文可编辑；
    3) 只读岛所有单元格加黄色底纹(FFF2CC) 辅助标识'不可编辑'；可编辑区白色；
    4) 打印预览/打印时 Word 默认不输出底纹与编辑高亮，呈灰白（领导'打印全灰'）。"""
    import zipfile as _zf
    import shutil as _sh
    bak = docx_path + ".prot.bak"
    _sh.copy(docx_path, bak)
    try:
        z = _zf.ZipFile(bak)
        names = z.namelist()
        data = {n: z.read(n) for n in names}
        z.close()
        # 1) 只读保护 + 自动更新域
        st = data["word/settings.xml"].decode("utf-8")
        if 'w:enforcement="0"' in st:
            st = st.replace('<w:documentProtection w:enforcement="0"/>',
                            '<w:documentProtection w:edit="readOnly" w:enforcement="1"/>'
                            '<w:updateFields w:val="true"/>')
        elif "<w:documentProtection" not in st:
            st = st.replace("</w:settings>",
                            '<w:documentProtection w:edit="readOnly" w:enforcement="1"/>'
                            '<w:updateFields w:val="true"/></w:settings>')
        elif "<w:updateFields" not in st:
            st = st.replace("</w:settings>",
                            '<w:updateFields w:val="true"/></w:settings>')
        data["word/settings.xml"] = st.encode("utf-8")
        # 2) 真实只读岛 perm + 黄色底纹辅助标识
        doc = data["word/document.xml"].decode("utf-8")
        doc = _shade_readonly_tables(doc)
        doc = _mark_readonly_tables(doc)
        data["word/document.xml"] = doc.encode("utf-8")
        with _zf.ZipFile(docx_path, "w", _zf.ZIP_DEFLATED) as zo:
            for n in names:
                zo.writestr(n, data[n])
    except Exception:
        _sh.copy(bak, docx_path)
    finally:
        try:
            os.remove(bak)
        except OSError:
            pass


# ===================== 平台数据只读保护（Content Control 方案）=====================
# 袁总 2026-09-02：10 张平台表整表只读，其余正文/手写表可编辑。
# 方案：用 w:sdt 内容控件包裹平台表并锁定内容(sdtContentLocked)，不依赖整文档
# documentProtection，规避此前 perm 注入 body 级导致 Word 空白的问题。

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


def _wrap_readonly_tables_with_sdt(doc):
    """用 w:sdt 包裹 READONLY_TABLE_KEYS 命中的平台表（内容锁定，其余可编辑）。"""
    spans = []
    for keys in READONLY_TABLE_KEYS:
        p2 = 0
        while True:
            r = _tbl_span(doc, p2, keys)
            if not r:
                break
            if not any(a < r[1] and r[0] < b for a, b in spans):
                spans.append(r)
            p2 = r[1]
    spans.sort(reverse=True)  # 从后往前插，避免索引偏移
    sid = 1
    for a, b in spans:
        seg = doc[a:b]
        repl = ('<w:sdt w:id="%d"><w:sdtPr><w:lock w:val="sdtContentLocked"/></w:sdtPr>'
                '<w:sdtContent>' % sid) + seg + '</w:sdtContent></w:sdt>'
        sid += 1
        doc = doc[:a] + repl + doc[b:]
    return doc


def _apply_sdt_readonly(docx_path):
    """对 docx 内 10 张平台表加 sdt 内容锁定（其余不受影响）。失败则回退原文件，保证文档不损坏。"""
    import zipfile as _zf
    import shutil as _sh
    bak = docx_path + ".sdt.bak"
    _sh.copy(docx_path, bak)
    try:
        z = _zf.ZipFile(bak)
        names = z.namelist()
        data = {n: z.read(n) for n in names}
        z.close()
        doc = data["word/document.xml"].decode("utf-8")
        doc = _wrap_readonly_tables_with_sdt(doc)
        data["word/document.xml"] = doc.encode("utf-8")
        with _zf.ZipFile(docx_path, "w", _zf.ZIP_DEFLATED) as zo:
            for n in names:
                zo.writestr(n, data[n])
    except Exception:
        _sh.copy(bak, docx_path)
    finally:
        try:
            os.remove(bak)
        except OSError:
            pass


def _estimate_pages(docx_path):
    import zipfile as _zf
    z = _zf.ZipFile(docx_path)
    xml = z.read("word/document.xml").decode("utf-8")
    z.close()
    text = re.sub(r"<[^>]+>", "", xml)
    return max(1, len(text) // 1500)


def _patch_placeholder_in_docx(docx_path, old, new):
    import zipfile as _zf
    import shutil as _sh
    bak = docx_path + ".patch.bak"
    _sh.copy(docx_path, bak)
    try:
        z = _zf.ZipFile(bak)
        names = z.namelist()
        data = {n: z.read(n) for n in names}
        z.close()
        doc = data["word/document.xml"].decode("utf-8")
        doc = doc.replace(old, new)
        data["word/document.xml"] = doc.encode("utf-8")
        with _zf.ZipFile(docx_path, "w", _zf.ZIP_DEFLATED) as zo:
            for n in names:
                zo.writestr(n, data[n])
    finally:
        try:
            os.remove(bak)
        except OSError:
            pass
