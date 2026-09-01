# -*- coding: utf-8 -*-
"""
SVN 提交服务（Service 层）。
作者：袁燕
功能：把生成的 docx 提交到 VisualSVN 仓库（袁总已部署）。
设计：高内聚（SVN 命令封装内聚）、低耦合（只被 doc 接口调用）。
     用 svn import 直接提交到目标路径，自动建中间目录，无需 checkout 工作副本。
"""
import os
import subprocess
import tempfile

from backend import config


def commit_docx(repo_url, username, password, rel_path, filename, data,
                commit_msg=None):
    """
    把 docx 字节流提交到 SVN 仓库。
    :param repo_url: 仓库根 URL，如 https://yuanyan/svn/R121/ （末尾斜杠可选）
    :param rel_path: 仓库内相对路径（不含文件名），如 trunk/项目管理/项目策划/项目计划
    :param filename: 文件名，如 R121_SDP.docx
    :param data: docx 字节
    :return: (revision:int or None, info:str)
    """
    repo_url = repo_url.rstrip("/")
    target_url = "{}/{}/{}".format(repo_url, rel_path.rstrip("/"), filename)
    commit_msg = commit_msg or "平台生成文档：{}".format(filename)

    # 临时落盘
    tmpdir = tempfile.mkdtemp(prefix="svn_doc_")
    local_file = os.path.join(tmpdir, filename)
    with open(local_file, "wb") as f:
        f.write(data)

    svn = config.SVN_EXE
    auth = ["--username", username, "--password", password,
            "--non-interactive", "--trust-server-cert", "--no-auth-cache"]
    # 若目标已存在，先删（支持重复提交覆盖）
    try:
        subprocess.run([svn, "delete", target_url, "-m", "平台覆盖提交 " + filename] + auth,
                       capture_output=True, text=True, timeout=60)
    except Exception:
        # 静默安全：delete 仅在覆盖旧文件前执行；首次提交时目标不存在属正常。
        pass
    cmd = [svn, "import", local_file, target_url, "-m", commit_msg] + auth
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        out = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode != 0:
            return None, "SVN 提交失败：" + out.strip()[-300:]
        rev = None
        for line in out.splitlines():
            if "Committed revision" in line:
                try:
                    rev = int(line.split("revision")[-1].strip().rstrip(".").strip())
                except Exception:
                    # 静默安全：rev 解析失败时保持默认 0，不影响提交事实。
                    pass
        return rev, "已提交到 " + target_url
    except subprocess.TimeoutExpired:
        return None, "SVN 提交超时"
    finally:
        try:
            os.remove(local_file)
            os.rmdir(tmpdir)
        except Exception:
            # 静默安全：临时目录清理失败不影响提交结果，留给系统回收。
            pass
