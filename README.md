# GJB5000B 项目管理平台

> 作者：袁燕 | 后端 Python(FastAPI) + 前端原生 HTML/CSS/JS | 数据库 MySQL

## 工程结构
```
5000BManagePro/
├── backend/            # 后端（FastAPI + SQLAlchemy + MySQL）
│   ├── config.py       # 配置集中（DB_URL / SVN / RBAC）
│   ├── main.py         # FastAPI 入口（CORS + 启动建表 + 挂载路由）
│   ├── db/             # 会话 / ORM 模型 / DAO 基类
│   ├── dao/            # 每领域一 DAO（requirement/risk/alert/stakeholder）
│   ├── schemas/        # Pydantic 契约（驼峰JSON↔蛇形ORM）
│   ├── services/       # 业务层门面
│   └── api/            # 路由层（只校验+调Service+JSON）
├── frontend/           # 前端（原生 HTML + CSS + JS，无框架）
│   ├── index.html      # 登录页
│   ├── config/         # 全局配置（company.js：logo/公司名）
│   ├── css/common.css  # 公共样式（框架/登录/四色/触屏）
│   ├── css/pages/      # 各页局部样式
│   ├── js/api.js       # 前后端通信封装（HTTP+JSON）
│   ├── js/shell.js     # 公共壳（topbar/sidebar/跳转）
│   ├── js/pages/       # 每页独立 js
│   └── pages/          # 每个子页面独立 html
├── start.bat           # 一键启动前后端
└── requirements.txt    # 后端依赖
```

## 打开与运行方式（袁总确认方案）
> 已生成 IDE 工程文件，直接打开即可，无需手动建工程。

- **后端：用 PyCharm 2025.1.6 打开并运行**
  1. PyCharm → Open → 选择项目根 `D:\5000\5000BManagePro`（已含 `.idea/` 工程文件，直接识别为 Python Project）
  2. 若 SDK 路径提示不对：Settings → Python Interpreter → 选本机 Python（如 `D:\Anaconda3\python.exe`），安装 `requirements.txt`
  3. 运行 `run_backend.py`（已内置把项目根加入 sys.path，Import 不会失败）
     Run Configuration：Script path = `run_backend.py`，Working directory = 项目根
  4. 后端监听 http://127.0.0.1:8000
- **前端：用 VS Code 打开并运行**（已含 `.vscode/` 配置）
  1. VS Code → Open 项目根（`.vscode/launch.json` 已配"前端静态服务"：起 8080 并打开浏览器）
  2. 或装 Live Server 插件，右键 `frontend/index.html` → Open with Live Server
  3. 前端访问 http://127.0.0.1:8080
- **一键启动**：双击 `start.bat`（自动起后端 8000 + 前端 8080，带端口检测）

## 分层铁律（继承智能柜 P18）
前端绝不直连 DB；取数只走 `js/api.js`（HTTP+JSON）。
后端严格 Page→Service→DAO→DB，路由层不写 SQL。

## 字段约定（P13）
前端/JSON 统一驼峰（reqId）；ORM/DB 内部蛇形（req_id）。

## 数据库
MySQL 8，库名 `gjb5000b`，`root/root@127.0.0.1:3306`，charset utf8mb4。
首次启动自动建表（Base.metadata.create_all）。
