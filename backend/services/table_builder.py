# -*- coding: utf-8 -*-
"""
整表动态生成器（Service 层）。

作者：袁燕

功能：把"整表锚点"从 template_anchors 里的死 XML 片段，升级为
      从业务表（risks ...）实时拼 OOXML。

C1 范围（项目方确认）：先做 risks 一张表动态化。
设计原则：
  - 高内聚：整表拼装逻辑内聚于此文件
  - 低耦合：只依赖 ORM 模型 + lxml，不碰 doc_engine 内部
  - 对齐 R121 附录A 项目风险管理表：4 行表头（元信息行 + 分组表头 + 子列表头）+ 15 列数据
  - 兜底：risks 表为空时，返回仅表头 + 一行"暂无风险"提示，不崩
  - 按 project_id 隔离（多项目支持，由 doc_service 传入当前项目）
"""

import os


from backend import config
from backend.db.session import SessionLocal
from backend.db.models import MeetingPlan, Project, Risk

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
TEMPLATES_DIR = os.path.join(config.BASE_DIR, "templates", "sdp")

# 页面可用宽度（dxa）：正文纵向约 9468，附录横向约 14406（由模板 sectPr 决定）。
# 动态表格列宽总和不得超过所在节可用宽，否则右侧被截、显示不完整（项目方反馈根因）。
PAGE_W_PORTRAIT = 9468
PAGE_W_LANDSCAPE = 14406


def _esc(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _cell(text: str, width: int, merge: str = None, gridspan: int = None) -> str:
    """单个单元格。merge: 'restart'/'continue'（vMerge 竖并）；gridspan: 横并列数。"""
    # 注意：OOXML 属性必须带 w: 命名空间前缀（w:w / w:type）；
    # 否则 Word 识别不到列宽，表格塌陷、显示不完整（项目方反馈"表格没有显示完整"的根因）。
    tcpr = f'<w:tcW w:w="{width}" w:type="dxa"/><w:vAlign w:val="center"/>'
    if gridspan:
        tcpr += f'<w:gridSpan w:val="{gridspan}"/>'
    if merge:
        tcpr += f'<w:vMerge w:val="{merge}"/>'
    return (f'<w:tc xmlns:w="{W}"><w:tcPr>{tcpr}</w:tcPr>'
            f'<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:t xml:space="preserve">{_esc(text)}</w:t></w:r></w:p></w:tc>')


def _row(cells: list) -> str:
    tcs = "".join(cells)
    return f'<w:tr xmlns:w="{W}"><w:trPr><w:trHeight w:val="270"/></w:trPr>{tcs}</w:tr>'


def build_risks_tbl(project_id: str = None) -> str:
    """从 risks 表动态拼 SDP 风险表 XML（字符串），完全对标 R121 附录A 项目风险管理表（表32）：
    19 列网格（列宽逐列取自 R121 原文）；
    行0 元信息：项目名称[3] | 值[10] | 软件编号[3] | 值[3]；
    行1 元信息：风险通报方式及频率[3] | 值[3] | 计划更新周期[6] | 双周[1] |
               风险状态最新更新日[3] | 日期[3]；
    行2 分组表头：风险识别[7] | 风险分析[5] | 处理与跟踪[7]；
    行3 15 列子表头（风险描述列为完整文案）；行4 预留空行；数据行 15 列全字段。"""
    import datetime
    db = SessionLocal()
    try:
        proj = db.query(Project).filter(Project.project_id == project_id).first() if project_id else None
        q = db.query(Risk)
        if project_id:
            q = q.filter(Risk.project_id == project_id)
        risks = q.order_by(Risk.risk_id).all()
    finally:
        db.close()

    proj_name = (proj.project_name if proj else "") or project_id or ""
    pid = project_id or ""
    # 风险状态最新更新日：取最新识别日期（对标 R121 数据习惯），无风险则用当天
    dates = [r.identified_date for r in risks if r.identified_date]
    today = max(dates) if dates else datetime.date.today().strftime("%Y-%m-%d")

    # R121 附录A 原文列宽（19 列；原文合计 14425，末列微调至 14400 以适配横向页可用宽）
    col_w = [396, 705, 218, 349, 708, 945, 898, 425, 426, 567, 567, 567,
             1134, 1417, 567, 142, 3118, 567, 709]
    n_grid = len(col_w)
    total_w = sum(col_w)

    class _Cur(object):
        """按列游标生成单元格：累计所跨列的真实宽度（非等宽）。"""

        def __init__(self):
            self.i = 0

        def cell(self, text, span=1):
            w = sum(col_w[self.i:self.i + span])
            self.i += span
            return _cell(text, w, gridspan=span)

    def mkrow(pairs):
        """pairs: [(text, span) ...]，按 R121 列顺序排布。"""
        c = _Cur()
        return _row([c.cell(t, sp) for t, sp in pairs])

    row0 = mkrow([("项目名称", 3), (proj_name, 10), ("软件编号", 3), (pid, 3)])
    row1 = mkrow([
        ("风险通报方式及频率", 3), ("阶段会议交流", 3), ("计划更新周期", 6),
        ("双周", 1), ("风险状态最新更新日", 3), (today, 3),
    ])
    row2 = mkrow([("风险识别", 7), ("风险分析", 5), ("处理与跟踪", 7)])
    sub_headers = [
        ("编号", 1), ("识别日期", 1), ("风险来源", 2), ("风险类别", 1),
        ("风险描述（包含可能导致的后果和可能发生时间区间）", 2),
        ("概率P", 1), ("影响I", 1), ("风险系数", 1),
        ("风险等级", 1), ("优先级", 1), ("风险预防措施", 2), ("责任人", 1),
        ("风险应对措施", 2), ("状态", 1), ("关闭日期", 1),
    ]
    row3 = mkrow(sub_headers)
    # 预留空行（对标 R121 原文表体首空行），span 分布与子表头一致
    row4 = mkrow([("", sp) for _, sp in sub_headers])

    if not risks:
        body = _row([_cell("暂无风险记录", total_w, gridspan=n_grid)])
    else:
        body_rows = []
        for r in risks:
            vals = [
                (r.risk_id or "", 1), (r.identified_date or "", 1), (r.source or "", 2),
                (r.category or "", 1), (r.description or "", 2), (r.probability or "", 1),
                (r.impact_level or "", 1), (r.risk_coef or "", 1), (r.level or "", 1),
                (r.priority or "", 1), (r.prevention or "", 2), (r.owner or "", 1),
                (r.mitigation or "", 2), (r.status or "", 1), (r.closed_date or "", 1),
            ]
            body_rows.append(mkrow([(str(v), sp) for v, sp in vals]))
        body = "".join(body_rows)

    tbl_pr = ('<w:tblPr xmlns:w="%s"><w:tblW w:w="14400" w:type="dxa"/>'
              '<w:tblLayout w:type="fixed"/>'
              '<w:tblBorders>'
              '<w:top w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:left w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:right w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '</w:tblBorders></w:tblPr>' % W)
    tbl_grid = '<w:tblGrid xmlns:w="%s">%s</w:tblGrid>' % (
        W, "".join(f'<w:gridCol w:w="%d"/>' % w for w in col_w))
    return (f'<w:tbl xmlns:w="{W}">{tbl_pr}{tbl_grid}'
            f'{row0}{row1}{row2}{row3}{row4}{body}</w:tbl>')


def build_stakeholder_plan_tbl(rows) -> str:
    """利益相关方参与计划（对标 R121 附录B 表33）：
    12 列两层复合表头（行0：序号 | 活动[跨2] | 利益相关方[跨9]；
    行1：序号(续) | 阶段 | 活动描述 | 9 个角色）；
    角色顺序（项目方确认 9 个）：顾客代表 | 项目经理 | 部门领导 | 项目负责人 |
    系统工程组 | EPG | QAG | CMG | OTG；
    阶段列竖向合并（vMerge）；标记仅 √（不再有 ○）；尾行"说明：√表示计划参与；"。
    列宽取自 R121 原文：[817,1227,4274,648,760,939,939,876,916,916,1071,1017]。
    rows: StakeholderPlan 对象列表（已按 seq 排序）。"""
    role_cols = ["customer_rep", "pm", "dept_lead", "proj_lead", "sys_eng",
                 "epg", "qag", "cmg", "otg"]
    role_headers = ["顾客代表", "项目经理", "部门领导", "项目负责人", "系统工程组",
                    "EPG", "QAG", "CMG", "OTG"]
    # R121 原文列宽（12 列）
    col_w = [817, 1227, 4274, 648, 760, 939, 939, 876, 916, 916, 1071, 1017]
    total_w = sum(col_w)
    n_col = len(col_w)

    # 行0：序号 | 活动[跨2] | 利益相关方[跨9]
    head0 = _row([
        _cell("序号", col_w[0], merge="restart"),
        _cell("活动", col_w[1] + col_w[2], gridspan=2),
        _cell("利益相关方", sum(col_w[3:]), gridspan=9),
    ])
    # 行1：序号(续) | 阶段 | 活动描述 | 9 角色
    head1 = _row(
        [_cell("", col_w[0], merge="continue")]
        + [_cell(h, col_w[i]) for i, h in enumerate(["阶段", "活动描述"] + role_headers, start=1)]
    )

    # 数据行：阶段列按分组竖并（阶段名变化时 restart，否则 continue）
    body_rows = []
    prev_phase = None
    for r in rows:
        phase = (r.phase or "").strip()
        restart = phase != prev_phase
        phase_cell = (_cell(phase, col_w[1], merge="restart") if restart
                      else _cell("", col_w[1], merge="continue"))
        marks = [getattr(r, c) for c in role_cols]
        body_rows.append(_row(
            [_cell(str(r.seq or ""), col_w[0]), phase_cell,
             _cell(r.activity or "", col_w[2])]
            + [_cell((m or "").strip(), col_w[3 + i]) for i, m in enumerate(marks)]
        ))
        prev_phase = phase
    body = "".join(body_rows) if body_rows else _row(
        [_cell("暂无数据", total_w, gridspan=n_col)])

    # 尾行：说明（对标 R121 原文，无 ○）
    note = _row([_cell("说明：√表示计划参与；", total_w, gridspan=n_col)])

    tbl_pr = ('<w:tblPr xmlns:w="%s"><w:tblW w:w="%d" w:type="dxa"/>'
              '<w:tblLayout w:type="fixed"/>'
              '<w:tblBorders>'
              '<w:top w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:left w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:right w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '</w:tblBorders></w:tblPr>' % (W, total_w))
    tbl_grid = '<w:tblGrid xmlns:w="%s">%s</w:tblGrid>' % (
        W, "".join('<w:gridCol w:w="%d"/>' % w for w in col_w))
    return (f'<w:tbl xmlns:w="{W}">{tbl_pr}{tbl_grid}'
            f'{head0}{head1}{body}{note}</w:tbl>')


def build_meeting_plan_tbl(project_id: str = None) -> str:
    """会议计划表（-> {{table.meeting_plan}}）：序号|会议类型|会议组织者|会议时机/时间。
    数据来源：meeting_plan 表（项目方要求：不再写死在模板里，改从数据库读取）。
    列宽逐列取自 R121 表14（合计 9186，在纵向页可用宽内）。"""
    db = SessionLocal()
    try:
        q = db.query(MeetingPlan)
        if project_id:
            q = q.filter(MeetingPlan.project_id == project_id)
        rows = q.order_by(MeetingPlan.seq).all()
    finally:
        db.close()
    headers = ["序号", "会议类型", "会议组织者", "会议时机/时间"]
    col_w = [750, 3364, 1485, 3587]
    data = [[str(r.seq or ""), r.meeting_type or "", r.organizer or "",
             r.timing or ""] for r in rows]
    return _simple_tbl(headers, col_w, data, empty_hint="暂无会议计划")


def build_hw_env_tbl(rows) -> str:
    """硬件环境资源（-> {{table.hw_env_res}}）。
    7 列对标 R121 表31：序号|资源名称|型号/图号/代号/版本/参数|用途|资源责任人|获取时间|跟踪情况。
    列宽取 R121 原文 [511,1347,1314,2024,1572,1262,1489] 按纵向页可用宽等比缩放，总宽 9400。"""
    headers = ["序号", "资源名称", "型号 / 图号 / 代号 / 版本 / 参数",
               "用途", "资源责任人", "获取时间", "跟踪情况"]
    col_w = [505, 1330, 1298, 1999, 1552, 1246, 1470]
    data = [[str(i), (r.name or ""), (r.spec or ""), (r.usage or ""),
             (r.owner or ""), "", ""] for i, r in enumerate(rows, start=1)]
    return _simple_tbl(headers, col_w, data)


def build_sw_env_tbl(rows) -> str:
    """软件环境资源（-> {{table.sw_env_res}}）。
    7 列对标 R121 表32：序号|软件名称|型号/图号/代号/版本/参数|用途|资源责任人|获取时间|跟踪情况。
    列宽取 R121 原文 [557,1545,1110,2683,992,1407,1346] 按纵向页可用宽等比缩放，总宽 9400。"""
    headers = ["序号", "软件名称", "型号 / 图号 / 代号 / 版本 / 参数",
               "用途", "资源责任人", "获取时间", "跟踪情况"]
    col_w = [543, 1506, 1082, 2616, 967, 1371, 1315]
    data = [[str(i), (r.name or ""), (r.spec or ""), (r.usage or ""),
             (r.owner or ""), "", ""] for i, r in enumerate(rows, start=1)]
    return _simple_tbl(headers, col_w, data)


# 数据管理表固定 33 行（逐字对标 R121 附录C TABLE 34/35/36），管理负责人按数据类别映射
# 元组：(数据类别, 内容说明, 数据形式, 存储方式, 管理要求, 管理方法, 收集时机, 负责人类别)
# 负责人类别：sw=软件负责人 qa=QA cm=配置管理 team=项目组人员 sw_cm=软件负责人(R121特例)
_DATA_MGMT_ROWS = [
    ("策划", "估计理由、假设表", "电子文档", "开发库", "安全", "SVN", "策划阶段", "sw"),
    ("策划", "外部资源跟踪表", "电子文档", "开发库", "安全", "SVN", "策划阶段", "sw"),
    ("策划", "估算汇总表", "电子文档", "开发库", "安全", "SVN", "策划阶段", "sw"),
    ("策划", "软件风险管理表", "电子文档", "开发库", "安全", "SVN", "阶段结束", "sw"),
    ("策划", "利益相关方参与表", "电子文档", "开发库", "安全", "SVN", "策划阶段", "sw"),
    ("监控", "任务分配表", "电子文档", "开发库", "安全", "SVN", "阶段结束", "sw"),
    ("监控", "软件会议纪要", "电子文档", "开发库", "安全", "SVN", "会议结束", "sw"),
    ("监控", "问题跟踪汇总表", "电子文档", "开发库", "安全", "SVN", "不定时", "sw"),
    ("需求", "需求跟踪矩阵", "电子文档", "开发库", "安全", "SVN", "每阶段", "sw"),
    ("需求", "需求状态表", "电子文档", "开发库", "安全", "SVN", "不定时", "sw"),
    ("监控", "评审报告", "电子文档", "开发库", "安全", "SVN", "评审结束", "sw"),
    ("监控", "项目通告", "电子文档", "开发库", "安全", "SVN", "签字完成", "sw"),
    ("监控", "阶段报告", "电子文档", "开发库", "安全", "SVN", "阶段结束", "sw"),
    ("测量分析", "软件测量分析报告", "电子文档", "开发库", "安全", "SVN", "阶段结束", "cm"),
    ("质量保证", "QA审查单", "电子文档", "开发库", "安全", "SVN", "阶段结束", "qa"),
    ("质量保证", "不符合项报告", "电子文档", "开发库", "安全", "SVN", "阶段结束", "qa"),
    ("质量保证", "不符合项汇总表", "电子文档", "开发库", "安全", "SVN", "阶段结束", "qa"),
    ("质量保证", "质量保证工作报告", "电子文档", "开发库", "安全", "SVN", "阶段结束", "qa"),
    ("质量保证", "质量保证报告", "电子文档", "开发库", "安全", "SVN", "阶段结束", "qa"),
    ("配置管理", "入库申请单", "电子文档", "开发库", "安全", "SVN", "审批通过", "cm"),
    ("配置管理", "变更申请单", "电子文档", "开发库", "安全", "SVN", "审批通过", "cm"),
    ("配置管理", "出库申请单", "电子文档", "开发库", "安全", "SVN", "审批通过", "cm"),
    ("配置管理", "基线发布申请单", "电子文档", "开发库", "安全", "SVN", "审批通过", "cm"),
    ("配置管理", "功能审核单", "电子文档", "开发库", "安全", "SVN", "审批通过", "cm"),
    ("配置管理", "物理审核单", "电子文档", "开发库", "安全", "SVN", "审批通过", "cm"),
    ("配置管理", "配置状态报告", "电子文档", "开发库", "安全", "SVN", "阶段结束前", "cm"),
    ("配置管理", "基线状态列表", "电子文档", "开发库", "安全", "SVN", "阶段结束前", "cm"),
    ("配置管理", "配置管理报告", "电子文档", "开发库", "安全", "SVN", "结项前", "cm"),
    ("配置管理", "软件产品发布/申请单", "电子文档", "开发库", "安全", "SVN", "结项前", "sw"),
    ("配置管理", "软件项目通告", "电子文档", "开发库", "安全", "SVN", "阶段结束", "cm"),
    ("监控", "个人周报", "电子文档", "开发库", "安全", "SVN", "阶段结束", "sw"),
    ("相关类别", "项目活动中产生的其它数据管理项", "纸质/电子文档", "开发库/资料室", "安全", "SVN/专人管理", "不定时", "team"),
    ("策划", "进度表", "电子文档", "开发库", "安全", "SVN", "每阶段", "sw"),
]


def _simple_tbl(headers: list, col_w: list, rows: list, empty_hint: str = "暂无数据") -> str:
    """通用表格：headers 表头 + col_w 列宽 + rows(每行为单元格文本列表)，空数据兜底提示行。"""
    total = sum(col_w)
    head = _row([_cell(h, col_w[i]) for i, h in enumerate(headers)])
    if not rows:
        body = _row([_cell(empty_hint, total, gridspan=len(headers))])
    else:
        body = "".join(_row([_cell(c, col_w[i]) for i, c in enumerate(r)]) for r in rows)
    tbl_pr = ('<w:tblPr xmlns:w="%s"><w:tblW w:w="%d" w:type="dxa"/>'
              '<w:tblLayout w:type="fixed"/>'
              '<w:tblBorders>'
              '<w:top w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:left w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:right w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '</w:tblBorders></w:tblPr>' % (W, total))
    tbl_grid = '<w:tblGrid xmlns:w="%s">%s</w:tblGrid>' % (
        W, "".join('<w:gridCol w:w="%d"/>' % w for w in col_w))
    return f'<w:tbl xmlns:w="{W}">{tbl_pr}{tbl_grid}{head}{body}</w:tbl>'


def build_schedule_tbl(rows) -> str:
    """工作量估算/进度表（-> {{table.schedule}}），完全对标 R105/R121：
    6 列 + 合计行；"调整后总工作量"= 总工作量四舍五入取整（R105：14.5→15、76.5→77）。"""
    # 项目方 2026-09-02：表7「各阶段工作量估计」单位对标 R121 口径，统一用"人时"
    headers = ["开发 / 阶段", "阶段 / 比例", "工程类工作量 / （人时）",
               "管理类工作量 / （人时）", "总工作量 / （人时）", "调整后总工作量（人时）"]
    # 列宽逐列取自 R121 表12（合计 8857，在纵向页可用宽内）
    col_w = [911, 709, 2125, 2268, 1305, 1539]
    data = []
    tot_eng = tot_mgr = tot_all = 0.0
    for r in rows:
        eng = float(r.eng_md or 0)
        mgr = float(r.mgr_md or 0)
        tot_eng += eng
        tot_mgr += mgr
        tot_all += eng + mgr
        adj = int(eng + mgr + 0.5)
        data.append([r.phase_name, r.ratio or "", _fmt(eng), _fmt(mgr),
                     _fmt(eng + mgr), str(adj)])
    data.append(["合计", "100%", _fmt(tot_eng), _fmt(tot_mgr),
                 _fmt(tot_all), str(int(tot_all + 0.5))])
    return _simple_tbl(headers, col_w, data)


def build_stakeholders_tbl(rows) -> str:
    """A14 利益相关方清单表（-> {{table.stakeholders}}）：角色|姓名/单位|职责|参与阶段。"""
    headers = ["角色", "姓名/单位", "职责", "参与阶段"]
    # 控制在纵向页可用宽（约 9468）之内，合计 9468
    col_w = [2400, 1900, 3500, 1668]
    data = [[r.role or "", r.name or "", r.responsibility or "", r.join_phase or ""] for r in rows]
    return _simple_tbl(headers, col_w, data, empty_hint="暂无相关方，请在项目策划页录入")


def build_data_mgmt_tbl(proj) -> str:
    """数据管理表（逐字对标 R121 附录C 33 行）：管理负责人按数据类别映射项目角色。
    策划/监控/需求 -> 软件负责人(proj.owner)；测量分析 -> 配置管理者（R121 由 CM 兼）；
    质量保证 -> QA(proj.qa)；配置管理 -> 配置管理(proj.config_manager)；
    软件产品发布/申请单 -> 软件负责人（R121 特例）；相关类别 -> 项目组人员。管理方法列=SVN。"""
    headers = ["序号", "数据类别", "内容说明", "数据形式", "存储方式",
               "数据管理要求（秘密、安全）", "管理负责人", "管理方法", "存储期限", "收集时机"]
    # 列宽对标 R121 附录C 原文并按横向页可用宽（约 14406）微调，合计 14400
    col_w = [567, 1206, 1984, 1134, 1001, 1834, 1386, 1733, 1875, 1893]
    owner_map = {
        "sw": (proj.owner if proj else '') or '软件负责人',
        "qa": (proj.qa if proj else '') or 'QA',
        "cm": (proj.config_manager if proj else '') or '配置管理',
        "team": "项目组人员",
    }
    data = []
    for i, (cat, name, form, store, req, method, timing, who) in enumerate(_DATA_MGMT_ROWS, start=1):
        data.append([str(i), cat, name, form, store, req,
                     owner_map[who], method, "按规定", timing])
    return _simple_tbl(headers, col_w, data)


def build_doc_scale_tbl(rows, kind: str = "est") -> str:
    """文档规模估计/复用表（-> {{table.doc_scale_est}}/{{table.doc_scale_reuse}}）。
    完全对标 R121：估计表=序号|文档名称|规模估计（A4页）|备注+总计行；
    复用表=序号|文档名称|规模估计（A4页）|复用页数|有效页数。"""
    if kind == "reuse":
        headers = ["序号", "文档名称", "规模估计（A4页）", "复用页数", "有效页数"]
        # 列宽逐列取自 R121 表08（合计 9416，在纵向页可用宽内）
        col_w = [891, 3235, 1794, 1748, 1748]
        data = []
        for i, r in enumerate(rows, start=1):
            est = r.pages_new or 0
            reuse = r.pages_reuse or 0
            data.append([str(i), r.name, str(est), str(reuse), str(est - reuse)])
        return _simple_tbl(headers, col_w, data)
    headers = ["序号", "文档名称", "规模估计（A4页）", "备注"]
    # 列宽逐列取自 R121 表07（合计 8430，在纵向页可用宽内）
    col_w = [980, 3556, 1972, 1922]
    data = []
    total = 0
    for i, r in enumerate(rows, start=1):
        pages = r.pages_new or 0
        total += pages
        data.append([str(i), r.name, str(pages), ""])
    data.append(["", "总计", str(total), ""])
    return _simple_tbl(headers, col_w, data)


def build_code_scale_tbl(project_id: str, kind: str = "est") -> str:
    """代码规模估计/复用表（-> {{table.code_scale_est}}/{{table.code_scale_reuse}}）。
    完全对标 R121：部件|规模估计（行）|备注（备注列业务数据暂无，留空）。"""
    from backend.db.session import SessionLocal
    from backend.dao import code_scale_dao
    db = SessionLocal()
    try:
        rows = code_scale_dao.CodeScaleDao.list_by_project(db, project_id)
    finally:
        db.close()
    headers = ["部件", "规模估计（行）", "备注"]
    # 控制在纵向页可用宽（约 9468）之内，合计 9400
    col_w = [3000, 3200, 3200]
    key = "est_loc" if kind == "est" else "reuse_loc"
    data = [[r.comp, str(getattr(r, key) or 0), ""] for r in rows]
    return _simple_tbl(headers, col_w, data)


def _fmt(v) -> str:
    """浮点格式化：去多余 .0。"""
    if v is None:
        return ""
    try:
        f = float(v)
        return str(int(f)) if f == int(f) else ("%.2f" % f)
    except (ValueError, TypeError):
        return str(v)
