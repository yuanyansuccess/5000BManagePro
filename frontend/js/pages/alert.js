// 作者：袁燕
// 功能：告警日志页（alert）。1:1 还原效果图：4 个 stat 卡 + 分类图例 + 10 列表格 + 状态流转。
// 设计：原型对标用前端静态真实数据（R105 仿真）；后期接后端 /api/alerts 时替换 alertLoad 即可。

// 告警类型 / 级别字典（对标 ALERT_KIND / ALERT_LV）
var ALERT_KIND = {
  tpl: { t: '模板问题', cls: 'warn', ic: '📄' },
  src: { t: '取数问题', cls: 'danger', ic: '🔗' },
  cons: { t: '一致性问题', cls: 'danger', ic: '⚖️' },
  proc: { t: '过程符合性', cls: 'warn', ic: '📐' }
};
var ALERT_LV = { high: { t: '高', cls: 'danger' }, mid: { t: '中', cls: 'warn' }, low: { t: '低', cls: 'info' } };

// 真实告警数据（R105 仿真，对标 ALERT_DATA）
var ALERT_DATA = [
  { id: 'AL-001', tm: '2024-06-20 09:12', kind: 'cons', lv: 'high', dom: 'RDM 需求管理', tpl: 'A1', obj: '软件需求跟踪矩阵 / 软件设计说明', desc: 'SDD 中需求编号 SR-018 在 A1 需求跟踪矩阵中不存在，双向追溯断链', st: '未处理', page: 'rdm' },
  { id: 'AL-002', tm: '2024-06-20 08:40', kind: 'src', lv: 'high', dom: 'PMC 项目监控', tpl: 'A17', obj: '阶段总结报告（设计实现阶段）', desc: '生成 A17 时「风险状态」取数为空，A11 未配置取数来源', st: '未处理', page: 'tpl' },
  { id: 'AL-003', tm: '2024-06-19 17:05', kind: 'tpl', lv: 'mid', dom: 'MA 测量分析', tpl: 'A32', obj: '软件测量与分析报告', desc: 'A32 模板缺「缺陷密度」章节，版次过期', st: '未处理', page: 'tpl' },
  { id: 'AL-004', tm: '2024-06-19 15:33', kind: 'src', lv: 'mid', dom: 'PMC 项目监控', tpl: 'A22', obj: '软件周/双周报（2024-06-17~06-23）', desc: '周报工作量取数来源未配置，内容空白', st: '处理中', page: 'pmc' },
  { id: 'AL-005', tm: '2024-06-18 14:20', kind: 'cons', lv: 'high', dom: 'CM 配置管理', tpl: 'A83', obj: '软件配置管理报告', desc: 'A83 基线 r1180 与受控库清单不一致', st: '未处理', page: 'cm' },
  { id: 'AL-006', tm: '2024-06-17 10:08', kind: 'proc', lv: 'low', dom: 'PQA 质量保证', tpl: 'A26', obj: '软件质量保证工作报告', desc: 'A26 引用审计依据为 CMMI 配置审计单（体系禁用），应改 Q/CEC R02.08', st: '已处理', page: 'pqa' },
  { id: 'AL-007', tm: '2024-06-16 16:45', kind: 'tpl', lv: 'mid', dom: 'PP 项目策划', tpl: 'A11', obj: '软件风险管理表', desc: 'A11 风险等级列缺失「关闭日期」字段', st: '已处理', page: 'pp' },
  { id: 'AL-008', tm: '2024-06-15 11:30', kind: 'src', lv: 'low', dom: 'RDM 需求管理', tpl: 'A1', obj: '需求跟踪矩阵', desc: 'A1 上游需求文件缺失，取数失败', st: '未处理', page: 'rdm' }
];

var ALERT_FILTER = { kind: '全部', lv: '全部', st: '全部' };

function alertRender() {
  const c = document.getElementById('content');
  c.innerHTML = '<div class="page"><div class="page-title">告警日志</div>' +
    '<div class="page-sub">文档生成与取数异常集中暴露 · 模板问题 / 取数问题 / 一致性问题 / 过程符合性　| <span class="modal-tag">项目维度：R105 飞管软件</span></div>' +
    '<div id="alertStats"></div>' +
    '<div class="panel" style="border:1px dashed #b7d3ff;background:#f7fbff;margin-bottom:16px;"><h3><span class="bar"></span>告警分类说明</h3><div class="legend">' +
    '<div class="lg"><span class="tag warn">📄 模板问题</span><span class="lg-t">模板缺章节、版次过期、占位符未替换，导致生成文档结构不符。</span></div>' +
    '<div class="lg"><span class="tag danger">🔗 取数问题</span><span class="lg-t">上游文件缺失、字段取空、取数来源未配置，导致生成内容空白或错误。</span></div>' +
    '<div class="lg"><span class="tag danger">⚖️ 一致性问题</span><span class="lg-t">同一数据在多份文档中取值不一致，破坏双向追溯。</span></div>' +
    '<div class="lg"><span class="tag warn">📐 过程符合性</span><span class="lg-t">GJB5000B 与公司体系要求的活动缺失、时序倒置或引用错误。</span></div>' +
    '</div></div>' +
    '<div class="toolbar"><div class="chips" id="alKindChips"></div></div>' +
    '<div class="toolbar"><div class="chips" id="alLvChips"></div><div class="chips" id="alStChips"></div></div>' +
    '<div id="alertList" class="loading">取数中…</div></div>';
  setTimeout(alertLoad, 50);
}

// stat 卡（对标 stat()）
function alertStatCard(bg, ic, lbl, num, sub) {
  return '<div class="stat"><div class="ic" style="background:' + bg + '">' + ic + '</div>' +
    '<div class="lbl">' + lbl + '</div><div class="num">' + num + '</div><div class="sub">' + sub + '</div></div>';
}

function alertRenderStats() {
  const un = ALERT_DATA.filter(a => a.st === '未处理').length;
  const ing = ALERT_DATA.filter(a => a.st === '处理中').length;
  const hi = ALERT_DATA.filter(a => a.lv === 'high' && a.st !== '已处理').length;
  const box = document.getElementById('alertStats');
  if (!box) return;
  box.className = 'stats';
  box.innerHTML = alertStatCard('#fff1f0', '🔴', '未处理告警', un, '需立即处理') +
    alertStatCard('#fff7e6', '🟠', '处理中', ing, '跟踪至关闭') +
    alertStatCard('#e6f0ff', '⚠️', '高级别未闭环', hi, '影响转段') +
    alertStatCard('#f6ffed', '✅', '累计告警', ALERT_DATA.length, '本项目');
}

function alertRenderChips() {
  const kinds = ['全部', 'tpl', 'src', 'cons', 'proc'];
  const lv = ['全部', 'high', 'mid', 'low'];
  const st = ['全部', '未处理', '处理中', '已处理'];
  const kc = document.getElementById('alKindChips');
  const lc = document.getElementById('alLvChips');
  const sc = document.getElementById('alStChips');
  if (kc) kc.innerHTML = kinds.map(k => '<span class="chip' + (ALERT_FILTER.kind === k ? ' on' : '') + '" onclick="alertSet(\'kind\',\'' + k + '\')">' + (k === '全部' ? '全部' : ALERT_KIND[k].ic + ' ' + ALERT_KIND[k].t) + '</span>').join('');
  if (lc) lc.innerHTML = lv.map(k => '<span class="chip' + (ALERT_FILTER.lv === k ? ' on' : '') + '" onclick="alertSet(\'lv\',\'' + k + '\')">' + (k === '全部' ? '全部级别' : ALERT_LV[k].t) + '</span>').join('');
  if (sc) sc.innerHTML = st.map(k => '<span class="chip' + (ALERT_FILTER.st === k ? ' on' : '') + '" onclick="alertSet(\'st\',\'' + k + '\')">' + k + '</span>').join('');
}

function alertSet(k, v) { ALERT_FILTER[k] = v; alertRenderStats(); alertRenderChips(); alertLoad(); }

function alertRows() {
  return ALERT_DATA.filter(a => {
    if (ALERT_FILTER.kind !== '全部' && a.kind !== ALERT_FILTER.kind) return false;
    if (ALERT_FILTER.lv !== '全部' && a.lv !== ALERT_FILTER.lv) return false;
    if (ALERT_FILTER.st !== '全部' && a.st !== ALERT_FILTER.st) return false;
    return true;
  });
}

function alertLoad() {
  alertRenderStats();
  alertRenderChips();
  const box = document.getElementById('alertList'); if (!box) return;
  const rows = alertRows();
  box.className = 'list';
  if (!rows.length) { box.innerHTML = '<div class="empty">当前筛选条件下无告警记录。</div>'; return; }
  let h = '<div class="panel"><div style="overflow-x:auto;"><table class="tbl" style="min-width:1500px;"><thead><tr>' +
    '<th style="width:6%">编号</th><th style="width:9%">时间</th><th style="width:8%">类型</th><th style="width:4%">级别</th>' +
    '<th style="width:9%">过程域</th><th style="width:5%">模板</th><th style="width:13%">告警对象</th><th style="width:26%">问题描述</th>' +
    '<th style="width:6%">状态</th><th style="width:10%">操作</th></tr></thead><tbody>';
  rows.forEach(function (a) {
    const k = ALERT_KIND[a.kind]; const l = ALERT_LV[a.lv];
    const stCls = a.st === '已处理' ? 'ok' : (a.st === '处理中' ? 'info' : 'warn');
    h += '<tr><td>' + a.id + '</td><td style="white-space:nowrap;">' + a.tm + '</td>' +
      '<td><span class="tag ' + k.cls + '">' + k.ic + ' ' + k.t + '</span></td>' +
      '<td><span class="tag ' + l.cls + '">' + l.t + '</span></td>' +
      '<td>' + a.dom + '</td><td><span class="ver-badge">' + a.tpl + '</span></td>' +
      '<td style="text-align:left">' + a.obj + '</td>' +
      '<td style="text-align:left;word-break:break-word;">' + a.desc + '</td>' +
      '<td><span class="tag ' + stCls + '">' + a.st + '</span></td>' +
      '<td><button class="btn-sm" onclick="alertDetail(\'' + a.id + '\')">详情</button>' +
      (a.st === '未处理' ? '<button class="btn-sm ok" onclick="alertStatus(\'' + a.id + '\',\'处理中\')">处理</button>' : '') +
      (a.st === '处理中' ? '<button class="btn-sm ok" onclick="alertStatus(\'' + a.id + '\',\'已处理\')">关闭</button>' : '') + '</td></tr>';
  });
  h += '</tbody></table></div></div>';
  box.innerHTML = h;
}

function alertStatus(id, st) {
  const a = ALERT_DATA.find(x => x.id === id);
  if (a) { a.st = st; alertLoad(); }
}

function alertDetail(id) {
  const a = ALERT_DATA.find(x => x.id === id);
  if (!a) return;
  const k = ALERT_KIND[a.kind]; const l = ALERT_LV[a.lv];
  const h = '<div class="modal-hd"><div class="mt">' + a.id + ' 告警详情</div><div class="mx" onclick="closeMask()">×</div></div>' +
    '<div class="modal-bd"><div class="frow"><span class="fn">类型</span><span class="tag ' + k.cls + '">' + k.ic + ' ' + k.t + '</span></div>' +
    '<div class="frow"><span class="fn">级别</span><span class="tag ' + l.cls + '">' + l.t + '</span></div>' +
    '<div class="frow"><span class="fn">过程域</span><span>' + a.dom + '</span></div>' +
    '<div class="frow"><span class="fn">模板</span><span class="ver-badge">' + a.tpl + '</span></div>' +
    '<div class="frow"><span class="fn">告警对象</span><span>' + a.obj + '</span></div>' +
    '<div class="note" style="margin-top:8px;">' + a.desc + '</div></div>' +
    '<div class="modal-ft"><span class="tag ' + (a.st === '已处理' ? 'ok' : 'warn') + '">' + a.st + '</span>' +
    '<button class="btn" onclick="closeMask()">关闭</button></div>';
  showMask(h);
}
