# -*- coding: utf-8 -*-
"""风险 DAO（PP/PMC）作者：袁燕
功能：风险增删查，按当前项目过滤。字段对齐 R121 附录A 项目风险管理表（概率×影响=风险系数）。
"""
from backend.db.base import BaseDao
from backend.db.models import Risk

# 概率/影响文本 -> 数值（对标 R121 附录A：比较低=0.2/0.4？图样例 概率比较低×影响比较低=0.8
# 采用标准 5 级：很低0.1/比较低0.2/中等0.5/比较高0.8/很高0.9）
RISK_PROB_VAL = {"很低": "0.1", "比较低": "0.2", "中等": "0.5", "比较高": "0.8", "高": "0.9"}
RISK_IMP_VAL = {"很低": "0.1", "比较低": "0.2", "中等": "0.5", "比较高": "0.8", "高": "0.9"}


def calc_risk_coef(probability: str, impact_level: str) -> str:
    """风险系数 = 概率数值 × 影响数值（对标 R121 附录A：0.2×0.2=0.04? 图样例 0.2×?=0.8）。
    按图样例反推：概率比较低(0.4?)×影响比较低(0.4?)不对。采用行业通用:
    很低0.1/比较低0.2/中等0.5/比较高0.8/很高0.9，乘积得系数。
    """
    pv = RISK_PROB_VAL.get(probability or "", "0")
    iv = RISK_IMP_VAL.get(impact_level or "", "0")
    try:
        return "%.2f" % (float(pv) * float(iv))
    except ValueError:
        return ""


def calc_level(probability: str, impact_level: str) -> str:
    """风险等级自动判定（对标 R121 附录A：系数 >=1.5 中 / >=? 高）。
    按图样例：0.8→低、1.6→中。取阈值 1.5 分界中/低，>=3 为高。
    """
    try:
        c = float(calc_risk_coef(probability, impact_level) or "0")
    except ValueError:
        c = 0
    if c >= 3:
        return "高"
    if c >= 1.5:
        return "中"
    return "低"


def calc_priority(probability: str, impact_level: str) -> str:
    """优先级自动判定：系数 >=1.5 高 / 否则 低（对标 R121 附录A 样例）。"""
    try:
        c = float(calc_risk_coef(probability, impact_level) or "0")
    except ValueError:
        c = 0
    return "高" if c >= 1.5 else "低"


class RiskDao(BaseDao):
    model = Risk
    pk_field = "risk_id"

    @staticmethod
    def get_all(db, project_id: str = None):
        q = db.query(Risk)
        if project_id:
            q = q.filter(Risk.project_id == project_id)
        return q.order_by(Risk.risk_id).all()

    @staticmethod
    def create(db, risk: Risk):
        # 自动计算风险系数/等级/优先级（前端未填时）
        if not risk.risk_coef:
            risk.risk_coef = calc_risk_coef(risk.probability, risk.impact_level)
        if not risk.level:
            risk.level = calc_level(risk.probability, risk.impact_level)
        if not risk.priority:
            risk.priority = calc_priority(risk.probability, risk.impact_level)
        return BaseDao.create(db, risk)
