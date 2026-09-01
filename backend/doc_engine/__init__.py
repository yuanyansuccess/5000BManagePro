# -*- coding: utf-8 -*-
"""
文档灌装引擎包（backend 内聚）。
对外暴露：SdpFiller / WordInjector / DocParser / SdpPlaceholderBuilder。
纯工具，无 FastAPI / DB 依赖，可独立测试。
"""
from backend.doc_engine.doc_engine import (
    SdpFiller,
    WordInjector,
    DocParser,
    SdpPlaceholderBuilder,
)

__all__ = ["SdpFiller", "WordInjector", "DocParser", "SdpPlaceholderBuilder"]
