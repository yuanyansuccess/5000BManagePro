# -*- coding: utf-8 -*-
"""
SVN 提交钩子推送脚本（客户端服务程序，作者：袁燕）
功能：部署到各研发机的 SVN 仓库 hooks/post-commit.bat 中，被 VisualSVN 提交后触发。
     用 svnlook 抓取本次提交信息，POST 给 5000B 管理平台 /api/svn/commit 接口。
参数：argv[1]=仓库路径  argv[2]=版本号
设计：钩子保持极简，只负责抓取+推送；匹配/关注逻辑在服务端平台完成。
所有配置集中在本文件顶部 CONFIG 区，部署时按需调整 PLATFORM_URL / HOOK_SECRET / SVNLOOK。
"""
import sys
import os
import subprocess
import json
import urllib.request
import urllib.error

# ===== 可配置项（集中管理，部署时改这里即可）=====
SVNLOOK = r"D:\Program Files\VisualSVN Server\bin\svnlook.exe"
PLATFORM_URL = "http://127.0.0.1:8000/api/svn/commit"
HOOK_SECRET = "gjb5000b-hook-2026"
# 仓库路径 -> 项目名称 映射（钩子传入仓库路径，据此识别项目名）
REPO_NAME_MAP = {
    "R105": "R105飞管软件",
    "R120": "R120项目",
    "R121": "R121项目",
}


def run(cmd):
    """执行命令返回 stdout 文本。"""
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return p.stdout.strip()


def main():
    if len(sys.argv) < 3:
        sys.stderr.write("用法: svn_post_commit_push.py <repo_path> <revision>\n")
        sys.exit(1)
    repo_path = sys.argv[1]
    revision = sys.argv[2]

    # 仓库名：取路径最后一段（如 D:\Repositories\R105 -> R105）
    repo_name = os.path.basename(repo_path.rstrip("\\/"))
    project_name = REPO_NAME_MAP.get(repo_name, repo_name)

    # svnlook 抓取提交信息
    author = run('"{0}" author "{1}" -r {2}'.format(SVNLOOK, repo_path, revision))
    # date 格式: "2026-08-11 17:05:24 +0800 (周二, 11 8月 2026)"，截掉中文括号尾部
    commit_time_raw = run('"{0}" date "{1}" -r {2}'.format(SVNLOOK, repo_path, revision))
    commit_time = commit_time_raw.split(" (")[0].strip() if commit_time_raw else ""
    changed_raw = run('"{0}" changed "{1}" -r {2}'.format(SVNLOOK, repo_path, revision))
    log_raw = run('"{0}" log "{1}" -r {2}'.format(SVNLOOK, repo_path, revision))

    # 改动文件清单：取每行第二列（路径）
    changed_files = "\n".join(
        line.split(None, 1)[1] for line in changed_raw.splitlines() if len(line.split(None, 1)) > 1
    )

    payload = {
        "repoName": repo_name,
        "commitUser": author,
        "revision": int(revision),
        "commitTime": commit_time,
        "changedFiles": changed_files,
        "projectName": project_name,
        "rawLog": log_raw,
        "secret": HOOK_SECRET,
    }

    # POST 给平台
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        PLATFORM_URL, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # 钩子失败不应阻断提交，仅记录平台返回详情
        body = e.read().decode("utf-8", errors="replace")
        sys.stderr.write("推送平台失败 HTTP %s: %s\n" % (e.code, body))
    except Exception as e:
        # 钩子失败不应阻断提交，仅记录
        sys.stderr.write("推送平台失败: %s\n" % e)


if __name__ == "__main__":
    main()
