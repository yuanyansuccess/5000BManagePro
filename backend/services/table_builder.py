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

# 字号常量（OOXML sz = 半磅值）
SZ_XIAOSI = 24      # 小四 = 12pt（表 2/5/7/13/19/21/23/24/25 正文表格）
SZ_WUHAO = 21       # 五号 = 10.5pt（附录 A 风险表 / 附录 B 利益相关方 / 表C.1 数据管理）

import re as _re
_ZH = r'\u4e00-\u9fff\u3000-\u303f\uff00-\uffef'
_ZH_CLS = r'\u4e00-\u9fff'
_PUNCT = r'\u3000-\u303f\uff00-\uffef，。；：、（）《》【】“”——'


def clean_space(text) -> str:
    """袁总 2026-09-04（多轮反复反馈"表格文字有空格看不清"）：
    彻底清除单元格文本中的空格——
      1) 首尾空白、连续空白折叠；
      2) 中文与中文之间、中文与中文标点之间的空格（如"袁 燕"→"袁燕"、
         "（ R105 ）"→"（R105）"）一律删除；
      3) 保留英文单词间必要的单空格（如"Keil 5"、"Windows 7"、"Stm32CubeMX V6.14"），
         避免把英文型号/版本号黏连成不可读串——这些英文串两侧不含中文。
    反复执行至稳定，处理"中 文 名"这类多点空格。"""
    s = str(text if text is not None else "")
    prev = None
    for _ in range(4):
        s = _re.sub(r'\s+', ' ', s).strip()
        # 中文/中文标点 之间的空格
        s = _re.sub(r'(?<=[%s])\s+(?=[%s])' % (_ZH, _ZH), '', s)
        s = _re.sub(r'(?<=[%s])\s+(?=[%s])' % (_ZH_CLS, _PUNCT), '', s)
        s = _re.sub(r'(?<=[%s])\s+(?=[%s])' % (_PUNCT, _ZH_CLS), '', s)
        s = _re.sub(r'(?<=[%s])\s+(?=[%s])' % (_PUNCT, _PUNCT), '', s)
        # 袁总 2026-09-04（表13 基线列表"功能基线 R105"空格）：删【中文或中文标点】后的空格
        # （无论后跟中文还是英文编号），如"功能基线 R105"→"功能基线R105"、
        # "R105_0201、 R105_0202"→"R105_0201、R105_0202"、"说明： Windows"→"说明：Windows"。
        # 仅保留【拉丁字母/数字单词间】空格（如"Keil 5"、"Windows 7"、"Stm32CubeMX V6.14"），
        # 因其前是拉丁字符而非中文，不被本规则匹配，避免型号黏连。
        s = _re.sub(r'(?<=[%s])\s+' % _ZH, '', s)
        if s == prev:
            break
        prev = s
    return s.strip()


def _esc(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _cell(text: str, width: int, merge: str = None, gridspan: int = None,
         nowrap: bool = False, size: int = None) -> str:
    """单个单元格。merge: 'restart'/'continue'（vMerge 竖并）；gridspan: 横并列数。
    nowrap=True：加 <w:noWrap/>，单元格内不自动换行（防"序号"被分两行）；
                  超长内容会溢出右列（表头短字段无影响）。
    size：OOXML sz 值（半磅，24=小四 12pt、21=五号 10.5pt、20=8 号），默认 None=不指定 rPr/sz。
    袁总 2026-09-04（多轮反复反馈）：
      - 所有表格文字统一走 clean_space() 去空格（中文间空格一律删除）；
      - 所有表格文字统一居中（水平 jc=center + 垂直 vAlign=center）——已具备；
      - 附录 A/B/C.1 传 size=SZ_WUHAO(21)，正文表格传 size=SZ_XIAOSI(24)。"""
    text = clean_space(text)
    # 注意：OOXML 属性必须带 w: 命名空间前缀（w:w / w:type）；
    # 否则 Word 识别不到列宽，表格塌陷、显示不完整（项目方反馈"表格没有显示完整"的根因）。
    tcpr = f'<w:tcW w:w="{width}" w:type="dxa"/><w:vAlign w:val="center"/>'
    if gridspan:
        tcpr += f'<w:gridSpan w:val="{gridspan}"/>'
    if merge:
        tcpr += f'<w:vMerge w:val="{merge}"/>'
    if nowrap:
        tcpr += '<w:noWrap/>'
    rpr = ''
    if size:
        rpr = f'<w:rPr><w:sz w:val="{size}"/><w:szCs w:val="{size}"/></w:rPr>'
    return (f'<w:tc xmlns:w="{W}"><w:tcPr>{tcpr}</w:tcPr>'
            f'<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r>{rpr}<w:t xml:space="preserve">{_esc(text)}</w:t></w:r></w:p></w:tc>')


def _row(cells: list, header: bool = False) -> str:
    """header=True 时该行加 <w:tblHeader/>：跨页时 Word 自动在每页顶部重复表头
    （即"续表"效果，对标 R121 数据管理表拆页每页带表头的呈现，且行数增减自动适应）。"""
    tcs = "".join(cells)
    hdr = '<w:tblHeader/>' if header else ''
    return f'<w:tr xmlns:w="{W}"><w:trPr>{hdr}<w:trHeight w:val="270"/></w:trPr>{tcs}</w:tr>'


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

    # 袁总 2026-09-04（多轮反复反馈"附录 A 风险表列窄、字看不清"）——根因定位：
    # 此前用 tblLayout="autofit"，Word 直接忽略 gridCol/tcW 而按内容重算列宽，
    # 导致长文本列吃掉宽度、短列被压成竖排。R121_SDP_V1.02 实测为
    # tblLayout="fixed" + tblW=14425 + 下列 19 列原始列宽（合计 14425 > 页宽 9026，
    # Word 在 fixed 布局下按比例整表缩放至页宽，呈现与 V1.02 完全一致）。
    # 逐列照抄 V1.02 gridCol，绝不自行重排。
    col_w = [396, 705, 218, 349, 708, 945, 898, 425, 426, 567, 567, 567,
             1134, 1417, 567, 142, 3118, 567, 709]
    n_grid = len(col_w)
    total_w = sum(col_w)          # 14425（与 V1.02 tblW 一致）

    class _Cur(object):
        """按列游标生成单元格：累计所跨列的真实宽度（非等宽）。"""

        def __init__(self):
            self.i = 0

        def cell(self, text, span=1, nowrap=False, size=None):
            w = sum(col_w[self.i:self.i + span])
            self.i += span
            return _cell(text, w, gridspan=span, nowrap=nowrap, size=size)

    def mkrow(pairs, nowrap=False, size=None):
        """pairs: [(text, span) ...]，按 V1.02 列顺序排布。
        袁总 2026-09-04：nowrap 默认关闭——<w:noWrap/> 会让长文本（风险描述/应对措施）
        溢出单元格被相邻列遮挡，正是"文字看不清"的根因之一；改为自动换行完整显示。"""
        c = _Cur()
        return _row([c.cell(t, sp, nowrap=nowrap, size=size) for t, sp in pairs])

    # 袁总 2026-09-04：字号改为五号（sz=21，对标 V1.02 #33 实测 sz=21），
    # 不再用 20(8 号)——配合 fixed 布局 + 原列宽，文字清晰且不再竖排。
    _sz = SZ_WUHAO
    row0 = mkrow([("项目名称", 3), (proj_name, 10), ("软件编号", 3), (pid, 3)], size=_sz)
    row1 = mkrow([
        ("风险通报方式及频率", 3), ("阶段会议交流", 3), ("计划更新周期", 6),
        ("双周", 1), ("风险状态最新更新日", 3), (today, 3),
    ], size=_sz)
    row2 = mkrow([("风险识别", 7), ("风险分析", 5), ("处理与跟踪", 7)], size=_sz)
    sub_headers = [
        ("编号", 1), ("识别日期", 1), ("风险来源", 2), ("风险类别", 1),
        ("风险描述（包含可能导致的后果和可能发生时间区间）", 2),
        ("概率P", 1), ("影响I", 1), ("风险系数", 1),
        ("风险等级", 1), ("优先级", 1), ("风险预防措施", 2), ("责任人", 1),
        ("风险应对措施", 2), ("状态", 1), ("关闭日期", 1),
    ]
    row3 = mkrow(sub_headers, size=_sz)
    # 预留空行（对标 R121 原文表体首空行），span 分布与子表头一致
    row4 = mkrow([("", sp) for _, sp in sub_headers], size=_sz)  # 预留空行不加 nowrap（避免空 cell 撑列）

    if not risks:
        body = _row([_cell("暂无风险记录", total_w, gridspan=n_grid, size=_sz)])
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
            body_rows.append(mkrow([(str(v), sp) for v, sp in vals], size=_sz))
        body = "".join(body_rows)

    # 袁总 2026-09-04 根因修复：autofit → fixed（V1.02 实测），tblW=14425 与列宽合计一致
    tbl_pr = ('<w:tblPr xmlns:w="%s"><w:tblW w:w="%d" w:type="dxa"/>'
              '<w:jc w:val="center"/>'
              '<w:tblLayout w:type="fixed"/>'
              '<w:tblBorders>'
              '<w:top w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
              '<w:left w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
              '<w:bottom w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
              '<w:right w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
              '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '</w:tblBorders></w:tblPr>' % (W, total_w))
    tbl_grid = '<w:tblGrid xmlns:w="%s">%s</w:tblGrid>' % (
        W, "".join(f'<w:gridCol w:w="%d"/>' % w for w in col_w))
    return _PAGE_BEFORE + (f'<w:tbl xmlns:w="{W}">{tbl_pr}{tbl_grid}'
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

    # 袁总 2026-09-04：字号统一五号（sz=21，对标 V1.02 #34 实测）；
    # 去掉 nowrap（避免长活动描述溢出被遮挡）；文字统一居中、去空格（_cell 内处理）。
    _sz = SZ_WUHAO
    # 行0：序号 | 活动[跨2] | 利益相关方[跨9]
    head0 = _row([
        _cell("序号", col_w[0], merge="restart", size=_sz),
        _cell("活动", col_w[1] + col_w[2], gridspan=2, size=_sz),
        _cell("利益相关方", sum(col_w[3:]), gridspan=9, size=_sz),
    ])
    # 行1：序号(续) | 阶段 | 活动描述 | 9 角色
    head1 = _row(
        [_cell("", col_w[0], merge="continue", size=_sz)]
        + [_cell(h, col_w[i], size=_sz) for i, h in enumerate(["阶段", "活动描述"] + role_headers, start=1)]
    )

    # 数据行：阶段列按分组竖并（阶段名变化时 restart，否则 continue）
    body_rows = []
    prev_phase = None
    for r in rows:
        phase = (r.phase or "").strip()
        restart = phase != prev_phase
        phase_cell = (_cell(phase, col_w[1], merge="restart", size=_sz) if restart
                      else _cell("", col_w[1], merge="continue", size=_sz))
        marks = [getattr(r, c) for c in role_cols]
        body_rows.append(_row(
            [_cell(str(r.seq or ""), col_w[0], size=_sz), phase_cell,
             _cell(r.activity or "", col_w[2], size=_sz)]
            + [_cell((m or "").strip(), col_w[3 + i], size=_sz) for i, m in enumerate(marks)]
        ))
        prev_phase = phase
    body = "".join(body_rows) if body_rows else _row(
        [_cell("暂无数据", total_w, gridspan=n_col, size=_sz)])

    # 尾行：说明（对标 R121 原文，无 ○）
    note = _row([_cell("说明：√表示计划参与；", total_w, gridspan=n_col, size=_sz)])

    # 袁总 2026-09-04 根因修复：autofit → fixed（V1.02 实测），整表居中
    tbl_pr = ('<w:tblPr xmlns:w="%s"><w:tblW w:w="%d" w:type="dxa"/>'
              '<w:jc w:val="center"/>'
              '<w:tblLayout w:type="fixed"/>'
              '<w:tblBorders>'
              '<w:top w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
              '<w:left w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
              '<w:bottom w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
              '<w:right w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
              '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '</w:tblBorders></w:tblPr>' % (W, total_w))
    tbl_grid = '<w:tblGrid xmlns:w="%s">%s</w:tblGrid>' % (
        W, "".join('<w:gridCol w:w="%d"/>' % w for w in col_w))
    return _PAGE_BEFORE + (f'<w:tbl xmlns:w="{W}">{tbl_pr}{tbl_grid}'
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
    # 袁总 2026-09-03：表7 会议计划超页边，整表居中
    return _simple_tbl(headers, col_w, data, empty_hint="暂无会议计划", align="center")


def build_hw_env_tbl(rows) -> str:
    """硬件环境资源（-> {{table.hw_env_res}}）。
    7 列对标 R121 表31：序号|资源名称|型号/图号/代号/版本/参数|用途|资源责任人|获取时间|跟踪情况。
    列宽取 R121 原文 [511,1347,1314,2024,1572,1262,1489] 按纵向页可用宽等比缩放，总宽 9400。"""
    headers = ["序号", "资源名称", "型号/图号/代号/版本/参数",
               "用途", "资源责任人", "获取时间", "跟踪情况"]
    # 列宽逐列取 R121_SDP_V1.02.docx 表31 原文（袁总 2026-09-02 对标指示），
    # 配合 tblLayout=autofit，Word 按内容自动微调
    # 袁总 2026-09-03：表头斜杠空格去除（R121 原版紧凑格式）
    col_w = [511, 1347, 1314, 2024, 1572, 1262, 1489]
    data = [[str(i), (r.name or ""), (r.spec or ""), (r.usage or ""),
             (r.owner or ""), "", ""] for i, r in enumerate(rows, start=1)]
    return _simple_tbl(headers, col_w, data)


def build_sw_env_tbl(rows) -> str:
    """软件环境资源（-> {{table.sw_env_res}}）。
    7 列对标 R121 表32：序号|软件名称|型号/图号/代号/版本/参数|用途|资源责任人|获取时间|跟踪情况。
    列宽取 R121 原文 [557,1545,1110,2683,992,1407,1346] 按纵向页可用宽等比缩放，总宽 9400。"""
    headers = ["序号", "软件名称", "型号/图号/代号/版本/参数",
               "用途", "资源责任人", "获取时间", "跟踪情况"]
    # 列宽逐列取 R121_SDP_V1.02.docx 表32 原文（袁总 2026-09-02 对标指示）
    # 袁总 2026-09-03：表头斜杠空格去除（R121 原版紧凑格式）
    col_w = [557, 1545, 1110, 2683, 992, 1407, 1346]
    data = [[str(i), (r.name or ""), (r.spec or ""), (r.usage or ""),
             (r.owner or ""), "", ""] for i, r in enumerate(rows, start=1)]
    # 袁总 2026-09-03：表25 软件环境超页边，整表居中
    return _simple_tbl(headers, col_w, data, align="center")


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


def _simple_tbl(headers: list, col_w: list, rows: list, empty_hint: str = "暂无数据",
                align: str = None, size: int = None) -> str:
    """通用表格：headers 表头 + col_w 列宽 + rows(每行为单元格文本列表)，空数据兜底提示行。
    align：表格整体水平对齐，"center"/"left"/"right"/None（默认 None=左对齐）。
    size：OOXML sz（半磅）24=小四(12pt) / 21=五号(10.5pt)；默认小四。
    袁总 2026-09-04（反复反馈"表格文字看不清"）根因修复，本处有两处致命旧逻辑：
      ① 列数 >= 5 自动降为 sz=12（6 号字）——字小到看不清，已删除；
      ② tblLayout="autofit" —— Word 忽略 gridCol/tcW 按内容重算列宽，
         导致列被压窄、文字竖排/截断，已改为 fixed（R121_SDP_V1.02 实测值）。
    现默认：小四(sz=24) + fixed 布局 + 文字水平垂直居中 + clean_space 去空格。
    项目方 2026-09-02：表21 软件进度表"整个表格要居中"——通过 tblPr/w:jc 实现（OOXML 合法子元素）。"""
    if size is None:
        # 袁总 2026-09-04（表7/9「字体应统一小四」）：正文表格一律小四(24)，
        # 不再按列宽自适应（否则同一张表出现 21/22/24 混排，袁总明确反对）。
        # 现 tblLayout=fixed，列宽固定，主体列宽均≥700dxa 足够横排小四汉字
        # （实测 Word 渲染无竖排）；附录 A/B/C.1 仍由调用方显式传 size=21 保持五号。
        def _col_size(w):
            return SZ_XIAOSI

        def _sz_for(i):
            return _col_size(col_w[i])
        total = sum(col_w)
        head = _row([_cell(h, col_w[i], size=_sz_for(i)) for i, h in enumerate(headers)], header=True)
        if not rows:
            body = _row([_cell(empty_hint, total, gridspan=len(headers), size=SZ_WUHAO)])
        else:
            body = "".join(_row([_cell(c, col_w[i], size=_sz_for(i)) for i, c in enumerate(r)]) for r in rows)
    else:
        total = sum(col_w)
        head = _row([_cell(h, col_w[i], size=size) for i, h in enumerate(headers)], header=True)
        if not rows:
            body = _row([_cell(empty_hint, total, gridspan=len(headers), size=size)])
        else:
            body = "".join(_row([_cell(c, col_w[i], size=size) for i, c in enumerate(r)]) for r in rows)
    jc_xml = ('<w:jc w:val="%s"/>' % align) if align else ''
    tbl_pr = ('<w:tblPr xmlns:w="%s"><w:tblW w:w="%d" w:type="dxa"/>'
              '%s'
              '<w:tblLayout w:type="fixed"/>'
              '<w:tblBorders>'
              '<w:top w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
              '<w:left w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
              '<w:bottom w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
              '<w:right w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
              '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '</w:tblBorders></w:tblPr>' % (W, total, jc_xml))
    tbl_grid = '<w:tblGrid xmlns:w="%s">%s</w:tblGrid>' % (
        W, "".join('<w:gridCol w:w="%d"/>' % w for w in col_w))
    return f'<w:tbl xmlns:w="{W}">{tbl_pr}{tbl_grid}{head}{body}</w:tbl>'


def build_schedule_tbl(rows) -> str:
    """工作量估算/进度表（-> {{table.schedule}}），完全对标 R105/R121：
    6 列 + 合计行；"调整后总工作量"= 总工作量四舍五入取整（R105：14.5→15、76.5→77）。"""
    # 项目方 2026-09-02：表7「各阶段工作量估计」单位对标 R121 口径，统一用"人时"
    # 袁总 2026-09-03（第三十九轮）：表头逐字对标 R121 表#12——紧凑格式
    # 无斜杠无空格（'开发阶段'/'阶段比例'/'工程类工作量（人时）'...），
    # 此前'开发 / 阶段'等斜杠空格正是袁总点名的"表格空格"。
    headers = ["开发阶段", "阶段比例", "工程类工作量（人时）",
               "管理类工作量（人时）", "总工作量（人时）", "调整后总工作量（人时）"]
    # 袁总 2026-09-04：列宽恢复【R121_SDP_V1.02 表#12 原始 gridCol】
    # （dump 取证 [911,709,2125,2268,1305,1539]，合计 8857）。
    # 此前"加宽第 1 列防竖排"是治标——真正的根因是 tblLayout=autofit 让 Word
    # 忽略列宽重算；现在 _simple_tbl 已改 fixed + 小四，按原列宽即可正常横排。
    col_w = [911, 709, 2125, 2268, 1305, 1539]
    data = []
    tot_eng = tot_mgr = tot_all = 0.0
    for r in rows:
        eng = float(r.eng_md or 0)
        mgr = float(r.mgr_md or 0)
        # 项目方 2026-09-02：只显示【有工作量】的阶段，过滤 0 值阶段。
        # （R105 的"项目启动/项目策划"两阶段工作量为 0，显示出来会被误判为数据缺失）
        if eng <= 0 and mgr <= 0:
            continue
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
    # 袁总 2026-09-03：表9 利益相关方超页边，整表居中
    return _simple_tbl(headers, col_w, data, empty_hint="暂无相关方，请在项目策划页录入", align="center")


def build_data_mgmt_tbl(proj) -> str:
    """数据管理表（逐字对标 R121 附录C 33 行）：管理负责人按数据类别映射项目角色。
    策划/监控/需求 -> 软件负责人(proj.owner)；测量分析 -> 配置管理者（R121 由 CM 兼）；
    质量保证 -> QA(proj.qa)；配置管理 -> 配置管理(proj.config_manager)；
    软件产品发布/申请单 -> 软件负责人（R121 特例）；相关类别 -> 项目组人员。管理方法列=SVN。
    袁总 2026-09-03：在表前加居中标题段落"表C.1 数据管理表"（之前是模板硬编码"附录C数据管理表"，
    现在改为生成时输出"表C.1 数据管理表"标题，让标题与续表"表C.1（续）"对齐）。"""
    # 袁总 2026-09-03：在表前插入"表C.1 数据管理表"标题段落（居中、粗体小四号）
    title_para = (
        '<w:p>'
        '<w:pPr><w:jc w:val="center"/>'
        '<w:rPr><w:rFonts w:ascii="宋体" w:hAnsi="宋体" w:hint="eastAsia"/>'
        '<w:b/><w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr></w:pPr>'
        '<w:r><w:rPr><w:rFonts w:ascii="宋体" w:hAnsi="宋体" w:hint="eastAsia"/>'
        '<w:b/><w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr>'
        '<w:t>表C.1 数据管理表</w:t></w:r></w:p>'
    )
    # 袁总 2026-09-04（"附录B 单独一页"）：附录 C 同样强制新页开始
    title_para = _PAGE_BEFORE + title_para
    headers = ["序号", "数据类别", "内容说明", "数据形式", "存储方式",
               "数据管理要求（秘密、安全）", "管理负责人", "管理方法", "存储期限", "收集时机"]
    # 袁总 2026-09-04：列宽改为【逐列照抄 R121_SDP_V1.02 表#35 原始 gridCol】
    # （dump 取证 [567,1206,1984,1134,1001,1834,1386,1733,1875,1893]，合计 14613）。
    # 此前用的 [549,1088,...] 是早期缩放估算值，列比例与 V1.02 有偏差 → 显示不一致。
    # 配合下方 tblLayout=fixed（V1.02 实测），Word 按比例整表缩放，呈现与 V1.02 一致。
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
    # 袁总 2026-09-04（反复反馈"表C.1（续）位置放错"）：
    # 逐字对标 R121_SDP_V1.02 实测结构——33 行数据被拆为【3 张独立分表】，
    # 行数分布 15 / 13 / 5（V1.02 表#35/#36/#37 实测），且"表C.1（续）"是
    # 位于【每个续表之前】的独立居中段落：
    #   表C.1 数据管理表（标题段）
    #   [表1: 表头 + 15 行]
    #   表C.1（续）（标题段）
    #   [表2: 表头 + 13 行]
    #   表C.1（续）（标题段）
    #   [表3: 表头 + 5 行]
    # 此前拆 2 张且续标题位置与 V1.02 不符，本次按实测分段点 [15, 28] 精确对齐。
    # 字号用五号（sz=21，袁总 2026-09-04 明确要求；V1.02 原为 22=11pt）。
    head_row = list(headers)          # 表头首列固定为"序号"
    return _split_data_mgmt_3parts(title_para, head_row, col_w, data,
                                   split_at=(15, 28), size=SZ_WUHAO)


def _split_data_mgmt_3parts(title_para, head_row, col_w, data, split_at=(15, 28), size=21):
    """按 R121_SDP_V1.02 实测拆为 3 张分表；"表C.1（续）"作为独立段落放在
    每个续表【之前】。

    袁总 2026-09-04（"附录续表的位置应该在换页后的位置出现，你这出现的位置不合理"）：
    此前仅在第 2→3 张之间加分页符，第 1→2 张之间【无分页符】——Word 排到第 2 张表时
    若当前页剩余空间不足，"表C.1（续）"标题会孤零零留在页底、表格被甩到下一页，
    正是袁总说的"位置不合理"。
    现改为【每个续表前都加硬分页符】：续标题必定落在新页页首，紧跟其后就是续表。
       表C.1 数据管理表
       [表1: 15 行]
       ── 分页 ──
       表C.1（续）        ← 新页页首
       [表2: 13 行]
       ── 分页 ──
       表C.1（续）        ← 新页页首
       [表3: 5 行]
    """
    a, b = split_at
    chunks = [data[:a], data[a:b], data[b:]]
    cont_title = _cont_title_para("表C.1（续）")
    # 每个续表前都放【硬分页符 + 续标题】：保证续标题出现在换页之后的新页页首
    page_break_para = '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'
    out = [title_para, _tbl_simple_with_size(head_row, col_w, chunks[0], size)]
    for idx in (1, 2):
        if not chunks[idx]:
            continue
        out.append(page_break_para + cont_title)
        out.append(_tbl_simple_with_size(head_row, col_w, chunks[idx], size))
    return "".join(out)


def _tbl_simple_with_size(head_row, col_w, data, size):
    """简单表（无 tblHeader 跨页重复），用于分表后的子表。"""
    W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    sz = size if size else 20
    total_w = sum(col_w)
    jc = '<w:jc w:val="center"/>'
    tbl_pr = (
        '<w:tblPr>'
        '<w:tblStyle w:val="a3"/>'
        f'<w:tblW w:w="{total_w}" w:type="dxa"/>'
        '<w:tblLayout w:type="fixed"/>'
        '<w:tblBorders>'
        '<w:top w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
        '<w:left w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
        '<w:bottom w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
        '<w:right w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
        '</w:tblBorders>' + jc + '</w:tblPr>'
    )
    grid_xml = "".join('<w:gridCol w:w="%d"/>' % w for w in col_w)
    tbl_grid = f'<w:tblGrid xmlns:w="{W}">{grid_xml}</w:tblGrid>'
    # 表头行（不含 tblHeader——不跨页重复，续标题用独立段落实现，对标 V1.02）
    head_cells = []
    for i, h in enumerate(head_row):
        head_cells.append(
            f'<w:tc><w:tcPr><w:tcW w:w="{col_w[i]}" w:type="dxa"/>'
            f'<w:vAlign w:val="center"/></w:tcPr>'
            f'<w:p><w:pPr>{jc}</w:pPr>'
            f'<w:r><w:rPr><w:b/><w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/></w:rPr>'
            f'<w:t xml:space="preserve">{_xml_escape(clean_space(h))}</w:t></w:r></w:p></w:tc>')
    head_tr = '<w:tr><w:trPr><w:trHeight w:val="270"/></w:trPr>' + "".join(head_cells) + '</w:tr>'
    body_trs = []
    for r in data:
        tcs = []
        for i, v in enumerate(r):
            tcs.append(
                f'<w:tc><w:tcPr><w:tcW w:w="{col_w[i]}" w:type="dxa"/>'
                f'<w:vAlign w:val="center"/></w:tcPr>'
                f'<w:p><w:pPr>{jc}</w:pPr>'
                f'<w:r><w:rPr><w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/></w:rPr>'
                f'<w:t xml:space="preserve">{_xml_escape(clean_space(v))}</w:t></w:r></w:p></w:tc>')
        body_trs.append('<w:tr>' + "".join(tcs) + '</w:tr>')
    return f'<w:tbl xmlns:w="{W}">{tbl_pr}{tbl_grid}{head_tr}{"".join(body_trs)}</w:tbl>'


def _tbl_with_tbl_header(head_row, col_w, data, size=None):
    """生成一张整表：第一行 trPr 含 <w:tblHeader/>（跨页自动重复），
    用于袁总"表C.1（续）只在换页时才出现"的需求。"""
    W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    total_w = sum(col_w)
    jc = '<w:jc w:val="center"/>'
    tbl_pr = (
        '<w:tblPr>'
        '<w:tblStyle w:val="a3"/>'
        f'<w:tblW w:w="{total_w}" w:type="dxa"/>'
        '<w:tblBorders>'
        '<w:top w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
        '<w:left w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
        '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
        '<w:right w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
        '</w:tblBorders>' + jc + '</w:tblPr>'
    )
    tbl_grid = '<w:tblGrid xmlns:w="%s">%s</w:tblGrid>' % (
        W, "".join(f'<w:gridCol w:w="{w}"/>' for w in col_w))
    # 表头行（含 tblHeader）
    head_cells = []
    for i, h in enumerate(head_row):
        head_cells.append(
            f'<w:tc><w:tcPr><w:tcW w:w="{col_w[i]}" w:type="dxa"/></w:tcPr>'
            f'<w:p><w:pPr>{jc}</w:pPr>'
            f'<w:r><w:rPr><w:b/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'
            f'<w:t xml:space="preserve">{_xml_escape(h)}</w:t></w:r></w:p></w:tc>')
    head_tr = (
        '<w:tr><w:trPr><w:tblHeader/>'
        '<w:trHeight w:val="270"/></w:trPr>'
        + "".join(head_cells) + '</w:tr>')
    # 数据行
    body_trs = []
    for r in data:
        tcs = []
        for i, v in enumerate(r):
            tcs.append(
                f'<w:tc><w:tcPr><w:tcW w:w="{col_w[i]}" w:type="dxa"/></w:tcPr>'
                f'<w:p><w:pPr>{jc}</w:pPr>'
                f'<w:r><w:rPr><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'
                f'<w:t xml:space="preserve">{_xml_escape(v)}</w:t></w:r></w:p></w:tc>')
        body_trs.append('<w:tr>' + "".join(tcs) + '</w:tr>')
    return f'<w:tbl xmlns:w="{W}">{tbl_pr}{head_tr}{"".join(body_trs)}</w:tbl>'


def _xml_escape(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _split_tbl_with_continuation(headers, col_w, data, rows_per_page=12,
                                 cont_title="表C.1（续）"):
    """把长表按 rows_per_page 拆为多张分表：
    - 第 1 张直接是表（无续表标题）
    - 第 2 张前输出"表C.1（续）"标题段落
    - 第 3 张起【不重复续表标题】（袁总 2026-09-03 反馈"最后两个多余的表C.1（续）删除"）
    返回多个兄弟元素的 XML 字符串（tbl / p / tbl / p ...）。"""
    if not data:
        return _simple_tbl(headers, col_w, data)
    chunks = [data[i:i + rows_per_page] for i in range(0, len(data), rows_per_page)]
    parts = []
    for i, chunk in enumerate(chunks):
        if i == 1:
            # 仅第 2 张前插续表标题，第 3+ 张不重复
            parts.append(_cont_title_para(cont_title))
        parts.append(_simple_tbl(headers, col_w, chunk))
    return "".join(parts)


def _cont_title_para(title: str) -> str:
    """续表标题段落（居中，宋体小四），如"表C.1（续）"。"""
    W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    return (
        '<w:p xmlns:w="%s">'
        '<w:pPr><w:jc w:val="center"/>'
        '<w:rPr><w:rFonts w:ascii="宋体" w:hAnsi="宋体" w:hint="eastAsia"/>'
        '<w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr></w:pPr>'
        '<w:r><w:rPr><w:rFonts w:ascii="宋体" w:hAnsi="宋体" w:hint="eastAsia"/>'
        '<w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr>'
        '<w:t xml:space="preserve">%s</w:t></w:r></w:p>'
    ) % (W_NS, title)


# 袁总 2026-09-04（"附录B 利益相关方参与计划表 单独在一页"）：
# 附录 A/B/C 标题段是模板硬编码、位于 {{table.xxx}} 占位符上方——
# 在每个附录表【前面】加一个 pageBreakBefore 段，强制该表从新页开始。
# 选 pageBreakBefore 而非硬分页符：_strip_breaks_between_caption_and_table
# 会删除 caption 后的 <w:br type="page"/>，而 pageBreakBefore 是段属性不会被删。
_PAGE_BEFORE = (
    '<w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    '<w:pPr><w:pageBreakBefore/></w:pPr></w:p>'
)


def build_baselines_tbl(groups) -> str:
    """基线列表（-> {{table.baselines}}），逐字对标 R121_SDP_V1.02 表20：
    4 列：基线名称 | 基线标识 | 基线包含的配置项 | 基线发布时机。
    袁总 2026-09-04 反复反馈"表 13 列宽比例请参考 V1.02"——V1.02 实测 4 列
    [763, 2551, 4204, 1895]=9413，基线类别（功能/分配/产品）直接写进"基线名称"列。
    此前为 6 列结构（独立"基线"+"名称"列）不在 V1.02 范围内，已按 V1.02 重写。
    groups: list[dict] = ConfigItemDao.list_baselines() 返回，每项
            baseline(类别) / baseline_name(名称) / baseline_id(标识)
            / ci_ids / items_str / count。
    多配置项用中文顿号"、"分隔。"""
    headers = ["基线名称", "基线标识", "基线包含的配置项", "基线发布时机"]
    # 列宽逐列取自 R121_SDP_V1.02 表20 dump 取证 [763, 2551, 4204, 1895]=9413
    col_w = [763, 2551, 4204, 1895]
    publish = "基线所包含的配置项完成入库后的一天内"
    data = []
    for g in groups or []:
        # "基线名称"列 V1.02 直接写"功能基线/分配基线/产品基线"
        # 将 baseline 类别 + baseline_name 合并为"分配基线 R105_0201"形式
        cat = (g.get("baseline") or "").strip()
        name = (g.get("baseline_name") or "").strip()
        baseline_name = ("%s %s" % (cat, name)).strip() if cat and name else (cat or name)
        data.append([
            baseline_name,
            g.get("baseline_id", ""),
            g.get("items_str", ""),
            publish,
        ])
    if not data:
        data = [["暂无基线/配置项数据", "请在「配置项管理」页录入 ci_id+baseline 字段",
                 "", ""]]
    # 袁总 2026-09-04：表13 基线列表超页边，整表居中；用 _simple_tbl 自适应字号
    return _simple_tbl(headers, col_w, data, align="center")


def build_org_chart_tbl(rows) -> str:
    """组织机构表（-> {{table.org_chart}}），对标 R121 表29：
    3 列：组织机构/角色 | 人员（代表） | 职责。
    rows: OrgChart 对象列表。数据来自平台 org_chart 表，文档中 sdt 锁定不可编辑。
    """
    headers = ["组织机构/角色", "人员（代表）", "职责"]
    # 袁总 2026-09-03：列宽严格对标 R121 表29（dump 取证 [3885, 2976, 2070]，
    # 合计 8931），不再自创 [3000,2200,4224]。
    col_w = [3885, 2976, 2070]
    data = []
    for r in rows or []:
        data.append([
            str(r.org_role or ""),
            str(r.representative or ""),
            str(r.duty or ""),
        ])
    if not data:
        data = [["暂无组织机构数据", "请在「项目策划」页录入", ""]]
    # 袁总 2026-09-03：表22 组织机构表超页边，整表居中
    return _simple_tbl(headers, col_w, data, align="center")


def build_human_resource_tbl(rows) -> str:
    """人力资源表（-> {{table.human_resource}}），对标 R121 表30：
    6 列：序号 | 姓名 | 角色/职责 | 技术素质要求 | 参加项目时段 | 投入精力（%）。
    rows: ProjectMember 对象列表。
    项目方 2026-09-02：表23 人力资源表所有【姓名】从 platform.project_members 读，
    后续在文档中以 sdt 锁定不可编辑。
    """
    # 袁总 2026-09-03：由 7 列改 6 列，严格对标 R121 表30——
    # "参加项目"与"时段"合并为"参加项目时段"一列（R121 原版即合并列）。
    headers = ["序号", "姓名", "角色/职责", "技术素质要求", "参加项目时段", "投入精力（%）"]
    # 列宽逐列取自 R121 表30（dump 取证 [653,1169,1556,3180,1129,1169]，合计 8857）
    col_w = [653, 1169, 1556, 3180, 1129, 1169]
    data = []
    for i, r in enumerate(rows or [], start=1):
        role = (r.role or "") + ("/" + r.auth if (r.auth and r.role) else (r.auth or ""))
        # 参加项目时段 = 项目名 + 阶段时段（R121 该列为"全部/需求"等自由文本）
        join_period = str(r.join_project or "R105")
        if r.period:
            join_period = join_period + str(r.period) if join_period else str(r.period)
        # 袁总 2026-09-04（反复反馈"表23 技术素质要求没有填写"）：
        # 数据库 skill_req 为空时，按【角色关键字】自动匹配 R121_SDP_V1.02 表23/表19
        # 中该角色的技术素质要求描述，保证该列不再留空。
        skill = str(r.skill_req or "").strip()
        if not skill:
            skill = _skill_req_by_role(role)
        data.append([
            str(i),
            str(r.name or ""),
            role,
            skill,
            join_period,
            str(r.effort_pct or ""),
        ])
    if not data:
        data = [["暂无人员数据", "请在「用户管理 - 项目人员」录入", "", "", "", ""]]
    # 袁总 2026-09-03：表23 人力资源表超页边，整表居中
    # 袁总 2026-09-04：表 23 显式传 size=SZ_XIAOSI 会让窄列（序号 653 dxa）
    # 字撑不下逐字竖排，改为传 None 由 _simple_tbl 按列宽自适应
    return _simple_tbl(headers, col_w, data, align="center", size=None)


# 袁总 2026-09-04：表23「技术素质要求」默认文案库——逐条取自 R121_SDP_V1.02
# 表30（人力资源表）实测内容，并与同项目表19「技能培训需求表」的角色技能要求一致。
# key 为角色关键字（命中即采用，按列表顺序优先匹配）。
_SKILL_REQ_BY_ROLE = (
    ("软件负责人", "熟悉GJB5000B运行流程，有软件项目管理经验；熟悉C、C++编程语言，具有软件开发经验"),
    ("需求", "熟悉C、C++编程语言，具有嵌入式软件类软件需求分析经验"),
    ("设计", "3年以上嵌入式软件类软件设计经验；有按照GJB438C编写设计文档的经验；熟悉公司编码规范"),
    ("实现", "熟悉C、C++编程语言，精通Keil和Stm32CubeMX嵌入式软件开发编译环境；具有软件开发经验及良好的软件编码规范"),
    ("测试", "熟悉C编程语言，具有软件测试及文档编制经验"),
    ("配置管理", "熟悉配置管理软件和配置管理制度和流程，具有GJB5000B软件配置管理经验"),
    ("测量分析", "熟悉GJB5000B测量分析工作"),
    ("质量保证", "熟悉GJB5000B运行QA的工作内容"),
    ("QA", "熟悉GJB5000B运行QA的工作内容"),
    ("CCB", "熟悉GJB5000B配置管理流程，具有变更控制委员会（CCB）评审与变更审批经验"),
    ("变更", "熟悉GJB5000B配置管理流程，具有变更控制委员会（CCB）评审与变更审批经验"),
    ("审批", "熟悉GJB5000B配置管理流程，具有变更控制委员会（CCB）评审与变更审批经验"),
)


def _skill_req_by_role(role: str) -> str:
    """按角色/职责文字匹配技术素质要求（袁总 2026-09-04：表23 该列不得留空）。"""
    r = str(role or "")
    for key, val in _SKILL_REQ_BY_ROLE:
        if key in r:
            return val
    return ""


def build_schedule_phases_tbl(rows) -> str:
    """进度阶段表（-> {{table.schedule_phases}}），对标 R121：
    4 列：阶段名称 | 计划开始时间 | 计划结束时间 | 备注。
    rows: SchedulePhase 对象列表（phase_name / start_date / end_date / milestone）。"""
    headers = ["阶段名称", "计划开始时间", "计划结束时间", "备注"]
    # 袁总 2026-09-03：列宽恢复 R121 表#28 原版 [2279,1701,2025,1417]（总宽 7422，
    # dump 取证）。此前第三十七轮自调的 [2000,1500,1800,1700] 偏离 R121，废弃。
    col_w = [2279, 1701, 2025, 1417]
    data = []
    for r in (rows or []):
        data.append([
            str(getattr(r, "phase_name", "") or ""),
            str(getattr(r, "start_date", "") or ""),
            str(getattr(r, "end_date", "") or ""),
            str(getattr(r, "milestone", "") or ""),
        ])
    # 项目方 2026-09-02：表21 软件进度表"整个表格要居中"。
    return _simple_tbl(headers, col_w, data, align="center")


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
        # 袁总 2026-09-03：表2 复用表超页边，整表居中
        return _simple_tbl(headers, col_w, data, align="center")
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
    # 袁总 2026-09-03：表2 估计表超页边，整表居中
    return _simple_tbl(headers, col_w, data, align="center")


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
