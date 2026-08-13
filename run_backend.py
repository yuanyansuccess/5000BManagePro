# -*- coding: utf-8 -*-
"""
后端启动脚本（调试用）
作者：袁燕
功能：从项目根目录启动 uvicorn，捕获启动异常并打印，便于排查。
用法：python run_backend.py
"""
import sys
import traceback
from pathlib import Path

# 确保项目根在 sys.path，backend 包可导入
ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))

try:
    import uvicorn
    from backend.main import app
    print("[启动] uvicorn 即将监听 http://127.0.0.1:8000")
    try:
        # 预连接测试，暴露 MySQL 连接错误
        from backend.db.session import Engine
        with Engine.connect() as c:
            print("[DB] MySQL 连接成功")
    except Exception as e:
        print("[DB错误]", repr(e))
        traceback.print_exc()
        sys.exit(1)
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
    except Exception:
        traceback.print_exc()
        sys.exit(1)
except Exception:
    print("[启动失败] 异常信息：")
    traceback.print_exc()
    sys.exit(1)
