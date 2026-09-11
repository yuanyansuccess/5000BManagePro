# -*- coding: utf-8 -*-
"""清理 backend / frontend 下已核对确认的失效/冗余文件。作者：袁燕

删除依据（均经引用核对 + 内容核对）：
backend/services/_final_verify.py      playwright 验证脚本，指向旧端口 8080（现 5500），失效且无引用
backend/services/_verify_http_risk.py  HTTP 验证脚本，指向旧端口 8011（现 8000），失效且无引用
backend/services/_selftest_proj.py     旧自测脚本，已由 tests/test_sdp_generate.py 取代，无引用
backend/services/_rsk.txt               调试输出文本
backend/services/_selftest_proj.txt     旧自测输出文本
backend/db/_migrate_project_v3.py       一次性迁移，4 字段已在 Project 模型中（新环境 create_all 自带）
backend/db/_migrate_svn_config.py       一次性 seed，SVN 配置数据已入库（2/6/2 条）
backend/db/_seed_stakeholder_plan.py    旧 9 角色结构，已被 16 角色结构取代，无引用
frontend/css/style.css.bak              孤儿备份（正身 style.css 不存在、无引用）
frontend/js/app.js.bak                  孤儿备份（正身 app.js 已被 shell.js 取代、无引用）

保留（有引用）：
backend/db/_migrate_proj_signoff.py     init_db() 调用
backend/db/_seed_doc_scale.py           session.py / data_service.py 调用
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TARGETS = [
    "backend/services/_final_verify.py",
    "backend/services/_verify_http_risk.py",
    "backend/services/_selftest_proj.py",
    "backend/services/_rsk.txt",
    "backend/services/_selftest_proj.txt",
    "backend/db/_migrate_project_v3.py",
    "backend/db/_migrate_svn_config.py",
    "backend/db/_seed_stakeholder_plan.py",
    "frontend/css/style.css.bak",
    "frontend/js/app.js.bak",
]


def main():
    done, missing = [], []
    for rel in TARGETS:
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        if os.path.exists(p):
            os.remove(p)
            done.append(rel)
        else:
            missing.append(rel)
    print("[删除 %d 个]" % len(done))
    for d in done:
        print("  -", d)
    if missing:
        print("[跳过（不存在）%d 个]" % len(missing))
        for m in missing:
            print("  -", m)

    # 复查：backend / frontend 下是否仍有 下划线开头 / .bak / .txt 文件
    left = []
    for base in ("backend", "frontend"):
        for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, base)):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fn in filenames:
                if fn.startswith("_") or fn.endswith(".bak") or fn.endswith(".txt"):
                    left.append(os.path.relpath(os.path.join(dirpath, fn), ROOT))
    print("\n[复查] 剩余可疑文件：%s" % (left if left else "无"))


if __name__ == "__main__":
    main()
