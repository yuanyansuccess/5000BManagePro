# -*- coding: utf-8 -*-
"""
SDP 生成回归测试（针对当前真实流程，替代已删除的旧 backend/doc_engine/test_doc_engine.py）。

作者：袁燕
背景：旧测试验证的是「SdpFiller 全灌装」旧路径（期望 10 个表格锚点、filler 一次灌完），
      改造后真实流程为 doc_service.load_anchors() + table_builder 从业务库动态生成表格，
      旧测试因此长期 2/5 失败（11≠10 锚点、data_mgmt 残留判定错误），已按袁总要求删除。
      本测试覆盖当前真实链路，保证后续改造不回退：
        1) 模板锚点可被扫描到（含 meta/table 两大类）
        2) 表格锚点数量与内容非空
        3) 工作量/进度表 7 阶段 + 合计 45.90/30.60/76.50/77
        4) 生成文档零残留（标量占位符 + 表格锚点全部被替换）
        5) 分类同步（est/risk/stake）生成的文档同样零残留

运行：python tests/test_sdp_generate.py        （无需后端进程，直连数据库）
"""
import io
import os
import re
import sys
import unittest
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services import doc_service                       # noqa: E402
from backend.services.table_builder import build_schedule_tbl   # noqa: E402
from backend.db.session import SessionLocal                    # noqa: E402
from backend.db.models import SchedulePhase                    # noqa: E402

PID = "R105"
TEMPLATE = "SDP"

# 当前模板实际承载的表格锚点（与 doc_service 动态聚合的表格一致）。
# 袁总 2026-09-01：删除 doc_scale_est（文档规模估计）与 code_scale_reuse（IAP 代码规模估计），
# 新增 meeting_plan（会议计划，从数据库读取）。
EXPECTED_TABLE_ANCHORS = [
    "{{table.risks}}", "{{table.schedule}}", "{{table.stakeholders}}",
    "{{table.stakeholder_plan}}", "{{table.hw_env_res}}", "{{table.sw_env_res}}",
    "{{table.doc_scale_reuse}}",
    "{{table.code_scale_est}}",
    "{{table.data_mgmt}}", "{{table.meeting_plan}}",
]


def _doc_text(data):
    """取 document.xml 的纯文本（去标签），用于残留检查。"""
    z = zipfile.ZipFile(io.BytesIO(data))
    xml = z.read("word/document.xml").decode("utf-8")
    return re.sub(r"<[^>]+>", "", xml)


def _residues(text):
    """返回文档中残留的占位符（meta 标量 + table 锚点）。"""
    phs = re.findall(r"\{\{[a-z_]+\.[a-z_]+\}\}", text)
    return [p for p in phs if p.startswith("{{meta.") or p.startswith("{{table.")]


class TestAnchors(unittest.TestCase):
    """锚点加载：模板锚点 + 业务库表格聚合。"""

    def test_load_anchors_has_tables(self):
        db = SessionLocal()
        try:
            ph_map, table_map = doc_service.load_anchors(db, PID, TEMPLATE)
        finally:
            db.close()
        for a in EXPECTED_TABLE_ANCHORS:
            self.assertIn(a, table_map, "缺少表格锚点: %s" % a)
            self.assertTrue(table_map[a].strip(), "表格锚点内容为空: %s" % a)
        # 关键标量（当前项目元信息，非 R121 硬编码）
        self.assertEqual(ph_map.get("{{meta.project_id}}"), PID)
        self.assertEqual(ph_map.get("{{meta.doc_ver_tag}}"), "D")  # 袁总：页眉永远 D 版

    def test_schedule_table_7_phases(self):
        """工作量/进度表：7 阶段（项目启动+项目策划+需求~验收），合计 45.90/30.60/76.50/77。"""
        db = SessionLocal()
        try:
            rows = db.query(SchedulePhase).filter(
                SchedulePhase.project_id == PID).order_by(SchedulePhase.phase_no).all()
        finally:
            db.close()
        self.assertEqual(len(rows), 7)
        txt = re.sub(r"<[^>]+>", "|", build_schedule_tbl(rows))
        for name in ["项目启动", "项目策划", "需求", "设计", "实现", "测试", "验收"]:
            self.assertIn(name, txt)
        self.assertIn("45.90", txt)
        self.assertIn("76.50", txt)
        self.assertIn("|77|", txt)  # 调整后合计 77 人日


class TestGenerateZeroResidue(unittest.TestCase):
    """生成文档：整篇 + 分类同步，均要求零残留。"""

    def test_full_generate(self):
        data = doc_service.generate_doc_bytes(PID, TEMPLATE, module=None)
        self.assertGreater(len(data), 10000)
        self.assertEqual(_residues(_doc_text(data)), [])

    def test_module_est(self):
        data = doc_service.generate_doc_bytes(PID, TEMPLATE, module="est")
        self.assertEqual(_residues(_doc_text(data)), [])

    def test_module_risk(self):
        data = doc_service.generate_doc_bytes(PID, TEMPLATE, module="risk")
        self.assertEqual(_residues(_doc_text(data)), [])

    def test_module_stake(self):
        data = doc_service.generate_doc_bytes(PID, TEMPLATE, module="stake")
        self.assertEqual(_residues(_doc_text(data)), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
