# 项目技术栈与路径上下文

> 作者：袁燕 | 创建：2026-08-10

## 路径
- 项目根：`D:\5000\5000BManagePro`
- 后端：`backend/`（FastAPI 应用包）
- 前端：`frontend/`（静态 HTML+SVG+JS，原生无框架）
- 效果图源：`d:\5000\平台效果图\页面UI效果图\preview.html`（645KB 单文件原型，复刻基准）
- 方案文档：`d:\5000\GJB5000B_项目管理平台总体方案new.docx`（5MB，框架权威依据）
- R105 数据：`d:\5000\R105\`（真实样例数据对标源）

## 技术栈（袁总确认）
- 后端：Python 3.9 + FastAPI 0.128 + SQLAlchemy 1.4 + Pydantic V2 + uvicorn + pymysql
- 数据库：MySQL 8（库名 gjb5000b，root/root@127.0.0.1:3306，charset utf8mb4）
- 前端：原生 HTML + CSS + JS（SVG 绘图），无第三方框架
- 文档生成（后续）：python-docx / openpyxl 锚点引擎 {{KEY}}

## 后端目录结构
```
backend/
  config.py          # 配置集中（DB_URL/SVN/RBAC）
  main.py             # FastAPI 入口（CORS+启动建表+挂载路由）
  db/session.py       # SQLAlchemy 引擎单例（唯一持连接）
  db/models.py         # 11 张 ORM 表 + 状态枚举
  db/base.py           # DAO 基类（通用 CRUD）
  dao/                 # 每领域一 DAO（requirement/risk...）
  schemas/             # Pydantic 契约（驼峰JSON↔蛇形ORM via alias_generator）
  services/            # 业务层（DataService 门面）
  api/                 # 路由层（只校验+调Service+JSON）
run_backend.py         # 启动脚本（含预连接测试+异常捕获）
scripts/init_db.py     # 建 MySQL 库
scripts/verify_backend.py # 后端自检（建表+CRUD闭环）
```

## 关键约定
- 前端/JSON 字段统一驼峰（reqId）；ORM/DB 内部蛇形（req_id）
- 状态枚举集中在 db/models.py（REQ_STATUS/RISK_STATUS 等），前端不发明
- API 路由不直连 DAO（继承智能柜 P18）；无效参数返回明确 400（P10）
- 启动自动建表（Base.metadata.create_all，继承 P22）

## 已验证端口
- 后端 API：http://127.0.0.1:8000
- 前端静态：http://127.0.0.1:8080

## 版本管理（Git / GitHub，2026-08-13 修正）
- 真实账号：**yuanyansuccess**（SSH），非全局 config 的 yuanyan。SSH key 在 ~/.ssh/id_ed25519
- 远程目标：git@github.com:yuanyansuccess/5000BManagePro.git（SSH 协议）
- 目录结构（分文件夹提交）：`backend/`（后端FastAPI）`frontend/`（前端原生）`client/`（客户端服务程序=SVN钩子推送脚本）`scripts/`（服务端脚本）
- 本机 git 已 init，已提交 2 个（初始化 + 记忆补充），共 61+ 代码文件（.gitignore 排除 .pyc/logs/.idea/temp）
- 当前状态（2026-08-13）：本地 master/main 已就绪，远端仓库**袁总需在 GitHub 网页手动建**（SSH key 不能建库）；建好后跑 temp/push_ssh.ps1 推送
- 提交铁律：袁总提醒后才 push；只提交代码；禁止 git add -A 裸用，精准 add；不提交 temp/logs/二进制
