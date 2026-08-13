# 会话动态日志

> 作者：袁燕 | 倒序看最新 | 跨会话生效

## 2026-08-13（第七轮：搭建Git版本管理 + client客户端目录）
- 需求：在 GitHub 新建 5000B 管理系统仓库，前端/后端/客户端分文件夹提交；本机工作区也建 client/ 便于同步；以后每轮袁总提醒即提交 GitHub
- 完成：
  - 新建 `client/svn_post_commit_push.py`（SVN钩子推送脚本，作为客户端服务程序独立目录，本机已建，与 scripts/ 服务端脚本区分）
  - 新建 `.gitignore`（排除 __pycache__/.pyc/logs/temp/.idea/.vscode/.env/*.pem/build 等，铁律：只提交代码）
  - `git init` + 首次 commit：61 个代码文件全入库（backend/frontend/client/scripts/.codebuddy 记忆/README 等），无 .pyc/.log/.idea 误入
  - 记忆更新：user-profile（Git账号 yuanyan/2500749455@qq.com + 提交约定）、project-context（目录结构+Git铁律）、本次日志
- 阻塞：GitHub 建远程库需 PAT。本机 Windows 凭据管理器无 GitHub token；connect_cloud_service 拿到的是 CodeBuddy 平台 token（对 GitHub API 无效，实测 401）；QtSmartCabinet 本地也无 GitHub remote。→ 已备脚本 temp/push_to_github.ps1：袁总提供 PAT 后 `$env:GH_PAT="ghp_xxx"; .\temp\push_to_github.ps1` 一键建库+推送（temp/ 不入库）。注：脚本用 Basic Auth 内嵌 token，推送后建议袁总去 GitHub 改密码/撤 token 不影响
- 坑13（待固化）：GitHub API 建库不能用 CodeBuddy 平台 token 顶替，必须是 GitHub 自己发的 PAT（repo 权限）

## 2026-08-13（补记：找回历史会话 + 强化记忆铁律）
- 起因：袁总反馈"之前的会话没了"，核查发现 08-11/08-12 两轮 SVN 集成工作未写入 session-log（本文件停更于 08-10），凭文件修改时间+代码内容补记
- 处理：补记 08-11/08-12 两轮日志；强化 work-rules.md 第5条（每次对话结束前必须写 session-log，写完记忆才能汇报）；建全局记忆索引
- 袁总追加确认：切换模型（如换成 HY3）也必须记住之前的会话，所有铁律照做 → session-init.md 顶部已写明"跨会话/跨账号/跨模型生效，任何模型第一件事先读记忆"
- 教训：坑12——"做完活没写记忆"等于白干，下次启动就像新会话；记忆写入是每轮工作的收尾动作，不是可选项

## 2026-08-12（第六轮：SVN客户端关注/更新闭环 + 一键启动脚本）
- 完成：SVN 集成服务端逻辑全部落地，start.bat 一键启动前后端
- data_service.py 新增 7 个方法：save_svn_commit / list_svn_commits / mark_affected_watches（提交命中关注路径标 pending）/ upsert_client_watch / list_client_watches / get_pending_updates（客户端轮询拿待更新）/ report_client_update（客户端回报结果）
- api/svn.py：钩子鉴权 secret 校验、client/updates 受 SVN_CLIENT_WATCH_ENABLED 开关控制、report 不存在返回 404
- config.py：SVN_HOOK_SECRET（默认 gjb5000b-hook-2026，可 env 覆盖）、SVN_POLL_INTERVAL=10s、SVN_CLIENT_WATCH_ENABLED=True、SVN_PLATFORM_BASE
- start.bat：一键起后端 uvicorn(8000)+前端静态服务(8080)，端口占用检测跳过，日志写 logs/
- 验证：logs/backend_out.log 有 08-12 10:45 运行记录（后端真实跑过）

## 2026-08-11（第五轮：SVN提交钩子接入）
- 完成：VisualSVN post-commit 钩子 → 平台 /api/svn/commit 全链路
- scripts/svn_post_commit_push.py：钩子脚本（svnlook 抓 author/date/changed/log → POST 平台），REPO_NAME_MAP 映射 R105/R120/R121，钩子失败不阻断提交仅记 stderr
- models.py 新增 2 张表：SvnCommitLog（提交记录）、ClientWatch（客户端关注路径+pending状态）
- schemas 新增：SvnCommitIn/Out、ClientWatchIn/Out、ClientUpdateQuery/Item、ClientReportIn
- api/svn.py 路由建立并挂载 main.py（/api/svn/commit、/commits、/watch、/client/updates、/client/report）

## 2026-08-10（第四轮：生成IDE工程文件 + 做完user/tpl/sys）
- 完成：生成 IDE 工程文件，user/tpl/sys 三页全部做完并多次验证
- IDE 工程文件（解决"project 文件没生成怎么打开"）：
  - 后端 PyCharm：`.idea/`（misc.xml 声明 Python 3.9 SDK + 代码风格；modules.xml 指向 .iml；5000BManagePro.iml 声明 backend/frontend/scripts 为源码根；.name）
  - 前端 VS Code：`.vscode/launch.json`（"前端静态服务"起 8080）+ `settings.json`（Live Server 8080 + 默认 interpreter）
  - 本机 Python：`D:\Anaconda3\python.exe`（3.9.7），已写进 .idea SDK；跨机器若 SDK 路径不对 PyCharm 会提示选 interpreter
  - README 更新：直接 Open 工程文件即可，无需手动建
- user 页：后端补 User 模型对应全链路（user_dao + schemas UserCreate/UserOut + DataService.list/create/delete_user + api/users.py 挂载 main）；前端 user.js 接 /api/users 增删查 + 角色下拉（6角色）
- tpl 页：模板中心，前端展示 10 类 A 文档模板库（对标 R105），点开查看锚点（showMask 弹窗），下载按钮
- sys 页：系统设置，前端展示数据源/SVN三库/RBAC角色/体系参数 4 块配置卡片
- 验证（多次）：
  - 后端 curl：/api/users GET/POST/DELETE 200、缺必填422；全接口 health/requirements/risks/stakeholders/alerts/users 均 200
  - 前端 Node 实跑：user/tpl/sys 渲染 + tplView 弹窗 PASS
  - preview_url 实际打开 user.html / tpl.html / sys.html 三页实测
- 新坑：坑10——PyCharm 打开需 .idea 工程文件，否则只当普通目录；已生成完整 .idea + .vscode 解决

## 2026-08-10（第三轮：PyCharm可跑 + 填充base/alert）
- 完成：后端可在 PyCharm 2025.1.6 打开编译跑；前端多页面解耦已就绪；填充 base/alert 真实数据
- PyCharm 方案（袁总确认）：后端用 PyCharm 跑（run_backend.py 已内置 sys.path 注入，Import 不失败）；前端用 VS Code + Live Server 跑；整个根目录可作 PyCharm Project。README.md 写了打开/运行说明。
- requirements.txt 建好（fastapi/uvicorn/sqlalchemy/pydantic/pymysql...），PyCharm 建 venv 一键装
- 后端新增：AlertLog 模型 + AlertDao + StakeholderDao + schemas(Alert/Stakeholder/RiskOut) + DataService 方法 + 3个API路由(risks/stakeholders/alerts) 挂载 main
- 前端：api.js 补 risk/stakeholder/alert 接口；base.js 改为"基础数据配置中心"(需求/风险/相关方三块增删查)；alert.js 接 /api/alerts(筛选+状态更新+模拟)
- 验证：后端 curl 全链路 health/risks/stakeholders/alerts GET/POST 200、PATCH 状态更新200、非法状态400、无ID 422；前端 Node 实跑 base/alert 渲染 PASS；preview_url 打开 base.html/alert.html 实测
- 新坑：8000 端口被旧后端占用导致新启动 bind 失败 → 先 taskkill 旧 PID 再启（坑9）

## 2026-08-10（第二轮：前端拆分）
- 完成：前端 1:1 复刻效果图框架，解耦分页面 + 样式拆分
  - index.html：登录页 + 框架壳（菜单分组/主节点 PP·PMC/topbar 统计），引用拆分后的 css/js
  - css/common.css：提取效果图 :root 变量 + 框架壳 + 登录页 + 触屏控件（公共，全站复用）
  - css/pages/base.css：基础数据页局部样式（约定示例）
  - js/router.js：菜单定义 + 按需动态加载页面 js/css + go(id) 路由分发 + 公共遮罩
  - js/pages/*.js：pp/pmc/alert/base/user/tpl/sys 各页独立文件（base 已接后端需求增删查，其余为风格一致占位骨架）
  - 旧聚合文件 style.css / app.js 重命名为 .bak 隔离（用户拒绝删除，保留备份）
- 验证：静态资源 200；Node 实跑 Pages.* 全部渲染 PASS；preview_url 打开实测
- 记忆：补齐 work-rules.md / qc-lessons.md(8坑) / session-log.md / user-profile.md

## 2026-08-10（第一轮：骨架搭建）
- 读方案 new.docx 提取框架（5.2 五层 / 5.3 技术栈 / 8.3 解耦 / 8.9 锚点引擎）
- 后端骨架：FastAPI + SQLAlchemy + MySQL，11 张 ORM 表，BaseDao/DAO/Service/API 分层
- 前端骨架：登录 + 框架壳 + 基础数据页（req 增删查走通后端）
- 前后端 JSON 通信全链路验证通过（create/list/delete/400/CORS）
- 建库脚本 scripts/init_db.py，自检 scripts/verify_backend.py
- 记忆：建 session-init.md / project-context.md
