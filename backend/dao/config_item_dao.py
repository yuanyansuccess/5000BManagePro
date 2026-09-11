# -*- coding: utf-8 -*-
"""配置项 DAO（CM A51~A59）作者：袁燕
按 project_id 维度隔离（项目方铁律）。通用 CRUD/list_by_project 全在 BaseDao，此处仅声明模型与排序。
基线列表（{{table.baselines}}）：按 baseline_id 分组，组内 ci_id 用"、"连接。
"""
from backend.db.base import BaseDao
from backend.db.models import ConfigItem


class ConfigItemDao(BaseDao):
    model = ConfigItem
    pk_field = "id"
    order_fields = (ConfigItem.baseline, ConfigItem.ci_id)

    @staticmethod
    def list_baselines(db, project_id: str):
        """按【基线标识 baseline_id】分组聚合（对标 R105 真实 5 条基线）：
        返回 [{"baseline","baseline_name","baseline_id","items_str","names","count"}, ...]
        同一基线内多个配置项用中文顿号"、"连接（项目方 2026-09-02 反馈）。
        分组键：基线标识（R105_JG_V1.00 / R105_0201_JF_V1.00 等），
        因为同一 "基线类别"（如分配基线）下会存在多条不同基线（0201/0202）。
        排序：功能基线 -> 分配基线 -> 产品基线（GJB5000B 基线演进顺序），
              同类内按基线名称升序（R105 -> R105_0201 -> R105_0202）。
        """
        items = db.query(ConfigItem).filter(
            ConfigItem.project_id == project_id
        ).order_by(ConfigItem.baseline_id, ConfigItem.ci_id).all()
        # 基线类别演进顺序（字母序 JC<JF<JG，不能直接按 baseline_id 排）
        bl_order = {"功能基线": 1, "分配基线": 2, "产品基线": 3}
        groups = {}
        for it in items:
            key = (it.baseline_id or it.baseline or "未分基线").strip() or "未分基线"
            groups.setdefault(key, []).append(it)
        result = []
        for key, rows in groups.items():
            head = rows[0]
            ids = [r.ci_id for r in rows]
            result.append({
                "baseline": head.baseline or "",
                "baseline_name": head.baseline_name or "",
                "baseline_id": key,
                "ci_ids": ids,
                "items_str": "、".join(ids),    # 中文顿号分隔
                "names": [r.name for r in rows],
                "count": len(ids),
            })
        result.sort(key=lambda g: (bl_order.get(g["baseline"], 9), g["baseline_name"]))
        return result
