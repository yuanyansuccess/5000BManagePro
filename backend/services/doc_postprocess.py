# -*- coding: utf-8 -*-
"""
SDP 文档后处理流水线（Service 层）。
作者：袁燕
功能：对灌装完成的 docx 文件做一系列 XML/包级后处理，最终产出对标 R105 的正式文档。
      步骤覆盖：只读保护(sdt/perm)、页眉阶段勾选、表格居中/紧凑/字号/宽度适配、
      空格清理、分页与附录整理、1.1b 配置项行、签字页、占位符兜底、
      域刷新(NUM/封面总页数，Word COM 子进程)等。
设计：本模块只操作 docx 文件本身（字符串/zip），不接触数据库；
      编排顺序统一在 doc_service.generate_doc_bytes 中，此处函数按处理阶段分区排列。
"""
import os
import re

# OOXML 命名空间（统计段落/打补丁占位符用）
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

# 平台 4 类录入内容对应的只读表（表头关键词须全部命中才判定）。
# 这些表的数据均来自"项目策划"页录入，生成文档后锁定为只读岛；
# 模板静态表（签署页/引用文件/评审计划/基线列表等）不在其中，保持可编辑。
READONLY_TABLE_KEYS = [
    ['规模估计', '复用页数'],
    ['规模估计（行）'],
    # 袁总 2026-09-02：表5「各阶段工作量估计」改为可编辑（移除 ['调整后总工作量']）；
    # 软件进度表/会议计划表本就未在本锁定列表（保持可编辑）。
    # 平台数据模型：生成后可改，下次重新生成会按数据库最新值回填覆盖。
    ['会议类型', '会议组织者'],
    ['姓名/单位'],
    ['顾客代表'],
    ['资源名称', '跟踪情况'],
    ['软件名称'],
    ['风险通报方式及频率'],
    ['数据类别', '收集时机'],
    # 项目方 2026-09-02：表23 人力资源表——所有"姓名"从 platform.project_members 读，
    # 生成后锁定不可编辑（人名属平台元数据，禁止文档内手改）。
    ['技术素质要求', '投入精力'],
    # 项目方 2026-09-02：表13 基线列表——配置项从 platform.config_items 读并按基线聚合，
    # 多配置项用顿号"、"连接，生成后锁定（数据单一源头）。
    ['基线标识', '基线包含的配置项'],
    # 项目方 2026-09-02：表22 组织机构表——对标 R121 表29，从 platform.org_chart 读，
    # 组织机构与人员代表均属平台元数据，生成后锁定不可编辑。
    ['组织机构', '人员（代表）'],
    # 袁总 2026-09-03（第三十九轮）：表10 配置管理活动角色定义（项目组织|姓名）
    # 姓名来自 Project 签署角色字段（{{role.ccb}}/{{role.org_config_manager}}，
    # 前端设置页可配置），整表 sdt 锁定不可编辑。
    ['项目组织', '姓名'],
    # 袁总 2026-09-03（第三十九轮）：表11 软件配置管理库（配置库|创建人角色|配置库路径）
    # 三库地址来自 {{cm.svn_*}}（平台统管），整表 sdt 锁定不可编辑。
    ['配置库', '创建人角色', '配置库路径'],
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
    项目方 2026-09-01 终审口径：平台录入数据真实不可编辑，其余正文均可编辑。"""
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
    """真实只读保护 + 只读区黄色底纹（项目方 2026-09-01 终审口径）：
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
# 项目方 2026-09-02：10 张平台表整表只读，其余正文/手写表可编辑。
# 方案：用 w:sdt 内容控件包裹平台表并锁定内容(sdtContentLocked)，不依赖整文档
# documentProtection，规避此前 perm 注入 body 级导致 Word 空白的问题。

def _ensure_tbl_center(seg):
    """对标 R121：确保平台表 tblPr 含 jc=center（表格居中）。
    注意 CT_TblPr 子元素有 schema 顺序，w:jc 必须排在 w:tblW 之后，否则 Word 可能忽略。"""
    m = re.search(r'<w:tbl(?: [^>]*)?>', seg)
    if not m:
        return seg
    after = m.end()
    tp = seg.find('<w:tblPr', after)
    if tp == -1 or tp > after + 300:
        return seg[:after] + '<w:tblPr><w:jc w:val="center"/></w:tblPr>' + seg[after:]
    tpend = seg.find('>', tp)
    if seg[tpend - 1] == '/':                      # 自闭合 <w:tblPr/>
        return seg[:tp] + '<w:tblPr><w:jc w:val="center"/></w:tblPr>' + seg[tpend + 1:]
    if 'w:jc' in seg[tp:tpend]:
        return seg                                  # 已有对齐设置，不覆盖
    tw = seg.find('<w:tblW', tp)
    if tw != -1 and tw < tpend:                     # jc 必须排在 tblW 之后
        twend = seg.find('/>', tw)
        if twend != -1:
            return seg[:twend + 2] + '<w:jc w:val="center"/>' + seg[twend + 2:]
        twend = seg.find('>', tw)
        return seg[:twend + 1] + '<w:jc w:val="center"/>' + seg[twend + 1:]
    return seg[:tpend + 1] + '<w:jc w:val="center"/>' + seg[tpend + 1:]


def _wrap_readonly_tables_with_sdt(doc):
    """用 w:sdt 包裹 READONLY_TABLE_KEYS 命中的平台表（内容锁定，其余可编辑）。
    同时调用 _ensure_tbl_center 让平台表居中（对标 R121）。"""
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
        seg = _ensure_tbl_center(doc[a:b])
        # 袁总 2026-09-02 确认：会议计划表【不锁】，让用户可编辑。
        # 判断：行0 文字同时含"会议类型/会议组织者/会议时机"则跳过 sdt 包裹（仍居中）。
        end_first_tr = seg.find("</w:tr>")
        head_seg = seg[:end_first_tr] if end_first_tr > 0 else seg
        if ("会议类型"in head_seg and "会议组织者"in head_seg
                and "会议时机"in head_seg):
            doc = doc[:a] + seg + doc[b:]   # 只替换居中结果，不加 sdt
            continue
        # appearance=hidden：隐藏内容控件外观，避免 Word 显示灰色边框/底纹
        repl = ('<w:sdt w:id="%d"><w:sdtPr><w:lock w:val="sdtContentLocked"/>'
                '<w:appearance w:val="hidden"/></w:sdtPr>'
                '<w:sdtContent>' % sid) + seg + '</w:sdtContent></w:sdt>'
        sid += 1
        doc = doc[:a] + repl + doc[b:]
    return doc


# 项目方 2026-09-02：需删除电子签名图片的人员（模板继承的历史签名，非本项目人员）
REMOVE_SIGNATURE_USERS = ("马慧芳",)


def _remove_signature_images(doc):
    """删除电子签名图片：descr 含 'USERNAME=<姓名>' 的整个 <w:drawing> 块。"""
    pat = re.compile(r"<w:drawing>.*?</w:drawing>", re.S)

    def _sub(m):
        seg = m.group(0)
        for u in REMOVE_SIGNATURE_USERS:
            if "USERNAME=" + u in seg:
                return ""
        return seg

    return pat.sub(_sub, doc)


def _fix_sdtd_version(doc, project_id, doc_version):
    """模板静态残留的引用文件编号缺版本号（如 R105_SDTD_）→ 补成 R105_SDTD_V1.00。"""
    if not project_id:
        return doc
    ver = (doc_version or "V1.00").strip()
    pat = re.compile(re.escape(project_id) + r"_SDTD_(?![0-9A-Za-z])")
    return pat.sub(project_id + "_SDTD_" + ver, doc)


# 阶段代码映射（袁总 2026-09-02 定）：F=方案 C=初样 S=正样 D=定型 P=批产
STAGE_LETTER_MAP = {
    "方案": "F",
    "初样": "C",
    "正样": "S",
    "定型": "D",
    "批产": "P",
}

def _balanced_span(s, open_tag, close_tag, start=0):
    """返回 (起, 止)：从 start 起第一个 open_tag 到其【标签平衡】的 close_tag 之后。
    用于正确处理嵌套结构（如表格内套表格），避免非贪婪正则在内层就截断导致 XML 失衡。"""
    i = s.find(open_tag, start)
    if i < 0:
        return None
    depth = 0
    pos = i
    while True:
        no = s.find(open_tag, pos)
        nc = s.find(close_tag, pos)
        if nc < 0:
            return None
        if 0 <= no < nc:
            depth += 1
            pos = no + len(open_tag)
        else:
            pos = nc + len(close_tag)
            depth -= 1
            if depth == 0:
                return (i, pos)


def _set_cell_text(tc, text):
    """把表格单元格 tc 的显示文本设为 text：清空所有 w:t，第一个 w:t 写入 text；
    若单元格无 w:t（空段落），则在其首个段落末尾插入一个 run。"""
    ws = list(re.finditer(r"<w:t[^>]*>[^<]*</w:t>", tc))
    if ws:
        # 先清空除第一个以外的所有 w:t
        for m in reversed(ws[1:]):
            tc = (tc[:m.start()]
                  + re.sub(r"(<w:t[^>]*>)[^<]*(</w:t>)", r"\1\2", m.group(0))
                  + tc[m.end():])
        m0 = re.search(r"<w:t[^>]*>[^<]*</w:t>", tc)
        if m0:
            tc = (tc[:m0.start()]
                  + re.sub(r"(<w:t[^>]*>)[^<]*(</w:t>)", r"\1" + text + r"\2", m0.group(0))
                  + tc[m0.end():])
    else:
        tc = tc.replace("</w:p></w:tc>",
                        "<w:r><w:t>%s</w:t></w:r></w:p></w:tc>" % text, 1)
    return tc


def _apply_header_protection(docx_path, phase):
    """页眉处理（袁总 2026-09-02）：
    1) 阶段勾选按平台所选阶段联动——页眉阶段表 行1 只在 phase 对应字母列打 √，其余列清空；
    2) 阶段表 + 所有含"配置项标识"的段落用 sdt 内容控件锁定（不可编辑）。
    任何异常回退原文件，保证文档不损坏。"""
    import zipfile as _zf
    import shutil as _sh
    letter = STAGE_LETTER_MAP.get((phase or "").strip(), "")
    bak = docx_path + ".hdr.bak"
    _sh.copy(docx_path, bak)
    try:
        z = _zf.ZipFile(bak)
        names = z.namelist()
        data = {n: z.read(n) for n in names}
        z.close()
        sid = 9000
        for n in names:
            if not re.match(r"word/header\d+\.xml$", n):
                continue
            x = data[n].decode("utf-8")

            # (1) 阶段联动：把行1 的 √ 移到 letter 对应列
            # 用平衡扫描取第一个表格（嵌套安全）
            sp = _balanced_span(x, "<w:tbl>", "</w:tbl>")
            seg = x[sp[0]:sp[1]] if sp else ""
            if seg and letter:
                trs = re.findall(r"<w:tr(?:\s[^>]*)?>.*?</w:tr>", seg, re.S)
                if len(trs) >= 2:
                    head, row1 = trs[0], trs[1]
                    tcs = re.findall(r"<w:tc>.*?</w:tc>", row1, re.S)
                    # 袁总 2026-09-03（√ 错位根因）：阶段表实际为 9 格布局
                    # [密级,空,空,阶段,F,C,S,D,P]，此前 STAGE_COL_IDX 按 7 格布局
                    # 硬编码 {"F":2,"C":3,...} 导致 √ 落到"阶段"标签格。
                    # 改为动态定位：取表头行(row0)每格 join 后的全部文本，
                    # 精确等于阶段字母(F/C/S/D/P)的格即目标列——任何布局都对。
                    head_tcs = re.findall(r"<w:tc>.*?</w:tc>", head, re.S)
                    head_texts = ["".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", h)).strip()
                                  for h in head_tcs]
                    idx = head_texts.index(letter) if letter in head_texts else -1
                    if 0 <= idx < len(tcs):
                        new_tcs = []
                        for i, tc in enumerate(tcs):
                            # 清空与填入成对执行：目标列写 √，其余列清空
                            new_tcs.append(_set_cell_text(tc, "√" if i == idx else ""))
                        new_row1 = row1
                        for tc, tc2 in zip(tcs, new_tcs):
                            new_row1 = new_row1.replace(tc, tc2, 1)
                        x = x.replace(seg, seg.replace(row1, new_row1, 1), 1)

            # (2) 锁定：阶段表（平衡扫描，嵌套安全）
            sp2 = _balanced_span(x, "<w:tbl>", "</w:tbl>")
            if sp2:
                blk = x[sp2[0]:sp2[1]]
                sid += 1
                x = x[:sp2[0]] + (
                    '<w:sdt w:id="%d"><w:sdtPr><w:lock w:val="sdtContentLocked"/></w:sdtPr>'
                    '<w:sdtContent>%s</w:sdtContent></w:sdt>' % (sid, blk)
                ) + x[sp2[1]:]

            # (3) 锁定：含"配置项标识"的段落（平衡扫描）
            pos = 0
            while True:
                ps = _balanced_span(x, "<w:p>", "</w:p>", pos)
                if not ps:
                    ps = x.find("<w:p ", pos)
                    if ps < 0:
                        break
                    end = x.find(">", ps)
                    sp3 = _balanced_span(x[:end + 1] + x[end + 1:], "<w:p>", "</w:p>", ps)
                    if not sp3:
                        break
                    ps = sp3
                blk = x[ps[0]:ps[1]]
                if "配置项标识" in blk:
                    sid += 1
                    wrapped = (
                        '<w:sdt w:id="%d"><w:sdtPr><w:lock w:val="sdtContentLocked"/></w:sdtPr>'
                        '<w:sdtContent>%s</w:sdtContent></w:sdt>' % (sid, blk))
                    x = x[:ps[0]] + wrapped + x[ps[1]:]
                    pos = ps[0] + len(wrapped)
                else:
                    pos = ps[1]
                if pos >= len(x):
                    break

            data[n] = x.encode("utf-8")

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


def _apply_sdt_readonly(docx_path, project_id=None, doc_version="V1.00"):
    """对 docx 内平台表加 sdt 内容锁定 + 黄底纹 + 居中（其余不受影响）。
    同时删除指定人员的电子签名图片、补齐 SDTD 版本号。
    任何异常都回退原文件，保证文档不损坏。"""
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
        doc = _remove_signature_images(doc)
        doc = _fix_sdtd_version(doc, project_id, doc_version)
        doc = _wrap_readonly_tables_with_sdt(doc)
        # 注意（项目方 2026-09-02 最新口径）：平台表【不再加底色】。
        # 此前为视觉区分只读区加过 FFF2CC 底纹，现按袁总要求去掉；
        # 只读由 sdt 锁定保证。_shade_readonly_tables 保留但不再调用。
        # doc = _shade_readonly_tables(doc)
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


def _remove_redundant_text(docx_path):
    """袁总 2026-09-03：删除正文冗余残句。
    "CB-B/DSQ-1AGIAP下位机软件     下位机软件" 是模板里 1.1 标识章节的历史残句，
    占位符替换后残留，需整段删除（含其所在段落）。
    """
    import zipfile as _zf
    import shutil as _sh
    from lxml import etree as _et
    bak = docx_path + ".rmtxt.bak"
    _sh.copy(docx_path, bak)
    try:
        z = _zf.ZipFile(bak)
        names = z.namelist()
        data = {n: z.read(n) for n in names}
        z.close()
        W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

        def q(t):
            return "{%s}%s" % (W, t)

        root = _et.fromstring(data["word/document.xml"])
        removed = 0
        for p in list(root.iter(q("p"))):
            txt = "".join((x.text or "") for x in p.iter(q("t")))
            # 匹配冗余残句：含 "IAP下位机软件" 且含多个空格 + "下位机软件" 结尾
            if "IAP下位机软件" in txt and re.search(r"下位机软件\s+下位机软件", txt):
                parent = p.getparent()
                if parent is not None:
                    parent.remove(p)
                    removed += 1
        if removed:
            data["word/document.xml"] = _et.tostring(
                root, encoding="UTF-8", xml_declaration=True, standalone=True)
            with _zf.ZipFile(docx_path, "w", _zf.ZIP_DEFLATED) as zo:
                for n in names:
                    zo.writestr(n, data[n])
        print("[_remove_redundant_text] 删除冗余段落数=%d" % removed)
    except Exception as _e:
        _sh.copy(bak, docx_path)
        print("[_remove_redundant_text] 失败回退: %s" % _e)
    finally:
        try:
            os.remove(bak)
        except OSError:
            pass


def _clean_all_table_spaces(docx_path):
    """袁总 2026-09-04（反复反馈"所有表格里的空格始终没解决掉"）：
    对文档【全部表格】单元格文本做强制去空格，覆盖此前未处理的三大盲区：
      ① 封面签署页/文件分发/更改栏等【模板静态表】——旧逻辑只 strip() 首尾，
         中间的"审  定""文  件  分  发""纸    质""单  位"等字间距空格全部残留；
      ② sdt 锁定控件包裹的动态表——旧逻辑按 body 直接子元素遍历时会漏掉；
      ③ 全角空格 U+3000、制表符——旧检测只认 ASCII 空格。

    清理规则（保留必要的西文分隔，避免改坏标准编号与型号）：
      删：全角空格/制表符；中文↔中文；中文↔中文标点；中文↔斜杠；段落首尾空白。
      留：ASCII 字母/数字之间的【单个】空格——这是标准编号与软件型号的固有写法
          （GJB 438C-2021、GB 9386-1988、Keil 4、Windows 7、SourceInsight 4.0），
          删掉会变成 GJB438C-2021 / Keil4 这类错误表述。
    任何异常回退原文件，保证文档不损坏。"""
    import zipfile as _zf
    import shutil as _sh
    import re as _re
    from lxml import etree as _et
    bak = docx_path + ".spc.bak"
    _sh.copy(docx_path, bak)
    try:
        z = _zf.ZipFile(bak)
        names = z.namelist()
        data = {n: z.read(n) for n in names}
        z.close()
        W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

        def q(t):
            return "{%s}%s" % (W, t)

        root = _et.fromstring(data["word/document.xml"])

        # ---- 识别签字页区域（袁总 2026-09-04："不要修改签字页的表格"）----
        # 文档最前面几张表属于封面/签署区（签署表、文件分发表、更改栏表），
        # 靠字间距空格手工对齐，一律整体跳过、保持原样。
        all_tbls = [t for t in root.iter(q("tbl")) if t.getparent().tag != q("tc")]

        def _is_sign_page(tbl):
            """签字页判定：表内出现签署类关键字即视为封面/签署区，不做任何改动。"""
            s = "".join((t.text or "") for t in tbl.iter(q("t")))
            for kw in ("签    字    栏", "签  署", "审  定", "文  件  分  发",
                       "更    改    栏", "标 审", "日  期"):
                if kw in s:
                    return True
            return False

        skipped = [i + 1 for i, t in enumerate(all_tbls[:4]) if _is_sign_page(t)]

        # ---- 逐表处理：去【前后】空格 + 全部内容居中 ----
        n_p = 0
        n_ctr = 0
        n_tail = 0
        for ti, tbl in enumerate(all_tbls, 1):
            if ti in skipped:
                continue
            for tc in tbl.iter(q("tc")):
                # ① 垂直居中（vAlign=center）
                tp = tc.find(q("tcPr"))
                if tp is None:
                    tp = _et.Element(q("tcPr"))
                    tc.insert(0, tp)
                va = tp.find(q("vAlign"))
                if va is None:
                    va = _et.SubElement(tp, q("vAlign"))
                va.set(q("val"), "center")
                # ② 水平居中（段落 jc=center）
                for p in tc.findall(q("p")):
                    pp = p.find(q("pPr"))
                    if pp is None:
                        pp = _et.Element(q("pPr"))
                        p.insert(0, pp)
                    jc = pp.find(q("jc"))
                    if jc is None:
                        jc = _et.SubElement(pp, q("jc"))
                    jc.set(q("val"), "center")
                    n_ctr += 1

                # ③ 去掉每段文本【前后】的空格（袁总口径：只去前面的空格，
                #    中间的空格一律保留——"GJB 438C-2021""Keil 4"等标准编号与
                #    型号的内部空格删除后会变成错误表述）
                for p in tc.findall(q("p")):
                    ts = list(p.iter(q("t")))
                    if not ts:
                        continue
                    orig = "".join((t.text or "") for t in ts)
                    if not orig:
                        continue
                    new = _re.sub(r'^[\s\u3000\u00a0]+|[\s\u3000\u00a0]+$', '', orig)
                    if new == orig:
                        continue
                    ts[0].text = new
                    for t in ts[1:]:
                        t.text = ""
                    n_p += 1

                # ④ 删除单元格【尾部】纯空白的多余空段落
                #    （如 "R105_0202_SRS_V1.00\n\n" 尾部换行会多出一个空行，
                #     属于单元格内容"后面"的空白，一并清掉让表格紧凑）。
                #    安全约束：每格必须保留至少 1 个 w:p，删空会让 Word 判定文档损坏。
                ps = tc.findall(q("p"))
                if len(ps) >= 2:
                    drop = []
                    for k in range(len(ps) - 1, -1, -1):
                        s = "".join((x.text or "") for x in ps[k].iter(q("t"))).strip()
                        if s:
                            break
                        if len(drop) < len(ps) - 1:
                            drop.append(ps[k])
                        else:
                            break
                    for p in drop:
                        tc.remove(p)
                    n_tail += len(drop)

        data["word/document.xml"] = _et.tostring(
            root, encoding="UTF-8", xml_declaration=True, standalone=True)
        with _zf.ZipFile(docx_path, "w", _zf.ZIP_DEFLATED) as zo:
            for n in names:
                zo.writestr(n, data[n])
        print("[_clean_all_table_spaces] 跳过签字页表=%s, 去前后空格段落=%d, "
              "删尾部空段=%d, 居中段落=%d" % (skipped, n_p, n_tail, n_ctr))
    except Exception as _e:
        import traceback
        traceback.print_exc()
        try:
            _sh.copy(bak, docx_path)
        except Exception:
            pass
        print("[_clean_all_table_spaces] 失败回退: %s" % _e)


def _fit_tables_to_page(docx_path, shrink_ratio=0.98):
    """袁总 2026-09-03：全文档表格宽度适配页面 + 整表居中。

    背景：纵向 A4 页可用宽仅 9468 dxa（pgSz 11906 - left 1701 - right 737），
    而模板静态表与生成表大量超宽（附录B 15083、附录A 14425、表24 10508…），
    Word 渲染时右侧被切出页边。

    处理：
    1) 读 sectPr 计算页面可用宽 AVAIL；
    2) 每张表算 gridCol 总宽，若 > AVAIL*shrink_ratio 则等比缩放
       （gridCol 与每行的 tcW 同步改，fixed 布局下必须同步才生效）；
    3) 给 tblPr 加 <w:jc w:val="center"/> 让整表居中；
    4) 幂等：已适配的表不再重复缩放（只补 jc）。

    任何异常回退原文件，保证文档不损坏。
    """
    import zipfile as _zf
    import shutil as _sh
    from lxml import etree as _et
    bak = docx_path + ".fit.bak"
    _sh.copy(docx_path, bak)
    try:
        z = _zf.ZipFile(bak)
        names = z.namelist()
        data = {n: z.read(n) for n in names}
        z.close()
        W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

        def q(t):
            return "{%s}%s" % (W, t)

        root = _et.fromstring(data["word/document.xml"])

        # 1) 按文档序收集各节可用宽（袁总 2026-09-03：附录节是横向页 16838 宽，
        #    此前统一用纵向 9468 压所有表，导致附录宽表（R121 原版 14613）被压坏、
        #    列挤压换行"表格太长"。现按每张表所在节的实际可用宽适配。
        #    sectPr 在节尾段落 pPr 内（该标记之后的内容属于下一节）。
        sect_avails = []
        for sect in root.iter(q("sectPr")):
            pg_sz = sect.find(q("pgSz"))
            pg_mar = sect.find(q("pgMar"))
            if pg_sz is None or pg_mar is None:
                sect_avails.append(9468)
                continue
            w = int(pg_sz.get(q("w"), 11906))
            left = int(pg_mar.get(q("left"), 0))
            right = int(pg_mar.get(q("right"), 0))
            sect_avails.append(max(w - left - right, 3000))
        if not sect_avails:
            sect_avails = [9468]
        sect_i = 0
        print("[_fit_tables_to_page] 各节可用宽=%s" % sect_avails)

        fitted = 0
        centered = 0
        # 文档序遍历：遇到 sectPr 切换到下一节的可用宽；表格用当前节的可用宽
        for el in root.iter():
            if el.tag == q("sectPr"):
                if sect_i < len(sect_avails) - 1:
                    sect_i += 1
                continue
            if el.tag != q("tbl"):
                continue
            # 跳过嵌套表（父级是单元格的外层表已整体适配，嵌套表跟随父表）
            par = el.getparent()
            if par is not None and par.tag == q("tc"):
                continue
            avail = sect_avails[sect_i]
            limit = int(avail * shrink_ratio)
            # --- 整表居中 ---
            tbl_pr = el.find(q("tblPr"))
            if tbl_pr is None:
                tbl_pr = _et.Element(q("tblPr"))
                el.insert(0, tbl_pr)
            jc = tbl_pr.find(q("jc"))
            if jc is None:
                jc = _et.SubElement(tbl_pr, q("jc"))
            if jc.get(q("val")) != "center":
                jc.set(q("val"), "center")
                centered += 1
            # --- 布局统一 fixed（袁总 2026-09-04 根因修复）---
            # R121_SDP_V1.02 实测 37 张表【全部】为 tblLayout="fixed"、autofit=0。
            # 而模板静态表（文件分发/更改栏/引用文件/监控阈值/项目组织/测量项等）
            # 仍带 autofit —— autofit 下 Word 忽略 gridCol/tcW 按内容重算列宽，
            # 正是"列被压窄、文字竖排看不清"的根因。此处统一改 fixed，
            # 并同步 tblW = gridCol 之和（fixed 布局要求二者一致，否则 Word 行为异常）。
            _lay = tbl_pr.find(q("tblLayout"))
            if _lay is None:
                _lay = _et.SubElement(tbl_pr, q("tblLayout"))
            _lay.set(q("type"), "fixed")

            # --- 宽度适配 ---
            grid = el.find(q("tblGrid"))
            if grid is None:
                continue
            cols = grid.findall(q("gridCol"))
            if not cols:
                continue
            total = sum(int(g.get(q("w"), 0)) for g in cols)
            # fixed 布局：tblW 必须等于 gridCol 之和，否则列宽错乱
            _tw = tbl_pr.find(q("tblW"))
            if _tw is None:
                _tw = _et.SubElement(tbl_pr, q("tblW"))
            _tw.set(q("w"), str(total))
            _tw.set(q("type"), "dxa")
            # 袁总 2026-09-04（"表13 基线列表 宽度比例与 V1.02 完全一致"）：
            # 基线列表宽度已严格按 R121_SDP_V1.02 表20 取证值
            # [763,2551,4204,1895]=9413 写死，且能容于所在节可用宽；
            # 但 _fit 的 0.98 保守系数会让 9413 > 9390(limit) 被轻微等比缩放
            # （差 ≤18dxa），破坏"完全一致"。故对基线列表整表跳过缩放，
            # 仅保留 jc 居中 + fixed 布局（其余表照常缩放）。
            _hdr0 = ""
            trs0 = el.findall(q("tr"))
            if trs0:
                _hdr0 = "".join((x.text or "") for x in trs0[0].iter(q("t")))
            if "基线名称" in _hdr0:
                continue
            if total <= limit:
                continue
            ratio = limit / float(total)
            for g in cols:
                old = int(g.get(q("w"), 0))
                g.set(q("w"), str(max(int(old * ratio), 200)))
            # 同步每行的 tcW（fixed 布局必须 gridCol 与 tcW 同步）
            for tr in el.findall(q("tr")):
                cells = tr.findall(q("tc"))
                for i, tc in enumerate(cells):
                    if i >= len(cols):
                        continue
                    tc_pr = tc.find(q("tcPr"))
                    if tc_pr is None:
                        continue
                    cw = tc_pr.find(q("tcW"))
                    if cw is not None:
                        old = int(cw.get(q("w"), 0))
                        cw.set(q("w"), str(max(int(old * ratio), 200)))
            fitted += 1

        data["word/document.xml"] = _et.tostring(
            root, encoding="UTF-8", xml_declaration=True, standalone=True)
        with _zf.ZipFile(docx_path, "w", _zf.ZIP_DEFLATED) as zo:
            for n in names:
                zo.writestr(n, data[n])
        print("[_fit_tables_to_page] 宽度适配表数=%d, 补居中表数=%d" % (fitted, centered))
    except Exception as _e:
        _sh.copy(bak, docx_path)
        print("[_fit_tables_to_page] 失败回退: %s" % _e)
    finally:
        try:
            os.remove(bak)
        except OSError:
            pass


def _fix_11b_cfg_items(docx_path, proj_id: str):
    """袁总 2026-09-04 第 N+1 轮（"1.1 标识 b 软件名称 应是两条但只显示一条"）根因：
    模板 1.1 b 章节只画了一行 "R105_0201"——原始模板只有主软件那一行。
    即便 ph_map 把 {{sys.cfg_items}} 设为 "R105_0201、R105_0202" 也只能放进第一行，
    第二行根本没有占位符挂载点。

    修复策略（不动模板、保证签字页原样）：在生成后处理时
      ① 找到 1.1 b 那行 R105_0201 的段落；
      ② 用 etree 复制该段（保留 sdt/pPr/缩进等结构）；
      ③ 改写复制段中 sdt 内的【名称/编号】文本（不破坏 sdt 锁定结构、不动 sdt 外的 t）；
      ④ 重新生成 sdt id（避免与原段 id 重复，否则 Word 渲染异常）。
    任何异常回退原文件。"""
    import zipfile as _zf
    import shutil as _sh
    import json
    import random
    from copy import deepcopy
    from lxml import etree as _et
    bak = docx_path + ".11b.bak"
    _sh.copy(docx_path, bak)
    try:
        from backend.db.session import SessionLocal
        from backend.db.models import Project
        db = SessionLocal()
        try:
            p = db.query(Project).filter(Project.project_id == proj_id).first()
            items = json.loads(p.cfg_items) if (p and p.cfg_items) else []
        finally:
            db.close()
        if not items or len(items) < 2:
            print("[_fix_11b_cfg_items] 配置项数=%d，跳过追加" % len(items))
            return

        z = _zf.ZipFile(bak)
        names = z.namelist()
        data = {n: z.read(n) for n in names}
        z.close()
        W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

        def q(t):
            return "{%s}%s" % (W, t)

        root = _et.fromstring(data["word/document.xml"])
        body = root.find(q("body"))

        # 定位第一行 R105_0201 段
        target = None
        for p in body.findall(q("p")):
            s = "".join((t.text or "") for t in p.iter(q("t")))
            if proj_id + "_0201" in s and "缩略语" not in s:
                target = p
                break
        if target is None:
            print("[_fix_11b_cfg_items] 未找到 R105_0201 段")
            return

        # 记录原段里所有 sdt 的位置（第 1 个 sdt = 名称, 第 2 个 sdt = 编号）
        sdt_path_in_target = []
        for child in target:
            if child.tag == q("sdt"):
                sdt_path_in_target.append(child)
        if len(sdt_path_in_target) < 2:
            print("[_fix_11b_cfg_items] 目标段 sdt 数量 < 2，无法安全追加")
            return

        for it in items[1:]:
            name = it.get("name", "")
            code = it.get("code", "")
            if not name:
                continue
            new_p = deepcopy(target)
            # ① 给所有 sdt 重新分配 id（避免重复）
            for sdt in new_p.iter(q("sdt")):
                sid = sdt.find(q("sdtPr"))
                if sid is not None:
                    idel = sid.find(q("id"))
                    if idel is not None:
                        idel.set(q("val"), str(random.randint(100000, 999999)))
            # ② 只改 sdt 内的 t 文本（不破坏锁定结构）
            #    编号形如 "R105_0201"：sdt[1] 内是项目号 "R105"，其后紧跟的 run 是后缀 "_0201"
            sdts = list(new_p.iter(q("sdt")))
            if len(sdts) >= 1:
                for t in sdts[0].iter(q("t")):
                    t.text = name
            if len(sdts) >= 2:
                suffix = code[len(proj_id):] if code.startswith(proj_id) else code
                for t in sdts[1].iter(q("t")):
                    t.text = proj_id
                after = sdts[1].getnext()
                if after is not None and after.tag == q("r"):
                    for t in after.findall(q("t")):
                        t.text = suffix
            # ③ 【关键·袁总 2026-09-04 第二轮】保留第一行所有 run 的文本不动：
            #    模板里第一行 sdt[0] 与 sdt[1] 之间夹两个 run，
            #    t.text = " "（名称与编号之间的视觉分隔）和 t.text = "            "（12 空格缩进）。
            #    上一版"清空纯空白 t"导致第二行这两 run 变空，Word 序列化为自闭合
            #    <w:t/> → 第二行格式与第一行不一致。
            #    此处只重置 sdt id（避免 Word 渲染冲突），其它文本一律保留。
            target.addnext(new_p)
            target = new_p

        n_added = len(items) - 1
        data["word/document.xml"] = _et.tostring(
            root, encoding="UTF-8", xml_declaration=True, standalone=True)
        with _zf.ZipFile(docx_path, "w", _zf.ZIP_DEFLATED) as zo:
            for n in names:
                zo.writestr(n, data[n])
        print("[_fix_11b_cfg_items] 追加 %d 行配置项（R105 共 %d 项）" % (n_added, len(items)))
    except Exception as _e:
        import traceback
        traceback.print_exc()
        try:
            _sh.copy(bak, docx_path)
        except Exception:
            pass
        print("[_fix_11b_cfg_items] 失败回退: %s" % _e)


def _ensure_signature_page(docx_path, proj_id):
    """袁总 2026-09-04（新增签字页）：生成独立"签字页"，单页布局，参考 R121 封面签署区做法。

    实现：在文档末尾（最终 sectPr 之前）插入【强制分页段落 + 标题段 + 签字表格】。
    表格 3 列（职务/签字/日期），行 = 编制/审核/会签/标准化/批准/批准(顾客代表)，
    角色姓名取自 Project 签署字段（与封面同源，数据单一源头），日期取 approve_date。
    整表 compact（仅 6 行 + 标题），固定布局 + 居中，确保只占一页。
    任何异常回退原文件，保证文档不损坏。"""
    import zipfile as _zf
    import shutil as _sh
    from lxml import etree as _et
    bak = docx_path + ".sign.bak"
    _sh.copy(docx_path, bak)
    try:
        from backend.db.session import SessionLocal
        from backend.db.models import Project
        db = SessionLocal()
        try:
            p = db.query(Project).filter(Project.project_id == proj_id).first()
            owner = (p.owner or "") if p else ""
            reviewer = (p.reviewer or "") if p else ""
            ccb = (p.ccb or "") if p else ""
            qa = (p.qa or "") if p else ""
            proj_lead = (p.proj_lead or "") if p else ""
            requirement = (p.requirement or "") if p else ""
            approve_date = (p.approve_date or "") if p else ""
        finally:
            db.close()

        z = _zf.ZipFile(bak)
        names = z.namelist()
        data = {n: z.read(n) for n in names}
        z.close()
        W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

        def q(t):
            return "{%s}%s" % (W, t)

        root = _et.fromstring(data["word/document.xml"])
        body = root.find(q("body"))

        def _cell(text, w, align="center"):
            tc = _et.Element(q("tc"))
            tcpr = _et.SubElement(tc, q("tcPr"))
            _et.SubElement(tcpr, q("vAlign")).set(q("val"), "center")
            tw = _et.SubElement(tcpr, q("tcW"))
            tw.set(q("w"), str(w))
            tw.set(q("type"), "dxa")
            p = _et.SubElement(tc, q("p"))
            ppr = _et.SubElement(p, q("pPr"))
            _et.SubElement(ppr, q("jc")).set(q("val"), align)
            r = _et.SubElement(p, q("r"))
            t = _et.SubElement(r, q("t"))
            t.text = text
            return tc

        # 标题段 "签　　字　　页"
        title_p = _et.Element(q("p"))
        tpr = _et.SubElement(title_p, q("pPr"))
        _et.SubElement(tpr, q("jc")).set(q("val"), "center")
        tr = _et.SubElement(title_p, q("r"))
        trpr = _et.SubElement(tr, q("rPr"))
        _et.SubElement(trpr, q("b"))
        sz = _et.SubElement(trpr, q("sz"))
        sz.set(q("val"), "36")  # 小二
        szcs = _et.SubElement(trpr, q("szCs"))
        szcs.set(q("val"), "36")
        tt = _et.SubElement(tr, q("t"))
        tt.text = "签　　字　　页"

        # 分页段落（强制新页）
        pb = _et.Element(q("p"))
        pbpr = _et.SubElement(pb, q("pPr"))
        _et.SubElement(pbpr, q("pageBreakBefore"))

        # 签字表
        rows = [
            ("编制", owner),
            ("审核", reviewer),
            ("会签", ccb),
            ("标准化", qa),
            ("批准", proj_lead),
            ("批准（顾客代表）", requirement),
        ]
        w_role, w_sign, w_date = 2400, 4000, 3013
        tbl = _et.Element(q("tbl"))
        tpr = _et.SubElement(tbl, q("tblPr"))
        _et.SubElement(tpr, q("tblLayout")).set(q("type"), "fixed")
        tw = _et.SubElement(tpr, q("tblW"))
        tw.set(q("w"), str(w_role + w_sign + w_date))
        tw.set(q("type"), "dxa")
        _et.SubElement(tpr, q("jc")).set(q("val"), "center")
        borders = _et.SubElement(tpr, q("tblBorders"))
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
            e = _et.SubElement(borders, q(edge))
            e.set(q("val"), "single")
            e.set(q("sz"), "4")
            e.set(q("color"), "auto")
        grid = _et.SubElement(tbl, q("tblGrid"))
        for w in (w_role, w_sign, w_date):
            _et.SubElement(grid, q("gridCol")).set(q("w"), str(w))
        # 表头行
        tr0 = _et.SubElement(tbl, q("tr"))
        for (lab, w) in (("职务", w_role), ("签字", w_sign), ("日期", w_date)):
            tr0.append(_cell(lab, w))
        # 数据行
        for (role, name) in rows:
            tr = _et.SubElement(tbl, q("tr"))
            tr.append(_cell(role, w_role))
            tr.append(_cell(name, w_sign, align="left"))
            tr.append(_cell(approve_date, w_date))

        # 插入到最终 sectPr 之前（保持 sectPr 为 body 末元素）
        final_sect = None
        for el in body:
            if el.tag == q("sectPr"):
                final_sect = el
        if final_sect is not None:
            final_sect.addprevious(pb)
            final_sect.addprevious(title_p)
            final_sect.addprevious(tbl)
        else:
            body.append(pb)
            body.append(title_p)
            body.append(tbl)

        data["word/document.xml"] = _et.tostring(
            root, encoding="UTF-8", xml_declaration=True, standalone=True)
        with _zf.ZipFile(docx_path, "w", _zf.ZIP_DEFLATED) as zo:
            for n in names:
                zo.writestr(n, data[n])
        print("[_ensure_signature_page] 插入签字页(6 行签署): 编制=%s 审核=%s 批准=%s"
              % (owner, reviewer, proj_lead))
    except Exception as _e:
        import traceback
        traceback.print_exc()
        try:
            _sh.copy(bak, docx_path)
        except Exception:
            pass
        print("[_ensure_signature_page] 失败回退: %s" % _e)


def _tighten_appendix_captions(docx_path):
    """袁总 2026-09-04（"附录 A/C 标题上下多余空白"）：
    删掉附录 A/B/C 标题上下相邻的多余【纯空段落】。

    重要约束（避免引入新排版问题）：
      * 绝不删除带 sectPr（分节符）的段落——否则会破坏分节、导致整篇重排暴涨页数；
      * 绝不删除带 pageBreakBefore / <w:br type=page/>（强制分页）的段落；
      * 绝不删除含图形/图片（w:drawing / w:pict / v:shape）的段落；
      * 上下各最多删 1 个纯空段，保留最少 1 个视觉间隔；
      * 用 getprevious()/getnext() 兄弟导航，避免索引失效。"""
    import zipfile as _zf
    import shutil as _sh
    from lxml import etree as _et
    bak = docx_path + ".cap.bak"
    _sh.copy(docx_path, bak)
    try:
        z = _zf.ZipFile(bak)
        names = z.namelist()
        data = {n: z.read(n) for n in names}
        z.close()
        W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

        def q(t):
            return "{%s}%s" % (W, t)

        root = _et.fromstring(data["word/document.xml"])
        body = root.find(q("body"))

        import re as _re
        def _norm(s):
            return _re.sub(r'[\s\u00a0\u3000]+', ' ', s).strip()
        # 关键词匹配（归一化 \xa0/全角空格/多空格），覆盖 TOC 条目与真实标题
        targets = [("附录A", "项目风险管理"), ("附录B", "相关方"),
                   ("附录C", "数据管理")]

        def is_protected(p):
            """受保护段落：含文字/分节符/分页/图形，均不可删。"""
            txt = "".join((t.text or "") for t in p.iter(q("t"))).strip()
            if txt:
                return True
            ppr = p.find(q("pPr"))
            if ppr is not None and ppr.find(q("sectPr")) is not None:
                return True
            if ppr is not None and ppr.find(q("pageBreakBefore")) is not None:
                return True
            if any(br.get(q("type")) == "page" for br in p.iter(q("br"))):
                return True
            # 注意：p.iter() 返回的是生成器对象（恒为真），必须用 next() 判空
            if next(p.iter(q("drawing")), None) is not None:
                return True
            if next(p.iter(q("pict")), None) is not None:
                return True
            if next(p.iter(q("imagedata")), None) is not None:
                return True
            return False

        to_remove = set()
        for p in body.iter(q("p")):
            s = _norm("".join((t.text or "") for t in p.iter(q("t"))))
            if not any(k1 in s and k2 in s for (k1, k2) in targets):
                continue
            # 上方：删除标题前所有连续紧邻纯空段（受保护段跳过）
            prev = p.getprevious()
            while prev is not None and prev.tag == q("p") and prev not in to_remove and not is_protected(prev):
                to_remove.add(prev)
                prev = prev.getprevious()
            # 下方：删除标题后所有连续紧邻纯空段（分页/分节段受保护，自动保留）
            nxt = p.getnext()
            while nxt is not None and nxt.tag == q("p") and nxt not in to_remove and not is_protected(nxt):
                to_remove.add(nxt)
                nxt = nxt.getnext()

        # 去重后删除
        seen = set()
        n_removed = 0
        for el in to_remove:
            if el in seen:
                continue
            seen.add(el)
            parent = el.getparent()
            if parent is not None:
                parent.remove(el)
                n_removed += 1
        data["word/document.xml"] = _et.tostring(
            root, encoding="UTF-8", xml_declaration=True, standalone=True)
        with _zf.ZipFile(docx_path, "w", _zf.ZIP_DEFLATED) as zo:
            for n in names:
                zo.writestr(n, data[n])
        print("[_tighten_appendix_captions] 删除多余空段=%d" % n_removed)
    except Exception as _e:
        import traceback
        traceback.print_exc()
        try:
            _sh.copy(bak, docx_path)
        except Exception:
            pass
        print("[_tighten_appendix_captions] 失败回退: %s" % _e)


def _unify_appendix_pages(docx_path):
    """袁总 2026-09-04（"附录A/B 要和下面表格挨着，48页去掉"）：
    附录A/B 当前布局 = 附录A（标题 + pageBreakBefore 空段 + 表）+ 附录B（标题 +
    pageBreakBefore 空段 + 表），两附录各占一页，导致总页数多 1 页（第48页）。

    修复策略（最小改动、不破坏既有"附录 A/C 分节横版"逻辑）：
      ① 删除"附录B 标题段前的 pageBreakBefore"——让 B 标题直接接在 A 的表后；
      ② 给附录B 标题段加 w:keepNext——确保 B 标题 + B 表不被分页拆开；
      ③ 删除"附录A 标题段前"的 pageBreakBefore 同理，让 A 紧贴上一节末内容（注释段）；
      ④ 保留附录C 的 pageBreakBefore（因为表C.1 在横版节，纵版正文须强制分节）。
    任何异常回退原文件。"""
    import zipfile as _zf
    import shutil as _sh
    from lxml import etree as _et
    bak = docx_path + ".unify.bak"
    _sh.copy(docx_path, bak)
    try:
        z = _zf.ZipFile(bak)
        names = z.namelist()
        data = {n: z.read(n) for n in names}
        z.close()
        W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

        def q(t):
            return "{%s}%s" % (W, t)

        root = _et.fromstring(data["word/document.xml"])

        def _norm(s):
            import re as _re
            return _re.sub(r'[\s\u00a0\u3000]+', ' ', s).strip()

        n_pb_removed = 0
        n_kn_added = 0
        # 文档序顶层 p/tbl
        seq = []
        for el in root.iter():
            if el.tag in (q("p"), q("tbl")):
                par = el.getparent()
                if par is not None and par.tag == q("tc"):
                    continue
                seq.append(el)

        # 找到"附录A/附录B/附录C"标题段（取归一后文字匹配）
        appendix_titles = {"附录A", "附录B", "附录C"}
        for i, el in enumerate(seq):
            if el.tag != q("p"):
                continue
            txt = _norm("".join((t.text or "") for t in el.iter(q("t"))))
            if not txt:
                continue
            # 标题以"附录A"/"附录B"/"附录C"开头
            hit_key = None
            for k in appendix_titles:
                if txt.startswith(k):
                    hit_key = k
                    break
            if not hit_key:
                continue
            if hit_key == "附录C":
                # 附录C 表是横版（final sectPr orient=landscape），
                # 横版可用高度仅 11906 dxa（约 21cm）。keepNext 会把
                # "标题+空段+表标题+表"绑成一大块装不下当页，整块推到
                # 下一页 → "附录C数据管理表"标题单独占一页（袁总反馈
                # "附录A/B 要挨着下面表格"问题的另一面）。所以附录C 标题
                # 不加 keepNext，让标题留当页、靠表的 keepNext 自然绑定。
                pass
            # ① 删除标题段本身的 pageBreakBefore（让 A/B 紧贴上一节内容）
            ppr = el.find(q("pPr"))
            if ppr is not None:
                pb = ppr.find(q("pageBreakBefore"))
                if pb is not None:
                    ppr.remove(pb)
                    n_pb_removed += 1
            # ②【关键·袁总 2026-09-04 第二轮】模板结构是"附录标题 + 含 pageBreakBefore
            #    的空段 + 表"，PB 写在标题段【之后】的空段上，导致 Word 把标题
            #    留在上页尾、表格跳到下页头，且每张附录独立占整页。
            #    修复：删除标题段【之后】的紧邻空段上的 pageBreakBefore（最多 3 个
            #    紧邻空段），让 keepNext 真正把标题与表格绑同页。
            for j in range(i + 1, min(i + 5, len(seq))):
                nxt = seq[j]
                if nxt.tag == q("tbl"):
                    break
                ptxt = _norm("".join((t.text or "") for t in nxt.iter(q("t"))))
                if ptxt:
                    break
                pppr = nxt.find(q("pPr"))
                if pppr is not None:
                    pb = pppr.find(q("pageBreakBefore"))
                    if pb is not None:
                        pppr.remove(pb)
                        n_pb_removed += 1
                # 同样去掉空段里的硬分页 br/page
                for br in list(nxt.iter(q("br"))):
                    if br.get(q("type")) == "page":
                        br.getparent().remove(br)
            # ③ 给标题段加 keepNext（标题与表格绑同页）；附录C 不加——
            #    横版高度不够装整块，加了反而让标题单独占一页。
            if hit_key != "附录C":
                if ppr is None:
                    ppr = _et.Element(q("pPr"))
                    el.insert(0, ppr)
                if ppr.find(q("keepNext")) is None:
                    ppr.insert(0, _et.Element(q("keepNext")))
                    n_kn_added += 1

        data["word/document.xml"] = _et.tostring(
            root, encoding="UTF-8", xml_declaration=True, standalone=True)
        with _zf.ZipFile(docx_path, "w", _zf.ZIP_DEFLATED) as zo:
            for n in names:
                zo.writestr(n, data[n])
        print("[_unify_appendix_pages] 删除pageBreakBefore=%d, 加keepNext=%d"
              % (n_pb_removed, n_kn_added))
    except Exception as _e:
        import traceback
        traceback.print_exc()
        try:
            _sh.copy(bak, docx_path)
        except Exception:
            pass
        print("[_unify_appendix_pages] 失败回退: %s" % _e)
    finally:
        try:
            os.remove(bak)
        except OSError:
            pass


def _adjust_appendix_pgnumtype(docx_path):
    """袁总 2026-09-04（"目录页码与实际不一致"根因）：
    模板 R121 的 final sectPr（附录 C 横版节）写死 pgNumType.start=34，
    R121 原版正文有 8. 注释等章节，所以附录 A 从 34 开始不重叠；
    R105 正文较短，项目组织/软硬件资源视觉页号就到 34-37，再让附录 A
    从 34 开始 → "附录 A 视觉页 34" 与"7.2 项目资源 视觉页 34"重号，
    用户视觉上两个"页 34"，目录 PAGEREF 与实际页对不上。

    修复：调用 word_pages.py 子进程取附录 A 全局页号，把 final sectPr
    的 pgNumType.start 改为该全局页号（让附录 C 节从该页号重新编号）。
    然后 word_pages.py 重新跑一次拿新 pagerefs，由 _update_fields_with_word
    改写所有 PAGEREF 缓存。"""
    import zipfile as _zf
    import shutil as _sh
    import subprocess as _sp
    import sys as _sys
    import json as _json
    import re as _re
    bak = docx_path + ".pgnum.bak"
    _sh.copy(docx_path, bak)
    try:
        proc = _sp.run(
            [_sys.executable, "-m", "backend.services.word_pages",
             os.path.abspath(docx_path)],
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))),
            capture_output=True, timeout=300,
        )
        out = (proc.stdout or b"").decode("utf-8", errors="replace")
        if "@@JSON@@" not in out:
            print("[_adjust_appendix_pgnumtype] 子进程输出无 @@JSON@@")
            return
        payload = out.split("@@JSON@@", 1)[1]
        depth, end_idx = 0, None
        for i, ch in enumerate(payload):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end_idx = i + 1
                    break
        data_j = _json.loads(payload[:end_idx] if end_idx else payload)
        appendix_a_global = data_j.get("appendix_a_global")
        if not appendix_a_global:
            print("[_adjust_appendix_pgnumtype] 未取得 appendix_a_global（=%s），跳过" % appendix_a_global)
            return

        z = _zf.ZipFile(docx_path)
        names = z.namelist()
        data = {n: z.read(n) for n in names}
        z.close()
        x = data["word/document.xml"].decode("utf-8")
        sp_matches = list(_re.finditer(r'<w:sectPr[^>]*>.*?</w:sectPr>', x, _re.DOTALL))
        if not sp_matches:
            return
        sp = sp_matches[-1].group(0)
        new_sp = _re.sub(
            r'(<w:pgNumType[^/>]*?)w:start="\d+"',
            lambda m: m.group(1) + 'w:start="%d"' % appendix_a_global,
            sp,
        )
        if new_sp == sp:
            # 没 start 属性，加一个
            if "<w:pgNumType" in new_sp:
                new_sp = _re.sub(
                    r'<w:pgNumType([^/>]*?)/>',
                    r'<w:pgNumType\1 w:start="%d"/>' % appendix_a_global,
                    new_sp, count=1)
            else:
                # 没 pgNumType，插一个
                new_sp = sp.replace(
                    ">", '><w:pgNumType w:start="%d"/>' % appendix_a_global, 1)
        if new_sp == sp:
            print("[_adjust_appendix_pgnumtype] sectPr 无 pgNumType 可改")
            return
        x_new = x[:sp_matches[-1].start()] + new_sp + x[sp_matches[-1].end():]
        data["word/document.xml"] = x_new.encode("utf-8")
        with _zf.ZipFile(docx_path, "w", _zf.ZIP_DEFLATED) as zo:
            for n in names:
                zo.writestr(n, data[n])
        print("[_adjust_appendix_pgnumtype] final sectPr pgNumType.start=34 → %d"
              % appendix_a_global)
    except Exception as _e:
        import traceback
        traceback.print_exc()
        try:
            _sh.copy(bak, docx_path)
        except Exception:
            pass
        print("[_adjust_appendix_pgnumtype] 失败回退: %s" % _e)
    finally:
        try:
            os.remove(bak)
        except OSError:
            pass


def _compact_table_headers(docx_path):
    """袁总 2026-09-03（第三十九轮·表格空格终极修复）：对标 R121 dump 取证——
    R121 全部表头均为紧凑格式：'序号'（无 \\xa0）、'型号/图号/代号/版本/参数'
    （斜杠两侧无空格）、'开发阶段'（无斜杠空格）。此前生成/模板表头是
    '序\\xa0号'、'型号 / 图号 / ...'，正是袁总反复点名"表格里有空格"的根因。

    处理：所有表格首行（表头行）的 w:t 文本：
      1) \\xa0（不间断空格）→ 删除（'序\\xa0号'→'序号'）；
      2) ' / ' → '/'（'型号 / 图号'→'型号/图号'）；
      3) strip 前后空白。
    不动普通空格（签署页/文件分发'单  位'等 R121 原版对齐空格完整保留）。
    任何异常回退原文件。"""
    import zipfile as _zf
    import shutil as _sh
    from lxml import etree as _et
    bak = docx_path + ".hdrc.bak"
    _sh.copy(docx_path, bak)
    try:
        z = _zf.ZipFile(bak)
        names = z.namelist()
        data = {n: z.read(n) for n in names}
        z.close()
        W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

        def q(t):
            return "{%s}%s" % (W, t)

        root = _et.fromstring(data["word/document.xml"])
        fixed = 0
        for tbl in root.iter(q("tbl")):
            rows = tbl.findall(q("tr"))
            if not rows:
                continue
            for t in rows[0].iter(q("t")):
                if not t.text:
                    continue
                s = t.text.replace("\u00a0", "").replace(" / ", "/").strip()
                if s != t.text:
                    t.text = s
                    fixed += 1
        data["word/document.xml"] = _et.tostring(
            root, encoding="UTF-8", xml_declaration=True, standalone=True)
        with _zf.ZipFile(docx_path, "w", _zf.ZIP_DEFLATED) as zo:
            for n in names:
                zo.writestr(n, data[n])
        print("[_compact_table_headers] 表头紧凑化文本数=%d" % fixed)
    except Exception as _e:
        _sh.copy(bak, docx_path)
        print("[_compact_table_headers] 失败回退: %s" % _e)
    finally:
        try:
            os.remove(bak)
        except OSError:
            pass


def _add_caption_keepnext(docx_path):
    """袁总 2026-09-03（第三十九轮·表标题与表格分页分离修复）：
    表22/23 等表格的标题段落（'组织机构表'/'人力资源表'等）与表格被分页拆开
    （标题留在上页尾、表格跳到下页头）。对表标题段落加 w:keepNext
    （与下一段落/表格保持同页），Word 排版自动把标题带到表格所在页。

    判定规则（取证自 v6 文档全部表标题形态）：
      - 段落文本 strip 后长度 ≤ 20；
      - 且（以'表'结尾，或以'表'开头（'表C.1 数据管理表'/'表C.1（续）'），
        或文本 ∈ {配置管理活动角色定义, 软件配置管理库, 基线列表, 软件风险管理表}）。

    袁总 2026-09-03（复核修正·keepNext 链）：仅给标题段落加 keepNext 无效——
    Word 实测标题与表格间常夹着【空段落】（如"人力资源表"后紧跟一个空段落），
    keepNext 只把标题绑到空段落，分页仍发生在空段落后 → 表格跳页。
    现改为：从标题段落起，其后直到表格前的【所有段落（含空段落）】都加
    keepNext，形成完整绑定链，Word 才会把标题连同表格首行一起推到下一页。
    任何异常回退原文件。"""
    import zipfile as _zf
    import shutil as _sh
    from lxml import etree as _et
    bak = docx_path + ".kn.bak"
    _sh.copy(docx_path, bak)
    try:
        z = _zf.ZipFile(bak)
        names = z.namelist()
        data = {n: z.read(n) for n in names}
        z.close()
        W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

        def q(t):
            return "{%s}%s" % (W, t)

        root = _et.fromstring(data["word/document.xml"])
        extra_caps = {"配置管理活动角色定义", "软件配置管理库", "基线列表", "软件风险管理表"}

        def _is_caption(txt):
            if not txt or len(txt) > 20:
                return False
            return (txt.endswith("表") or txt.startswith("表") or txt in extra_caps)

        def _ensure_keep_next(p):
            ppr = p.find(q("pPr"))
            if ppr is None:
                ppr = _et.Element(q("pPr"))
                p.insert(0, ppr)
            if ppr.find(q("keepNext")) is None:
                # keepNext 须在 pPr 子元素序列前部（schema 顺序：先于 jc/ind 等）
                ppr.insert(0, _et.Element(q("keepNext")))
                return 1
            return 0

        fixed = 0
        # 袁总 2026-09-03（再次修正）：把"标题 + 其后所有段落 + 表格"绑成一大块
        # 反而有害——Word 实测会留出【整页空白】（第35页全空，表23 被推到36页）。
        # 正确策略：只在"标题紧贴表格"（中间至多 1 个空段落）时绑定；
        # 标题后若有其他有内容的段落（如连续的层级标题），不绑定，避免大块推页。
        # 先收集文档序的顶层元素序列
        seq = []
        for el in root.iter():
            if el.tag in (q("p"), q("tbl")):
                par = el.getparent()
                if par is not None and par.tag == q("tc"):
                    continue
                seq.append(el)
        for i, el in enumerate(seq):
            if el.tag != q("p"):
                continue
            txt = "".join((t.text or "") for t in el.iter(q("t"))).strip()
            if not _is_caption(txt):
                continue
            # 向后看：标题后第 1 / 第 2 个元素
            nxt1 = seq[i + 1] if i + 1 < len(seq) else None
            nxt2 = seq[i + 2] if i + 2 < len(seq) else None
            if nxt1 is not None and nxt1.tag == q("tbl"):
                fixed += _ensure_keep_next(el)          # 标题紧贴表格
            elif (nxt1 is not None and nxt1.tag == q("p")
                  and not "".join((t.text or "") for t in nxt1.iter(q("t"))).strip()
                  and nxt2 is not None and nxt2.tag == q("tbl")):
                # 标题 + 一个空段落 + 表格：标题与空段落都绑（空段落是上一版
                # 遗漏导致表格跳页的关键）
                fixed += _ensure_keep_next(el)
                fixed += _ensure_keep_next(nxt1)
        data["word/document.xml"] = _et.tostring(
            root, encoding="UTF-8", xml_declaration=True, standalone=True)
        with _zf.ZipFile(docx_path, "w", _zf.ZIP_DEFLATED) as zo:
            for n in names:
                zo.writestr(n, data[n])
        print("[_add_caption_keepnext] keepNext段落数=%d" % fixed)
    except Exception as _e:
        _sh.copy(bak, docx_path)
        print("[_add_caption_keepnext] 失败回退: %s" % _e)
    finally:
        try:
            os.remove(bak)
        except OSError:
            pass


def _strip_breaks_between_caption_and_table(docx_path):
    """袁总 2026-09-03（空白页/标题表格分离的真因）：模板在表标题与其表格之间
    留了【两个含硬分页符的空段落】(<w:br w:type="page"/>)，Word 逐字渲染会
    连续换两页 → 中间产生【整页空白】（实测第35页全空，表23 被推到第36页），
    且硬分页让 keepNext 失效（标题被强行留在上页）。

    处理：对每个表标题，删除它与紧随其后那张表之间的所有硬分页符 br/page；
    若因此出现多个连续空段落，只保留一个（作标题与表格的分隔）。
    分页交给 Word 自然排版 + keepNext，不再硬分页。
    任何异常回退原文件。"""
    import zipfile as _zf
    import shutil as _sh
    from lxml import etree as _et
    bak = docx_path + ".brk.bak"
    _sh.copy(docx_path, bak)
    try:
        z = _zf.ZipFile(bak)
        names = z.namelist()
        data = {n: z.read(n) for n in names}
        z.close()
        W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

        def q(t):
            return "{%s}%s" % (W, t)

        def _is_caption2(txt):
            if not txt or len(txt) > 20:
                return False
            return (txt.endswith("表") or txt.startswith("表") or txt in
                    {"配置管理活动角色定义", "软件配置管理库", "基线列表", "软件风险管理表"})

        root = _et.fromstring(data["word/document.xml"])
        seq = []
        for el in root.iter():
            if el.tag in (q("p"), q("tbl")):
                par = el.getparent()
                if par is not None and par.tag == q("tc"):
                    continue
                seq.append(el)

        removed_br = 0
        removed_p = 0
        for i, el in enumerate(seq):
            if el.tag != q("p"):
                continue
            txt = "".join((t.text or "") for t in el.iter(q("t"))).strip()
            if not _is_caption2(txt):
                continue
            # 找紧随其后的表格
            tbl_at = None
            for j in range(i + 1, min(i + 5, len(seq))):
                if seq[j].tag == q("tbl"):
                    tbl_at = j
                    break
            if tbl_at is None:
                continue
            # 1) 删除标题与表格之间所有硬分页符
            for j in range(i + 1, tbl_at):
                p = seq[j]
                for br in list(p.iter(q("br"))):
                    if br.get(q("type")) == "page":
                        br.getparent().remove(br)
                        removed_br += 1
            # 2) 连续空段落只保留一个
            empties = []
            for j in range(i + 1, tbl_at):
                p = seq[j]
                t = "".join((x.text or "") for x in p.iter(q("t"))).strip()
                if not t:
                    empties.append(j)
            for j in reversed(empties[1:]):
                p = seq[j]
                par = p.getparent()
                if par is not None:
                    par.remove(p)
                    removed_p += 1
        data["word/document.xml"] = _et.tostring(
            root, encoding="UTF-8", xml_declaration=True, standalone=True)
        with _zf.ZipFile(docx_path, "w", _zf.ZIP_DEFLATED) as zo:
            for n in names:
                zo.writestr(n, data[n])
        print("[_strip_breaks_between_caption_and_table] 删除硬分页符=%d, 合并多余空段=%d"
              % (removed_br, removed_p))
    except Exception as _e:
        _sh.copy(bak, docx_path)
        print("[_strip_breaks_between_caption_and_table] 失败回退: %s" % _e)
    finally:
        try:
            os.remove(bak)
        except OSError:
            pass


def _strip_cover_to_toc_blanks(docx_path):
    """袁总 2026-09-04（正文前空白页·实测 P3 全空）：封面签署区最后一张表
    （更改栏表）之后、"目  录"标题之前残留 2 个纯空段，Word 把它们渲染成
    独立空白页（封面 P1、签署区 P2、空白 P3、目录 P4）。

    修复：删除目录标题之前、封面签署区之后的所有【纯空段】
    （无文本、无 pageBreakBefore、无 <w:br type=page/>、无 sectPr、无图形），
    让目录紧贴签署区，空白页消失；目录是否从新页开始交给 Word 自然排版。
    绝不删除带分页符/分节符/图形的段落，避免破坏排版。任何异常回退原文件。"""
    import zipfile as _zf
    import shutil as _sh
    from lxml import etree as _et
    bak = docx_path + ".covtoc.bak"
    _sh.copy(docx_path, bak)
    try:
        z = _zf.ZipFile(bak)
        names = z.namelist()
        data = {n: z.read(n) for n in names}
        z.close()
        W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

        def q(t):
            return "{%s}%s" % (W, t)

        root = _et.fromstring(data["word/document.xml"])
        body = root.find(q("body"))

        # 定位目录标题段（封面后第一个"目  录"）
        toc_i = None
        for i, el in enumerate(body):
            if el.tag != q("p"):
                continue
            txt = "".join((t.text or "") for t in el.iter(q("t"))).strip()
            if re.match(r"^目\s*录", txt):
                toc_i = i
                break
        if toc_i is None:
            return

        # 向前收集可删除的纯空段索引（遇到表/非空段/特殊段即停）
        to_delete = []
        j = toc_i - 1
        while j >= 0:
            el = body[j]
            if el.tag == q("tbl"):
                break
            if el.tag == q("p"):
                txt = "".join((t.text or "") for t in el.iter(q("t"))).strip()
                ppr = el.find(q("pPr"))
                has_pb = ppr is not None and ppr.find(q("pageBreakBefore")) is not None
                has_bp = any(br.get(q("type")) == "page"
                             for br in (ppr.iter(q("br")) if ppr is not None else []))
                has_sect = ppr is not None and ppr.find(q("sectPr")) is not None
                has_drawing = el.find(q("drawing")) is not None or el.find(q("pict")) is not None
                if txt == "" and not has_pb and not has_bp and not has_sect and not has_drawing:
                    to_delete.append(j)
                    j -= 1
                    continue
                break
            break
        # 按原始索引从大到小删除，避免删前元素导致后续索引偏移误删其他段落
        for j in sorted(to_delete, reverse=True):
            body.remove(body[j])
        data["word/document.xml"] = _et.tostring(
            root, encoding="UTF-8", xml_declaration=True, standalone=True)
        with _zf.ZipFile(docx_path, "w", _zf.ZIP_DEFLATED) as zo:
            for n in names:
                zo.writestr(n, data[n])
        print("[_strip_cover_to_toc_blanks] 删除目录前空段=%d" % len(to_delete))
    except Exception as _e:
        _sh.copy(bak, docx_path)
        print("[_strip_cover_to_toc_blanks] 失败回退: %s" % _e)
    finally:
        try:
            os.remove(bak)
        except OSError:
            pass


def _finalize_placeholders(docx_path, ph_map=None):
    """袁总 2026-09-03（第四十二轮·"不要再出现任何占位符"）：终极兜底后处理。
    扫描 document.xml + 所有 header*/footer*.xml，对每个 {{...}} 占位符：
      - ph_map 有值（非空）→ 替换为该值
      - ph_map 无键 / 值为空 → 替换为 'V1.00'（袁总拍板：默认 v1.00）
    处理 w:t 文本和 w:instrText 文本两处；不动其他结构。回退原文件。"""
    import zipfile as _zf
    import shutil as _sh
    bak = docx_path + ".fph.bak"
    _sh.copy(docx_path, bak)
    try:
        z = _zf.ZipFile(bak)
        names = z.namelist()
        data = {n: z.read(n) for n in names}
        z.close()
        # 默认兜底映射（ph_map 无键或空值时使用）
        default_value = "V1.00"

        def _resolve(m):
            key = m.group(1).strip()
            v = (ph_map or {}).get(key)
            if v:
                return v
            return default_value

        pat = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_.]*)\s*\}\}")
        # 对正文/页眉/页脚 xml 部件：替换 w:t 和 w:instrText 文本
        fixed_files = 0
        fixed_total = 0
        for n in names:
            if not n.endswith(".xml"):
                continue
            if not (n == "word/document.xml" or n.startswith("word/header")
                    or n.startswith("word/footer") or n == "word/settings.xml"
                    or n == "word/styles.xml"):
                continue
            try:
                x = data[n].decode("utf-8")
            except Exception:
                continue
            if "{{" not in x:
                continue
            new_x, count = pat.subn(_resolve, x)
            if count > 0:
                data[n] = new_x.encode("utf-8")
                fixed_files += 1
                fixed_total += count
        with _zf.ZipFile(docx_path, "w", _zf.ZIP_DEFLATED) as zo:
            for n in names:
                zo.writestr(n, data[n])
        print("[_finalize_placeholders] 兜底替换: %d处/%d文件" % (fixed_total, fixed_files))
    except Exception as _e:
        _sh.copy(bak, docx_path)
        print("[_finalize_placeholders] 失败回退: %s" % _e)
    finally:
        try:
            os.remove(bak)
        except OSError:
            pass


def _auto_size_all_tables(docx_path):
    """袁总 2026-09-04（"表 5/7/19/23/24/25 看不全"）根因修复：
    对【全文档所有表格】（含 sdt 锁定控件内的动态表 + 模板静态表）按列宽
    强制设置字号，让窄列不再"开/发/阶/段"逐字竖排：

      列宽 ≥ 2000 dxa → sz=24（小四，宽列用袁总指定字号）
      1200 ≤ 列宽 < 2000 → sz=22（小一，对齐 V1.02 默认 11pt）
      列宽 <  1200 dxa → sz=21（五号，V1.02 极窄列实测口径）

    与 _simple_tbl 内的自适应分支口径一致；本函数额外覆盖：
      ① 模板静态表（如表 19 技能培训）—— build 函数未生成，无 sz 设置；
      ② sdt 包裹的动态表——如果 _simple_tbl 调用出错也不会漏。
    任何异常回退原文件。"""
    import zipfile as _zf
    import shutil as _sh
    from lxml import etree as _et
    bak = docx_path + ".asz.bak"
    _sh.copy(docx_path, bak)
    try:
        z = _zf.ZipFile(bak)
        names = z.namelist()
        data = {n: z.read(n) for n in names}
        z.close()
        W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

        def q(t):
            return "{%s}%s" % (W, t)

        root = _et.fromstring(data["word/document.xml"])
        n_set = 0

        # 袁总 2026-09-04（表7/9「字体应统一小四」）：正文表格统一 sz=24（小四）；
        # 附录 A/B/C.1（横向节、R121 对标五号）保持 sz=21。按表格前文标题判定。
        _APPENDIX_MARKS = ("附录A", "附录B", "附录C", "表C.1",
                           "项目风险管理表", "利益相关方参与计划", "数据管理表")
        def _col_size(w, cap=""):
            if any(m in (cap or "") for m in _APPENDIX_MARKS):
                return 21
            return 24

        # 收集每个表格对应的前文标题，用于区分附录表（保持五号）/正文表（小四）
        _cap_map = {}
        _last_cap = [""]
        def _walk(parent):
            for el in parent:
                if el.tag == q("p"):
                    t = "".join((x.text or "") for x in el.iter(q("t")))
                    if t.strip():
                        _last_cap[0] = t.strip()
                elif el.tag == q("sdt"):
                    _walk(el)
                elif el.tag == q("tbl"):
                    _cap_map[id(el)] = _last_cap[0]
        _walk(root.find(q("body")))

        for tbl in root.iter(q("tbl")):
            # 跳过嵌套表（父级是 tc 的外层表已整体适配，嵌套表跟随父表）
            if tbl.getparent() is not None and tbl.getparent().tag == q("tc"):
                continue
            g = tbl.find(q("tblGrid"))
            if g is None:
                continue
            cols = [int(c.get(q("w"), 0)) for c in g.findall(q("gridCol"))]
            if not cols:
                continue
            for tr in tbl.findall(q("tr")):
                cells = tr.findall(q("tc"))
                for i, tc in enumerate(cells):
                    if i >= len(cols):
                        continue
                    sz = _col_size(cols[i], _cap_map.get(id(tbl), ""))
                    for r in tc.iter(q("r")):
                        rpr = r.find(q("rPr"))
                        if rpr is None:
                            rpr = _et.Element(q("rPr"))
                            r.insert(0, rpr)
                        # 删旧 sz/szCs 后写新值
                        for old in list(rpr.findall(q("sz"))):
                            rpr.remove(old)
                        for old in list(rpr.findall(q("szCs"))):
                            rpr.remove(old)
                        sze = _et.SubElement(rpr, q("sz"))
                        sze.set(q("val"), str(sz))
                        szcse = _et.SubElement(rpr, q("szCs"))
                        szcse.set(q("val"), str(sz))
                        n_set += 1

        data["word/document.xml"] = _et.tostring(
            root, encoding="UTF-8", xml_declaration=True, standalone=True)
        with _zf.ZipFile(docx_path, "w", _zf.ZIP_DEFLATED) as zo:
            for n in names:
                zo.writestr(n, data[n])
        print("[_auto_size_all_tables] 强制设字号 run 数=%d" % n_set)
    except Exception as _e:
        try:
            _sh.copy(bak, docx_path)
        except Exception:
            pass
        print("[_auto_size_all_tables] 失败回退: %s" % _e)


def _trim_trailing_empty_paragraphs(docx_path):
    """袁总 2026-09-03：删除文档末尾（sectPr 之前）多余的空段落，
    消除 Word 渲染出的【末页空白页】。只删末尾连续的无文本、无分页符、
    无图形对象的空段落，遇到有内容的段落立即停止。
    任何异常回退原文件。"""
    import zipfile as _zf
    import shutil as _sh
    from lxml import etree as _et
    bak = docx_path + ".tmd.bak"
    _sh.copy(docx_path, bak)
    try:
        z = _zf.ZipFile(bak)
        names = z.namelist()
        data = {n: z.read(n) for n in names}
        z.close()
        W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

        def q(t):
            return "{%s}%s" % (W, t)

        root = _et.fromstring(data["word/document.xml"])
        body = root.find(q("body"))
        if body is None:
            return
        removed = 0
        i = len(body) - 1
        while i >= 0:
            el = body[i]
            if el.tag == q("sectPr"):
                i -= 1
                continue
            if el.tag == q("p"):
                txt = "".join((t.text or "") for t in el.iter(q("t"))).strip()
                has_obj = any(x.tag in (q("br"), q("drawing"), q("pict"),
                                        q("object")) for x in el.iter())
                # 袁总 2026-09-04（"48页那根横线把它放在47页"）：
                # 文档末尾那个空段落里带 <w:pict><w:line> —— 正是那根【横线】。
                # 旧逻辑遇到含对象的段落直接 break，导致它前面 7 个纯空段落
                # 一个都删不掉，横线被这些空段落挤到第 48 页。
                # 现改为：纯空段落照删；【空但含图形对象】的段落保留并【继续往前】删，
                # 让横线上移一页（48 页 → 47 页）。遇有文本的段落才停。
                if not txt:
                    if not has_obj:
                        body.remove(el)
                        removed += 1
                    i -= 1
                    continue
            break
        data["word/document.xml"] = _et.tostring(
            root, encoding="UTF-8", xml_declaration=True, standalone=True)
        with _zf.ZipFile(docx_path, "w", _zf.ZIP_DEFLATED) as zo:
            for n in names:
                zo.writestr(n, data[n])
        print("[_trim_trailing_empty_paragraphs] 删除末尾空段落=%d" % removed)
    except Exception as _e:
        _sh.copy(bak, docx_path)
        print("[_trim_trailing_empty_paragraphs] 失败回退: %s" % _e)
    finally:
        try:
            os.remove(bak)
        except OSError:
            pass


def _separate_adjacent_tables(docx_path):
    """袁总 2026-09-03（表22/23"和到一起"根因）：OOXML 规范中两张相邻的 w:tbl
    之间无段落分隔时，Word 将其渲染合并为一张表。模板里相邻的两个表格占位符
    段落（如 {{table.org_chart}} 与 {{table.human_resource}}）被整表替换后，
    原占位段落消失，两张表直接相邻即触发合并。
    本函数在所有同父级相邻表格对之间插入空段落 <w:p/> 强制分隔。
    任何异常回退原文件，保证文档不损坏。"""
    import zipfile as _zf
    import shutil as _sh
    from lxml import etree as _et
    bak = docx_path + ".sep.bak"
    _sh.copy(docx_path, bak)
    try:
        z = _zf.ZipFile(bak)
        names = z.namelist()
        data = {n: z.read(n) for n in names}
        z.close()
        W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

        def q(t):
            return "{%s}%s" % (W, t)

        root = _et.fromstring(data["word/document.xml"])
        sep = 0
        for parent in list(root.iter()):
            children = list(parent)
            idxs = []
            for i in range(len(children) - 1):
                if children[i].tag == q("tbl") and children[i + 1].tag == q("tbl"):
                    idxs.append(i + 1)
            for i in reversed(idxs):
                parent.insert(i, _et.Element(q("p")))
                sep += 1
        data["word/document.xml"] = _et.tostring(
            root, encoding="UTF-8", xml_declaration=True, standalone=True)
        with _zf.ZipFile(docx_path, "w", _zf.ZIP_DEFLATED) as zo:
            for n in names:
                zo.writestr(n, data[n])
        print("[_separate_adjacent_tables] 分隔相邻表数=%d" % sep)
    except Exception as _e:
        _sh.copy(bak, docx_path)
        print("[_separate_adjacent_tables] 失败回退: %s" % _e)
    finally:
        try:
            os.remove(bak)
        except OSError:
            pass


_FLD_BEGIN = '<w:fldChar w:fldCharType="begin"/>'
_FLD_END = '<w:fldChar w:fldCharType="end"/>'
_FLD_SEPARATE = '<w:fldChar w:fldCharType="separate"/>'


def _iter_field_spans(x):
    """按【标签平衡】逐个返回域片段 (start, end)。

    袁总 2026-09-03：目录条目是【嵌套域】（HYPERLINK 包 PAGEREF），
    非贪婪正则 begin.*?end 会错配（取到 HYPERLINK 的 begin + PAGEREF 的 end），
    导致读到的指令是 HYPERLINK 而非 PAGEREF → TOC 页码永远写不进去。
    本函数遇 begin 深度+1、遇 end 深度-1，深度归零即为完整域。"""
    pos = 0
    while True:
        b = x.find(_FLD_BEGIN, pos)
        if b < 0:
            return
        depth = 0
        p = b + len(_FLD_BEGIN)     # 跳过自身 begin，否则自己被算作嵌套
        while True:
            nb = x.find(_FLD_BEGIN, p)
            ne = x.find(_FLD_END, p)
            if ne < 0:
                return
            if 0 <= nb < ne:
                depth += 1
                p = nb + len(_FLD_BEGIN)
            else:
                seg_end = ne + len(_FLD_END)
                if depth == 0:
                    yield (b, seg_end)
                    pos = seg_end
                    break
                depth -= 1
                p = ne + len(_FLD_END)


def _seg_is_page_field(x, begin_pos):
    """判断 begin_pos 处的域是否为页码类域（NUMPAGES / PAGEREF）：
    取其后 900 字符内第一个 instrText 的指令文本判断。
    仅页码类域才标记 w:dirty（避免把 eq/HYPERLINK/SEQ 等域也设脏导致打开变慢）。"""
    seg = x[begin_pos:begin_pos + 900]
    m = re.search(r'<w:instrText[^>]*>([^<]*)</w:instrText>', seg)
    if not m:
        return False
    instr = m.group(1).strip()
    return instr.startswith("NUMPAGES") or instr.startswith("PAGEREF")


def _update_fields_with_word(docx_path):
    """袁总 2026-09-03（封面总页码错误根因）：NUMPAGES 域的缓存结果在生成时
    无法精确计算（真实页数依赖 Word 排版分页），仅靠 settings.xml 的
    updateFields 提示在部分 Word 配置下打开时并不重算（袁总实测封面仍是旧值）。

    实现方式（袁总 2026-09-03 定稿 + 同日复核修正）：
    1) 【COM 子进程隔离】——uvicorn worker 是 MTA 环境，进程内直接调 COM 时
       ComputeStatistics 可用但 Bookmarks/Range 静默失败（实测 pagerefs 恒空、
       TOC 页码写不进去，坑17）。现改为 subprocess 拉起独立子进程
       （backend/services/word_pages.py，纯 STA）读页数与书签页码，JSON 回传。
    2) 【绝不 Save】——Word COM 保存会产出 sdtContent 不闭合的坏 XML（坑50），
       故只在子进程里【只读】读取，改写由 Python 直接操作 document.xml 域缓存。
    3) 页码真值取书签所在页的 Information(1)（逻辑页码），不用 f.Result.Text
       （后者受 TOC 更新顺序影响，实测偏移 1 页）。
    无 Word/pywin32 或子进程失败时跳过，不阻断生成。"""
    import subprocess
    import sys as _sys
    pages = None
    pagerefs = {}
    try:
        proc = subprocess.run(
            [_sys.executable, "-m", "backend.services.word_pages",
             os.path.abspath(docx_path)],
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))),
            capture_output=True, timeout=300,
        )
        out = (proc.stdout or b"").decode("utf-8", errors="replace")
        if "@@JSON@@" in out:
            payload = out.split("@@JSON@@", 1)[1]
            # 只取第一个 JSON 对象（避免子进程其它输出干扰）
            import json as _json
            depth, end = 0, None
            for i, ch in enumerate(payload):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            data_j = _json.loads(payload[:end] if end else payload)
            pages = data_j.get("pages")
            pagerefs = data_j.get("pagerefs") or {}
            if data_j.get("error"):
                print("[_update_fields_with_word] 子进程报错: %s" % data_j["error"])
    except Exception as _e:
        print("[_update_fields_with_word] 子进程取页数失败(不阻断): %s" % _e)

    if not pages:
        print("[_update_fields_with_word] 未取得页数，保留原域缓存")
        return
    # Python 层改写域结果缓存：NUMPAGES（封面总页数）+ PAGEREF（目录各章节页码）
    import zipfile as _zf
    import shutil as _sh
    bak = docx_path + ".pg.bak"
    _sh.copy(docx_path, bak)
    try:
        z = _zf.ZipFile(bak)
        names = z.namelist()
        data = {n: z.read(n) for n in names}
        z.close()
        x = data["word/document.xml"].decode("utf-8")
        replaced = [0, 0]
        # 袁总 2026-09-03（TOC 页码终极方案）：目录条目是
        # 【HYPERLINK 内嵌 PAGEREF】的嵌套结构，按"域片段"整体处理时
        # 取到的指令是外层 HYPERLINK，内层 PAGEREF 永远轮不到。
        # 改为：按 instrText 逐个定位——每条页码指令，找它之后最近的
        # separate → 替换其后的第一个 w:t 为真实页码。绕开嵌套，简单可靠。
        edits = []      # [(start, end, new_text)]
        for im in re.finditer(r'<w:instrText[^>]*>([^<]*)</w:instrText>', x):
            instr = im.group(1).strip()
            if instr.startswith("NUMPAGES"):
                val = str(pages)
            elif instr.startswith("PAGEREF") and pagerefs:
                toks = instr.split()
                bm = toks[1] if len(toks) > 1 else ""
                val = pagerefs.get(bm)
                if not val:
                    continue
            else:
                continue
            sp = x.find(_FLD_SEPARATE, im.end())
            if sp < 0:
                continue
            tw = re.search(r'<w:t[^>]*>[^<]*</w:t>', x[sp:sp + 900])
            if not tw:
                continue
            old_seg = tw.group(0)
            new_seg = re.sub(r'(<w:t[^>]*>)[^<]*(</w:t>)',
                             lambda mm: mm.group(1) + val + mm.group(2),
                             old_seg, count=1)
            if new_seg == old_seg:
                continue
            edits.append((sp + tw.start(), sp + tw.end(), new_seg))
            replaced[0 if instr.startswith("NUMPAGES") else 1] += 1
        # 倒序替换，避免位置偏移
        for (s0, e0, new_seg) in reversed(edits):
            x = x[:s0] + new_seg + x[e0:]
        data["word/document.xml"] = x.encode("utf-8")
        with _zf.ZipFile(docx_path, "w", _zf.ZIP_DEFLATED) as zo:
            for n in names:
                zo.writestr(n, data[n])
        print("[_update_fields_with_word] 页数=%s, NUMPAGES=%d处, TOC页码=%d处"
              % (pages, replaced[0], replaced[1]))
    except Exception as _e:
        _sh.copy(bak, docx_path)
        print("[_update_fields_with_word] 改写失败回退: %s" % _e)
    finally:
        try:
            os.remove(bak)
        except OSError:
            pass


def _center_index_columns(docx_path):
    """项目方 2026-09-02：所有表格"序号"列统一居中（水平+垂直）+ 清理多余空格。
    遍历 document.xml 全部 w:tbl（含 sdtContent 内的动态表），
    表头文本为"序号"的列 → 该列所有单元格 vAlign=center + 段落 jc=center。

    袁总 2026-09-02：含序号列的数据表，表头与表体单元格内有多余空格
    （模板静态表残留的前后空白/纯空白文本，如 '12.8 '、'  '），
    以及模板继承的悬挂缩进 ind(left=-480 firstLine=480) 造成的视觉偏移留白。
    本函数对这类表【全部单元格】strip 文本、清空纯空白，
    并对序号列移除 w:ind（序号列不需要缩进，左缩进会让序号视觉偏移）。
    签署页/文件分发等【无序号列】的手工排版表不处理（其空格用于对齐，保留原貌）。
    任何异常回退原文件，保证文档不损坏。"""
    import zipfile as _zf
    import shutil as _sh
    from lxml import etree as _et
    bak = docx_path + ".idx.bak"
    _sh.copy(docx_path, bak)
    try:
        z = _zf.ZipFile(bak)
        names = z.namelist()
        data = {n: z.read(n) for n in names}
        z.close()
        W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

        def q(t):
            return "{%s}%s" % (W, t)

        root = _et.fromstring(data["word/document.xml"])
        fixed = 0
        stripped = 0
        # 靠空格手工对齐的固定格式表（签署页/文件分发/更改栏）原来整体 SKIP，
        # 但 cell#62 介质发放、cell#63 纸质/磁盘/光盘 在 SKIP 表内时其前后空格无法清理，
        # 袁总 2026-09-03 反馈"表格里还是有空格"。
        # 现取消表级 SKIP：strip() 只去【前后】空格不动【中间】对齐空格
        # （如"纸    质"中间多空格完整保留），文件分发表/更改栏对齐不被破坏。
        for tbl in root.iter(q("tbl")):
            rows = tbl.findall(q("tr"))
            if not rows:
                continue
            # 袁总 2026-09-02（第三十一轮第二轮）：含"序号"列的表，强制 tblLayout=fixed
            # + 让 textDirection=lrTb 真正生效。autofit 模式下 Word 重算列宽时
            # 可能把"序号"列缩到不够两字横排（约 600dxa），导致个别表仍竖排；
            # 强制 fixed 后 Word 严格按 gridCol/tcW 的 1100 dxa 渲染，横排生效。
            for ci0, c0 in enumerate(rows[0].findall(q("tc"))):
                t0 = "".join((x.text or "") for x in c0.iter(q("t"))).strip()
                if re.sub(r'[\s\u00A0\u3000]+', '', t0) == "序号":
                    _tblpr0 = tbl.find(q("tblPr"))
                    if _tblpr0 is not None:
                        _layout = _tblpr0.find(q("tblLayout"))
                        if _layout is not None:
                            _layout.set(q("type"), "fixed")
                        else:
                            _layout = _et.SubElement(_tblpr0, q("tblLayout"))
                            _layout.set(q("type"), "fixed")
                    break
            # 袁总 2026-09-02：所有表统一去单元格文本前后空白。
            # 袁总 2026-09-03：取消原 SKIP_TRIM_HEADS 表级跳过——
            # 之前 file 分发/更改栏靠空格对齐的表被整体跳过，导致 cell#62/#63
            # 介质发放/纸质 等前后空格残留。strip() 只去前后不动中间，对齐空格安全。
            for r in rows:
                for c in r.findall(q("tc")):
                    for _t in c.iter(q("t")):
                        if _t.text is not None:
                            _s = _t.text.strip()
                            if _t.text != _s:
                                _t.text = _s
                                stripped += 1
            # 表头行里找"序号"列（兼容"序 号"等空格写法）
            idx_cols = []
            for i, c in enumerate(rows[0].findall(q("tc"))):
                t = "".join((x.text or "") for x in c.iter(q("t"))).strip()
                if t.replace(" ", "").replace("\u3000", "") == "序号":
                    idx_cols.append(i)
            if not idx_cols:
                continue
            # 袁总 2026-09-02（第三十一轮）：序号列表头"序号"两字在模板里无分隔符，
            # 修复（三管齐下）：
            # ① 清掉模板里的 <w:snapToGrid w:val="0"/>（关键！这是让两字独立布局的元凶）
            # ② 两字间加不间断空格 \u00A0 + xml:space=preserve（语义兜底）
            # ③ 单元格宽 900 → 1100 dxa 留出余量
            # 实际 Word COM 渲染验证（2026-09-02）：必须 ①+② 同时做才能横排，
            # 单 ② 或单 ③ 都不够。
            for i in idx_cols:
                _ht = rows[0].findall(q("tc"))[i]
                # ① 清掉序号列表头段落 + 所属表 tblPr 的 snapToGrid
                # （snapToGrid 多在 tblPr 内，不在 pPr 里——之前漏了）
                for _p in _ht.iter(q("p")):
                    _ppr = _p.find(q("pPr"))
                    if _ppr is not None:
                        _stg = _ppr.find(q("snapToGrid"))
                        if _stg is not None:
                            _ppr.remove(_stg)
                _tblpr = tbl.find(q("tblPr"))
                if _tblpr is not None:
                    _stg = _tblpr.find(q("snapToGrid"))
                    if _stg is not None:
                        _tblpr.remove(_stg)
                # ② 序号列单元格加 <w:textDirection w:val="lrTb"/>（关键！左→右横排）
                # Word 对东亚"两字 token"默认竖排（即使有 noWrap + 大列宽 + 不间断空格）。
                # textDirection=lrTb (left-to-right, top-to-bottom) 强制水平方向渲染。
                # 这是 Word COM 实测（2026-09-02 第四轮）唯一让"序\u00A0号"两字横排的属性。
                _cp0 = _ht.find(q("tcPr"))
                if _cp0 is None:
                    _cp0 = _et.SubElement(_ht, q("tcPr"))
                    _ht.insert(0, _cp0)
                # 移除旧的 textDirection
                for old in _cp0.findall(q("textDirection")):
                    _cp0.remove(old)
                _td = _et.SubElement(_cp0, q("textDirection"))
                _td.set(q("val"), "lrTb")
                # ③ 两字间插不间断空格 + ④ 字号缩 9pt（保险）
                for _t in _ht.iter(q("t")):
                    if _t.text == "序号":
                        _t.text = "序\u00A0号"
                        _t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                        stripped += 1
            # 序号列加宽到 1500 dxa（袁总 2026-09-02 第31轮第三轮：textDirection=lrTb + fixed
            # tblLayout + 加大列宽，三管齐下才让部分"序号"表横排——但 page 12 仍竖排。
            # 再加 1500 dxa 给足余量，确保"序\u00A0号"两字 + 数字列绝对能横排）。
            # 关键：fixed 布局下 Word 优先按 tblGrid/gridCol 渲染，
            # 只改 tcW 无效，必须 gridCol 与 tcW 同步改。
            grid = tbl.find(q("tblGrid"))
            if grid is not None:
                gcs = grid.findall(q("gridCol"))
                for i in idx_cols:
                    if i < len(gcs):
                        gcs[i].set(q("w"), "1500")
            # 对标 R121（袁总 2026-09-02）：数据类表（含序号列）整表内容居中，
            # 不止序号列——R121 数据表几乎所有单元格均为水平+垂直居中。
            for r in rows:
                cells = r.findall(q("tc"))
                for i in range(len(cells)):
                    if i in idx_cols:
                        _cp = cells[i].find(q("tcPr"))
                        if _cp is None:
                            _cp = _et.SubElement(cells[i], q("tcPr"))
                            cells[i].insert(0, _cp)
                        _cw = _cp.find(q("tcW"))
                        if _cw is not None:
                            _cw.set(q("w"), "900")
                        # 序号列单元格加 noWrap：防表头"序号"被自动分两行。
                        # （袁总 2026-09-02 全文档所有有序号表的通用问题；含模板静态表，
                        #   noWrap 插到 vAlign 前以尽量贴近 OOXML tcPr 元素顺序）
                        if _cp.find(q("noWrap")) is None:
                            _nw = _et.Element(q("noWrap"))
                            _va = _cp.find(q("vAlign"))
                            if _va is not None:
                                _cp.insert(list(_cp).index(_va), _nw)
                            else:
                                _cp.append(_nw)
                        # 袁总 2026-09-02 第31轮第三轮：序号列宽度 1500 dxa（与 gridCol 同步）。
                        _cw = _cp.find(q("tcW"))
                        if _cw is not None:
                            _cw.set(q("w"), "1500")
                    c = cells[i]
                    tcPr = c.find(q("tcPr"))
                    if tcPr is None:
                        tcPr = _et.SubElement(c, q("tcPr"))
                        c.insert(0, tcPr)
                    vA = tcPr.find(q("vAlign"))
                    if vA is None:
                        vA = _et.SubElement(tcPr, q("vAlign"))
                    vA.set(q("val"), "center")
                    for p in c.findall(q("p")):
                        ppr = p.find(q("pPr"))
                        if ppr is None:
                            ppr = _et.SubElement(p, q("pPr"))
                            p.insert(0, ppr)
                        # 袁总 2026-09-02：序号列移除模板继承的悬挂缩进
                        # （ind left=-480/firstLine=480 会让序号视觉偏移、产生留白）。
                        if i in idx_cols:
                            _ind = ppr.find(q("ind"))
                            if _ind is not None:
                                ppr.remove(_ind)
                        jc = ppr.find(q("jc"))
                        if jc is None:
                            jc = _et.SubElement(ppr, q("jc"))
                        jc.set(q("val"), "center")
                    # （文本去空白已在表级别统一处理，此处不重复）
            fixed += 1
        data["word/document.xml"] = _et.tostring(
            root, encoding="UTF-8", xml_declaration=True, standalone=True)
        with _zf.ZipFile(docx_path, "w", _zf.ZIP_DEFLATED) as zo:
            for n in names:
                zo.writestr(n, data[n])
        print("[_center_index_columns] 序号列居中表格数=%d, 清理空格文本数=%d"
              % (fixed, stripped))
    except Exception as _e:
        _sh.copy(bak, docx_path)
        print("[_center_index_columns] 失败回退: %s" % _e)
    finally:
        try:
            os.remove(bak)
        except OSError:
            pass


def _apply_doc_fields(docx_path, total_pages=None):
    """项目方 2026-09-02：封面"共 N 页"改为 NUMPAGES 域 + 打开自动刷新。
    1) settings.xml 加 <w:updateFields w:val="true"/>（Word 打开/打印时自动重算域）；
    2) 把页数哨兵 %TP% 换成 NUMPAGES 域（w:fldSimple），域结果随文档内容自动更新，
       不再依赖生成时估算的固定数字。

    袁总 2026-09-03（第三十三轮）：total_pages 改为可选，None 时内部自行统计。
    原因：原先页数在"表格宽度适配/删除冗余段落"【之前】统计，后续步骤改变了
    文档实际页数，导致封面"（共 18 页）"与实际不符。
    现在在所有会改变页数的后处理【之后】再调用一次本函数（不传 total_pages），
    用最新内容重新统计并刷新域内结果。
    任何异常回退原文件，保证文档不损坏。"""
    if total_pages is None:
        total_pages = _estimate_pages(docx_path)
    import zipfile as _zf
    import shutil as _sh
    bak = docx_path + ".fld.bak"
    _sh.copy(docx_path, bak)
    try:
        z = _zf.ZipFile(bak)
        names = z.namelist()
        data = {n: z.read(n) for n in names}
        z.close()
        # (1) 打开时自动刷新域
        if "word/settings.xml" in data:
            st = data["word/settings.xml"].decode("utf-8")
            if "<w:updateFields" not in st:
                st = st.replace("</w:settings>",
                                '<w:updateFields w:val="true"/></w:settings>')
                data["word/settings.xml"] = st.encode("utf-8")
        # (2b) 把 NUMPAGES 域的【域内结果】更新为估算页数。
        # 关键：域结果必须位于 separate 与 end 之间（域内），这样 Word 打开时
        # updateFields 才会用真实总页数覆盖它，实现"新增页自动联动"。
        # 严禁写到域外——域外是普通文本，永远不会更新（历史 bug：数字曾被插到
        # fldChar end 之后，导致"（共 18 页）"是死数字，加页不变）。
        x = data["word/document.xml"].decode("utf-8")

        def _np_result_sub(m):
            # 向前找最近的域指令，确认是 NUMPAGES，避免误改 PAGEREF/TOC 等
            # 其它域的结果（否则目录页码会被整体改成总页数）。
            before = x[max(0, m.start() - 1500):m.start()]
            instrs = re.findall(r"<w:instrText[^>]*>([^<]*)</w:instrText>", before)
            if not instrs or "NUMPAGES" not in instrs[-1]:
                return m.group(0)
            return (m.group(1) + m.group(2) + str(total_pages)
                    + m.group(3) + m.group(4))

        np_res_pat = re.compile(
            r'(<w:fldChar[^>]*w:fldCharType="separate"[^>]*/></w:r>)'
            r'(\s*<w:r>\s*<w:rPr>(?:(?!</w:rPr>).)*?<w:noProof/>.*?</w:rPr>'
            r'\s*<w:t>)\d+(</w:t>\s*</w:r>)'
            r'(\s*<w:r>(?:<w:rPr>.*?</w:rPr>)?'
            r'<w:fldChar[^>]*w:fldCharType="end"[^>]*/></w:r>)',
            re.S)
        x = np_res_pat.sub(_np_result_sub, x)
        data["word/document.xml"] = x.encode("utf-8")

        # (3) 页数哨兵 -> NUMPAGES 域
        # 注意：%TP% 常与前后文字同在一个 w:t 内（如"共 %TP% 页"），
        # 不能整元素替换，需把该 run 拆成 [前文字 run] + [域] + [后文字 run]。
        x = data["word/document.xml"].decode("utf-8")
        field = ('<w:fldSimple w:instr=" NUMPAGES ">'
                 '<w:r><w:rPr><w:noProof/></w:rPr><w:t>%d</w:t></w:r>'
                 '</w:fldSimple>' % total_pages)

        def _tp_sub(m):
            whole = m.group(0)
            t = re.search(r"<w:t[^>]*>([^<]*%TP%[^<]*)</w:t>", whole)
            if not t:
                return whole
            inner = t.group(1)
            pre, post = inner.split("%TP%", 1)
            rpr = re.search(r"<w:rPr>(.*?)</w:rPr>", whole)
            rpr_s = rpr.group(1) if rpr else ""
            run_tpl = '<w:r><w:rPr>%s</w:rPr><w:t xml:space="preserve">%s</w:t></w:r>'
            out = (run_tpl % (rpr_s, pre)) if pre else ""
            out += field
            out += (run_tpl % (rpr_s, post)) if post else ""
            return out

        if "%TP%" in x:
            # 注意：run 常带属性(<w:r w:rsidR="...">)，不能锚定无属性的 <w:r>
            x = re.sub(r"<w:r(?:\s[^>]*)?>(?:(?!</w:r>).)*?%TP%(?:(?!</w:r>).)*?</w:r>",
                       _tp_sub, x, flags=re.S)
        x = x.replace("%TP%", str(total_pages))      # 兜底：异常残留
        data["word/document.xml"] = x.encode("utf-8")
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
