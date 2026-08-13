# 5000BManagePro 项目启动自检清单

> 作者：袁燕 | 创建：2026-08-10 | 跨会话/跨账号/跨模型生效（2026-08-13 袁总确认）

【最高优先级】无论使用哪个模型（CodeBuddy 内置/HY3/其他任何模型）、哪个账号、哪次会话，打开本项目后第一件事就是按此清单读记忆恢复上下文，禁止当作新会话从零开始。所有铁律（三轮分析/验证/触屏/对标/记忆必写）对任何模型一视同仁照做。

每次启动本项目，按此清单恢复上下文：

1. 读 `project-context.md` — 技术栈/路径/DB 结构
2. 读 `work-rules.md` — 编码铁律/测试要求/触屏标准
3. 读 `qc-lessons.md` — 本项目踩坑记录（必看，避免重蹈）
4. 读 `session-log.md` — 最近动态（倒序看最新）

## 当前进度（2026-08-13 更新）
- 项目从空文件夹重启，采用方案 new.docx 框架
- 后端骨架已搭（FastAPI+SQLAlchemy+MySQL），前后端通信已通
- 前端已完成「1:1 复刻效果图 + 解耦分页面 + 样式拆分」：
  - 框架壳（登录/topbar菜单分组/主节点PP·PMC）已对齐效果图
  - css/common.css 公共样式 + css/pages/*.css 页面局部样式
  - js/router.js 路由加载器 + js/pages/*.js 各页独立（base/alert/user 已接后端增删查，tpl/sys 展示页，其余占位骨架）
- IDE 工程文件已生成：.idea（PyCharm 后端，Python 3.9 SDK=D:\Anaconda3）+ .vscode（前端 Live Server 8080）
- SVN 集成已通（08-11/08-12）：post-commit 钩子 scripts/svn_post_commit_push.py → /api/svn/commit；SvnCommitLog/ClientWatch 两表；客户端轮询更新+回报闭环；start.bat 一键启动前后端
- 记忆系统已建全：session-init / project-context / work-rules / qc-lessons / session-log / user-profile
- 下一步：逐步把 placeholder 过程域页（PP/PMC/RDM...）填充为真实数据页

## 铁律（袁总确认，跨会话生效）
- 数据库用 MySQL（gjb5000b，root/root@127.0.0.1:3306）
- 后端 Python 3 + FastAPI + SQLAlchemy；前端 Web(HTML+SVG) 原生，无 Vue/React
- 前后端 HTTP+JSON 通讯，前端绝不直连 DB
- 每次完成工作必写记忆（做了什么+踩的坑）
- 修改前三轮分析，验证通过才结束
