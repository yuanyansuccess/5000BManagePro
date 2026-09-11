# GJB5000B 项目管理平台

> 作者：袁燕 | 后端 Python(FastAPI) + 前端原生 HTML/CSS/JS | 数据库 MySQL
> 详细开发维护手册见 `docs/GJB5000B平台开发维护手册.docx`（含架构/链路/规范/新增模块步骤/Python 常用方法提示）。

## 工程结构
```
5000BManagePro/
├── backend/                  # 后端（FastAPI + SQLAlchemy + MySQL）
│   ├── config.py             # 配置集中（DB_URL / SVN / 锁定密钥）
│   ├── main.py               # FastAPI 入口（CORS + 启动建表 + 挂载 10 个路由）
│   ├── db/                   # session(会话/建表) / models(30个ORM模型) / base(DAO基类)
│   ├── dao/                  # 数据访问层：每个领域一 DAO，SQL 只在此层
│   ├── schemas/              # Pydantic 契约（驼峰JSON↔蛇形ORM 双向映射）
│   ├── api/                  # 路由层 10 个文件（只校验+调DAO/Service+统一ApiResp）
│   ├── services/             # 业务层
│   │   ├── data_service.py   #   全域 CRUD 门面 + 认证 + SVN 集成
│   │   ├── doc_service.py    #   SDP 生成编排（占位符映射/锚点/生成流水线）
│   │   ├── doc_postprocess.py#   SDP docx 后处理流水线（只读保护/页眉/表格/分页/刷域）
│   │   ├── table_builder.py  #   14 个整表 OOXML 构建
│   │   ├── word_pages.py     #   Word COM 子进程刷真实页码
│   │   └── svn_service.py    #   svn 提交封装
│   └── doc_engine/           # 纯灌装引擎（SdpFiller/WordInjector/DocParser/SdpPlaceholderBuilder）
├── frontend/                 # 前端（原生 HTML + CSS + JS，无框架，多页应用）
│   ├── index.html            # 登录页
│   ├── pages/                # 8 个业务子页（独立 html，互不干扰）
│   ├── js/api.js             # 前后端通信唯一入口（约 40 个方法）
│   ├── js/shell.js           # 公共壳（topbar/sidebar/登录/项目弹窗）
│   ├── js/crud_table.js      # 通用行内编辑 CRUD 表格工厂（10 组表格复用）
│   ├── css/common.css        # 公共样式；css/pages/ 仅 pmc/user 有局部样式
│   └── config/company.js     # 公司名/logo 配置
├── templates/sdp/            # SDP 占位符模板（SDP_占位符版.docx + 历史备份 .bak_*）
├── scripts/                  # 长期脚本 6 个（frontend_server/init_db/seed_users/
│   └── archive/              #   backup_db/svn_post_commit_push/code_review_scan）
│                             #   一次性历史脚本全部归档在 archive/
├── client/                   # 分发到研发机的 SVN post-commit 钩子副本
├── tests/                    # SDP 生成回归测试（pytest）
├── docs/                     # 文档（开发维护手册 / R105 基准 SDP）
├── database/                 # 全库 SQL 备份
├── start.bat                 # 一键启动前后端（8000/8080，带孤儿进程清理与探活）
├── 打开前端页面.bat           # 只起前端并打开浏览器（后端没起时页面无数据）
├── run_backend.py            # 生产启动入口（MySQL 预检 + uvicorn 多进程）
└── requirements.txt          # 后端依赖
```

## 启动方式（三条链路，按场景选）

| 场景 | 方式 | 说明 |
|---|---|---|
| 日常使用 | 双击 `start.bat` | 杀旧进程→起后端 8000+前端 8080→探活成功才提示 |
| 只看页面 | 双击 `打开前端页面.bat` | 8080 没起则拉起，再自动开浏览器（无后端则无数据） |
| 断点调试 | PyCharm/VSCode 调试配置「后端 FastAPI 调试」 | uvicorn 单进程 `--reload`，改代码自动重启，可打断点 |

> 注意：生产入口 `run_backend.py` 是 **8 进程**模式（绕 GIL 加速 docx 生成），断点调试无效；
> 调试务必走单进程配置。重启后端须杀干净全部 uvicorn 孤儿 worker（start.bat 已内置）。

## 分层铁律（继承智能柜 P18）
前端绝不直连 DB；取数只走 `js/api.js`（HTTP+JSON）。
后端严格 API→(Service)→DAO→DB，SQL 只写在 DAO 层（通用 CRUD 全在 `db/base.py` BaseDao，
各领域 DAO 只声明 model + 主键 + 排序字段）。

## 字段约定（P13）
前端/JSON 统一驼峰（`skillReq`）；ORM/DB 内部蛇形（`skill_req`）。
Pydantic 模型多词字段必须 `Field(alias="camelName")` + `populate_by_name=True`（两种写法都收）。

## 数据库
MySQL 8，库名 `gjb5000b`，`root/root@127.0.0.1:3306`，charset utf8mb4。
首次启动自动建表（Base.metadata.create_all + 幂等兜底 ensure_tables）。
初始数据：`python scripts/init_db.py` → `python scripts/seed_users.py`。

## 测试与验证
- 回归测试：`python -X utf8 -m pytest tests/test_sdp_generate.py -q`
- 接口级 CRUD 冒烟：`python temp/test_batch_b_apis.py`（五组资源全链路，自动清理）
- SDP 生成效果验证必须用 Word COM 实测（temp/final_verify.py / verify_final_all.py），只查 XML 会假绿
