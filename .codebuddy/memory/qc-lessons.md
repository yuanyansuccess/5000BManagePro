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

## 坑13 · GitHub 建库/推送不能用 CodeBuddy 平台 token【凭证坑】
- 现象：connect_cloud_service 拿到的 token 调 GitHub API 报 401 Bad credentials；本机无 gh CLI、无 Windows 凭据里 GitHub token
- 根因：CodeBuddy IDE 会话 token ≠ GitHub PAT，两者不通
- 修复：GitHub 操作必须向袁总要 GitHub 自己发的 Personal Access Token（repo 权限）；已备 temp/push_to_github.ps1（Basic Auth 内嵌 token 建库+push），袁总给 PAT 即跑。严禁用平台 token 顶替

## 坑14 · python-docx 估算页数严重低估（表格按行数算）【文档解析坑】
- 现象：DocPageCounter 对 R121 SRS 估算 13 页，袁总 Word 打开是 26 页，差一倍
- 根因：estimate_lines 原逻辑 `for table: lines += len(table.rows)` 把表格只按行数计，每张表单元格内多行文字被忽略；且 CHARS_PER_LINE/LINES_PER_PAGE 粗糙
- 修复：表格改为按单元格文字量折行累加（与段落同等处理）；参数校准 CHARS_PER_LINE=38、LINES_PER_PAGE=40，R121 实测 26 页与 Word 一致
- 铁律固化：① 文档页数一律按内容真实估算，绝不读封面 {{doc.pages}} 占位符（_read_numpages_field 返回 None 即走估算）；② 表格篇幅要算单元格文字，不能只算行数；③ 调参后用真实文档反向校准（R121=26 页为基准）

## 坑15 · pytest 单跑普通函数报 fixture not found【测试坑】
- 现象：PyCharm pytest runner 单跑 verify_5000b_parse.py::test_pagecount 报 `fixture 't' not found`
- 根因：test_functional/test_boundary/test_pagecount 是普通函数（由 verify() 手动传 t/r121/tpl），非 pytest 用例；pytest 把形参当 fixture 查，找不到即报错
- 修复：加 `import pytest` + 三个 fixture（t 返回 Tester()、r121/tpl 返回 Document 加载），函数签名保持 t/r121/tpl 不变，pytest 按同名注入；__main__ 直跑路径不受影响
- 铁律固化：凡要同时支持"直跑 + pytest 单跑"的验证脚本，测试函数须配同名 fixture；报告用 _log(lines, echo=True) 同时打控制台，便于直接看页数

## 坑16 · 验证脚本报告只写文件不打控制台【易用性坑】
- 现象：verify_5000b_parse.py 原只把报告写 temp/verify_5000b_parse.log，控制台只打印一句结论，袁总不便查看页数
- 修复：_log(lines, echo=True) 增加 echo 参数，True 时 print 完整报告；verify() 调用 _log(lines, echo=True)，控制台同步可见，文件照旧写 temp/

## 坑17 · Word COM 在 PyCharm/pytest 宿主内必崩，必须子进程隔离【COM坑】
- 现象：_word_page_count 在纯 python -c 跑正常，但在 PyCharm/pytest 的 _jb_pytest_runner 宿主里反复报 Windows fatal exception 0x800706be / 0x800706ba（RPC 服务器不可用），堆栈出现在 Documents.Open / Quit / CoUninitialize 内部。STA 套间修复(坑17初版)无效
- 根因：PyCharm pytest runner 宿主进程是 MTA + 多线程；Word COM 要求 STA。任何在宿主内直接调 Word 的原生调用都会触发进程级 fatal，try/except 只能兜返回值、兜不住 fatal exception（崩溃发生在原生层）
- 修复（最终解）：把 Word COM 调用隔离到**独立子进程**——主进程用 subprocess 起干净 python -c 子进程（纯 STA 环境，已验证稳定）调 Word 读页数，子进程把结果 print 到 stdout，主进程读回。COM 崩溃被关在子进程，绝不污染 pytest 宿主
- 铁律固化：凡在 PyCharm/pytest 里调用 Word/Excel COM，必须 subprocess 子进程隔离，禁止在宿主进程内直接 Dispatch Word/Excel。子进程内用 CoInitializeEx(STA)+EnsureDispatch+用完 Quit

## 坑19 · pytest.skip 写在会被直跑的函数里会中断整个 verify 导致日志不生成【测试坑】
- 现象：袁总删除 verify_5000b_parse.log 后重跑，Python 不再自动生成日志；有时能生成有时不能
- 根因：test_pagecount 里写了 pytest.skip("...") 防 Word 不可用。verify() 是普通函数直跑，pytest.skip() 在普通函数内会 raise Skipped 异常 → verify() 在调用 test_pagecount 处崩溃中断，末尾的 _log() 永远执行不到 → 日志不生成。Word 偶发不可用（子进程没起来返回-1）时必触发，故"有时能有时不能"
- 修复：把 pytest.skip() 改为 t.warn(...)+return（不抛异常）；Word 不可用时记警告并跳过该项，不误报失败，verify 正常走完写日志。日志机制本身没问题（os.makedirs+open "w" 会建文件），问题全在 skip 中断
- 铁律固化：凡在"既能被 pytest 调、又能被 __main__ 直跑"的函数里，禁止用 pytest.skip()；改用 warn/return 等不抛异常的方式表达跳过

## 坑20 · pytest 不执行 __main__，日志写在 __main__ 里导致不生成【测试坑】
- 现象：袁总用 PyCharm run verify_5000b_parse.py 后，temp/verify_5000b_parse.log 不生成；但 python 直跑又正常
- 根因：PyCharm 对含 test 字样文件默认用 pytest runner，pytest 只收集执行 test_* 函数，**不执行 if __name__=="__main__" 块**。日志写入(_log)原本只在 __main__ 里的 verify() 中 → pytest 模式从不调用 → 不生成
- 修复：把 _log(t.lines, echo=False) 放到每个 test_* 函数末尾（不止 verify() 内），pytest 调 test_* 时各自落盘。verify() 内的聚合 _log 保留作直跑最终完整版
- 铁律固化：凡要"既 pytest 单跑、又脚本直跑"都产出日志/产物的代码，关键副作用(写文件/落库)不能只放在 __main__，必须放在被测函数内部；PyCharm 对 *test* 文件默认 pytest 跑

## 坑18 · python-docx 估算页数不可靠，必须真实渲染【文档解析坑】
- 现象：DocPageCounter.estimate_lines 按字符/行估算，R121 真实26页估出30页、demo_tpl 真实9页估出4页，完全不准；袁总指出"所有文档页数验证方法都有问题"
- 根因：python-docx 无渲染引擎，估算无法反映段距/图片/样式分页/页边距，对"靠分页撑页"的短文档尤其失真
- 修复：新增 _word_page_count 经本机 Word COM（ComputeStatistics(2)=wdStatisticPages）读真实页数；total_pages(path, renderer="word") 优先用真值，estimate_lines 降级为兜底。Win COM 每篇文档必须独立实例、用完即 Quit（同进程连开多篇会 <unknown>.Open + RPC 失效）
- 铁律固化：文档页数一律走 Word/LibreOffice 真实渲染，禁止再依赖拍参数估算

## 坑21 · Word 占位符模板：签名图片 descr/属性内嵌人名漏替换【文档解析坑】
- 现象：gen_sdp/gen_srs 占位符脚本跑完，python-docx 扫描 paragraph.text 显示人名已替换，但字节级 grep document.xml 仍残留"袁燕/张星竹/杜晟"等
- 根因：残留人名来自两处，replace_block 遍历 w:t 节点根本碰不到：①手写签名图片的 alt text 在 wp:docPr 的 descr 属性（如 descr="杜晟 - 副本"）、name 属性；②图片元数据里 MARKNAME=手写签名\nUSERNAME=袁燕 这类自定义文本不在 w:t 节点
- 修复：新增 replace_attributes(parent) 对元素 iter 递归处理 el.text 与所有属性值做 do_replace；main 中 replace_runs 之后追加 replace_attributes(doc.element.body) 调用
- 铁律固化：做"整文档查找替换"类工具时，不能只遍历 w:t 文本节点，必须同时处理①元素属性值(descr/name)②非 w:t 的自定义文本节点；否则图片/签名/文本框里的具体数据会漏替换。验证必须字节级(zipfile 读 xml 确认)，不能只信 python-docx 的 paragraph.text

## 坑22 · 查找替换长串优先：含短占位符子串的完整串必须前置【文档解析坑】
- 现象：REPLACEMENTS 里已有 ("R121","{{meta.project_id}}")，后加 ("https://.../trunk/R121","{{cm.svn_trunk}}")，结果 URL 里的 R121 被先替换成 {{meta.project_id}}，完整 URL 映射失效，生成文档出现 https://.../trunk/{{meta.project_id}} 残留。
- 根因：do_replace 按顺序逐条 text.replace，短串先匹配会破坏长串的后续匹配。
- 修复：把含 project_id 子串的完整 URL/路径映射移到 REPLACEMENTS 列表最前（长串优先原则）。
- 铁律固化：查找替换映射表必须按"串越长越靠前"排序；任何完整串若包含其他映射的键（如 R121 是 project_id 的键），该完整串必须排在被包含键之前。新增映射时先做"是否含已有键"的自检。

## 坑23 · 页眉 VML 框跨 run 合并必须早于逐节点替换【文档解析坑】
- 现象：replace_header_precision 先 replace_runs(逐 w:t 节点 do_replace) 再分段合并，导致页眉里跨 run 的 R121_SDP_V1.02（拆成 R121_SDP_V1.0 + 2 两个 w:t）被单节点 R121 提前替换成 {{meta.project_id}}_SDP_V1.02，整体畸形。
- 根因：逐节点替换在分段合并之前执行，破坏了跨 run 完整串。
- 修复：replace_header_precision 删除前置 replace_runs 调用，改为"先分段合并(含触发键的连续 w:t)做 do_replace → 再对剩余节点保守兜底"；配合 REPLACEMENTS 长串优先排序(坑22)，整串优先匹配。
- 铁律固化：处理 VML 页眉/文本框等多 run 文本的精准替换时，严禁先逐节点替换再合并；必须"先合并跨 run 段、整段 do_replace、写回首节点清空其余"，保护版式且避免短键提前拆串。

## 坑24 · uvicorn 多 worker + Windows multiprocessing.spawn 遗留孤儿 worker 抢端口【服务端致命坑】
- 现象：前端下载/接口偶发"一直处理中"，后端接口单独 curl 却能 200 返回；或前端 30 秒超时提示"请求超时"。
- 根因：run_backend.py 用 `uvicorn.run(..., workers=8)`，Windows 上 workers 通过 `multiprocessing.spawn` 派生 8 个独立 python 子进程（命令行含 `multiprocessing.spawn.spawn_main`）。`taskkill /F /PID 父进程 /T` **杀不掉这些 spawn 子进程**（Windows spawn 模型下 /T 递归不全）。反复启停 start.bat 后，累积十几~二十几个**孤儿 worker 仍 LISTEN 8000 端口**（父进程已死）。Windows SO_REUSEPORT 把新 TCP 连接负载均衡分发到这些进程，有一定概率路由到僵尸 worker → 连接建立但不返回任何数据 → 前端 fetch 永远 pending → 触发 30 秒兜底超时。
- 排查关键：① netstat -ano 看 8000 有几个 LISTENING（不止一个 PID 即异常）；② Get-CimInstance Win32_Process 看 `multiprocessing.spawn*spawn_main*` 进程数，以及它们的 ParentProcessId 是否还活着；③ 用 PowerShell 并发发多个请求，若偶发卡说明有坏 worker 在抢连接。
- 修复：start.bat 的 kill_port 子程序在杀端口占用进程后，**额外扫一遍所有 `multiprocessing.spawn*spawn_main*` 进程，凡是 ParentPid 已死（在所有存活 PID 列表里找不到）的孤儿一律 taskkill**，活的（ParentPid 还活着）不动。
- 铁律固化：① 凡用 uvicorn workers=N(>1) 在 Windows 跑，start 脚本必须能清理孤儿 spawn worker，不能只杀端口；② 排查"偶发卡"优先想"进程是否干净"，而不是先怀疑代码逻辑；③ 不要反复启停后端不清理，会累积孤儿。

## 坑25 · batch 标签必须用单冒号 `:label`，`::` 只是注释不是标签【Windows bat 致命坑】
- 现象：`start.bat` 双击报 `The system cannot find the batch label specified - kill_port/start_backend/start_frontend`，整个脚本启动不起来。
- 根因：我在 start.bat 里把 `::kill_port`、`::start_backend`、`::start_frontend` 当标签写。`::` 在 cmd.exe 里**只是注释（REM 的变体），不是合法 goto/call 标签**。合法标签是**单冒号 `:kill_port`**。很多网贴错写成 `::`，但袁总机的 cmd 严格报错。
- 验证方法：写最小 bat，`call :x` 配 `:x` 能跑、`::x` 必报"找不到标签"，直接复现。
- 修复：所有标签改单冒号 `:label`。顺手加 UTF-8 BOM（防中文 REM 乱码），并把 `%ROOT%logs` 改成 `%ROOT%\logs`（%~dp0 末尾带反斜杠，不显式加分隔符会吞掉 'l' 导致路径错）。
- 铁律固化：Windows batch 的 `call`/`goto` 目标必须 `:label`（单冒号）；`::` 永远只当注释用，绝不作标签。

## 坑26 · 前端"卡处理中"要把承诺(Promise)挂起和"抛异常"分开想【前端排查坑】
- 现象：下载弹窗进度条停在 90% 处理中、或卡 30 秒超时，按钮不变。
- 根因分两类，必须分清：① **Promise 永不 settle**（fetch 发出去但连接被坏后端/坏 worker 吞掉，resp 一直不来）→ 进度条停在 90% 循环"处理中"，catch 也进不去；② **Promise 已 resolve/reject 但 then/catch 内部抛异常或 UI 没更新** → 进度条到 100% 但按钮不变。
- 排查关键：F12 → Network 过滤 `save-to-local`，看请求到底有没有发出、状态码是什么。有请求且 200 但 UI 不变=逻辑 bug；没请求或一直 pending=网络/后端问题。
- 修复手段(防御性)：① 进度条加 30 秒总超时兜底——`Date.now()-startTs>30000 && 按钮文案含'下载中'` 就强制 clearInterval + 红色失败 + 按钮还原（保证永不"永远卡"）；② catch 里用 `getElementById('dl-confirm-btn')` 拿按钮（不靠 textContent 找，避开文字已变找不到）；③ 失败提示给出排查方向（路径存在/可写/文件是否被 Word 占用）。
- 铁律固化：任何"先转圈再等异步结果"的 UI，必须配超时兜底，不能让用户面对"永不动的圈"。Promise 挂起和抛异常是两回事，先靠 Network 面板定类。

## 坑27 · 前端缓存导致改了代码袁总还看到旧行为【前端部署坑】
- 现象：后端已修好、Playwright 实跑 1 秒成功，但袁总浏览器仍"卡"。
- 根因：浏览器强缓存了旧 pp.js（改前版本 Promise 不 settle）。即使我已给 pp.js 加 `?v=5` query，袁总那次没硬刷，仍用老文件。
- 修复：① 前端服务 scripts/frontend_server.py 对所有响应加 `Cache-Control: no-cache, no-store, must-revalidate` + `Pragma: no-cache` + `Expires: 0`；② 改版时升级引用 `pp.js?v=N&t=日期` 强制破缓存；③ 袁总侧 Ctrl+F5 硬刷。
- 铁律固化：改了前端文件，必须同时①升版本号/加日期戳 ②确认前端服务 no-cache；否则袁总看到的是旧版，排查会走偏（误以为后端问题）。

## 坑28 · 后端写盘要先 makedirs 父目录，filename 不应含路径前缀由前端拼【后端健壮性坑】
- 现象：袁总在下载弹窗"文件名"输入框填 `uploads/R121_SDP_V1.00`，后端报 `[Errno 2] No such file or directory: 'D:/5000/R121\\uploads/R121_SDP_V1.00.docx'`。
- 根因：D:\5000\R121\uploads 子目录不存在，open() 直接写报错。袁总把"子目录"误填进文件名框。
- 修复：save-to-local 里 `full=os.path.join(local_path, filename)` 后，先 `os.makedirs(os.path.dirname(full), exist_ok=True)` 自动建子目录；同时校验 filename 不允许 `..` 或盘符（防注入）。
- 铁律固化：凡"按路径写文件"的接口，必须 makedirs 父目录；不要让用户靠手填子目录路径，UI 上文件名框只收纯文件名更直观。

## 坑29 · 排查要"先验证不靠推断"，偶发问题用并发/多实例复现【通用方法论坑】
- 现象：本次"卡处理中"我一度推断是"前端缓存旧代码/旧 Promise 逻辑"，但真因是服务端孤儿 worker 抢端口——两类原因长得很像（都表现为卡），靠推断会误诊。
- 根因：没第一时间做"端到端真实验证"——应该先 `netstat` 看 8000 有几个 LISTENING、用 `Get-CimInstance` 看 spawn worker 父子关系、用并发 curl 看是否偶发，而不是在代码层猜。
- 铁律固化（举一反三）：遇到"偶发卡/时好时坏"，优先级：① 看进程/端口是否干净 → ② 并发发请求看是否概率性 → ③ 才是代码逻辑。偶发必是"有坏实例在抢资源"，不要只在单请求成功就下结论。

## 坑30 · AI 做完活必须写 session-log 记忆，不能只交差（本次重蹈坑12）【流程坑】
- 现象：本次从"点提交页面死"→"一直下载中"→"卡处理中"→"启动不起来"，连续多轮修复，但前几轮**没写 session-log / qc-lessons**，违反 work-rules 第5条；直到袁总点醒"每次做完要记录、复盘、举一反三"才补。
- 根因：把"修复-回复"当主线，把"写记忆"当可选项；且本次新坑（孤儿 worker/bat 标签/前端缓存/写盘 makedirs）都是可复用的硬知识，不记下次必重踩。
- 修复：本次全部新坑已补入 qc-lessons(坑24~29)、过程补入 session-log、进度更新 session-init。
- 铁律固化（袁总强调）：① 每轮对话结束前**必须**写 session-log（做了什么+所有坑），写完才能汇报；② 踩新坑即写 qc-lessons；③ 任何修改要"举一反三"——同模式问题（多 worker 清理/前端缓存破/异步超时兜底）是否别处也存在、能否做成通用能力；④ 不交半成品（如选目录按钮拿不到绝对路径就别硬上）。

## 坑31 · 改代码后必须真实走用户操作路径验证，不能只跑内部函数/TestClient 就宣称"已验证"【验证铁律坑】
- 现象：R105_SDP.docx 袁总反馈"打开还是空"。第十一轮我仅用 `TestClient` + `generate_doc_bytes` 断言"文档有数据(324KB)"就回复"代码没问题、是您运行态"，袁总震怒质问"你自己没验证吗"。
- 根因：① 没走用户真实路径（启后端→浏览器点 save-to-local→真实落盘→真实打开）；② 袁总机器上跑的是我**改代码前的旧后端进程**，旧代码生成空文件；且袁总 Word 一直开着那份旧空文件，刷新看到内存旧内容。内部函数/TestClient 跑的是最新代码，天然发现不了"旧进程/旧文件"这类运行态问题。
- 修复：第十二轮补真实验证——真实启 uvicorn(8011) 真实 HTTP 调 save-to-local 落盘→324251字节/31表/125行/含全数据；真实杀旧进程(PID 6736)、前台启最新代码后端常驻 8000(PID 17844)；真实 HTTP 打 8000 重新生成 D:/5000/R105/R105_SDP.docx=324KB 含全数据。确认代码生成正确后，重启后端+重新生成覆盖旧空文件，并提示袁总"必须关闭 Word 重新打开"。
- 铁律固化：改完代码验证分三层，缺一不可——①单元/接口层(内部函数/TestClient)；②**真实运行态层**（启真实后端进程+真实 HTTP 调用户实际点的接口+真实落盘）；③**打开层**（解析/打开产物确认可见）。凡用户报"显示空/旧/不对"，先怀疑运行态（旧进程未重启、浏览器缓存、文件被占用锁定、打开的是旧路径文件），并用真实路径复现，不靠推断下"代码没问题"的结论。这与坑27(前端缓存)、坑29(先验证不靠推断)同源。

## 坑32 · perm 只读保护标记非法注入导致 Word 打开空白 + 孤儿 worker 占端口让"重启"失效【双重致命坑】
- 现象：R105_SDP.docx 连续三轮"打开是空"。zipfile/正则解析 document.xml 显示内容全在（31表/2670文本节点），但真实 Word 打开表格=0、正文=1，完全空白。
- 根因1（文档层）：`_mark_readonly_tables` 注入 permStart/permEnd 位置违反 OOXML 规范——首个 permStart 插在 document.xml **位置 0（XML 根元素外）**，其余插在 body 级与 `<w:tbl>` 平级（规范要求必须在**段落内部**）。Word 解析遇非法结构**静默丢弃全部内容**。XML 解析器宽松不报错，所以"XML 有内容"≠"Word 能渲染"。
- 根因2（进程层）：8000 端口被旧代码**孤儿 multiprocessing worker** 占据——run_backend.py 启动 2~8 个 worker，taskkill 只杀主进程时 worker 变孤儿继续持 socket 服务旧代码；且 netstat 显示的 LISTEN PID 可能是已死主进程，taskkill 杀了个寂寞。多次"重启后端"实际从未换到新代码（文件大小指纹可判：324251=带bug旧代码 / 323255=修复后）。
- 修复：①回退 `_protect_readonly_zones(tmp_path)` 调用（doc_service.py，函数保留待另行攻关，perm 须插段内）；②杀光全部 cmdline 含 run_backend|backend.main 的 python 进程；③start.bat `:stop_port` 加兜底：cmd 调 PowerShell 按 cmdline 匹配清理本项目后端进程（已实测 8000 释放）。
- 铁律固化：①**验证生成文档必须用真实 Word COM 打开**（表格数/Content.Text 长度/关键字三项），XML/zipfile 解析不算数（PowerShell COM 脚本沉淀 temp/word_open_check.ps1，注意 ps1 中文需 UTF-8 BOM）；②**杀多 worker 服务必须连 worker 全杀**（taskkill /T + 按 cmdline 兜底），重启后必须核验"新进程 PID 真在监听端口"且用文件大小指纹确认产物来自新代码；③凡给 docx 注入 OOXML 标记（perm/保护/底纹），注入后必跑真实 Word 打开验证，规范位置不确定时不注入。

## 坑33 · 文档"部分区域只读"用 Content Control(sdt) 而非 permStart/permEnd，规避 Word 空白【OOXML坑】
- 现象：需求"平台生成的数据在文档中不可编辑、其余可编辑"。坑32 用 permStart/permEnd 注入，因位置非法(根元素外/body级)导致 Word 打开静默丢全部内容变空白。
- 根因：OOXML 的 permStart/permEnd 是 run 级元素，必须置于段落(w:p)内部；放 body 级或与 `<w:tbl>` 平级即非法，Word 静默丢弃内容。整文档 documentProtection+perm 例外方案对位置要求极严、极易错。
- 修复（推荐方案）：改用 Content Control——用 `<w:sdt w:id><w:sdtPr><w:lock w:val="sdtContentLocked"/></w:sdtPr><w:sdtContent>…目标块…</w:sdtContent></w:sdt>` 包裹"要锁定的块"（如平台表），内容锁定不可编辑，其余区域默认可编辑；sdt 作为 body 的 block 级子元素合法，Word 打开稳定不空白。
- 适用：凡"某几张表/某段只读、其余可编辑"的需求，首选 sdt 锁定，不要碰 perm；若确需整文档保护+可编辑例外，permStart/permEnd 必须严格插在段落内部(w:p 直接子级)并用真实 Word COM 打开验证不空白。
- 铁律固化（与坑32同源）：凡给 docx 注入 OOXML 标记（perm/保护/底纹/sdt），注入后必跑真实 Word COM 打开（表格数/文本长度/关键字）验证，不能只看 XML/zipfile 解析。

## 坑34 · 只读保护"假验证"：只数 XML 标记≠锁定生效，且用户看的可能是旧文件【验证铁律坑】
- 现象：袁总反馈"开发计划全篇可编辑"，质疑 AI 幻觉。AI 上一轮只统计 XML 里 `<w:sdt>` 出现 10 次就宣称"10张平台表已锁定"，未验证 Word 是否真的识别与锁定。
- 真因两层：①**验证漏洞**——标记存在 ≠ Word 识别为内容控件 ≠ 锁定生效；②**用户打开的是旧文件**——袁总打开的 `D:\5000\R105\trunk\项目管理\项目策划\项目计划\R105_SDP.docx`(331294字节, 2026/8/28) 是旧版无保护文件，而新生成的带保护文件是 323610 字节（放在 D:/5000/R105/ 根目录）。
- 权威验证（补做）：真实 Word COM 打开新生成文件 → `ContentControls.Count=10`、`cc[0..9] LockContents=True / LockContentControl=True` → **锁定真实生效**（10 张平台表不可编辑、不可删除，其余可编辑）。
- 铁律固化（务必执行）：①凡"只读/保护"类需求，验证必须查 **Word 侧真实属性**（ContentControls.Count + LockContents + LockContentControl），不能只数注入的 XML 标记；②交付/排查时必须核对用户打开文件的**路径+大小+时间戳**（文件大小指纹：**323610=带sdt保护的新文件 / 331294=8/28旧版无保护**），避免"用户开旧文件"导致的误判；③用户反馈与自测不符时，第一反应是查"他打开的到底是不是我刚生成的文件、跑的是不是新代码进程"，而不是先怀疑代码或否定用户。


## 坑35 · 换方案只移植"主能力"、漏掉配套能力（只读保护在、颜色没了）【方案移植坑】
- 现象：袁总反馈"可读可写只能做成有颜色区分的，这次不论是否可编辑，颜色都没了"。
- 根因：上一轮(第十轮)`_protect_readonly_zones` 是**两件事打包**：①perm 真实保护 ②`_shade_readonly_tables` 给只读单元格加 **FFF2CC 黄底纹**（视觉区分）。第十三轮因 ①perm 位置非法导致 Word 空白而换 sdt 方案时，我只移植了"锁定"这一件事，**把②底纹函数整个落下**——`_apply_sdt_readonly` 里只有 sdt 包裹，没有任何底纹逻辑。
- 修复：在 `_apply_sdt_readonly` 里 `doc = _shade_readonly_tables(doc)` 补回底纹。实测恢复 `w:fill="FFF2CC"` 共 955 处。
- **铁律固化：换技术方案时必须列"原方案能力清单"逐项对齐**——原方案做了 A+B+C，新方案不能只做 A。保护与视觉标识是两件事，必须同时做；改完要按清单逐项验证（本例：锁定=ContentControls/LockContents、颜色=FFF2CC 计数、居中=jc=center 计数）。

## 坑36 · 统计文档表格必须用递归 iter()，body.findall() 会漏掉 sdt/嵌套结构里的表【验证脚本坑】
- 现象：我用 `body.findall(W+'tbl')` 统计生成文件只有 21 张表，而正则统计是 31 张，一度误判"10 张平台表全部丢失"（袁总也反馈"表7 没有了"）。
- 根因：**10 张平台表被 sdt 包裹在 `body/sdt/sdtContent/tbl`**，不是 body 直接子级，`findall` 只取直接子级所以全部漏掉。表一直都在。
- 正解：统计表格一律用 `body.iter(W+'tbl')`（递归所有层级），或先用正则 `<w:tbl[ >]` 计数校验；**两种统计法结果不一致时，必是统计方式问题，不是文档问题**。
- **铁律固化：任何"东西不见了"的结论，先用两种独立方法(递归解析 + 正则计数)交叉验证再下结论**，否则又是"幻觉式判断"。

## 坑37 · 表格居中缺失：table_builder 生成的表没写 tblPr/jc=center【格式对标坑】
- 现象：袁总反馈"很多表格没有居中、文字也没对齐"。取证：生成文件 31 张表中 **15 张 `jc=-`**（未居中），且**未居中的全是平台动态表**；R121 基准对应表均为 `jc=center`。
- 根因：`table_builder` 生成的平台表未设置 `<w:tblPr><w:jc w:val="center"/>`（模板静态表大多自带）。
- 修复：新增 `_ensure_tbl_center(seg)`，在 sdt 包裹平台表时补 jc=center。注意 **CT_TblPr 子元素有 schema 顺序，`w:jc` 必须排在 `w:tblW` 之后**（放错位置 Word 会忽略）；已有 jc 则不覆盖。修复后居中表 26/31。
- **铁律固化：对标格式不能靠肉眼看，要逐属性取证比对（tblJc / cellJc / vAlign 计数），并与基准文档(R121_SDP_V1.02.docx)做差集**。

## 坑38 · 区分"占位符值"与"模板静态残留"：R105_SDTD_ 不是占位符【数据溯源坑】
- 现象：袁总要求把引用文件里的 `R105_SDTD_` 改成 `R105_SDTD_V1.00`。查库发现 `ref_sdtd_doc_number = 'CEC-SDTD-R105'`（完全不同的值）→ 说明文档里的 `R105_SDTD_` 是**模板静态文本残留**，不是占位符填充结果，改库无效。
- 修复：新增 `_fix_sdtd_version()`，在生成时对 `<project_id>_SDTD_` 且后跟非字母数字的情况补上文档版本号。
- **铁律固化：文档里出现的具体值，先查清来源是"占位符填充 / 模板静态 / 代码写死"再动手**，否则改错地方（改库 or 改模板 or 改代码）白费功夫。三类来源的修法完全不同。

## 坑39 · 删除电子签名图片：按 descr 里的 USERNAME=<姓名> 定位整个 w:drawing【文档处理坑】
- 需求：袁总要求"删除马慧芳的电子签字"。取证发现 5 处"马慧芳"：**2 处是电子签名图片**（`wp:docPr`/`pic:cNvPr` 的 `descr` 含 `MARKNAME=手写签名&#10;USERNAME=马慧芳&#10;DATETIME=...`），**3 处是正文/表格里的姓名文本**。
- 修复：新增 `_remove_signature_images()`，用正则 `<w:drawing>.*?</w:drawing>` 匹配、若块内含 `USERNAME=<姓名>` 则整块删除（只删签名图，保留正文姓名，因为袁总说的是"电子签字"）。
- **铁律固化：文档里的"人名/签名"可能是图片元数据(descr/USERNAME)而非纯文本**（参见坑21：签名图片 descr 漏替换）。处理前先 grep 全文定位形态（属性 vs 文本），再决定删除/替换策略。


## 坑40 · lxml 遍历时修改树会让迭代器失效（后端 500）【XML处理坑】
- 现象：在 `for t in _all_tags(root, "t")` 循环里直接 remove/insert run（包裹 sdt），接口直接 500，前端只见 Internal Server Error。
- 根因：边遍历 lxml 树边改结构，迭代器失效。
- 修复：先遍历收集目标节点到 list，遍历结束后再统一修改。
- 铁律固化：凡"遍历 XML 树并修改结构"，一律【先收集、后修改】；看到 500 先查后端日志堆栈，不要只看前端报错。

## 坑41 · 往类里插入新方法时，必须确认插入点是方法结尾【代码编辑坑】
- 现象：新增 `_lock_run_of` 时，把新方法插在了 `fill_tree` 的"属性循环"之后，但那**不是方法结尾**（后面还有"第3步 跨run合并 + return root"），导致后续代码被吞进新方法体，报 `NameError: root is not defined`。
- 修复：读取方法完整定义确认边界后重新插入，把被吞的代码归位。
- 铁律固化：用 replace 插入函数时，old_str 必须确认是【方法最后一行】（可先 read_file 看后续代码）；插完立即 lint + 跑一次真实生成验证。

## 坑42 · 非表格占位符锁定：用 inline sdt 包 run（区分平台填/用户填）【只读保护坑】
- 需求：除 10 张平台表外，封面 R105、软件名称等**由占位符填入的值**也不可编辑，而签字页/用户填写区要能编辑。
- 实现：在 `WordInjector.fill_tree` 替换标量占位符后，把该 `<w:t>` 所属的 `<w:r>` 包成 inline 内容控件：
  `<w:sdt><w:sdtPr><w:id w:val="N"/><w:lock w:val="sdtContentLocked"/></w:sdtPr><w:sdtContent><w:r>原内容</w:r></w:sdtContent></w:sdt>`
- 关键点：①**只锁含占位符的 run**，未含占位符的（用户填写区/手写签字区）天然不锁，天然区分"平台填/用户填"，无需额外标记；②CT_SdtPr 子元素有 schema 顺序，**w:id 必须排在 w:lock 之前**；③inline sdt 可直接作段落子元素（CT_SdtRun），无需外套 run。
- 效果：本项目实测 inline sdt 163 个 + 平台表 block sdt 10 个 = 173，Word 侧 `ContentControls=173` 且 `LockContents` 173/173 全锁定。

## 坑43 · 数据按基准图校准：表头跨列合并会让"按行0字符串比对"误判【数据核对坑】
- 现象：附录B 相关方矩阵本已存在（12 列 / 9 角色），但我按"行0 前30字"与基准比对，行0 因跨列合并只显示 3 格（序号|活动|利益相关方），被误判为"缺失"。
- 实际差异只有数据：DB 多了一行"其它/双周例会"（基准图无"其它"阶段），√ 分布其余一致。
- 修复：dump 表的所有行（含 vMerge、各角色 √）逐格核对，再按图修数据（DELETE 多余行）。
- 铁律固化：核对表格是否"缺失/一致"必须 dump **全部行**，不能只看表头行；跨列合并(gridSpan)的表头单元格数会少于实际列数。


## 坑44 · 模板封面"共 N 页"不显示：域标记被非法嵌套在 <w:t> 内【OOXML坑】
- 现象：生成文档封面显示"（共页）"，页数数字缺失。此前误判为"模板无 NUMPAGES 占位符需自己加域"，实际模板**有** NUMPAGES 域。
- 根因（取证所得）：模板该段落写作 `<w:t>（共 <w:r><w:fldChar begin/></w:r>...<w:instrText>NUMPAGES</w:instrText>...<w:fldChar end/></w:r> 页）</w:t>`——域的 `<w:r>` 被**嵌套进 `<w:t>` 文本节点内部**。`<w:t>` 只能含文本，不能含 run，Word 解析后域失效 → 数字不显示。
- 修复：把嵌套的域 run 提取为平级 run 序列：`<w:r><w:t>（共 </w:t></w:r> <w:r><w:fldChar begin/></w:r> <w:r><w:instrText> NUMPAGES </w:instrText></w:r> <w:r><w:fldChar end/></w:r> <w:r><w:t> 页）</w:t></w:r>`，配合 settings 的 `w:updateFields` 打开自动刷新。
- 铁律固化：文档不显示某值时，先 dump 该处原始 XML 看结构是否合法，不要凭"有没有占位符"下结论。

## 坑45 · 正则替换 XML 片段时必须把闭合标签一并消耗【XML处理坑】
- 现象：修复页数域后模板 XML 报 `Opening and ending tag mismatch: p line 2 and r`，后端 500。
- 根因：正则只匹配到 `</w:t>` 就结束，原外层的 `</w:r>` 未被消耗，替换后又新开了 `<w:r>...</w:r>`，导致多出一个 `</w:r>`。
- 修复：把 `</w:r>` 纳入匹配模式一起替换；并保留备份（*.bak）便于回滚。
- 铁律固化：改模板(docx)这类核心资产前**必须先备份**；正则替换 XML 片段后，必须做一次 XML 解析校验（etree.fromstring）确认结构合法。

## 坑46 · 只读锁定白名单要收窄：正文高频键不能锁【只读保护坑】
- 现象：按"所有由占位符填入的值都锁"实现后，锁定 163 处，导致系统概述、资源描述等**描述性正文也不可编辑**（袁总要求这些可编辑）。
- 根因：白名单包含了 `sys.short`(型号)、`org.*`(单位)、`ref.*`(引用文件)、`cm.svn_*`(SVN地址) 等——这些在正文段落中大量出现，一锁就把整段正文变只读。
- 修复：白名单收窄为 `meta.project_id / meta.doc_number / meta.doc_version / meta.doc_ver_tag / meta.approve_date / meta.total_pages / sys.software_full / header.form_no`（锁定从 163 → 113）。
- 铁律固化："只锁选中字段"类需求，必须先确认该占位符在文档中的**出现频次与位置**——高频出现在正文的键不进锁定白名单；锁定后要统计数量并复核正文是否仍可编辑。

## 坑47 · NUMPAGES 域结果写到域外，“共 N 页”永不联动【OOXML致命坑】
- 现象：生成文档封面显示“（共 18 页）”，新增页后数字不变，袁总质疑“页码确定改对了吗”
- 根因：doc_service.py 的 _apply_doc_fields 第(2b)步把 total_pages 当 fallback
  插到 <w:fldChar end> **之后（域外）** —— 域外就是普通文本，Word 永不更新；
  且模板原生域本身是坏域（begin -> instrText -> end，缺 separate，没有结果值）
- 修复：
  ① 模板用 lxml 重建标准域结构（begin -> instrText -> separate -> 结果 -> end），
     坏域去重（NUMPAGES 数 2 -> 1）；
  ② 代码改为把结果写入**域内**（separate 与 end 之间），不再写到域外；
  ③ 替换前向前找最近 instrText 校验是 NUMPAGES，避免误改 PAGEREF
     （否则目录页码会被整体改成总页数）
- 铁律：Word 域的“结果值”必须在 separate 与 end 之间；在域外补数字 = 死数字。
  配套 settings.xml 需 <w:updateFields w:val="true"/>，打开时才自动重算。

## 坑48 · 核对脚本正则误报：XML属性被当业务数据 / 表标题靠猜【验证脚本坑】
- 现象：核对报告称“日期未改 14 处”“表7 丢失”，实际全是误报
- 根因1：日期正则 20\d\d-\d\d-\d\d 在**整个 document.xml** 上跑，
  会匹配到 XML 属性（如列宽 w:w="2025" 拼出的数字），误报“日期未改”
  （真实剩余 14 处是平台进度计划业务日期 2024-xx-xx，本就该保留）
- 根因2：搜“各阶段工作量估计”找不到表，因为真实表头是
  “开发阶段|阶段比例|工程类工作量（人日）…”，标题名与猜测不一致 -> 误判“表丢了”
- 修复：① 日期类正则只在 <w:t> 正文文本里搜；
  ② 先列出全部 <w:tbl> 的表头文本再匹配，绝不靠猜标题
- 铁律：下“缺失 / 未修改”结论前，必须先排掉两件事——
  正则是否匹配到了 XML 属性、关键词是否与文档真实写法一致。

## 决策 · 只读区颜色（袁总 2026-09-02 拍板）
- 结论：**全部保留无色**，不加任何底纹（FFF2CC 等）。
- 落地：_shade_readonly_tables 在 _apply_sdt_readonly 中维持注释状态，不得再恢复调用。
- 说明：只读由 sdt（Content Control）锁定保证，不依赖颜色标识；
  加底色会导致打印呈灰白，故袁总选择无色。

## 坑49 · _merge_runs 递归收集 run 遇嵌套表格清空页眉【docx处理坑】
- 现象：生成的 SDP 正文/附录页眉（header4/5）全部文本为空，袁总反馈"页眉没有了"
- 根因：页眉 XML 存在"整张表格嵌在 w:p 内"的非标准结构，_merge_runs 用 _all_tags(p,'r') 递归收集段落全部 run（跨表格单元格），join 后含 {{ 占位符触发合并逻辑 → 删除"其余"run（即表格各格的 run 全删）→ 全表文本清空；且第一个 run 无 w:t 时合并文本也丢
- 修复：段落含 tbl 直接 return（单元格内段落稍后作为独立 p 处理）+ first_t 为空时新建 w:t 承载文本
- 铁律固化：凡用递归 iter 收集 OOXML 元素（run/段落/文本），必须防御嵌套表格——先判 p.iter() 里有无 tbl

## 坑50 · Word COM Fields.Update+Save 产出坏 XML + NUMPAGES 懒分页【COM坑】
- 现象：用 COM 更新域后保存，document.xml 出现 sdtContent 标签不闭合（lxml 解析失败）；且 NUMPAGES 更新后=6 而真实 50 页
- 根因（两层）：① Word 序列化 bug——Fields.Update 触发后保存会写出不闭合的 sdt（二分法实测：只 Open+Save XML OK，加域更新即 BAD）；② Word 懒分页——打开时文档未完全分页，Fields.Update 时 NUMPAGES 按已渲染部分计算
- 修复（最终方案）：COM 只读打开 → ComputeStatistics(2) 强制全量分页取真实页数 N → 不保存直接关 → Python 改 document.xml 中 NUMPAGES 域 separate~end 之间的 w:t 缓存为 N。XML 全程合法、页数精确
- 铁律固化：① 生成端写页码一律"COM 只读算页数 + Python 改域缓存"，禁止 COM Save；② COM 里任何统计前先 ComputeStatistics 强制分页

## 坑51 · 相邻两张 w:tbl 无段落分隔会被 Word 合并渲染 + 表格适配不分节压坏横向附录【docx格式坑】
- 现象：表22/23 "和到一起"变成一张表；附录C 宽表（R121 原宽 14613）被压到 9278 列挤压换行"表格太长"
- 根因：① OOXML 里同父级相邻两张 tbl 中间无段落时 Word 合并渲染为一张表（模板相邻占位符段落被整表替换后触发）；② _fit_tables_to_page 只取第一个 sectPr 的纵向宽（9468）压所有表，而附录 sect#4 是横向页（可用宽 14406）
- 修复：① 新增 _separate_adjacent_tables 同父级相邻表对插空段落；② 按文档序收集各节可用宽 [9468,9590,9590,14406]，遍历时遇 sectPr 切换，每表用所在节的宽（嵌套表跳过）
- 铁律固化：① 整表替换占位符后必须检查相邻表格；② 多节文档的表格宽度适配必须分节计算（横向节 pgSz w=16838）

## 坑52 · fill_tree 单段全锁漏锁 + R121 表头无空格铁证【docx处理坑】
- 现象：封面"CB-B/DSQ-1AG终点/轮载开关模拟器驱动软件"未锁定；表头"序 号"(\xa0)、"型号 / 图号"被袁总反复点名"表格里有空格"
- 根因1：fill_tree 中相邻多个锁定占位符（{{sys.short}}{{sys.software_full}}）替换后合并成【单段全锁】，len(merged)<=1 分支直接 continue（注释说"走旧逻辑"但旧逻辑 _lock_run_of 从未被调用）→ 漏锁。修复：单段全锁也调 _lock_run_of——同时补上所有"占位符独占 w:t"场景的漏锁
- 根因2：R121 dump 取证全部表头为紧凑格式（'序号'无\xa0、'型号/图号/代号/版本/参数'无空格、'开发阶段'无斜杠）——R105 模板/生成表头的 \xa0 和" / "正是袁总说的空格。修复：_compact_table_headers 全局清理（只动 \xa0 与" / "，'单  位'等签署页对齐空格保留）+ 模板静态 CB-B/DSQ-1AG 5 处改 {{sys.short}} 占位符（锁定需经占位符路径）
- 铁律固化：①凡"锁定占位符值"，合并后单段全锁也必须包 sdt；②对标格式必须 dump 原版逐字符取证（repr 显示 \xa0）；③模板静态文本要锁定必须先改占位符；④表标题段落加 keepNext 防分页分离（_add_caption_keepnext）

## 坑53 · Word COM 在 uvicorn worker(MTA) 内静默失败——必须子进程隔离【COM坑·二次确认】
- 现象：生成接口里调 _update_fields_with_word，ComputeStatistics 能返回页数(50)，但 Bookmarks/Range 相关调用全部静默失败（pagerefs 恒空），TOC 页码永远写不进去；单独脚本跑同一段代码却完全正常
- 根因：uvicorn worker 是 MTA 多线程环境，Word COM 要求 STA（同坑17 在 PyCharm/pytest 的表现）
- 修复：新增 backend/services/word_pages.py 独立子进程（纯 STA），subprocess 拉起、JSON 回传 {"pages":N,"pagerefs":{...}}；主进程只解析 JSON，永不直接 Dispatch
- 铁律固化：任何在 FastAPI/uvicorn worker 内取 Word 数据（页数/书签/域）的操作，必须 subprocess 子进程隔离

## 坑54 · TOC 书签是隐藏书签 + HYPERLINK 内嵌 PAGEREF【docx域处理坑】
- 现象：目录页码写不进去 / 写错 1 页
- 根因1：TOC 的书签（_TocXXXX）是【隐藏书签】，doc.Bookmarks.Count 只有 5（实际 PAGEREF 引用 88 个），必须先 `doc.Bookmarks.ShowHidden = True` 才能按名访问，否则 Exists 恒 False
- 根因2：目录条目是【HYPERLINK 域内嵌 PAGEREF 域】的嵌套结构，按"begin...end 平衡片段"整体处理时取到的指令是外层 HYPERLINK，内层 PAGEREF 永远轮不到
- 根因3：不能用 f.Result.Text 作页码真值（受 TOC 更新顺序影响，实测偏移 1 页）
- 修复：按 instrText 逐个定位——每条 NUMPAGES/PAGEREF 指令，找它之后最近的 separate → 替换其后的第一个 w:t；页码真值取 `Bookmarks(bm).Range.Information(1)`（逻辑页码）
- 铁律固化：① 访问隐藏书签前 ShowHidden=True；② 处理嵌套域不要整体取片段，按 instrText 逐个定位；③ 页码真值用书签 Information(1)，不用域结果

## 坑55 · 表标题与表格分页分离的两个真因：硬分页符 + keepNext 链过长【Word排版坑】
- 现象：表22/23/24/25 标题留在上页尾、表格跳到下页（袁总反复反馈三次以上）
- 真因1（主因）：模板在表标题与表格之间留了【两个含硬分页符的空段落】(<w:br w:type="page"/>)，Word 连续换两页 → 中间整页空白，且硬分页让 keepNext 完全失效
- 真因2：keepNext 把"标题 + 其后所有段落 + 表格"绑成一大块，Word 放不下时整体推页 → 也会产生空白页
- 修复：① _strip_breaks_between_caption_and_table 删除标题与表格之间的硬分页符、多个连续空段落只留一个；② keepNext 只在"标题紧贴表格（中间至多 1 个空段）"时绑定，不做长链
- 铁律固化：Word 分页问题先查硬分页符（br type=page / pageBreakBefore），再谈 keepNext；keepNext 链不宜超过 2 段

## 坑56 · 表22/23 结构错位：占位符段落位置错误【模板坑】
- 现象：袁总反复说"表22 组织机构表和表23 人力资源表乱"——实际是【组织机构表】标题下没有表格，表22 实体排在【人力资源表】标题之后
- 根因：模板里 {{table.org_chart}} 占位符段落被插在"人力资源表"标题段落之后（@431），而 {{table.human_resource}} 在其后（@433）
- 修复：temp/patch_tpl_orgchart.py 把 {{table.org_chart}} 段落移动到「组织机构表」标题之后（备份 .bak_orgchart）
- 铁律固化：整表占位符插入后必须打印"标题→表格"文档序复核，确认每个标题下挂的是对应的表

## 坑57 · _merge_runs 与 run 级锁定冲突：要么整段被锁，要么占位符残留【docx处理坑·双向陷阱】
- 现象A：模板段落"{{sys.software_full}}和主控板控制软件采用C语言进行开发…"整段不可编辑（袁总要求描述性正文可编辑）
- 现象B：为修 A 把 _merge_runs 改成"段落含 sdt 就 return"，结果跨 run 的占位符（{{sw.name_iap}} 被拆在多个 run）永远合并不了 → 文档里残留未替换的 {{sw.name_iap}}
- 根因：_merge_runs 用 _all_tags(p,'r') 递归收集【全部】run（含已锁在 sdt 内的），合并时把后续正文塞进已锁定的 run（现象A）；直接 return 又放弃了跨 run 占位符替换（现象B）
- 修复：只合并【未锁定】的 run——`runs = [r for r in _all_tags(p,'r') if not WordInjector._in_sdt(r)]`，锁定 run 原样保留；新增 _in_sdt(run) 判断祖先是否有 sdtContent
- 铁律固化：凡"部分锁定"的段落做 run 合并，必须排除已锁定 run；既不能全合并（污染锁定），也不能全不合并（占位符残留）

## 坑58 · 模板静态残留标题与生成标题叠加，导致附录C 末尾多出 3 个无表跟随的标题【模板坑】
- 现象：袁总截图指出附录C 末尾"最后的这个删除掉"——末尾有 3 个多余标题（表C.1 数据管理表 / 表C.1（续）×2）且后面没有表格
- 根因：模板里附录C 原本就静态写着这些标题，而 build_data_mgmt_tbl（含 _split_tbl_with_continuation）生成时又输出一份标题与续表标题 → 叠加重复
- 修复：temp/patch_tpl_trailing.py 删除 {{table.data_mgmt}} 占位符【之后】的残留标题段落（备份 .bak_trailing），保留生成时输出的那份
- 铁律固化：整表占位符替换后，必须检查占位符【之后】是否还有同名的静态残留标题/表格；生成侧输出标题时，模板侧的同名静态标题必须清掉

## 坑59 · 15 列宽表列宽不够容中文 4 字 → 文字每字竖排【docx格式坑】
- 现象：附录A 项目风险管理表（15 列 31 行）每字占一行"竖排"，根本看不完
- 真因：build_risks_tbl 列宽直接搬 R121（最小 142 dxa），中文 4 字约需 700-800 dxa 才容下横排。模板/纵向节 avail=9468 → 横向节 14406；15 列 × 900 dxa = 13500（窄列）→ 文字每字换行
- 修复：① _simple_tbl / _cell 加 size 参数（OOXML sz 半磅，21=10.5号/20=8号）；② 重排附录 A 列宽（描述列 2200+措施列 1700+其余最小 800，总 14300 在横向节内）；③ build_risks_tbl 调用 mkrow 时 size=20 让所有 15 列均用 8 号字，确保 700-800 dxa 列也能容中文 4 字
- 铁律固化：宽表（≥10 列）必须【同时考虑列宽 + 字号】，对标 R121 的列宽只适用于 R121 的字号；本项目沿用 R121 列宽但需缩字号到 8 号

## 坑60 · 模板宽表与对标来源不匹配：R121 根本没有附录A 风险宽表【模板坑】
- 现象：build_risks_tbl 按 15 列对标 R121 生成，但实际 R121 附录A 是文字段落或窄列描述
- 真因：早期误判 R121 表头数与 R105 一致，未做 dump 取证；R121 最高列数表是 12 列（附录B 利益相关方矩阵），没有 P/I 列宽表
- 修复：dump_r121_tables.json 全表头列表 + 列宽取证；15 列宽表实际是我们自创的，需独立设计列宽与字号
- 铁律固化：对标前必须先 dump 参考文档【全部】表格（列宽+列数+表头），确认存在该表型再"对标"，否则就是自创
