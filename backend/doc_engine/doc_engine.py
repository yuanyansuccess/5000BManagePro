# -*- coding: utf-8 -*-
"""
GJB5000B 文档引擎（高内聚核心模块）

作者：袁燕

职责：把 Word/Excel 文档的「模板生成、占位符解析、数据灌装、表格替换、
文档解析（页数/分节/范围保护）」全部收敛到本文件，便于整体迁移到正式项目。

对外公开类：
    DocParser          文档解析（读取正文/表格/占位符）
    DocPageCounter     页数统计
    DocRangeProtector  文档范围保护（只读/编辑区域）
    DataResolver       解析用户填写的 JSON/YAML 数据
    TemplateMiner      从源文档采集可复用片段（表/页眉）
    WordInjector       Word 占位符灌装
    ExcelInjector      Excel 占位符灌装
    SdpPlaceholderBuilder  生成 SDP 占位符模板（REPLACEMENTS 映射 + 生成函数）
    SdpFiller          SDP 正式文档灌装（fill_scalar + 整表替换）

设计原则：高内聚、低耦合；无脏数据修复逻辑；纯业务逻辑。
"""

import os
import re
import json
import zipfile
from lxml import etree

# ===================== OOXML 命名空间 =====================
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NSMAP = {"w": W_NS}
W = "{%s}" % W_NS
QN = etree.QName


def _localname(tag):
    return etree.QName(tag).localname if isinstance(tag, str) else ""


def _ns_tag(local):
    return "{%s}%s" % (W_NS, local)


def _all_tags(parent, local):
    """返回 parent 下所有指定本地名的元素（含嵌套）。"""
    if parent is None:
        return []
    return [e for e in parent.iter() if _localname(e.tag) == local]


# ============================================================
# 一、文档解析层
# ============================================================

class DocParser:
    """解析 docx 文档：提取正文文本、表格、占位符清单。"""

    def __init__(self, path):
        self.path = path
        self._tree = None
        self._root = None

    # ---------- 内部加载 ----------
    def _load(self):
        if self._root is not None:
            return
        with zipfile.ZipFile(self.path) as z:
            xml = z.read("word/document.xml")
        self._tree = etree.fromstring(xml)
        self._root = self._tree

    def document_root(self):
        """返回 word/document.xml 的 body 根元素。"""
        self._load()
        return self._root

    # ---------- 正文文本 ----------
    def extract_text(self):
        """提取全文档纯文本（段落级合并）。"""
        self._load()
        out = []
        for p in _all_tags(self._root, "p"):
            out.append(self._para_text(p))
        return "\n".join(out)

    @staticmethod
    def _para_text(p):
        return "".join(t.text or "" for t in _all_tags(p, "t"))

    # ---------- 表格 ----------
    def extract_tables(self):
        """返回所有表格的二维文本列表。"""
        self._load()
        tables = []
        for tbl in _all_tags(self._root, "tbl"):
            rows = []
            for tr in _all_tags(tbl, "tr"):
                cells = []
                for tc in _all_tags(tr, "tc"):
                    cells.append(self._tc_text(tc))
                rows.append(cells)
            tables.append(rows)
        return tables

    @staticmethod
    def _tc_text(tc):
        return " / ".join(DocParser._para_text(p) for p in _all_tags(tc, "p"))

    @staticmethod
    def _set_tc_text(tc, text):
        """覆盖单元格首个段落的首个 w:t 文本。"""
        ps = _all_tags(tc, "p")
        if not ps:
            return
        ts = _all_tags(ps[0], "t")
        if ts:
            ts[0].text = text
        else:
            t = etree.SubElement(ps[0], _ns_tag("t"))
            t.text = text

    # ---------- 占位符 ----------
    PLACEHOLDER_RE = re.compile(r"\{\{[a-zA-Z0-9_.\-]+\}\}")

    def find_placeholders(self):
        """扫描全文档，返回去重后的占位符集合。"""
        self._load()
        found = set()
        text = etree.tostring(self._root, encoding="unicode")
        for m in self.PLACEHOLDER_RE.finditer(text):
            found.add(m.group(0))
        return found

    def placeholder_stats(self):
        """统计各类占位符数量，用于自检。"""
        phs = self.find_placeholders()
        cats = {}
        for ph in phs:
            cat = ph.split(".")[0].strip("{}")
            cats[cat] = cats.get(cat, 0) + 1
        return {"total": len(phs), "by_category": cats}


class DocPageCounter:
    """统计 docx 页数（基于分节符 + 估算，供范围保护参考）。"""

    @staticmethod
    def count_sections(path):
        """统计分节数（sectPr 个数）。"""
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml")
        root = etree.fromstring(xml)
        return len(_all_tags(root, "sectPr"))

    @staticmethod
    def count_pages_approx(path):
        """按段落数粗估页数（每页约 38 段）。仅供校验。"""
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml")
        root = etree.fromstring(xml)
        paras = _all_tags(root, "p")
        return max(1, (len(paras) + 37) // 38)


class DocRangeProtector:
    """对文档指定范围设置只读/编辑区域保护（基于书签或分节）。"""

    def __init__(self, path):
        self.path = path

    def protect_section(self, section_index, password=None):
        """对第 section_index 个分节加编辑保护。"""
        with zipfile.ZipFile(self.path) as z:
            xml = z.read("word/document.xml")
        root = etree.fromstring(xml)
        sects = _all_tags(root, "sectPr")
        if section_index < 0 or section_index >= len(sects):
            raise IndexError("分节索引越界")
        sect = sects[section_index]
        doc_protect = etree.SubElement(sect, _ns_tag("docProtect"))
        doc_protect.set(_ns_tag("edit"), "readOnly")
        if password:
            doc_protect.set(_ns_tag("pwd"), password)
        return etree.tostring(root, xml_declaration=True,
                              encoding="UTF-8", standalone=True)


# ============================================================
# 二、模板引擎层
# ============================================================

class DataResolver:
    """解析用户填写的数据源（JSON / dict），支持嵌套取值。"""

    @staticmethod
    def load(path_or_dict):
        if isinstance(path_or_dict, dict):
            return path_or_dict
        if isinstance(path_or_dict, str):
            if path_or_dict.strip().startswith("{"):
                return json.loads(path_or_dict)
            with open(path_or_dict, "r", encoding="utf-8") as f:
                return json.load(f)
        raise TypeError("DataResolver.load 仅接受 dict / JSON 字符串 / 文件路径")

    @staticmethod
    def get(data, dotted_key, default=""):
        """data['a']['b'] 形式按 'a.b' 取值，缺省返回 default。"""
        cur = data
        for part in dotted_key.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return default
        return cur


class TemplateMiner:
    """从源文档采集可复用片段（整表、页眉图片）。"""

    @staticmethod
    def extract_table_xml(path, table_index):
        """提取第 table_index 张表的完整 <w:tbl> XML 字符串。"""
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml")
        root = etree.fromstring(xml)
        tbls = _all_tags(root, "tbl")
        if table_index < 0 or table_index >= len(tbls):
            raise IndexError("表索引越界")
        return etree.tostring(tbls[table_index], encoding="unicode")

    @staticmethod
    def extract_header_pict(path):
        """提取页眉中的 VML 图片 shape（用于复用边框样式）。"""
        with zipfile.ZipFile(path) as z:
            header_xml = z.read("word/header1.xml")
        return header_xml


class WordInjector:
    """Word 占位符灌装引擎（通用，不绑定具体项目）。"""

    @staticmethod
    def fill_scalar_text(text, mapping, keys_desc=None):
        """对一段文本按 mapping（占位符->真值，键按长度降序）做替换。"""
        if keys_desc is None:
            keys_desc = sorted(mapping.keys(), key=lambda k: -len(k))
        for ph in keys_desc:
            if ph in text:
                text = text.replace(ph, mapping[ph])
        return text

    @staticmethod
    def fill_tree(root, mapping, keys_desc=None):
        """遍历 root 下所有 w:t 文本节点与元素属性做占位符替换。"""
        if keys_desc is None:
            keys_desc = sorted(mapping.keys(), key=lambda k: -len(k))
        # 1) 文本节点
        for t in _all_tags(root, "t"):
            if t.text and "{{" in t.text:
                t.text = WordInjector.fill_scalar_text(t.text, mapping, keys_desc)
        # 2) 元素属性（签名 descr / 图片说明等）
        for el in root.iter():
            for attr, val in list(el.attrib.items()):
                if "{{" in val:
                    el.attrib[attr] = WordInjector.fill_scalar_text(val, mapping, keys_desc)
        # 3) 跨 run 合并
        for p in _all_tags(root, "p"):
            WordInjector._merge_runs(p, mapping, keys_desc)
        return root

    @staticmethod
    def _merge_runs(p, mapping, keys_desc):
        runs = _all_tags(p, "r")
        if len(runs) < 2:
            return
        full = "".join((t.text or "") for r in runs for t in _all_tags(r, "t"))
        if "{{" not in full:
            return
        new_text = WordInjector.fill_scalar_text(full, mapping, keys_desc)
        # 保留第一个 run，清空其余，写入合并后文本
        first_r = runs[0]
        first_t = _all_tags(first_r, "t")
        if first_t:
            first_t[0].text = new_text
        for r in runs[1:]:
            parent = r.getparent()
            if parent is not None:
                parent.remove(r)

    @staticmethod
    def replace_table_anchor(root, anchor, table_xml):
        """将含 anchor 占位符的段落替换为整张表。"""
        for p in _all_tags(root, "p"):
            txt = DocParser._para_text(p)
            if anchor in txt:
                tbl_el = etree.fromstring(table_xml.encode("utf-8"))
                parent = p.getparent()
                idx = list(parent).index(p)
                parent.remove(p)
                parent.insert(idx, tbl_el)
                return True
        return False


class ExcelInjector:
    """Excel 占位符灌装（xlsx，基于 openpyxl 风格字符串替换）。"""

    @staticmethod
    def fill_cell_values(cells, mapping, keys_desc=None):
        if keys_desc is None:
            keys_desc = sorted(mapping.keys(), key=lambda k: -len(k))
        for row in cells:
            for i, val in enumerate(row):
                if isinstance(val, str) and "{{" in val:
                    row[i] = WordInjector.fill_scalar_text(val, mapping, keys_desc)
        return cells


# ============================================================
# 三、SDP 占位符模板生成（原 gen_sdp_placeholder_docx.py 核心）
# ============================================================

class SdpPlaceholderBuilder:
    """生成 SDP 占位符版文档（原文字 -> 占位符映射 + 生成脚本）。"""

    # ----- 原文字 -> 占位符 映射（灌装脚本反向复用）-----
    REPLACEMENTS = [
        ("CWM160-1 测发控设备嵌入式软件", "{{meta.doc_name}}"),
        ("CWM160-1 测发控设备嵌入式软件系统", "{{meta.doc_name_full}}"),
        ("CWM160-1 测发控设备嵌入式软件研制任务书", "{{meta.task_book}}"),
        ("（加盖本级精度储备印章）", "{{meta.precision_seal}}"),
        ("R121-SDP", "{{meta.doc_number}}"),
        ("R121", "{{meta.project_id}}"),
        ("D", "{{meta.doc_ver_tag}}"),
        ("V1.02", "{{meta.doc_version}}"),
        ("CWM160-1", "{{sys.short}}"),
        ("CWM160-1测发控设备嵌入式软件", "{{sys.short_full}}"),
        ("CWM160-1测发控设备嵌入式软件系统", "{{sys.full}}"),
        ("测发控设备嵌入式软件", "{{sys.product}}"),
        ("中国电子科技集团公司第二十九研究所", "{{org.full}}"),
        ("二十九所", "{{org.short}}"),
        ("CETC29", "{{org.abbr}}"),
        ("软件开发计划", "{{doc.type}}"),
        ("项目负责人", "{{role.project_lead}}"),
        ("项目技术负责人", "{{role.tech_lead}}"),
        ("软件负责人", "{{role.software_lead}}"),
        ("软件配置管理员", "{{role.cm}}"),
        ("软件质量保证员", "{{role.qa}}"),
        ("需求分析人员", "{{role.requirement}}"),
        ("设计人员", "{{role.design}}"),
        ("实现人员", "{{role.coder}}"),
        ("测试人员", "{{role.tester}}"),
        ("同行评审专家", "{{role.peer_review}}"),
        ("审批人", "{{role.approver}}"),
        ("批准人", "{{role.authorizer}}"),
        ("二〇二四年一月", "{{cm.issue_date}}"),
        ("2024年01月", "{{cm.issue_date_short}}"),
        ("2024年01月05日", "{{cm.issue_full}}"),
        ("北京", "{{cm.city}}"),
        ("硬件环境需求", "{{hw.env_title}}"),
        ("支撑环境需求", "{{hw.support_title}}"),
        ("软件环境需求", "{{sw.env_title}}"),
        ("CEC 设表022", "{{header.form_no}}"),
        # ----- 补全：当年生成遗漏 / 模板手改新增的真实字段 -----
        ("https://yuanyan/svn/R121/trunk", "{{cm.svn_trunk}}"),
        ("https://yuanyan/svn/R121/branches", "{{cm.svn_branches}}"),
        ("https://yuanyan/svn/R121/tags", "{{cm.svn_tags}}"),
        ("CubeMX", "{{hw.ide_name}}"),
        ("STM32", "{{hw.mcu_model}}"),
        ("2024年07月05日", "{{meta.approve_date}}"),
        ("CubeMX 6.0", "{{meta.ide_version}}"),
        ("V1.02", "{{meta.sw_version_example}}"),
        ("62", "{{meta.total_pages}}"),
        ("总体单位", "{{org.customer_dept}}"),
        ("中国电子科技集团公司第二十九研究所", "{{org.dev_dept}}"),
        ("软件开发组", "{{org.developer}}"),
        ("软件保障组", "{{org.maintainer}}"),
        ("R121-SQAP", "{{ref.sqap_doc_number}}"),
        ("R121-SDTD", "{{ref.sdtd_doc_number}}"),
        ("配置控制委员会", "{{role.ccb}}"),
        ("软件配置管理员", "{{role.config_manager}}"),
        ("设计人员", "{{role.designer}}"),
        ("组织级配置管理员", "{{role.org_config_manager}}"),
        ("评审专家", "{{role.reviewer}}"),
        ("评审专家（二）", "{{role.reviewer_2}}"),
        ("评审专家（三）", "{{role.reviewer_3}}"),
        ("作者", "{{role.author}}"),
        ("上位机监控程序", "{{sw.name_host}}"),
        ("BootLoader在线升级程序", "{{sw.name_iap}}"),
        ("CWM160-1测发控设备嵌入式软件系统", "{{sys.software_full}}"),
        ("CWM160-1测发控设备", "{{sys.name}}"),
    ]

    # 平台表锚点（SDP 表 9/10/11）
    PLATFORM_TABLES = {
        "hw_env_res": "{{table.hw_env_res}}",
        "sw_env_res": "{{table.sw_env_res}}",
        "stakeholders": "{{table.stakeholders}}",
    }

    def __init__(self, src_path, out_path):
        self.src_path = src_path
        self.out_path = out_path

    # ----- 公共替换原语（供子类/脚本复用）-----
    @staticmethod
    def do_replace(text):
        for orig, ph in SdpPlaceholderBuilder.REPLACEMENTS:
            text = text.replace(orig, ph)
        return text

    @staticmethod
    def replace_block(node, local):
        for child in node.iter():
            if _localname(child.tag) == local and child.text:
                child.text = SdpPlaceholderBuilder.do_replace(child.text)

    @staticmethod
    def replace_header_precision(root):
        for pict in _all_tags(root, "pict"):
            for td in _all_tags(pict, "txbxContent"):
                for p in _all_tags(td, "p"):
                    SdpPlaceholderBuilder.replace_block(p, "t")

    @staticmethod
    def remove_foreword(root):
        """删除前言章节（标题含'前言'的段落及其后续直到下一标题）。"""
        paras = list(_all_tags(root, "p"))
        start = None
        for i, p in enumerate(paras):
            if "前言" in DocParser._para_text(p):
                start = i
                break
        if start is None:
            return
        # 找到下一个一级标题作为结束
        end = len(paras)
        for j in range(start + 1, len(paras)):
            p = paras[j]
            style = p.find(_ns_tag("pPr"))
            if style is not None and style.find(_ns_tag("pStyle")) is not None:
                end = j
                break
        body = root if _localname(root.tag) == "body" else root.find(_ns_tag("body"))
        for p in paras[start:end]:
            parent = p.getparent()
            if parent is not None:
                parent.remove(p)

    @staticmethod
    def fix_header_ident_row(tr):
        """配置项标识行分格：tc[1]=doc_number, tc[3]=doc_version, 标签列保留。"""
        tcs = _all_tags(tr, "tc")
        if len(tcs) >= 6:
            DocParser._set_tc_text(tcs[1], "{{meta.doc_number}}")
            DocParser._set_tc_text(tcs[3], "{{meta.doc_version}}")
            DocParser._set_tc_text(tcs[2], "版本")
            DocParser._set_tc_text(tcs[4], "页码")

    def build(self):
        """生成占位符版文档（含去前言 + 页眉分格 + 平台表锚点）。"""
        with zipfile.ZipFile(self.src_path) as z:
            data = {n: z.read(n) for n in z.namelist()}
        # document.xml 处理
        root = etree.fromstring(data["word/document.xml"])
        body = root.find(_ns_tag("body"))
        for p in _all_tags(body, "p"):
            SdpPlaceholderBuilder.replace_block(p, "t")
        SdpPlaceholderBuilder.replace_header_precision(root)
        # 页眉分格
        for hdr in ["word/header1.xml", "word/header2.xml", "word/header3.xml"]:
            if hdr in data:
                hroot = etree.fromstring(data[hdr])
                for tr in _all_tags(hroot, "tr"):
                    if "配置项标识" in DocParser._tc_text(tr):
                        SdpPlaceholderBuilder.fix_header_ident_row(tr)
                data[hdr] = etree.tostring(hroot, xml_declaration=True,
                                           encoding="UTF-8", standalone=True)
        data["word/document.xml"] = etree.tostring(root, xml_declaration=True,
                                                   encoding="UTF-8", standalone=True)
        with zipfile.ZipFile(self.out_path, "w", zipfile.ZIP_DEFLATED) as z:
            for n, b in data.items():
                z.writestr(n, b)


# ============================================================
# 四、SDP 正式文档灌装（原 fill_sdp_template.py 核心）
# ============================================================

class SdpFiller:
    """把占位符模板灌装为正式文档。"""

    # 模板标识：多模板（SDP / SRS / 各类管理文档）共用引擎时的区分前缀
    TEMPLATE_ID = "SDP"

    # 整表锚点 -> 表片段文件（文件名带 TEMPLATE_ID 前缀，便于多模板共存）
    # 生产环境可改为数据库 builder：anchor -> build_xxx_tbl(project_id)
    TABLE_FILES = {
        "{{table.doc_scale_est}}": "sdp__tbl_doc_scale_est.xml",
        "{{table.doc_scale_reuse}}": "sdp__tbl_doc_scale_reuse.xml",
        "{{table.code_scale_est}}": "sdp__tbl_code_scale_est.xml",
        "{{table.code_scale_reuse}}": "sdp__tbl_code_scale_reuse.xml",
        "{{table.stakeholders}}": "sdp__tbl_stakeholders.xml",
        "{{table.schedule}}": "sdp__tbl_schedule.xml",
        "{{table.hw_env_res}}": "sdp__tbl_hw_env_res.xml",
        "{{table.sw_env_res}}": "sdp__tbl_sw_env_res.xml",
        "{{table.risks}}": "sdp__tbl_risks.xml",
        "{{table.stakeholder_plan}}": "sdp__tbl_stakeholder_plan.xml",
    }

    def __init__(self, tpl_path, out_path, asset_dir=None):
        self.tpl_path = tpl_path
        self.out_path = out_path
        self.asset_dir = asset_dir or os.path.dirname(os.path.abspath(tpl_path))

    def fill(self):
        # 反向映射：占位符 -> 真值（直接源自本模块 SdpPlaceholderBuilder）
        PH_MAP = {ph: orig for orig, ph in SdpPlaceholderBuilder.REPLACEMENTS}
        PH_MAP.setdefault("{{header.form_no}}", "CEC 设表022")
        PH_KEYS = sorted(PH_MAP.keys(), key=lambda k: -len(k))

        with zipfile.ZipFile(self.tpl_path) as z:
            data = {n: z.read(n) for n in z.namelist()}

        # 1) 标量回填
        for part in ["word/document.xml", "word/header1.xml",
                     "word/header2.xml", "word/header3.xml", "word/footer1.xml"]:
            if part in data:
                root = etree.fromstring(data[part])
                WordInjector.fill_tree(root, PH_MAP, PH_KEYS)
                data[part] = etree.tostring(root, xml_declaration=True,
                                            encoding="UTF-8", standalone=True)

        # 2) 整表替换
        root = etree.fromstring(data["word/document.xml"])
        for anchor, fname in self.TABLE_FILES.items():
            fpath = os.path.join(self.asset_dir, fname)
            if os.path.exists(fpath):
                with open(fpath, "r", encoding="utf-8") as f:
                    WordInjector.replace_table_anchor(root, anchor, f.read())
        data["word/document.xml"] = etree.tostring(root, xml_declaration=True,
                                                   encoding="UTF-8", standalone=True)

        with zipfile.ZipFile(self.out_path, "w", zipfile.ZIP_DEFLATED) as z:
            for n, b in data.items():
                z.writestr(n, b)

    def fill_from_data(self, ph_map, table_map):
        """库驱动灌装：ph_map=标量占位符映射, table_map=锚点->整表XML字符串。

        与 fill() 行为一致，但数据源从「REPLACEMENTS + TABLE_FILES 文件」
        改为外部传入，便于接入数据库（template_anchors 表）。
        """
        PH_KEYS = sorted(ph_map.keys(), key=lambda k: -len(k))

        with zipfile.ZipFile(self.tpl_path) as z:
            data = {n: z.read(n) for n in z.namelist()}

        # 1) 标量回填（覆盖 document + 全部 header*/footer* 部件，避免多页眉模板残留）
        for part in data:
            if part == "word/document.xml" or part.startswith("word/header") or part.startswith("word/footer"):
                if part.endswith(".xml"):
                    root = etree.fromstring(data[part])
                    WordInjector.fill_tree(root, ph_map, PH_KEYS)
                    data[part] = etree.tostring(root, xml_declaration=True,
                                                encoding="UTF-8", standalone=True)

        # 2) 整表替换（从 table_map 取，而非 TABLE_FILES 文件）
        root = etree.fromstring(data["word/document.xml"])
        for anchor, xml in table_map.items():
            WordInjector.replace_table_anchor(root, anchor, xml)
        data["word/document.xml"] = etree.tostring(root, xml_declaration=True,
                                                   encoding="UTF-8", standalone=True)

        with zipfile.ZipFile(self.out_path, "w", zipfile.ZIP_DEFLATED) as z:
            for n, b in data.items():
                z.writestr(n, b)


# 兼容旧脚本 import 别名
DocEngine = None  # 占位，避免误用
