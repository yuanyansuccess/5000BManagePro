# -*- coding: utf-8 -*-
"""
后端启动脚本（调试用）
作者：袁燕
功能：从项目根目录启动 uvicorn，捕获启动异常并打印，便于排查。
用法：python run_backend.py
设计：多 worker 进程，绕过 GIL 让文档生成类 CPU 密集请求并发处理，
      避免多项目同时下载时被单进程串行排队（袁总反馈的"卡 90% 慢"根因）。
      注意 Windows 上多进程必须用 if __name__ == '__main__' 保护，否则 spawn 报错。
"""
import sys
import traceback
from pathlib import Path

# 确保项目根在 sys.path，backend 包可导入
ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))


def main():
    import multiprocessing
    import uvicorn
    # 预连接测试，暴露 MySQL 连接错误
    try:
        from backend.db.session import Engine
        with Engine.connect() as c:
            print("[DB] MySQL 连接成功")
    except Exception as e:
        print("[DB错误]", repr(e))
        traceback.print_exc()
        sys.exit(1)
    # workers 多进程：绕过 GIL 让文档生成类 CPU 密集请求并发处理
    workers = max(2, min(8, (multiprocessing.cpu_count() or 4)))
    print(f"[启动] uvicorn workers={workers}（多进程并发生成文档）监听 http://127.0.0.1:8000")
    # 必须用 import string 形式，workers 才会生效
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, workers=workers, log_level="info")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("[启动失败] 异常信息：")
        traceback.print_exc()
        sys.exit(1)
