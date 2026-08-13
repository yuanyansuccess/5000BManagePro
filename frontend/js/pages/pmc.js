// 作者：袁燕
// 功能：项目监控 PMC 页（核心节点）。1:1 对标效果图 preview.html 的 tab 结构（过程域总览 + 5 阶段工作台），填充 R105 真实监控数据。
// 设计：顶部 5 阶段步骤条（pmcStep，橙色渐变+脉动动画）+ 6 子页签（node-tabs，吸顶），内容由 PMC_TABS[].fn 生成。

// 公共 tag 辅助（对标效果图 tag(cls, txt)）
function tag(cls, txt) { return '<span class="tag ' + cls + '">' + txt + '</span>'; }

// 5 阶段名称（对标 PMC_STEPS）
var PMC_PHASES = ['项目策划', '软件需求分析', '设计实现', '软件测试', '验收结项'];
var PMC_CUR_PHASE = 0; // 默认策划阶段；真正的"当前阶段"由步骤条的 active 控制

// 6 子页签（对标效果图 DOM.pmc.tabs：ov + ph0~ph4）
var PMC_TABS = [
  { key: 'ov', label: '过程域总览', fn: 'PMC_WIDGET' },
  { key: 'ph0', label: '① 项目策划', fn: 'PMC_PHASE_STAGE', arg: 0 },
  { key: 'ph1', label: '② 软件需求分析', fn: 'PMC_PHASE_STAGE', arg: 1 },
  { key: 'ph2', label: '③ 设计实现', fn: 'PMC_PHASE_STAGE', arg: 2 },
  { key: 'ph3', label: '④ 软件测试', fn: 'PMC_PHASE_STAGE', arg: 3 },
  { key: 'ph4', label: '⑤ 验收结项', fn: 'PMC_PHASE_STAGE', arg: 4 }
];
var PMC_CUR_TAB = 'ov';

// 当前项目阶段（5 阶段索引）：R105 已进入测试阶段（ph3）
function curPhaseIdx5() { return 3; }

// 阶段时间窗（对标 PMC_STAGE_WINDOW）
function PMC_STAGE_WINDOW() {
  return ['项目启动 ~ 策划基线发布', '需求分析启动 ~ 需求基线评审', '设计启动 ~ 详细设计/编码完成', '测试启动 ~ 回归测试完成', '验收启动 ~ 产品交付'];
}

// 阶段责任人（对标 PMC_STAGE_OWNER）
function PMC_STAGE_OWNER() {
  return ['软件负责人（策划）', '辛峥峰（需求）', '罗臻/吴明森（设计实现）', '测试组（测试）', '软件负责人+质保（结项）'];
}

// 每阶段产出块（对标 PMC_STAGE_BLOCKS，精简版保留核心监控项）
function PMC_STAGE_BLOCKS() {
  return [
    {
      ph: '项目策划', items: [
        { nm: '进度表（A16）', note: 'R105 18 任务进度，计划/实际/偏差', act: 'go(\'pp\')' },
        { nm: '风险与机遇管理', note: '风险项/影响等级/应对/预防措施/机遇', act: 'goRiskManage()' },
        { nm: '外部资源跟踪表', note: '策划期资源到位率 100%', act: 'go(\' pp\')' },
        { nm: '配置管理计划', note: 'A51 配置管理计划 · 基线建立', act: 'go(\'cm\')' }
      ]
    },
    {
      ph: '软件需求分析', items: [
        { nm: '需求状态表（A2）', note: '需求状态五态流转、双向追溯', act: 'openReqDialogPmc(0)' },
        { nm: '风险与机遇管理', note: '需求阶段风险跟踪，更新影响等级与应对', act: 'goRiskManage()' },
        { nm: '质量保证报告', note: '需求评审审计', act: 'go(\'pqa\')' },
        { nm: '问题跟踪', note: '需求阶段问题', act: 'goIssue(1)' }
      ]
    },
    {
      ph: '设计实现', items: [
        { nm: '需求状态表（A2）', note: '设计实现阶段需求状态 · 已设计+已实现', act: 'openReqDialogPmc(1)' },
        { nm: '软件设计说明(SDD)', note: '工程文档，从 SVN 受控库拉取', act: 'go(\'pp\')' },
        { nm: '代码检视表（A4）', note: '代码检视问题表 · 代码 1021 行', act: 'go(\'pp\')' },
        { nm: '风险与机遇管理', note: '设计/编码阶段风险，更新应对与预防', act: 'goRiskManage()' },
        { nm: '质量保证报告', note: '设计/代码审计', act: 'go(\'pqa\')' },
        { nm: '问题跟踪', note: '接口/设计问题', act: 'goIssue(2)' }
      ]
    },
    {
      ph: '软件测试', items: [
        { nm: '需求状态表（A2）', note: '测试阶段需求状态 · 已测试', act: 'openReqDialogPmc(2)' },
        { nm: '测试计划/说明/报告(三件套)', note: '工程文档，SVN 拉取/同步', act: 'go(\'pp\')' },
        { nm: '风险与机遇管理', note: '测试阶段风险（漏测/回归），更新应对', act: 'goRiskManage()' },
        { nm: '质量保证报告', note: '测试过程审计', act: 'go(\'pqa\')' },
        { nm: '问题跟踪', note: '测试缺陷跟踪至关闭', act: 'goIssue(3)' }
      ]
    },
    {
      ph: '验收结项', items: [
        { nm: '需求状态表（A2）', note: '验收结项需求状态 · 全生命周期总览', act: 'openReqDialogPmc(3)' },
        { nm: '风险与机遇管理', note: '全阶段风险收口，机遇落账', act: 'goRiskManage()' },
        { nm: '结项配置报告/产品库入库', note: '受控库→产品库', act: 'go(\'cm\')' },
        { nm: '质量保证报告', note: '最终质量评价', act: 'go(\'pqa\')' },
        { nm: '问题跟踪', note: '全部问题清零确认', act: 'goIssue(4)' }
      ]
    }
  ];
}

// 阶段对标依据（对标 PMC_STAGE_REF）
function PMC_STAGE_REF() {
  return {
    '项目策划': { r105: '《软件开发计划 V3.01》第5.2 策划基线 · A16 进度表 / A11 风险 / A79 资源 / A51 配置计划', sys: '公司体系：Q/CEC 过程资产库管理规程、配置管理过程定义' },
    '软件需求分析': { r105: '《软件开发计划 V3.01》5.4 软件需求分析；A1 需求跟踪矩阵 / A2 需求状态表 / SRS', sys: '公司体系：需求管理过程、配置管理过程（需求文档入分配基线）' },
    '设计实现': { r105: '《软件开发计划 V3.01》5.5 设计 / 5.6 编码；SDD / DDD / 代码检视 A4', sys: '公司体系：设计开发过程、配置管理过程（设计/代码入产品基线）' },
    '软件测试': { r105: '《软件开发计划 V3.01》5.7 软件测试；测试计划/说明/报告三件套；A32 缺陷密度', sys: '公司体系：验证与确认过程、配置管理过程（测试版本受控）' },
    '验收结项': { r105: '《软件开发计划 V3.01》5.8 验收与结项；A19 验收报告 / A56 结项配置 / A76 产品库', sys: '公司体系：结项管理过程、配置管理过程（受控库→产品库）' }
  };
}

// 阶段×监控表总览（对标 PMC_PHASE_SHEETS）
var PMC_PHASE_SHEETS = [
  { ph: '策划', prog: '已出', week: '4 份', pr: '4 份', issue: '已出（0 遗留）' },
  { ph: '需求', prog: '已出', week: '6 份', pr: '6 份', issue: '已出（1 遗留）' },
  { ph: '设计实现', prog: '更新中', week: '8 份（进行中）', pr: '8 份（进行中）', issue: '编制中（2 遗留）' },
  { ph: '测试', prog: '待出', week: '—', pr: '—', issue: '—' },
  { ph: '结项', prog: '待出', week: '—', pr: '—', issue: '—' }
];

// 测量分析数据（A32 实际值，对标 R105）
var PMC_MEASURE = [
  { item: '生产率', val: '1.2 KLOC/人月', base: '≥0.8', st: 'ok' },
  { item: '进度偏差', val: '+3%', base: '≤±10%', st: 'ok' },
  { item: '缺陷密度', val: '2.1/千行', base: '≤5', st: 'ok' },
  { item: '评审缺陷率', val: '4.2%', base: '≤8%', st: 'ok' },
  { item: '测试覆盖率', val: '92%', base: '≥90%', st: 'ok' },
  { item: '用例通过率', val: '97%', base: '≥95%', st: 'ok' }
];

// ===== 页面渲染入口 =====

function pmcRender() {
  var c = document.getElementById('content');
  c.innerHTML = pmcNodePage();
}

// 阶段步骤条（对标 PMC_STEPPER，5 步，橙色渐变+脉动）
function pmcStepBar() {
  var cur5 = curPhaseIdx5();
  var steps = PMC_PHASES.map(function (p, i) {
    var cls = i < cur5 ? 'done' : (i === cur5 ? 'active' : '');
    return '<div class="step ' + cls + '" onclick="pmcGoPhase(' + i + ')">'
      + '<span class="dot-num">' + (i + 1) + '</span>'
      + '<span class="step-label">' + p + '</span></div>';
  }).join('');
  var nextBtn = '';
  if (cur5 < PMC_PHASES.length - 1) {
    nextBtn = '<button class="pmc-switch-btn" onclick="alert(\'阶段切换：当前阶段 → ' + PMC_PHASES[cur5 + 1] + '（功能待接入）\')">✓ 阶段完成 · 切换到下一阶段</button>';
  }
  return '<div class="pmc-step" style="display:flex;align-items:center;flex-wrap:wrap;">'
    + '<div style="flex:1;min-width:200px;"><div class="pmc-step-hd">当前阶段：<b>第 ' + (cur5 + 1) + ' 点 · ' + PMC_PHASES[cur5] + '</b></div>'
    + '<div class="pmc-step-bar">' + steps + '</div></div>'
    + nextBtn + '</div>';
}

// 子页签条
function pmcTabBar() {
  return '<div class="node-tabs sticky">' + PMC_TABS.map(function (t) {
    return '<button class="ntab' + (t.key === PMC_CUR_TAB ? ' on' : '') + '" onclick="pmcGoTab(\'' + t.key + '\')">' + t.label + '</button>';
  }).join('') + '</div>';
}

// 阶段状态卡（对标 pmcStageStatusCard，动态取自 PMC_STAGE_BLOCKS）
function pmcStageStatusCard() {
  var curTab = PMC_TABS.find(function (t) { return t.key === PMC_CUR_TAB; });
  if (!curTab || curTab.key === 'ov' || curTab.arg == null) return '';
  var phIdx = curTab.arg;
  var S = PMC_STAGE_BLOCKS();
  var st = S[phIdx];
  if (!st) return '';
  var win = PMC_STAGE_WINDOW()[phIdx];
  var own = PMC_STAGE_OWNER()[phIdx];
  var cur5 = curPhaseIdx5();
  var stt = phIdx < cur5 ? 'done' : (phIdx === cur5 ? 'cur' : 'todo');
  var stTxt = stt === 'done' ? '已完成' : (stt === 'cur' ? '进行中' : '未开始');
  var stCls = stt === 'done' ? 'ok' : (stt === 'cur' ? 'warn' : 'info');
  var sheet = PMC_PHASE_SHEETS[phIdx] || { prog: '—' };
  var progTxt = sheet.prog || '—';
  var progCls = progTxt.indexOf('已出') >= 0 ? 'ok' : (progTxt.indexOf('更新') >= 0 || progTxt.indexOf('进行') >= 0 ? 'warn' : 'info');
  return '<div class="pmc-status pmc-status-' + stt + '">'
    + '<div class="psc-main"><span class="psc-ph">' + st.ph + ' 阶段</span>' + tag(stCls, stTxt) + '</div>'
    + '<div class="psc-kv"><span class="psc-k">时间窗</span><span class="psc-v">' + win + '</span></div>'
    + '<div class="psc-kv"><span class="psc-k">阶段责任</span><span class="psc-v">' + own + '</span></div>'
    + '<div class="psc-kv"><span class="psc-k">阶段产出</span><span class="psc-v">' + st.items.length + ' 项（进度表/风险/问题等）</span></div>'
    + '<div class="psc-kv"><span class="psc-k">进度表状态</span><span class="psc-v">' + tag(progCls, progTxt) + '</span></div>'
    + '<div class="psc-kv"><span class="psc-k">关联风险</span><span class="psc-v">点击「风险与机遇管理」跟踪</span></div>'
    + '</div>';
}

// 组装 PMC 页面
function pmcNodePage() {
  var curTab = PMC_TABS.find(function (t) { return t.key === PMC_CUR_TAB; });
  var stageCard = (curTab && curTab.arg != null) ? pmcStageStatusCard() : '';
  var content = pmcTabContent();
  // 步骤条仅概览 tab 显示（对标效果图 PMC_WIDGET 内含 PMC_STEPPER）
  var stepBar = (PMC_CUR_TAB === 'ov') ? pmcStepBar() : '';
  return '<div class="page" id="page-pmc">'
    + '<div class="page-title">项目监控 PMC</div>'
    + '<div class="page-sub"><span class="modal-tag">项目：R105（K409）飞管软件</span></div>'
    + stepBar
    + pmcTabBar()
    + '<div class="node-body" id="pmc-body">' + stageCard + content + '</div>'
    + '</div>';
}

// 阶段切换：更新步骤条+状态卡+内容
function pmcGoPhase(i) {
  PMC_CUR_PHASE = i;
  // 切换到对应阶段 tab
  PMC_CUR_TAB = 'ph' + i;
  pmcRebuildBody();
}

function pmcGoTab(key) {
  PMC_CUR_TAB = key;
  pmcRebuildBody();
}

function pmcRebuildBody() {
  var body = document.getElementById('pmc-body');
  var bar = document.querySelector('#page-pmc .node-tabs');
  if (!body) return;
  body.classList.add('switching');
  setTimeout(function () {
    // 步骤条：仅概览 tab 时更新（对标 PMC_WIDGET 内含 PMC_STEPPER）
    var step = document.querySelector('#page-pmc .pmc-step');
    if (PMC_CUR_TAB === 'ov') {
      if (step) step.outerHTML = pmcStepBar();
    } else {
      if (step) step.remove();
    }
    if (bar) bar.outerHTML = pmcTabBar();
    body.innerHTML = (PMC_CUR_TAB !== 'ov' ? pmcStageStatusCard() : '') + pmcTabContent();
    body.classList.remove('switching');
  }, 220);
}

function pmcTabContent() {
  var tab = PMC_TABS.find(function (t) { return t.key === PMC_CUR_TAB; });
  if (!tab) return '';
  var fn = window[tab.fn];
  if (typeof fn !== 'function') return '<div class="placeholder">' + tab.label + '（建设中）</div>';
  return tab.arg != null ? fn(tab.arg) : fn();
}

// ===== 过程域总览（对标 PMC_WIDGET） =====

function PMC_WIDGET() {
  // 测量分析已出报告数
  var maData = [
    { ph: '策划', st: '已出' }, { ph: '需求', st: '已出' }, { ph: '设计实现', st: '进行中' },
    { ph: '测试', st: '待出' }, { ph: '结项', st: '待出' }
  ];
  var maOut = maData.filter(function (r) { return r.st === '已出'; }).length;

  function mc(name, rpt, icon, status, act, lbl) {
    return '<div class="mc-card">'
      + '<div class="mc-h">' + icon + ' ' + name + '</div>'
      + '<div class="mc-rpt">' + rpt + '</div>'
      + '<div class="mc-st"><span class="svn-ok">✓ 已同步 SVN</span> ' + status + '</div>'
      + '<div class="mc-ops"><button class="btn sm" onclick="' + act + '">' + lbl + '</button></div>'
      + '</div>';
  }

  var cards = mc('测量与分析', 'A32 测量分析报告', '📊',
    '已出报告 ' + maOut + ' 个阶段 · 全部阶段汇总', 'mcViewMaRpt()', '查看报告')
    + mc('配置管理', 'A83 软件配置管理报告', '🗂',
      '配置项 96 项 · 基线 4 条', 'mcViewCmRpt()', '查看报告')
    + mc('风险管理', 'A11 风险跟踪', '⚠',
      '风险 4 项（全部已关闭）', 'goRiskManage()', '查看报告')
    + mc('问题跟踪', 'A23 问题跟踪汇总', '🔧',
      '各阶段问题录入、跟踪至关闭', 'goIssue(3)', '查看报告')
    + mc('周报/双周报', 'A22 周/双周报', '📅',
      '进度表预制 → 周任务 → 个人周报', 'mcViewWeekRpt()', '查看报告')
    + mc('阶段评审', 'A17 阶段报告', '📑',
      '汇总测量/配置/评审/问题数据', 'mcViewStageRpt()', '查看报告');

  return '<div class="panel" style="border:1px solid #ffe0c2;"><h3><span class="bar" style="background:#fa8c16"></span>项目监控 · 过程域总览</h3>'
    + '<div class="note" style="margin-bottom:10px;">各过程域数据已在平台录入并同步 SVN，下方可一键「查看报告」调阅对应报告。</div>'
    + '<div class="mc-grid">' + cards + '</div>'
    + '<div class="mc-flow"><span class="mc-flow-t">数据流</span>平台录入(原始数据) → 自动算偏差/风险 → 生成报告 → 同步 SVN</div>'
    + '</div>'
    + pmcPhaseTable()
    + '<div class="note" style="margin-top:12px;">风险跟踪对象取自基础数据字典池（当前已选风险 4 项）。各阶段监控内容与平台录入见下方选项卡，点击即可切换查看。</div>';
}

// ===== 阶段工作台（对标 PMC_PHASE_STAGE） =====

function PMC_PHASE_STAGE(phIdx) {
  var S = PMC_STAGE_BLOCKS();
  var st = S[phIdx];
  if (!st) return '';
  var ref = PMC_STAGE_REF()[st.ph] || { r105: '（见开发计划）', sys: '' };

  // 产出清单表格
  var blockRows = st.items.map(function (it) {
    var isAuto = (it.nm.indexOf('报告') >= 0 || it.nm.indexOf('三件套') >= 0);
    var kind = isAuto ? 'auto' : 'input';
    var way = isAuto
      ? '<span class="tag info">自动生成 · 同步 SVN</span>'
      : '<span class="tag ok">平台录入</span>';
    var ops = isAuto
      ? '<button class="btn sm" style="height:32px;min-width:60px;font-size:13px;border-radius:8px;background:var(--primary);color:#fff;border:none;cursor:pointer;" onclick="alert(\'生成/查看：' + it.nm + '（功能待接入）\')">生成 / 查看</button>'
      : '<button class="btn sm" style="height:32px;min-width:60px;font-size:13px;border-radius:8px;background:var(--primary);color:#fff;border:none;cursor:pointer;" onclick="alert(\'修改：' + it.nm + '（功能待接入）\')">修改</button> '
        + '<button class="btn sm" style="height:32px;min-width:60px;font-size:13px;border-radius:8px;background:#fff;color:var(--text-2);border:1px solid var(--border);cursor:pointer;" onclick="alert(\'删除：' + it.nm + '（功能待接入）\')">删除</button>';
    var hint = isAuto ? '<span class="oe-hint">由平台相关数据自动生成，在报告中点「同步 SVN」提交受控库</span>' : '';
    return '<tr class="out-row ' + kind + '"><td class="out-name">' + it.nm + '</td>'
      + '<td class="out-desc">' + (isAuto ? '由平台数据自动生成（' + it.note + '）' : it.note) + (hint ? '　' + hint : '') + '</td>'
      + '<td class="ctr">' + way + '</td><td class="ctr out-ops">' + ops + '</td></tr>';
  }).join('');

  var blocks = '<table class="tbl"><tr><th style="width:20%;">产出 / 监控项</th><th>说明 / 操作指引</th><th style="width:14%;">来源</th><th style="width:24%;">操作</th></tr>' + blockRows + '</table>';

  // R105 对标依据
  var refHtml = '<div class="note" style="margin-bottom:8px;padding:10px 14px;background:#f5f7fa;border-radius:10px;">'
    + '<b>R105 对标：</b>' + ref.r105 + '<br><b>体系依据：</b>' + ref.sys + '</div>';

  // 测量状态
  var maHtml = '';
  var maOut = (phIdx < 2) ? '已出' : (phIdx === 2 ? '进行中' : '待出');
  var maCls = maOut === '已出' ? 'ok' : (maOut === '进行中' ? 'warn' : 'info');
  maHtml = '<div class="kv"><span>阶段测量状态</span><b>' + tag(maCls, maOut) + '</b></div>'
    + '<div class="note" style="margin-top:8px;">本阶段测量项 6 项（工作量/进度偏差/缺陷密度等），点击「测量分析报告」可录入/查看实际值并自动算偏差。</div>';

  return '<div class="panel" style="border:1px solid #e3e8f0;margin-top:14px;"><h3><span class="bar"></span>本阶段全部监控项</h3>'
    + refHtml
    + blocks + '</div>'
    + '<!-- 进度表 -->'
    + '<div class="sched-panel"><h3><span class="bar"></span>进度表（A16）· ' + st.ph + ' 阶段</h3>'
    + '<table class="tbl"><thead><tr><th>任务</th><th>计划开始</th><th>计划结束</th><th>实际日期</th><th>偏差</th><th>状态</th></tr></thead><tbody>'
    + pmcSchedRows(st.ph)
    + '</tbody></table><div class="note" style="margin-top:8px;">进度偏差控制在 ±10% 阈值内，偏差任务已纳入纠偏措施跟踪。</div></div>'
    + '<!-- 测量分析快捷面板 -->'
    + '<div class="panel" style="margin-top:12px;"><h3><span class="bar"></span>测量分析（A32）· ' + st.ph + ' 阶段</h3>'
    + maHtml
    + '<table class="tbl"><thead><tr><th>测量项</th><th>实测值</th><th>基准</th><th>状态</th></tr></thead><tbody>'
    + PMC_MEASURE.map(function (m) {
      return '<tr><td style="text-align:left">' + m.item + '</td><td><b>' + m.val + '</b></td><td>' + m.base
        + '</td><td>' + tag(m.st, m.st === 'ok' ? '达标' : '关注') + '</td></tr>';
    }).join('')
    + '</tbody></table></div>';
}

// 进度表行（按阶段分）
function pmcSchedRows(ph) {
  var phRows = {
    '项目策划': [
      ['编制开发计划', '2024-03-18', '2024-03-29', '2024-03-29', '0', 'ok', '完成'],
      ['策划评审', '2024-04-01', '2024-04-15', '2024-04-12', '-3', 'ok', '完成']
    ],
    '软件需求分析': [
      ['需求分析', '2024-04-16', '2024-04-24', '2024-04-25', '+1', 'warn', '完成'],
      ['需求评审', '2024-04-25', '2024-04-30', '2024-04-30', '0', 'ok', '完成']
    ],
    '设计实现': [
      ['概要设计', '2024-05-09', '2024-05-28', '2024-05-26', '-2', 'ok', '完成'],
      ['详细设计', '2024-05-29', '2024-06-14', '2024-06-17', '+3', 'warn', '完成'],
      ['编码实现', '2024-06-17', '2024-06-28', '2024-06-30', '+2', 'warn', '完成']
    ],
    '软件测试': [
      ['单元测试', '2024-07-06', '2024-07-16', '2024-07-17', '+1', 'warn', '完成'],
      ['集成测试', '2024-07-17', '2024-07-24', '2024-07-26', '+2', 'warn', '完成'],
      ['系统测试', '2024-07-26', '2024-08-02', '—', '—', 'warn', '进行中']
    ],
    '验收结项': [
      ['验收测试', '2024-08-03', '2024-08-07', '—', '—', 'info', '待启动'],
      ['产品交付', '2024-08-08', '2024-08-09', '—', '—', 'info', '待启动']
    ]
  };
  var rows = phRows[ph] || [['—', '', '', '', '', 'info', '无数据']];
  return rows.map(function (r) {
    var stCls = r[5] === 'ok' ? 'ok' : (r[5] === 'warn' ? 'warn' : 'info');
    return '<tr><td style="text-align:left;font-weight:600;">' + r[0] + '</td>'
      + '<td>' + r[1] + '</td><td>' + r[2] + '</td><td>' + r[3] + '</td><td>' + (r[4] === '—' ? '<span style="color:#bbb;">—</span>' : r[4]) + '</td>'
      + '<td>' + tag(stCls, r[6]) + '</td></tr>';
  }).join('');
}

// 阶段表总览（对标 pmcPhaseTable）
function pmcPhaseTable() {
  var cur5 = curPhaseIdx5();
  var rows = PMC_PHASE_SHEETS.map(function (r, i) {
    var mark = i === cur5 ? ' <span class="tag info">当前</span>' : '';
    return '<tr' + (i === cur5 ? ' style="background:#fff4e6;"' : '') + '><td>' + r.ph + mark + '</td>'
      + '<td>' + phCell(r.prog) + '</td><td>' + phCell(r.week) + '</td><td>' + phCell(r.pr) + '</td><td>' + phCell(r.issue) + '</td></tr>';
  }).join('');
  return '<div class="panel"><h3><span class="bar"></span>阶段监控表总览</h3>'
    + '<table class="tbl"><tr><th>阶段</th><th>进度表</th><th>周任务分配</th><th>个人周报</th><th>问题跟踪</th></tr>' + rows + '</table></div>';
}

function phCell(v) {
  if (v === '—') return '<span style="color:#bbb;">—</span>';
  if (v.indexOf('已出') >= 0) return tag('ok', v);
  if (v.indexOf('中') >= 0) return tag('warn', v);
  if (v === '待出') return tag('info', v);
  return v;
}

// ===== 过程域总览卡片按钮 =====

function mcViewMaRpt() { alert('查看全部阶段测量分析报告（A32）\n' + PMC_MEASURE.map(function(m){ return m.item + ': ' + m.val + ' (' + (m.st === 'ok' ? '达标' : '关注') + ')'; }).join('\n')); }
function mcViewCmRpt() { alert('查看配置管理报告（A83）\n配置项 96 项 · 基线 r1180 · 受控库状态正常'); }
function goRiskManage() { alert('风险与机遇管理\n4 项风险全部已关闭（RK-01~04）\n关闭日期：2024-06-14 ~ 2024-07-05'); }
function goIssue(ph) { alert('问题跟踪（阶段 ' + ph + '）\n共录入 3 项问题，已关闭 2 项，1 项待关闭'); }
function mcViewWeekRpt() { alert('周/双周报（A22）\n本周（9/11）任务完成，滞后 2 项'); }
function mcViewStageRpt() { alert('阶段报告（A17）\n里程碑 M3 达成，交付物全部入库'); }
function openReqDialogPmc(idx) { alert('需求状态表（A2）· 阶段 ' + idx + '\n需求状态五态流转，双向追溯'); }
