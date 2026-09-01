// 作者：袁燕
// 功能：项目策划 PP 页（核心节点）。1:1 还原效果图的「阶段条 + 子页签」机制，子页签填充 R105 真实数据。
// 设计：阶段条 phaseBar + 子页签 node-tabs，内容由 PP_TABS[].fn 生成 widget。取数走 Api（绝不直连 DB）。

// 项目阶段（GJB 研制阶段）
var PP_PHASES = ['策划', '需求', '设计', '实现', '测试', '结项'];

// 子页签定义（fn 指向本文件内的 widget 函数）
var PP_TABS = [
  { key: 'gen', label: '生成软件开发计划', fn: 'ppGenPlan' },
  { key: 'est', label: '软件估算与收敛', fn: 'ppEstPanel' },
  { key: 'risk', label: '风险与资源', fn: 'ppRiskTab' },
  { key: 'docscale', label: '文档规模估算', fn: 'ppDocScale' },
  // 进度表（sched）已按袁总要求隐藏（数据源仍在库，需要时把本行放开即可恢复）
  { key: 'stake', label: '利益相关方', fn: 'ppStakeTab' }
];

// 利益相关方参与计划：9 角色列（对标 R121 附录B，与数据库 stakeholder_plan 列一致）
var PP_STAKE_ROLES = ["customer_rep", "pm", "dept_lead", "proj_lead", "sys_eng", "epg", "qag", "cmg", "otg"];
var PP_STAKE_LABELS = ["顾客代表", "项目经理", "部门领导", "项目负责人", "系统工程组", "EPG", "QAG", "CMG", "OTG"];

var PP_CUR_TAB = 'gen';

// 注：Delphi 估算收敛表（est_items）已按袁总要求从页面删除；数据与后端接口保留。


function ppRender() {
  const c = document.getElementById('content');
  c.innerHTML = ppNodePage();
}

// 阶段条（1:1 还原 phaseBar）
function ppPhaseBar() {
  const active = [0, 1, 2]; // 当前项目覆盖阶段（R105：策划/需求/设计已完成，进入实现）
  const minA = Math.min.apply(null, active);
  let h = '<div class="phasebar">';
  PP_PHASES.forEach(function (p, i) {
    const cls = active.indexOf(i) >= 0 ? 'cur' : (i < minA ? 'done' : 'todo');
    h += '<div class="ph-step ' + cls + '"><span class="ph-dot">' + (cls === 'done' ? '✓' : (i + 1)) + '</span><span class="ph-nm">' + p + '</span></div>';
    if (i < PP_PHASES.length - 1) h += '<div class="ph-line ' + ((cls === 'done' || active.indexOf(i) >= 0) ? 'done' : '') + '"></div>';
  });
  return h + '</div>';
}

// 子页签条
function ppTabBar() {
  return '<div class="node-tabs sticky">' + PP_TABS.map(function (t) {
    return '<button class="ntab' + (t.key === PP_CUR_TAB ? ' on' : '') + '" onclick="ppGoTab(\'' + t.key + '\')">' + t.label + '</button>';
  }).join('') + '</div>';
}

// 节点页（标题 + 阶段条 + 操作栏 + 子页签 + 内容）
function ppNodePage() {
  let h = '<div class="page" id="page-pp">';
  h += '<div class="page-title">项目策划 PP</div>';
  h += '<div class="page-sub"><span class="tag">项目：' + Api.curProjectId() + ' ' + shellCurProjName() + '</span></div>';
  h += ppNodeActions();
  h += ppTabBar();
  h += '<div class="node-body" id="pp-body">' + ppTabContent() + '</div>';
  h += '</div>';
  setTimeout(function () {
    var sp = document.getElementById('sidebar-proj');
    if (sp) sp.textContent = Api.curProjectId() + ' ' + shellCurProjName();
  }, 0);
  return h;
}

// 节点级操作栏（1:1 还原 ppNodeActions）
function ppNodeActions() {
  // 袁总要求：删除"按模块同步"3 按钮（46bce8d394 截图去整块），只保留"一键提交"主按钮
  return '<div class="node-actions"><div class="na-row">' +
    '<button class="btn primary" onclick="ppSyncAll()">⬆ 一键提交所有策划数据到 SVN</button>' +
    '</div></div>';
}

function ppGoTab(key) {
  PP_CUR_TAB = key;
  const body = document.getElementById('pp-body');
  if (body) { body.classList.add('switching'); setTimeout(function () { body.innerHTML = ppTabContent(); body.classList.remove('switching'); ppRefreshTabBar(); }, 220); }
}

function ppRefreshTabBar() {
  const bar = document.querySelector('#page-pp .node-tabs');
  if (bar) bar.outerHTML = ppTabBar();
}

// 子页签内容分发
function ppTabContent() {
  const tab = PP_TABS.find(function (t) { return t.key === PP_CUR_TAB; });
  if (!tab) return '';
  const fn = window[tab.fn];
  return typeof fn === 'function' ? fn() : '<div class="placeholder">' + tab.label + '（建设中）</div>';
}

/* ===== 各子页签 widget（对标效果图真实内容，R105 数据） ===== */

// 生成软件开发计划（4 个汇总面板 + 一键生成）
function ppGenPlan() {
  // 统计卡片：数据全部异步取自数据库接口（袁总铁律：显示数据一律从库读）
  let h = '<div class="stats">' +
    '<div class="stat"><div class="v" id="gc-est">加载中…</div><div class="k">工作量估算（人日 / 阶段数）</div><div class="sub"><span class="tag ok">已入库</span></div></div>' +
    '<div class="stat"><div class="v" id="gc-risk">加载中…</div><div class="k">风险资源（硬件 / 软件项）</div><div class="sub"><span class="tag ok">已入库</span></div></div>' +
    '<div class="stat"><div class="v" id="gc-doc">加载中…</div><div class="k">文档规模（类数 / 合计页数）</div><div class="sub"><span class="tag info">可取数</span></div></div>' +
    '<div class="stat"><div class="v" id="gc-stake">加载中…</div><div class="k">利益相关方（活动行 × 9 角色）</div><div class="sub"><span class="tag info">可取数</span></div></div>' +
    '</div>';
  h += '<div class="panel"><h3><span class="bar"></span>生成《软件开发计划》（SDP）</h3>' +
    '<div class="note">由估算收敛 / 风险资源 / 文档规模 / 利益相关方 自动汇总生成《软件开发计划》。' +
    '可下载到本机指定 SVN 工作副本路径，或直接提交到 VisualSVN 受控库（仓库/路径在「设置」页配置）。' +
    '<b>分类同步</b>：点某一类「同步到 SVN」，仅重新拉取该类最新数据生成文档并提交，其余章节保持原样。</div>' +
    '<div class="row">' +
    '<button class="btn primary" id="pp-dl-btn" onclick="ppDownloadLocal()">⬇ 下载到本地指定路径</button> ' +
    '<button class="btn warn" id="pp-svn-btn" onclick="ppCommitSvn()">⬆ 提交到 SVN</button>' +
    '<span id="pp-gen-msg" style="margin-left:12px;font-size:13px;"></span></div>' +
    '<div class="row" style="margin-top:10px;">' +
    '<button class="btn ghost sm" onclick="ppCommitSvn(\'est\')">⬆ 同步估算到 SVN</button> ' +
    '<button class="btn ghost sm" onclick="ppCommitSvn(\'risk\')">⬆ 同步风险资源到 SVN</button> ' +
    '<button class="btn ghost sm" onclick="ppCommitSvn(\'stake\')">⬆ 同步利益相关方到 SVN</button>' +
    '</div></div>';
  setTimeout(ppGenPlanLoad, 0);
  return h;
}

// 统计卡数据装载：全部来自数据库接口（项目维度）
function ppGenPlanLoad() {
  var pid = Api.curProjectId();
  Api.listDocScale(pid).then(function (r) {
    var rows = (r && r.data) || [];
    var pages = rows.reduce(function (s, x) { return s + (+x.pages_new || 0); }, 0);
    var el = document.getElementById('gc-doc');
    if (el) el.textContent = rows.length + ' 类文档 / ' + pages + ' 页';
  }).catch(function () {});
  Api.listStakeholderPlan(pid).then(function (r) {
    var rows = (r && r.data) || [];
    var el = document.getElementById('gc-stake');
    if (el) el.textContent = rows.length + ' 活动行 × 9 角色';
  }).catch(function () {});
  Promise.all([Api.listHwRes(pid), Api.listSwRes(pid)]).then(function (rs) {
    var hw = ((rs[0] && rs[0].data) || []).length;
    var sw = ((rs[1] && rs[1].data) || []).length;
    var el = document.getElementById('gc-risk');
    if (el) el.textContent = '硬件 ' + hw + ' 项 / 软件 ' + sw + ' 项';
  }).catch(function () {});
  Api.listSchedule(pid).then(function (r) {
    var rows = (r && r.data) || [];
    var eng = rows.reduce(function (s, x) { return s + (+x.eng_md || 0); }, 0);
    var mgr = rows.reduce(function (s, x) { return s + (+x.mgr_md || 0); }, 0);
    var el = document.getElementById('gc-est');
    if (el) el.textContent = (Math.round((eng + mgr) * 10) / 10) + ' 人日 / ' + rows.length + ' 阶段';
  }).catch(function () {});
}


// 方式1：下载到本机指定路径（弹窗填路径，默认取当前项目配置或 D:\5000\R105）
function ppDownloadLocal() {
  var pid = Api.curProjectId();
  var def = (window.__curProj && window.__curProj.localPath) || ('D:\\5000\\' + pid);
  var html = '<div class="modal-mask" onclick="if(event.target===this)this.remove()">' +
    '<div class="modal"><div class="modal-hd">下载到本机 SVN 路径</div><div class="modal-bd">' +
    '<div class="field"><label>本机本地路径 *</label>' +
    '<div style="display:flex;gap:8px;">' +
    '<input id="dl-path" style="flex:1;" value="' + def + '" placeholder="如 D:\\5000\\' + pid + '">' +
    '<button class="btn ghost" type="button" onclick="ppPickLocalDir()">📁 选择目录</button>' +
    '</div>' +
    '<div class="field"><label>文件名（可选）</label><input id="dl-name" placeholder="留空用 ' + pid + '_SDP.docx"></div>' +
    '<div id="dl-progress-wrap" style="display:none;margin:4px 0 8px;">' +
    '<div style="height:10px;border-radius:6px;background:#ececf3;overflow:hidden;">' +
    '<div id="dl-progress-bar" style="height:100%;width:0%;border-radius:6px;background:linear-gradient(90deg,#4a6cf7,#6f8bff);transition:width .25s ease;"></div></div>' +
    '<div id="dl-progress-text" style="font-size:12px;color:#5a5a78;margin-top:4px;">0%</div>' +
    '</div>' +
    '<div id="dl-msg" style="font-size:13px;min-height:18px;color:#5a5a78;">提示：点「选择目录」从本机选取，或手动输入。请确认路径可写（文件夹存在且有写权限）。</div>' +
    '</div><div class="modal-ft">' +
    '<button class="btn ghost" onclick="this.closest(\'.modal-mask\').remove()">取消</button>' +
    '<button class="btn primary" id="dl-confirm-btn" onclick="ppDoDownload()">确定下载</button></div></div></div>';
  document.body.insertAdjacentHTML('beforeend', html);
}

// 点击「选择目录」：用 File System Access API 弹出系统目录选择框，拿到真实绝对路径
function ppPickLocalDir() {
  var msg = document.getElementById('dl-msg');
  if (window.showDirectoryPicker) {
    window.showDirectoryPicker().then(function (handle) {
      // 逐层向上拼出完整路径
      var parts = [handle.name];
      var cur = handle;
      var guard = 0;
      var chain = [];
      (function walk(h) {
        if (h && h.parent) {
          return h.parent.then(function (p) { if (p) { chain.unshift(p.name); return walk(p); } });
        }
        return Promise.resolve();
      })(handle).then(function () {
        var full = chain.concat(parts).join('\\');
        var box = document.getElementById('dl-path');
        if (box) box.value = full;
        if (msg) { msg.style.color = '#5a5a78'; msg.textContent = '已选择目录：' + full; }
      });
    }).catch(function (err) {
      if (msg) { msg.style.color = '#e74c3c'; msg.textContent = '未选择目录：' + (err.message || err); }
    });
  } else {
    // 降级：不支持的浏览器引导去设置页配置
    if (msg) { msg.style.color = '#e74c3c'; msg.textContent = '当前浏览器不支持系统目录选择，请手动输入或在「设置」页配置本机 SVN 根路径。'; }
  }
}

function ppDoDownload() {
  var path = document.getElementById('dl-path').value.trim();
  var name = document.getElementById('dl-name').value.trim();
  var msg = document.getElementById('dl-msg');
  var btn = document.getElementById('dl-confirm-btn');
  var wrap = document.getElementById('dl-progress-wrap');
  var bar = document.getElementById('dl-progress-bar');
  var pct = document.getElementById('dl-progress-text');
  if (!path) {
    msg.style.color = '#e74c3c';
    msg.textContent = '路径必填';
    return;
  }
  // 显示进度条并开始动画（0→90% 平滑推进，到 90% 后保持"处理中"动效，等接口返回再补满）
  if (wrap) wrap.style.display = 'block';
  var p = 0;
  if (bar) { bar.style.width = '0%'; bar.style.background = 'linear-gradient(90deg,#4a6cf7,#6f8bff)'; }
  if (pct) pct.textContent = '0%';
  var startTs = Date.now();
  var timer = setInterval(function () {
    // 越接近 90 越慢，到达 90 后不再前进（等后端真实返回），但持续显示"处理中"避免误判卡死
    if (p < 90) {
      p += Math.max(1, (90 - p) * 0.08);
      if (p > 90) p = 90;
      if (bar) bar.style.width = p.toFixed(0) + '%';
      if (pct) pct.textContent = p.toFixed(0) + '%';
    } else if (pct) {
      // 90% 后保持"处理中"提示（不静止），让用户知道仍在工作
      var dots = (pct.textContent.match(/·/g) || []).length;
      pct.textContent = '处理中' + '·'.repeat((dots % 3) + 1);
    }
    // 兜底：30 秒还没结果 → 强制失败（防止网络挂起导致 UI 永远卡死）
    if (Date.now() - startTs > 30000 && btn && btn.textContent.indexOf('下载中') !== -1) {
      clearInterval(timer);
      if (bar) { bar.style.width = '100%'; bar.style.background = 'linear-gradient(90deg,#e74c3c,#ff6b6b)'; }
      if (pct) pct.textContent = '失败';
      if (msg) { msg.style.color = '#e74c3c'; msg.textContent = '失败：请求超时（30 秒未收到后端响应）。请检查后端服务是否正常启动，或刷新页面重试。'; }
      btn.disabled = false;
      btn.textContent = btn.dataset.orig || '确定下载';
    }
  }, 200);
  if (btn) { btn.disabled = true; btn.dataset.orig = '确定下载'; btn.textContent = '下载中…'; }
  if (msg) { msg.style.color = '#5a5a78'; msg.textContent = '正在生成并写入文件，请稍候…'; }
  Api.saveToLocal(Api.curProjectId(), 'SDP', { local_path: path, filename: name || undefined }).then(function (r) {
    clearInterval(timer);
    if (bar) { bar.style.width = '100%'; bar.style.background = 'linear-gradient(90deg,#27ae60,#2ecc71)'; }
    if (pct) pct.textContent = '100%';
    if (msg) { msg.style.color = '#27ae60'; msg.textContent = '✅ 下载完成：' + (r.data && r.data.path || path); }
    if (btn) { btn.disabled = false; btn.textContent = '关闭'; btn.onclick = function () { var m = document.querySelector('.modal-mask'); if (m) m.remove(); }; }
    ppGenMsg('已保存到 ' + (r.data && r.data.path || path), true);
  }).catch(function (e) {
    clearInterval(timer);
    if (bar) { bar.style.width = '100%'; bar.style.background = 'linear-gradient(90deg,#e74c3c,#ff6b6b)'; }
    if (pct) pct.textContent = '失败';
    // 失败时按钮必须还原（用 id 直接定位，避开 textContent 已变的坑）
    var b2 = document.getElementById('dl-confirm-btn');
    if (b2) { b2.disabled = false; b2.textContent = b2.dataset.orig || '确定下载'; }
    if (msg) { msg.style.color = '#e74c3c'; msg.textContent = '失败：' + (e.message || e) + '（请检查路径是否存在/有写权限，或文件是否被其他程序占用）'; }
  });
}

// 方式2：直接提交到 VisualSVN（module 可选：est/risk/stake，表示"只更新该类数据后提交整篇"）
// 一键提交：整篇生成并提交 SVN（module 为空 = 全部数据用库最新值，并刷新各分类快照）
function ppSyncAll() {
  ppCommitSvn();   // 复用分类提交通道：不传 module 即整篇提交
}

function ppCommitSvn(module) {
  var btn = document.getElementById('pp-svn-btn');
  var msg = document.getElementById('pp-gen-msg');
  var btnText = btn ? btn.textContent : '⬆ 提交到 SVN';
  var label = { est: '估算', risk: '风险资源', stake: '利益相关方' }[module];
  if (btn) { btn.disabled = true; btn.textContent = label ? ('同步' + label + '中…') : '提交中…'; }
  ppGenMsg('', true);
  var q = module ? ('?module=' + module) : '';
  Api.commitSvn(Api.curProjectId(), 'SDP' + q).then(function (r) {
    var rev = r.data && r.data.revision;
    ppGenMsg((label ? ('已同步' + label + '并') : '') + '提交 SVN，修订号 r' + rev, true);
    if (btn) { btn.disabled = false; btn.textContent = btnText; }
  }).catch(function (e) {
    ppGenMsg('提交失败：' + (e.message || e), false);
    if (btn) { btn.disabled = false; btn.textContent = btnText; }
  });
}

function ppGenMsg(text, ok) {
  var el = document.getElementById('pp-gen-msg');
  if (!el) return;
  el.textContent = text;
  el.style.color = ok ? '#27ae60' : '#e74c3c';
}

// 代码规模（构件级，按项目维度；对应 {{table.code_scale_est}}/{{table.code_scale_reuse}}）
function ppEstPanel() {
  // 袁总要求：删除「软件估算与收敛（Delphi 法）」表格（含两轮切换 + est_items 表），
  //           仅保留下方「代码规模（构件级）」表（对应 {{table.code_scale_*}}）。
  var h = '<div class="panel"><div class="panel-hd"><h3><span class="bar"></span>代码规模（构件级，新开发/复用）</h3>' +
    '<button class="btn primary sm" onclick="ppCodeScaleAdd()">＋ 新增构件</button></div>' +
    '<div style="overflow-x:auto;"><table class="tbl"><thead><tr><th>构件/模块</th><th>预计规模(行)</th><th>复用规模(行)</th><th>操作</th></tr></thead>' +
    '<tbody id="codescale-tbody"><tr><td colspan="4" style="text-align:center;color:#999;">加载中…</td></tr></tbody></table></div></div>';
  setTimeout(function () { ppCodeScaleLoad(); }, 0);
  return h;
}

// 注：Delphi 估算收敛表（ppEstLoad/ppEstSave/ppEstDel/ppEstSwitchRound）已按袁总要求删除；
//     est_items 数据与后端接口保留（如需恢复，还原上述四个函数 + ppEstPanel 中的表格区块即可）。
function ppCodeScaleLoad() {
  var tb = document.getElementById('codescale-tbody');
  if (!tb) return;
  Api.listCodeScale(Api.curProjectId()).then(function (r) {
    var rows = (r && r.data) || [];
    if (!rows.length) { tb.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#999;">暂无构件，点「新增构件」录入</td></tr>'; return; }
    tb.innerHTML = rows.map(function (x) {
      return '<tr><td><input data-f="comp" data-id="' + x.id + '" value="' + (x.comp || '') + '" style="width:100%;min-width:160px"></td>' +
        '<td><input data-f="est_loc" data-id="' + x.id + '" value="' + (x.est_loc || 0) + '" style="width:100%;min-width:100px"></td>' +
        '<td><input data-f="reuse_loc" data-id="' + x.id + '" value="' + (x.reuse_loc || 0) + '" style="width:100%;min-width:100px"></td>' +
        '<td><button class="btn ghost sm" onclick="ppCodeScaleSave(' + x.id + ')">保存</button> <button class="btn ghost sm" onclick="ppCodeScaleDel(' + x.id + ')">删</button></td></tr>';
    }).join('');
  }).catch(function (e) { tb.innerHTML = '<tr><td colspan="4" style="color:#e74c3c;">加载失败：' + (e.message || e) + '</td></tr>'; });
}
function ppCodeScaleAdd() {
  var html = '<div class="modal-mask" onclick="if(event.target===this)this.remove()"><div class="modal modal-lg"><div class="modal-hd">新增构件</div><div class="modal-bd grid2">' +
    '<div class="field"><label>构件/模块</label><input id="cs-comp"></div><div class="field"><label>预计规模(行)</label><input id="cs-est" type="number" value="0"></div>' +
    '<div class="field"><label>复用规模(行)</label><input id="cs-reuse" type="number" value="0"></div>' +
    '<div id="cs-msg" class="span2" style="color:#e74c3c;font-size:13px;min-height:16px;"></div></div>' +
    '<div class="modal-ft"><button class="btn ghost" onclick="this.closest(\'.modal-mask\').remove()">取消</button><button class="btn primary" onclick="ppCodeScaleSaveNew()">保存</button></div></div></div>';
  document.body.insertAdjacentHTML('beforeend', html);
}
function ppCodeScaleSaveNew() {
  var msg = document.getElementById('cs-msg');
  Api.createCodeScale(Api.curProjectId(), { comp: document.getElementById('cs-comp').value.trim(), est_loc: +document.getElementById('cs-est').value || 0, reuse_loc: +document.getElementById('cs-reuse').value || 0 })
    .then(function () { document.querySelector('.modal-mask').remove(); ppCodeScaleLoad(); })
    .catch(function (e) { msg.textContent = '保存失败：' + (e.message || e); });
}
function ppCodeScaleSave(id) {
  var get = function (f) { return document.querySelector('#codescale-tbody [data-id="' + id + '"][data-f="' + f + '"]').value.trim(); };
  Api.updateCodeScale(Api.curProjectId(), id, { comp: get('comp'), est_loc: +get('est_loc') || 0, reuse_loc: +get('reuse_loc') || 0 })
    .then(function () { ppCodeScaleLoad(); }).catch(function (e) { alert('保存失败：' + (e.message || e)); });
}
function ppCodeScaleDel(id) {
  if (!confirm('确认删除？')) return;
  Api.deleteCodeScale(Api.curProjectId(), id).then(function () { ppCodeScaleLoad(); }).catch(function (e) { alert('删除失败：' + (e.message || e)); });
}

// 风险与资源（A11 风险 + 硬件 + 软件）
// 风险表字段完全对齐 R121 附录A 项目风险管理表（4 行表头 + 15 列），分项目，当前项目从配置读
function ppRiskTab() {
  let h = '';
  let pid = Api.curProjectId();
  // A11 风险（平台录入）
  h += '<div class="panel"><div class="panel-hd"><h3><span class="bar"></span>A11 软件风险管理表（' + pid + '）</h3>' +
    '<button class="btn primary sm" onclick="ppRiskAdd()">＋ 新增风险</button></div>';
  h += '<div style="overflow-x:auto;"><table class="tbl"><thead><tr>' +
    '<th>编号</th><th>识别日期</th><th>风险来源</th><th>风险类别</th><th>风险描述</th><th>概率P</th><th>影响I</th><th>风险系数</th><th>风险等级</th><th>优先级</th><th>风险预防措施</th><th>责任人</th><th>风险应对措施</th><th>状态</th><th>关闭日期</th><th>操作</th></tr></thead>' +
    '<tbody id="risk-tbody"><tr><td colspan="16" style="text-align:center;color:#999;">加载中…</td></tr></tbody></table></div>';
  h += '<div class="note">字段对齐 R105 附录A 项目风险管理表（预置 4 条真实风险，责任人 辛峥峰）：概率×影响=风险系数（很低0.1/比较低0.2/中等0.5/比较高0.8/很高0.9），等级/优先级自动。行内点「修改」编辑、「删除」移除。分项目隔离，当前项目：' + pid + '。</div></div>';
  // 硬件资源（按项目维度，可编辑；对应 {{table.hw_env_res}}）
  h += '<div class="panel"><div class="panel-hd"><h3><span class="bar"></span>硬件资源（A79 项目资源跟踪表）</h3>' +
    '<button class="btn primary sm" onclick="ppHwAdd()">＋ 新增硬件</button></div>' +
    '<div style="overflow-x:auto;"><table class="tbl"><thead><tr>' +
    '<th>名称</th><th>规格</th><th>用途</th><th>责任人</th><th>操作</th></tr></thead>' +
    '<tbody id="hw-tbody"><tr><td colspan="5" style="text-align:center;color:#999;">加载中…</td></tr></tbody></table></div></div>';
  // 软件资源（按项目维度，可编辑；对应 {{table.sw_env_res}}）
  h += '<div class="panel"><div class="panel-hd"><h3><span class="bar"></span>软件资源（A79 项目资源跟踪表）</h3>' +
    '<button class="btn primary sm" onclick="ppSwAdd()">＋ 新增软件</button></div>' +
    '<div style="overflow-x:auto;"><table class="tbl"><thead><tr>' +
    '<th>名称</th><th>版本</th><th>用途</th><th>责任人</th><th>操作</th></tr></thead>' +
    '<tbody id="sw-tbody"><tr><td colspan="5" style="text-align:center;color:#999;">加载中…</td></tr></tbody></table></div></div>';
  // 进入即拉取风险/硬件/软件数据
  setTimeout(function () { ppRiskLoad(); ppHwLoad(); ppSwLoad(); }, 0);
  return h;
}

// 拉取当前项目风险并渲染表格（R121 附录A 15 列对齐）
function ppRiskLoad() {
  var tb = document.getElementById('risk-tbody');
  if (!tb) return;
  Api.listRisks().then(function (res) {
    var rows = (res && res.data) || [];
    if (!rows.length) {
      tb.innerHTML = '<tr><td colspan="16" style="text-align:center;color:#999;">暂无风险记录，点击「新增风险」录入</td></tr>';
      return;
    }
    tb.innerHTML = rows.map(function (r) {
      var lv = r.level || '';
      var lvCls = lv === '高' ? 'danger' : (lv === '中' ? 'warn' : 'info');
      var stCls = r.status === '已关闭' ? 'ok' : (r.status === '已发生' ? 'warn' : 'info');
      return '<tr><td>' + (r.riskId || '') + '</td>' +
        '<td>' + (r.identifiedDate || '') + '</td>' +
        '<td>' + (r.source || '') + '</td>' +
        '<td>' + (r.category || '') + '</td>' +
        '<td style="text-align:left">' + (r.description || '') + '</td>' +
        '<td>' + (r.probability || '') + '</td>' +
        '<td>' + (r.impactLevel || '') + '</td>' +
        '<td><b>' + (r.riskCoef || '') + '</b></td>' +
        '<td><span class="tag ' + lvCls + '">' + lv + '</span></td>' +
        '<td>' + (r.priority || '') + '</td>' +
        '<td style="text-align:left">' + (r.prevention || '') + '</td>' +
        '<td>' + (r.owner || '') + '</td>' +
        '<td style="text-align:left">' + (r.mitigation || '') + '</td>' +
        '<td><span class="tag ' + stCls + '">' + (r.status || '未发生') + '</span></td>' +
        '<td>' + (r.closedDate || '') + '</td>' +
        '<td><button class="btn ghost sm" onclick="ppRiskEdit(\'' + (r.riskId || '') + '\')">修改</button> <button class="btn ghost sm" onclick="ppRiskDel(\'' + (r.riskId || '') + '\')">删除</button></td></tr>';
    }).join('');
  }).catch(function (e) {
    tb.innerHTML = '<tr><td colspan="16" style="text-align:center;color:#e74c3c;">加载失败：' + (e.message || e) + '</td></tr>';
  });
}

// 编辑风险（弹窗带当前值；保存走 PUT 只更新改动字段）
function ppRiskEdit(riskId) {
  Api.listRisks().then(function (res) {
    var rows = (res && res.data) || [];
    var r = null;
    for (var i = 0; i < rows.length; i++) { if (String(rows[i].riskId) === String(riskId)) { r = rows[i]; break; } }
    if (!r) { alert('未找到该风险'); return; }
    var optProb = function (cur) {
      return ['很低', '比较低', '中等', '比较高', '很高'].map(function (o) {
        return '<option' + (o === (cur || '比较低') ? ' selected' : '') + '>' + o + '</option>';
      }).join('');
    };
    var optCat = function (cur) {
      return ['人员', '技术', '需求', '计划编制风险', '测试', '进度', '质量'].map(function (o) {
        return '<option' + (o === (cur || '人员') ? ' selected' : '') + '>' + o + '</option>';
      }).join('');
    };
    var optSt = function (cur) {
      return ['未发生', '已发生', '已关闭'].map(function (o) {
        return '<option' + (o === (cur || '未发生') ? ' selected' : '') + '>' + o + '</option>';
      }).join('');
    };
    var html = '<div class="modal-mask" onclick="if(event.target===this)this.remove()">' +
      '<div class="modal modal-lg"><div class="modal-hd">修改风险（编号 ' + riskId + '）</div>' +
      '<div class="modal-bd grid2">' +
      '<div class="field"><label>识别日期（点击选择）</label><input id="rk-date" type="date" value="' + (r.identifiedDate || '') + '"></div>' +
      '<div class="field"><label>风险来源</label><select id="rk-src">' + ['公司内部', '公司外部', '客户', '供应商', '其他'].map(function (o) { return '<option' + (o === (r.source || '公司内部') ? ' selected' : '') + '>' + o + '</option>'; }).join('') + '</select></div>' +
      '<div class="field"><label>风险类别</label><select id="rk-cat">' + optCat(r.category) + '</select></div>' +
      '<div class="field span2"><label>风险描述</label><input id="rk-desc" value="' + (r.description || '').replace(/"/g, '&quot;') + '"></div>' +
      '<div class="field"><label>概率P</label><select id="rk-p" onchange="ppCalcRisk()">' + optProb(r.probability) + '</select></div>' +
      '<div class="field"><label>影响I</label><select id="rk-i" onchange="ppCalcRisk()">' + optProb(r.impactLevel) + '</select></div>' +
      '<div class="field"><label>风险系数(自动)</label><span id="rk-coef" style="font-weight:700;">' + (r.riskCoef || '') + '</span></div>' +
      '<div class="field"><label>风险等级(自动)</label><select id="rk-lv">' + ['高', '中', '低'].map(function (o) { return '<option' + (o === (r.level || '低') ? ' selected' : '') + '>' + o + '</option>'; }).join('') + '</select></div>' +
      '<div class="field"><label>优先级(自动)</label><select id="rk-pr">' + ['高', '低'].map(function (o) { return '<option' + (o === (r.priority || '低') ? ' selected' : '') + '>' + o + '</option>'; }).join('') + '</select></div>' +
      '<div class="field span2"><label>风险预防措施</label><input id="rk-pre" value="' + (r.prevention || '').replace(/"/g, '&quot;') + '"></div>' +
      '<div class="field"><label>责任人</label><input id="rk-owner" value="' + (r.owner || '') + '"></div>' +
      '<div class="field"><label>状态</label><select id="rk-st">' + optSt(r.status) + '</select></div>' +
      '<div class="field span2"><label>风险应对措施</label><input id="rk-mit" value="' + (r.mitigation || '').replace(/"/g, '&quot;') + '"></div>' +
      '<div class="field"><label>关闭日期（点击选择）</label><input id="rk-cdate" type="date" value="' + (r.closedDate || '') + '"></div>' +
      '<div id="rk-emsg" class="span2" style="color:#e74c3c;font-size:13px;min-height:16px;"></div>' +
      '</div><div class="modal-ft"><button class="btn ghost" onclick="this.closest(\'.modal-mask\').remove()">取消</button>' +
      '<button class="btn primary" onclick="ppRiskSaveEdit(\'' + riskId + '\')">保存</button></div></div></div>';
    document.body.insertAdjacentHTML('beforeend', html);
  }).catch(function (e) { alert('加载失败：' + (e.message || e)); });
}
// 保存风险编辑（仅收集改动字段，PUT 只更新传入字段防误清）
function ppRiskSaveEdit(riskId) {
  var msg = document.getElementById('rk-emsg');
  var orig = null;
  Api.listRisks().then(function (res) {
    var rows = (res && res.data) || [];
    for (var i = 0; i < rows.length; i++) { if (String(rows[i].riskId) === String(riskId)) { orig = rows[i]; break; } }
    if (!orig) { msg.textContent = '未找到该风险'; return; }
    var g = function (id) { return document.getElementById(id).value.trim(); };
    var cand = {
      identifiedDate: g('rk-date'), source: g('rk-src'), category: g('rk-cat'),
      description: g('rk-desc'), probability: g('rk-p'), impactLevel: g('rk-i'),
      riskCoef: document.getElementById('rk-coef').textContent.trim(),
      level: g('rk-lv'), priority: g('rk-pr'), prevention: g('rk-pre'),
      owner: g('rk-owner'), mitigation: g('rk-mit'), status: g('rk-st'), closedDate: g('rk-cdate'),
    };
    // 只传有变化的字段
    var payload = {};
    Object.keys(cand).forEach(function (k) {
      var nv = cand[k] == null ? '' : String(cand[k]);
      var ov = orig[k] == null ? '' : String(orig[k]);
      if (nv !== ov) payload[k] = nv;
    });
    if (Object.keys(payload).length === 0) { document.querySelector('.modal-mask').remove(); return; }
    Api.updateRisk(riskId, payload).then(function () {
      document.querySelector('.modal-mask').remove();
      ppRiskLoad();
    }).catch(function (e) { msg.textContent = '保存失败：' + (e.message || e); });
  }).catch(function (e) { if (msg) msg.textContent = '加载失败：' + (e.message || e); });
}

// 概率/影响数值（对标 R121 附录A）
var PP_PROB_VAL = { '很低': 0.1, '比较低': 0.2, '中等': 0.5, '比较高': 0.8, '很高': 0.9 };
// 风险系数/等级/优先级自动算（与后端一致）
function ppCalcRisk() {
  var p = document.getElementById('rk-p').value;
  var i = document.getElementById('rk-i').value;
  var pv = PP_PROB_VAL[p] || 0, iv = PP_PROB_VAL[i] || 0;
  var c = (pv * iv);
  var coef = c ? c.toFixed(2) : '';
  var lv = (c >= 3) ? '高' : (c >= 1.5 ? '中' : '低');
  var pr = (c >= 1.5) ? '高' : '低';
  document.getElementById('rk-coef').textContent = coef;
  document.getElementById('rk-lv').value = lv;
  document.getElementById('rk-pr').value = pr;
}

// 新增风险弹窗（字段与列表完全一致：编号/识别日期/来源/类别/描述/概率/影响/
// 系数/等级/优先级/预防措施/责任人/应对措施/状态/关闭日期）
// 布局：宽版 modal-lg + 两列 grid2（一行两条信息）；日期用日历选择器
function ppRiskAdd() {
  var optProb = '<option>很低</option><option selected>比较低</option><option>中等</option><option>比较高</option><option>很高</option>';
  var html = '<div class="modal-mask" onclick="if(event.target===this)this.remove()">' +
    '<div class="modal modal-lg"><div class="modal-hd">新增风险（对标 R105 附录A 风险管理表）</div>' +
    '<div class="modal-bd grid2">' +
    '<div class="field"><label>编号 *</label><input id="rk-id" placeholder="如 5"></div>' +
    '<div class="field"><label>识别日期（点击选择）</label><input id="rk-date" type="date"></div>' +
    '<div class="field"><label>风险来源</label><select id="rk-src"><option selected>公司内部</option><option>公司外部</option><option>客户</option><option>供应商</option><option>其他</option></select></div>' +
    '<div class="field"><label>风险类别</label><select id="rk-cat"><option selected>人员</option><option>技术</option><option>需求</option><option>计划编制风险</option><option>测试</option><option>进度</option><option>质量</option></select></div>' +
    '<div class="field span2"><label>风险描述 *（含可能导致的后果+发生时间区间）</label><input id="rk-desc"></div>' +
    '<div class="field"><label>概率P</label><select id="rk-p" onchange="ppCalcRisk()">' + optProb + '</select></div>' +
    '<div class="field"><label>影响I</label><select id="rk-i" onchange="ppCalcRisk()">' + optProb + '</select></div>' +
    '<div class="field"><label>风险系数(自动)</label><span id="rk-coef" style="font-weight:700;">0.04</span></div>' +
    '<div class="field"><label>风险等级(自动)</label><select id="rk-lv"><option>高</option><option selected>中</option><option>低</option></select></div>' +
    '<div class="field"><label>优先级(自动)</label><select id="rk-pr"><option>高</option><option selected>低</option></select></div>' +
    '<div class="field"><label>责任人</label><input id="rk-owner" placeholder="如 辛峥峰"></div>' +
    '<div class="field span2"><label>风险预防措施（事前规避）</label><input id="rk-pre"></div>' +
    '<div class="field span2"><label>风险应对措施（发生后的处置）</label><input id="rk-mit"></div>' +
    '<div class="field"><label>状态</label><select id="rk-st"><option selected>未发生</option><option>已发生</option><option>已关闭</option></select></div>' +
    '<div class="field"><label>关闭日期（点击选择）</label><input id="rk-cdate" type="date"></div>' +
    '<div id="rk-msg" class="span2" style="color:#e74c3c;font-size:13px;min-height:16px;"></div>' +
    '</div><div class="modal-ft">' +
    '<button class="btn ghost" onclick="this.closest(\'.modal-mask\').remove()">取消</button>' +
    '<button class="btn primary" onclick="ppRiskSave()">保存</button></div></div></div>';
  document.body.insertAdjacentHTML('beforeend', html);
}

// 保存风险（R121 附录A 全字段）
function ppRiskSave() {
  var id = document.getElementById('rk-id').value.trim();
  var desc = document.getElementById('rk-desc').value.trim();
  var msg = document.getElementById('rk-msg');
  if (!id || !desc) { msg.textContent = '编号与风险描述必填'; return; }
  Api.createRisk({
    riskId: id, description: desc,
    identifiedDate: document.getElementById('rk-date').value.trim(),
    source: document.getElementById('rk-src').value,
    category: document.getElementById('rk-cat').value,
    probability: document.getElementById('rk-p').value,
    impactLevel: document.getElementById('rk-i').value,
    level: document.getElementById('rk-lv').value,
    priority: document.getElementById('rk-pr').value,
    prevention: document.getElementById('rk-pre').value.trim(),
    owner: document.getElementById('rk-owner').value.trim(),
    mitigation: document.getElementById('rk-mit').value.trim(),
    status: document.getElementById('rk-st').value,
    closedDate: document.getElementById('rk-cdate').value.trim()
  }).then(function () {
    document.querySelector('.modal-mask').remove();
    ppRiskLoad();
  }).catch(function (e) { msg.textContent = '保存失败：' + (e.message || e); });
}

// 删除风险
function ppRiskDel(riskId) {
  if (!confirm('确认删除风险 ' + riskId + '？')) return;
  Api.deleteRisk(riskId).then(function () { ppRiskLoad(); })
    .catch(function (e) { alert('删除失败：' + (e.message || e)); });
}

// ===== 硬件资源（按项目维度，对应 {{table.hw_env_res}}）=====
function ppHwLoad() {
  var tb = document.getElementById('hw-tbody');
  if (!tb) return;
  Api.listHwRes(Api.curProjectId()).then(function (r) {
    var rows = (r && r.data) || [];
    if (!rows.length) { tb.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#999;">暂无硬件资源，点「新增硬件」录入</td></tr>'; return; }
    tb.innerHTML = rows.map(function (x) {
      return '<tr><td><input data-f="name" data-id="' + x.id + '" value="' + (x.name || '') + '" style="width:100%;min-width:90px"></td>' +
        '<td><input data-f="spec" data-id="' + x.id + '" value="' + (x.spec || '') + '" style="width:100%;min-width:110px"></td>' +
        '<td><input data-f="usage" data-id="' + x.id + '" value="' + (x.usage || '') + '" style="width:100%;min-width:140px"></td>' +
        '<td><input data-f="owner" data-id="' + x.id + '" value="' + (x.owner || '') + '" style="width:100%;min-width:80px"></td>' +
        '<td><button class="btn ghost sm" onclick="ppHwSave(' + x.id + ')">保存</button> <button class="btn ghost sm" onclick="ppHwDel(' + x.id + ')">删</button></td></tr>';
    }).join('');
  }).catch(function (e) { tb.innerHTML = '<tr><td colspan="5" style="color:#e74c3c;">加载失败：' + (e.message || e) + '</td></tr>'; });
}
function ppHwAdd() {
  var html = '<div class="modal-mask" onclick="if(event.target===this)this.remove()"><div class="modal modal-lg"><div class="modal-hd">新增硬件资源</div><div class="modal-bd grid2">' +
    '<div class="field"><label>名称</label><input id="hw-name"></div><div class="field"><label>规格/型号</label><input id="hw-spec"></div>' +
    '<div class="field"><label>用途</label><input id="hw-use"></div><div class="field"><label>责任人</label><input id="hw-owner"></div>' +
    '<div id="hw-msg" class="span2" style="color:#e74c3c;font-size:13px;min-height:16px;"></div></div>' +
    '<div class="modal-ft"><button class="btn ghost" onclick="this.closest(\'.modal-mask\').remove()">取消</button><button class="btn primary" onclick="ppHwSaveNew()">保存</button></div></div></div>';
  document.body.insertAdjacentHTML('beforeend', html);
}
function ppHwSaveNew() {
  var pid = Api.curProjectId();
  var msg = document.getElementById('hw-msg');
  Api.createHwRes(pid, { name: document.getElementById('hw-name').value.trim(), spec: document.getElementById('hw-spec').value.trim(), usage: document.getElementById('hw-use').value.trim(), owner: document.getElementById('hw-owner').value.trim() })
    .then(function () { document.querySelector('.modal-mask').remove(); ppHwLoad(); })
    .catch(function (e) { msg.textContent = '保存失败：' + (e.message || e); });
}
function ppHwSave(id) {
  var tr = document.querySelector('#hw-tbody tr'); // 仅定位，真正按 data-id 找输入
  var get = function (f) { return document.querySelector('#hw-tbody [data-id="' + id + '"][data-f="' + f + '"]').value.trim(); };
  Api.updateHwRes(Api.curProjectId(), id, { name: get('name'), spec: get('spec'), usage: get('usage'), owner: get('owner') })
    .then(function () { ppHwLoad(); }).catch(function (e) { alert('保存失败：' + (e.message || e)); });
}
function ppHwDel(id) {
  if (!confirm('确认删除？')) return;
  Api.deleteHwRes(Api.curProjectId(), id).then(function () { ppHwLoad(); }).catch(function (e) { alert('删除失败：' + (e.message || e)); });
}

// ===== 软件资源（按项目维度，对应 {{table.sw_env_res}}）=====
function ppSwLoad() {
  var tb = document.getElementById('sw-tbody');
  if (!tb) return;
  Api.listSwRes(Api.curProjectId()).then(function (r) {
    var rows = (r && r.data) || [];
    if (!rows.length) { tb.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#999;">暂无软件资源，点「新增软件」录入</td></tr>'; return; }
    tb.innerHTML = rows.map(function (x) {
      return '<tr><td><input data-f="name" data-id="' + x.id + '" value="' + (x.name || '') + '" style="width:100%;min-width:90px"></td>' +
        '<td><input data-f="spec" data-id="' + x.id + '" value="' + (x.spec || '') + '" style="width:100%;min-width:110px"></td>' +
        '<td><input data-f="usage" data-id="' + x.id + '" value="' + (x.usage || '') + '" style="width:100%;min-width:140px"></td>' +
        '<td><input data-f="owner" data-id="' + x.id + '" value="' + (x.owner || '') + '" style="width:100%;min-width:80px"></td>' +
        '<td><button class="btn ghost sm" onclick="ppSwSave(' + x.id + ')">保存</button> <button class="btn ghost sm" onclick="ppSwDel(' + x.id + ')">删</button></td></tr>';
    }).join('');
  }).catch(function (e) { tb.innerHTML = '<tr><td colspan="5" style="color:#e74c3c;">加载失败：' + (e.message || e) + '</td></tr>'; });
}
function ppSwAdd() {
  var html = '<div class="modal-mask" onclick="if(event.target===this)this.remove()"><div class="modal modal-lg"><div class="modal-hd">新增软件资源</div><div class="modal-bd grid2">' +
    '<div class="field"><label>名称</label><input id="sw-name"></div><div class="field"><label>版本/型号</label><input id="sw-spec"></div>' +
    '<div class="field"><label>用途</label><input id="sw-use"></div><div class="field"><label>责任人</label><input id="sw-owner"></div>' +
    '<div id="sw-msg" class="span2" style="color:#e74c3c;font-size:13px;min-height:16px;"></div></div>' +
    '<div class="modal-ft"><button class="btn ghost" onclick="this.closest(\'.modal-mask\').remove()">取消</button><button class="btn primary" onclick="ppSwSaveNew()">保存</button></div></div></div>';
  document.body.insertAdjacentHTML('beforeend', html);
}
function ppSwSaveNew() {
  var pid = Api.curProjectId();
  var msg = document.getElementById('sw-msg');
  Api.createSwRes(pid, { name: document.getElementById('sw-name').value.trim(), spec: document.getElementById('sw-spec').value.trim(), usage: document.getElementById('sw-use').value.trim(), owner: document.getElementById('sw-owner').value.trim() })
    .then(function () { document.querySelector('.modal-mask').remove(); ppSwLoad(); })
    .catch(function (e) { msg.textContent = '保存失败：' + (e.message || e); });
}
function ppSwSave(id) {
  var get = function (f) { return document.querySelector('#sw-tbody [data-id="' + id + '"][data-f="' + f + '"]').value.trim(); };
  Api.updateSwRes(Api.curProjectId(), id, { name: get('name'), spec: get('spec'), usage: get('usage'), owner: get('owner') })
    .then(function () { ppSwLoad(); }).catch(function (e) { alert('保存失败：' + (e.message || e)); });
}
function ppSwDel(id) {
  if (!confirm('确认删除？')) return;
  Api.deleteSwRes(Api.curProjectId(), id).then(function () { ppSwLoad(); }).catch(function (e) { alert('删除失败：' + (e.message || e)); });
}

// 文档规模估算
function ppDocScale() {
  let h = '<div class="panel"><div class="panel-hd"><h3><span class="bar"></span><span id="docscale-title">文档规模估算</span></h3>' +
    '<button class="btn primary sm" onclick="ppDocScaleAdd()">＋ 新增文档</button></div>' +
    '<div style="overflow-x:auto;"><table class="tbl"><thead><tr><th>代号</th><th>文档名称</th><th>新开发(页)</th><th>复用(页)</th><th>操作</th></tr></thead>' +
    '<tbody id="docscale-tbody"><tr><td colspan="5" style="text-align:center;color:#999;">加载中…</td></tr></tbody></table></div></div>';
  setTimeout(function () { ppDocScaleLoad(); }, 0);
  return h;
}
// 文档规模按项目维度加载（对应 {{table.doc_scale_est}}/{{table.doc_scale_reuse}}）；标题动态显示类数/合计页数
function ppDocScaleLoad() {
  var tb = document.getElementById('docscale-tbody');
  if (!tb) return;
  Api.listDocScale(Api.curProjectId()).then(function (r) {
    var rows = (r && r.data) || [];
    var title = document.getElementById('docscale-title');
    if (title) title.textContent = '文档规模估算（共 ' + rows.length + ' 类 · 合计 ' +
      rows.reduce(function (s, x) { return s + (+x.pages_new || 0); }, 0) + ' 页）';
    if (!rows.length) { tb.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#999;">暂无文档，点「新增文档」录入</td></tr>'; return; }
    tb.innerHTML = rows.map(function (x) {
      return '<tr><td><input data-f="code" data-id="' + x.id + '" value="' + (x.code || '') + '" style="width:100%;min-width:70px"></td>' +
        '<td><input data-f="name" data-id="' + x.id + '" value="' + (x.name || '') + '" style="width:100%;min-width:160px"></td>' +
        '<td><input data-f="pages_new" data-id="' + x.id + '" value="' + (x.pages_new || 0) + '" style="width:100%;min-width:80px"></td>' +
        '<td><input data-f="pages_reuse" data-id="' + x.id + '" value="' + (x.pages_reuse || 0) + '" style="width:100%;min-width:80px"></td>' +
        '<td><button class="btn ghost sm" onclick="ppDocScaleSave(' + x.id + ')">保存</button> <button class="btn ghost sm" onclick="ppDocScaleDel(' + x.id + ')">删</button></td></tr>';
    }).join('');
  }).catch(function (e) { tb.innerHTML = '<tr><td colspan="5" style="color:#e74c3c;">加载失败：' + (e.message || e) + '</td></tr>'; });
}
function ppDocScaleAdd() {
  var html = '<div class="modal-mask" onclick="if(event.target===this)this.remove()"><div class="modal modal-lg"><div class="modal-hd">新增文档</div><div class="modal-bd grid2">' +
    '<div class="field"><label>代号</label><input id="ds-code"></div><div class="field"><label>文档名称</label><input id="ds-name"></div>' +
    '<div class="field"><label>新开发(页)</label><input id="ds-new" type="number" value="0"></div><div class="field"><label>复用(页)</label><input id="ds-reuse" type="number" value="0"></div>' +
    '<div id="ds-msg" class="span2" style="color:#e74c3c;font-size:13px;min-height:16px;"></div></div>' +
    '<div class="modal-ft"><button class="btn ghost" onclick="this.closest(\'.modal-mask\').remove()">取消</button><button class="btn primary" onclick="ppDocScaleSaveNew()">保存</button></div></div></div>';
  document.body.insertAdjacentHTML('beforeend', html);
}
function ppDocScaleSaveNew() {
  var msg = document.getElementById('ds-msg');
  Api.createDocScale(Api.curProjectId(), { code: document.getElementById('ds-code').value.trim(), name: document.getElementById('ds-name').value.trim(), pages_new: +document.getElementById('ds-new').value || 0, pages_reuse: +document.getElementById('ds-reuse').value || 0 })
    .then(function () { document.querySelector('.modal-mask').remove(); ppDocScaleLoad(); })
    .catch(function (e) { msg.textContent = '保存失败：' + (e.message || e); });
}
function ppDocScaleSave(id) {
  var get = function (f) { return document.querySelector('#docscale-tbody [data-id="' + id + '"][data-f="' + f + '"]').value.trim(); };
  Api.updateDocScale(Api.curProjectId(), id, { code: get('code'), name: get('name'), pages_new: +get('pages_new') || 0, pages_reuse: +get('pages_reuse') || 0 })
    .then(function () { ppDocScaleLoad(); }).catch(function (e) { alert('保存失败：' + (e.message || e)); });
}
function ppDocScaleDel(id) {
  if (!confirm('确认删除？')) return;
  Api.deleteDocScale(Api.curProjectId(), id).then(function () { ppDocScaleLoad(); }).catch(function (e) { alert('删除失败：' + (e.message || e)); });
}

// 利益相关方（按项目维度，对应 {{table.stakeholders}}/{{table.stakeholder_plan}}）
function ppStakeTab() {
  // R121/R105 附录B：利益相关方参与计划（阶段×活动×角色打勾矩阵）
  // 交互（袁总指示）：默认只读；点「修改」进入编辑态才能点框；点「保存」批量提交并提示；不用弹窗
  // 袁总确认：仅 9 个角色（对标 R121 附录B），顺序与数据库列一致
  var roles = PP_STAKE_ROLES;
  var roleLabels = PP_STAKE_LABELS;
  var head = '<th style="width:44px">序号</th><th style="width:90px">阶段</th><th>活动描述</th>' +
    roles.map(function (r) { return '<th style="min-width:56px">' + roleLabels[roles.indexOf(r)] + '</th>'; }).join('');
  var body = '<tbody id="stake-tbody"><tr><td colspan="' + (roles.length + 3) + '" style="text-align:center;color:#999;">加载中…</td></tr></tbody>';
  var h = '<div class="panel"><div class="panel-hd"><h3><span class="bar"></span>利益相关方参与计划（对标附录B）</h3><div>' +
    '<button class="btn primary sm" id="stake-edit-btn" onclick="ppStakeEditMode()">✎ 修改</button> ' +
    '<button class="btn ok sm" id="stake-save-btn" style="display:none" onclick="ppStakeSaveAll()">✔ 保存</button> ' +
    '<button class="btn ghost sm" id="stake-cancel-btn" style="display:none" onclick="ppStakeExitEdit()">取消</button></div></div>' +
    '<div style="overflow-x:auto;"><table class="tbl"><thead><tr>' + head + '</tr></thead>' + body + '</table></div>' +
    '<div class="note" id="stake-note">√ 表示计划参与。默认只读；点「修改」进入编辑状态后才能点击单元格（空 ⇄ √ 切换），改完点「保存」统一提交。</div></div>';
  setTimeout(function () { ppStakeLoad(); }, 0);
  return h;
}

// 编辑状态与暂存区（行id -> {field: 新值}）
var PP_STAKE_EDITING = false;
var PP_STAKE_PENDING = {};

function ppStakeLoad() {
  var tb = document.getElementById('stake-tbody');
  if (!tb) return;
  Api.listStakeholderPlan(Api.curProjectId()).then(function (r) {
    var rows = (r && r.data) || [];
    if (!rows.length) { tb.innerHTML = '<tr><td colspan="12" style="text-align:center;color:#999;">暂无数据</td></tr>'; return; }
    // 袁总确认：仅 9 个角色（对标 R121 附录B）
    var roles = PP_STAKE_ROLES;
  var roleLabels = PP_STAKE_LABELS;
    tb.innerHTML = rows.map(function (x) {
      var cells = roles.map(function (f) {
        var mk = (x[f] || '').trim();
        // 袁总要求：只保留 √（计划参与），不再有 ○；(PP_STAKE_EDITING ? '' : ' ro')
        var cls = 'chk' + (mk === '√' ? ' on' : '') + (PP_STAKE_EDITING ? '' : ' ro');
        return '<td style="text-align:center;"><button class="' + cls + '" data-id="' + x.id + '" data-f="' + f + '" onclick="ppStakeToggle(this)">' + mk + '</button></td>';
      }).join('');
      return '<tr><td>' + (x.seq || '') + '</td><td>' + (x.phase || '') + '</td><td style="text-align:left;">' + (x.activity || '') + '</td>' + cells + '</tr>';
    }).join('');
    ppStakeSyncNote();
  }).catch(function (e) { tb.innerHTML = '<tr><td colspan="12" style="color:#e74c3c;">加载失败：' + (e.message || e) + '</td></tr>'; });
}

// 进入/退出编辑态（编辑态才能点框）
function ppStakeEditMode() {
  PP_STAKE_EDITING = true;
  PP_STAKE_PENDING = {};
  document.getElementById('stake-edit-btn').style.display = 'none';
  document.getElementById('stake-save-btn').style.display = '';
  document.getElementById('stake-cancel-btn').style.display = '';
  ppStakeLoad();
}
function ppStakeExitEdit() {
  PP_STAKE_EDITING = false;
  PP_STAKE_PENDING = {};
  document.getElementById('stake-edit-btn').style.display = '';
  document.getElementById('stake-save-btn').style.display = 'none';
  document.getElementById('stake-cancel-btn').style.display = 'none';
  ppStakeLoad();
}

function ppStakeSyncNote() {
  var n = document.getElementById('stake-note');
  if (!n) return;
  var cnt = Object.keys(PP_STAKE_PENDING).length;
  n.textContent = PP_STAKE_EDITING
    ? ('编辑中：可直接点单元格勾选/取消 √，已改动 ' + cnt + ' 行，改完点「保存」统一提交。')
    : '√ 表示计划参与。默认只读；点「修改」进入编辑状态后才能勾选，改完点「保存」统一提交。';
}

// 勾选切换：仅编辑态生效，写入暂存区（不立即提交）
function ppStakeToggle(btn) {
  if (!PP_STAKE_EDITING) { if (window.toast) toast('请先点「修改」进入编辑状态'); return; }
  var id = btn.getAttribute('data-id');
  var f = btn.getAttribute('data-f');
  var on = btn.classList.contains('on');
  if (!PP_STAKE_PENDING[id]) PP_STAKE_PENDING[id] = {};
  // 两态切换：空 ⇄ √(计划参与)（袁总要求取消 ○）
  var next = btn.classList.contains('on') ? '' : '√';
  PP_STAKE_PENDING[id][f] = next;
  btn.classList.toggle('on', next === '√');
  btn.textContent = next;
  ppStakeSyncNote();
}

// 批量保存暂存改动（逐行 PUT），完成后提示并退出编辑态
function ppStakeSaveAll() {
  var ids = Object.keys(PP_STAKE_PENDING);
  if (!ids.length) { if (window.toast) toast('没有改动'); return; }
  var pid = Api.curProjectId();
  var done = 0;
  var failed = false;
  ids.forEach(function (id) {
    Api.updateStakeholderPlanRow(pid, id, PP_STAKE_PENDING[id]).then(function () {
      done++;
      if (done === ids.length && !failed) {
        PP_STAKE_PENDING = {};
        ppStakeExitEdit();
        if (window.toast) toast('已保存 ' + done + ' 行');
      }
    }).catch(function (e) {
      failed = true;
      if (done >= ids.length - 1 || true) { /* 任一失败即提示 */ }
      alert('保存失败：' + (e.message || e));
      ppStakeExitEdit();
    });
  });
}
/* 操作栏按钮（占位，已废弃，保留 ppSvnCommit 供其他页调用） */
function ppSvnCommit(no) { alert('已同步模块 ' + no + ' 到 SVN（示例）'); }
