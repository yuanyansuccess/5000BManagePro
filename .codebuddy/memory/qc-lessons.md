# 本项目踩坑记录（QC 经验库）

> 作者：袁燕 | 创建：2026-08-10 | 必看，避免重蹈

## 坑1 · 包导入失败 No module named 'backend'
- 现象：从 backend/ 子目录运行 uvicorn 报找不到包
- 根因：PYTHONPATH 未包含项目根
- 修复：从项目根运行，设置 PYTHONPATH=D:\5000\5000BManagePro，改用 run_backend.py 启动

## 坑2 · Pydantic V2 警告 orm_mode renamed
- 现象：FastAPI 0.128 + Pydantic V2 报 orm_mode 已更名
- 修复：schemas 用 model_config = ConfigDict(from_attributes=True)；from_orm → model_validate

## 坑3 · MySQL Unknown database 'gjb5000b'
- 现象：create_all 报库不存在
- 根因：之前建库 Python 命令因转义报错未实际执行
- 修复：写 scripts/init_db.py 文件执行建库成功

## 坑4 · create 返回 500（from_orm 漏改）
- 现象：POST /api/requirements 返回 500
- 根因：requirements.py 遗漏 from_orm 未改 model_validate
- 修复：改 model_validate(obj)

## 坑5 · list/create 返回 500（驼峰/蛇形字段不对齐）【核心坑】
- 现象：Pydantic 字段 reqId 但 ORM 属性 req_id，from_attributes 读不到 → 500
- 修复：schemas 用 ConfigDict(alias_generator=AliasGenerator(
    serialization_alias=to_camel, validation_alias=to_snake))
  实现驼峰 JSON ↔ 蛇形 ORM 双向映射，输出驼峰

## 坑6 · 后台启动 uvicorn 隐藏窗口不稳定
- 现象：Start-Process 隐藏窗口启动，连接被拒
- 修复：改用 cmd.exe /c "... > svc.log 2>&1" 重定向日志后台启动，确认 startup complete 后再测

## 坑7 · 前端拆分后页面按需加载
- 现象：验证脚本只加载 base.js，其余 Pages.* 未定义
- 根因：router 是按需动态加载 js，验证时必须把所有 pages/*.js 都加载
- 修复：验证脚本 readdirSync(pages) 全部 vm.runInContext 后再测

## 坑8 · 浏览器 TestClient portal 异常（非真实 bug）
- 现象：异步 event loop 冲突
- 修复：改用真实 HTTP curl 验证，不信 TestClient 假错

## 坑9 · 8000 端口被旧后端占用导致新启动 bind 失败
- 现象：run_backend.py 报 [Errno 10048] address already in use，startup 后立即 shutdown
- 根因：上一轮启动的后端进程（PID）仍在监听 8000，未释放
- 修复：netstat -ano 查占用 PID → taskkill /PID xxx /F → 再启动；start.bat 已带端口检测可避免重复启动

## 坑10 · 超长 base64（logo）复制被截断导致图片损坏不显示【致命】
- 现象：登录页/首页企业 logo 不显示（裂图）。Node 解码 base64 头部恰是 PNG 头所以没报错，但浏览器无法渲染损坏图片
- 根因：从效果图 preview.html 提取 COMPANY_LOGO 时，grep 输出有 `[2]` 截断标记，只复制了前 4063/49784 字符（不到 1/10），写入 company.js 的 base64 不完整
- 修复：用 Python re 从 preview.html 提取完整 COMPANY_LOGO（49784 字符，解码 37338 字节 PNG），重写 company.js；并给所有引用加 ?v=2 防浏览器缓存旧文件
- 铁律固化：① 任何超长字符串（base64/锚点模板）禁止靠肉眼/grep 截断复制，必须用脚本（python re/Node fs）程序化提取写入；② 写入后必须解码校验（base64.b64decode 字节数 + PNG 头 89504e47）

## 坑11 · PyCharm 打开需 .idea 工程文件
- 现象：无工程文件时 PyCharm 只当普通目录打开，无法直接 Run
- 修复：生成 .idea/（misc.xml/modules.xml/.iml/.name）+ .vscode/，README 写明直接 Open 工程根

## 坑12 · 做完工作没写 session-log，下次会话像全新一样【流程坑】
- 现象：08-11/08-12 两轮 SVN 集成（钩子脚本/两张表/客户端关注闭环/start.bat）做完未写记忆，session-log 停更于 08-10，袁总下次开会话以为历史全丢
- 根因：把"写记忆"当成可选项，做完活直接交差
- 修复：凭文件 LastWriteTime + 代码内容倒推补记；work-rules 第5条强化为"每次对话结束前必须写 session-log，写完记忆才能汇报"
