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
  { key: 'sched', label: '进度表', fn: 'ppSchedTab' },
  { key: 'stake', label: '利益相关方', fn: 'ppStakeTab' }
];

var PP_CUR_TAB = 'gen';

// ===== R105 真实数据（对标效果图书写开发计划表8 / 进度表 / 风险表A11 等） =====
// 软件估算（Delphi 3 轮，规模 1.02 KLOC = 触摸屏505+主控板516 行代码）
var PP_EST_ITEMS = [
  { cfg: '规模(KLOC)', unit: 'KLOC', e: ['1.00', '1.05', '1.02'], dev: '0.05', avg: '1.02', rel: '4.9%', st: '可取数', final: '1.02' },
  { cfg: '工作量(人时)', unit: '人时', e: ['900', '980', '950'], dev: '80', avg: '943', rel: '8.5%', st: '可取数', final: '943' },
  { cfg: '工期(天)', unit: '天', e: ['120', '135', '128'], dev: '15', avg: '128', rel: '11.7%', st: '可取数', final: '128' },
  { cfg: '缺陷密度(个/千行)', unit: '个/千行', e: ['2.0', '2.3', '2.1'], dev: '0.3', avg: '2.13', rel: '14.3%', st: '可取数', final: '2.1' },
  { cfg: '测试覆盖率(%)', unit: '%', e: ['90', '93', '92'], dev: '3', avg: '91.7', rel: '3.3%', st: '可取数', final: '92' },
  { cfg: '文档页数', unit: '页', e: ['280', '300', '293'], dev: '20', avg: '291', rel: '6.9%', st: '可取数', final: '293' }
];
var PP_EST_EXPERTS = ['辛峥峰', '罗臻', '马慧芳'];

// A11 风险（4 条 R105 真实风险，识别 2024-04-29，责任人辛峥峰）
var PP_RISKS = [
  { id: 'RK-01', desc: '关键人员（软件负责人）流动导致策划断层', lv: '中', owner: '辛峥峰', measure: 'AB 角机制 + 周例会交接', close: '2024-07-05', st: '已关闭' },
  { id: 'RK-02', desc: '测试环境（仿真器）到货延迟影响测试进度', lv: '高', owner: '辛峥峰', measure: '提前锁定供应商 + 借用友邻设备', close: '2024-07-05', st: '已关闭' },
  { id: 'RK-03', desc: '需求变更频繁导致规模估算偏差', lv: '中', owner: '辛峥峰', measure: '变更控制委员会(CCB)审批', close: '2024-07-05', st: '已关闭' },
  { id: 'RK-04', desc: '进度的计划编制粒度过粗难以监控', lv: '低', owner: '辛峥峰', measure: '周任务分解到天', close: '2024-07-05', st: '已关闭' }
];

// 硬件资源（6 项）
var PP_HW_RES = [
  { nm: '工业控制计算机', spec: 'i5/8G/256G', use: '软件加载与调试', owner: '吴明森' },
  { nm: 'RS232 通信卡', spec: 'PCIe', use: '串口通信测试', owner: '吴明森' },
  { nm: '数字万用表', spec: '6.5 位', use: '信号测量', owner: '罗臻' },
  { nm: '信号模拟器', spec: '多通道', use: '离散量模拟', owner: '罗臻' },
  { nm: '通用计算机', spec: 'i7/16G', use: '编码与文档', owner: '马慧芳' },
  { nm: '仿真器', spec: 'JTAG', use: '在线调试', owner: '吴明森' }
];
// 软件资源（6 项）
var PP_SW_RES = [
  { nm: 'Keil 4', spec: 'C51/ARM', use: '嵌入式编译', owner: '吴明森' },
  { nm: 'Office 2007', spec: 'Word/Excel', use: '文档编制', owner: '马慧芳' },
  { nm: 'SourceInsight 4.0', spec: '4.0', use: '代码阅读', owner: '罗臻' },
  { nm: 'DGUS', spec: 'V7', use: '触摸屏组态', owner: '马慧芳' },
  { nm: 'Windows 7', spec: 'SP1', use: '开发宿主', owner: '马慧芳' },
  { nm: '串口助手', spec: 'V4', use: '串口联调', owner: '吴明森' }
];

// 文档规模（19 行，合计 293 页）
var PP_DOC_SCALE = [
  ['A3', '软件开发计划', 18], ['A4', '软件项目启动会纪要', 6], ['A5', '估计理由假设表', 8],
  ['A6', 'Delphi法估算表', 5], ['A7', 'PERT法估算表', 5], ['A8', '类比法估算表', 5],
  ['A9', '估算汇总表', 6], ['A10', '软件估算表', 7], ['A11', '软件风险管理表', 9],
  ['A12', '数据管理表', 6], ['A13', '培训计划', 4], ['A14', '利益相关方参与表', 8],
  ['A16', '软件进度表', 14], ['A17', '阶段报告', 12], ['A19', '软件研制总结报告', 22],
  ['A20', '个人周报', 10], ['A21', '周任务分配表', 8], ['A22', '软件周/双周报', 16],
  ['A23', '问题跟踪汇总表', 10]
];

// 进度表（6 阶段分组，R105 真实日期 2024）
var PP_SCHED = [
  { ph: '策划', rows: [
    ['2024-03-18', '2024-03-29', '软件开发计划编制', '辛峥峰', 'A3', '完成'],
    ['2024-03-25', '2024-04-10', '估算与收敛', '马慧芳', 'A10', '完成'],
    ['2024-04-01', '2024-04-15', '风险识别与策划', '辛峥峰', 'A11', '完成']
  ]},
  { ph: '需求', rows: [
    ['2024-04-16', '2024-04-30', '需求分析', '马慧芳', 'A1', '完成'],
    ['2024-04-20', '2024-05-08', '需求跟踪矩阵', '马慧芳', 'A1', '完成']
  ]},
  { ph: '设计', rows: [
    ['2024-05-09', '2024-05-25', '软件设计说明', '罗臻', 'A2', '完成'],
    ['2024-05-20', '2024-06-05', '详细设计', '吴明森', 'A2', '完成']
  ]},
  { ph: '实现', rows: [
    ['2024-06-06', '2024-06-28', '编码实现', '吴明森', '—', '完成'],
    ['2024-06-15', '2024-07-05', '单元测试', '罗臻', '—', '完成']
  ]},
  { ph: '测试', rows: [
    ['2024-07-06', '2024-07-25', '软件测试', '谢柯薪', 'A32', '完成'],
    ['2024-07-20', '2024-08-02', '配置项测试', '谢柯薪', 'A83', '完成']
  ]},
  { ph: '结项', rows: [
    ['2024-08-03', '2024-08-09', '研制总结与入库', '辛峥峰', 'A19', '完成']
  ]}
];

// 利益相关方（13 活动 × 16 角色矩阵，√=参与）
var PP_STAKE_ACTS = ['立项', '策划', '需求', '设计', '实现', '测试', '评审', '配置', '测量', '质保', '风险', '培训', '结项'];
var PP_STAKE_ROLES = ['项目负责人', '软件负责人', '需求', '设计', '实现', '测试', 'CM', 'QA', 'EPG', 'CCB', '配置管理员', '评审组', '培训', '质保组', '客户经理', '高层'];
// 参与标记：用 role 索引集合表示每项活动参与的角色
var PP_STAKE_MATRIX = {
  '立项': [0, 1, 8, 9, 13, 15], '策划': [0, 1, 2, 7, 8, 9],
  '需求': [1, 2, 7, 11], '设计': [1, 3, 7, 11], '实现': [1, 4, 7, 11],
  '测试': [1, 5, 6, 7, 11], '评审': [1, 7, 9, 11, 12], '配置': [1, 6, 10],
  '测量': [1, 7, 8], '质保': [1, 7, 14], '风险': [0, 1, 9], '培训': [1, 12, 10], '结项': [0, 1, 6, 7, 9, 15]
};
// 角色真实姓名（R105 名册）
var PP_STAKE_NAMES = ['孙超', '辛峥峰', '马慧芳', '罗臻', '吴明森', '谢柯薪', '张莉', '杜晟', '许宏刚', '廖建英', '张星竹', '评审组', '培训专员', '质保组', '客户经理', '高层'];

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
  h += '<div class="page-sub"><span class="tag">项目：R105（K409）飞管软件</span></div>';
  h += ppPhaseBar();
  h += ppNodeActions();
  h += ppTabBar();
  h += '<div class="node-body" id="pp-body">' + ppTabContent() + '</div>';
  h += '</div>';
  return h;
}

// 节点级操作栏（1:1 还原 ppNodeActions）
function ppNodeActions() {
  const mods = [{ no: 'A10', nm: '估算收敛' }, { no: 'A11', nm: '风险资源' }, { no: 'A14', nm: '利益相关方' }];
  const btns = mods.map(function (m) {
    return '<button class="btn ghost sm" onclick="ppSvnCommit(\'' + m.no + '\')">⬆ ' + m.nm + '</button>';
  }).join('');
  return '<div class="node-actions"><div class="na-row">' +
    '<button class="btn primary" onclick="ppSyncAll()">⬆ 一键提交所有策划数据到 SVN</button>' +
    '<span class="na-sep">按模块同步：</span>' + btns + '</div></div>';
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
  const cards = [
    { t: '估算收敛', d: '规模 1.02 KLOC · 工作量 943 人时 · 工期 128 天', st: 'ok', sv: '已对齐' },
    { t: '风险与资源', d: '风险 4 项（已关闭）· 硬件 6 · 软件 6', st: 'ok', sv: '已对齐' },
    { t: '文档规模', d: '19 类文档 · 合计 293 页', st: 'info', sv: '可取数' },
    { t: '利益相关方', d: '16 角色 × 13 活动参与矩阵', st: 'info', sv: '可取数' }
  ];
  let h = '<div class="stats">';
  cards.forEach(function (c) {
    h += '<div class="stat"><div class="v">' + c.t + '</div><div class="k">' + c.d + '</div>' +
      '<div class="sub"><span class="tag ' + c.st + '">' + c.sv + '</span></div></div>';
  });
  h += '</div>';
  h += '<div class="panel"><h3><span class="bar"></span>生成《软件开发计划》</h3>' +
    '<div class="note">由估算收敛 / 风险资源 / 文档规模 / 利益相关方 自动汇总生成 A3《软件开发计划》，并同步 SVN 受控库。</div>' +
    '<div class="row"><button class="btn primary" onclick="ppSyncAll()">⬆ 一键生成并同步 SVN</button></div></div>';
  return h;
}

// 软件估算与收敛（Delphi 3 轮）
function ppEstPanel() {
  let h = '<div class="panel"><h3><span class="bar"></span>软件估算与收敛（Delphi 法 3 轮）</h3>';
  h += '<div class="rt-tabs"><span class="rt-tab on">第 1 轮</span><span class="rt-tab">第 2 轮</span><span class="rt-tab">第 3 轮（收敛）</span></div>';
  h += '<div style="overflow-x:auto;"><table class="tbl"><thead><tr>' +
    '<th>配置项</th><th>估算单元</th>' + PP_EST_EXPERTS.map(function (e) { return '<th>' + e + '</th>'; }).join('') +
    '<th>偏差</th><th>本轮平均</th><th>相对偏差</th><th>状态</th><th>最终值</th></tr></thead><tbody>';
  PP_EST_ITEMS.forEach(function (it) {
    h += '<tr><td>' + it.cfg + '</td><td>' + it.unit + '</td>' +
      it.e.map(function (v) { return '<td>' + v + '</td>'; }).join('') +
      '<td>' + it.dev + '</td><td>' + it.avg + '</td><td>' + it.rel + '</td>' +
      '<td><span class="tag info">' + it.st + '</span></td><td><b>' + it.final + '</b></td></tr>';
  });
  h += '</tbody></table></div>';
  h += '<div class="note">规模 1.02 KLOC（触摸屏 505 + 主控板 516 行代码），3 轮收敛后偏差 &lt; 15%，符合 GJB5000B 估算要求。</div></div>';
  return h;
}

// 风险与资源（A11 风险 + 硬件 + 软件）
function ppRiskTab() {
  let h = '';
  // A11 风险
  h += '<div class="panel"><h3><span class="bar"></span>A11 软件风险管理表</h3><div style="overflow-x:auto;"><table class="tbl"><thead><tr>' +
    '<th>编号</th><th>风险描述</th><th>等级</th><th>责任人</th><th>应对措施</th><th>关闭日期</th><th>状态</th></tr></thead><tbody>';
  PP_RISKS.forEach(function (r) {
    h += '<tr><td>' + r.id + '</td><td style="text-align:left">' + r.desc + '</td><td><span class="tag ' +
      (r.lv === '高' ? 'danger' : (r.lv === '中' ? 'warn' : 'info')) + '">' + r.lv + '</span></td><td>' + r.owner +
      '</td><td style="text-align:left">' + r.measure + '</td><td>' + r.close + '</td><td><span class="tag ok">' + r.st + '</span></td></tr>';
  });
  h += '</tbody></table></div></div>';
  // 硬件资源
  h += '<div class="panel"><h3><span class="bar"></span>硬件资源（A79 项目资源跟踪表）</h3><div style="overflow-x:auto;"><table class="tbl"><thead><tr>' +
    '<th>名称</th><th>规格</th><th>用途</th><th>责任人</th></tr></thead><tbody>';
  PP_HW_RES.forEach(function (r) {
    h += '<tr><td>' + r.nm + '</td><td>' + r.spec + '</td><td style="text-align:left">' + r.use + '</td><td>' + r.owner + '</td></tr>';
  });
  h += '</tbody></table></div></div>';
  // 软件资源
  h += '<div class="panel"><h3><span class="bar"></span>软件资源（A79 项目资源跟踪表）</h3><div style="overflow-x:auto;"><table class="tbl"><thead><tr>' +
    '<th>名称</th><th>版本</th><th>用途</th><th>责任人</th></tr></thead><tbody>';
  PP_SW_RES.forEach(function (r) {
    h += '<tr><td>' + r.nm + '</td><td>' + r.spec + '</td><td style="text-align:left">' + r.use + '</td><td>' + r.owner + '</td></tr>';
  });
  h += '</tbody></table></div></div>';
  return h;
}

// 文档规模估算
function ppDocScale() {
  let total = 0;
  PP_DOC_SCALE.forEach(function (r) { total += r[2]; });
  let h = '<div class="panel"><h3><span class="bar"></span>文档规模估算（共 ' + PP_DOC_SCALE.length + ' 类 · 合计 ' + total + ' 页）</h3>' +
    '<div style="overflow-x:auto;"><table class="tbl"><thead><tr><th>编号</th><th>文档名称</th><th>页数</th></tr></thead><tbody>';
  PP_DOC_SCALE.forEach(function (r) {
    h += '<tr><td><span class="ver-badge">' + r[0] + '</span></td><td style="text-align:left">' + r[1] + '</td><td>' + r[2] + '</td></tr>';
  });
  h += '</tbody></table></div></div>';
  return h;
}

// 进度表（6 阶段分组）
function ppSchedTab() {
  let h = '<div class="panel"><h3><span class="bar"></span>A16 软件进度表（R105 · 2024）</h3>';
  PP_SCHED.forEach(function (g) {
    h += '<div class="phase-h">' + g.ph + '阶段</div>';
    h += '<div style="overflow-x:auto;"><table class="tbl"><thead><tr><th>开始</th><th>结束</th><th>任务</th><th>责任人</th><th>产出</th><th>状态</th></tr></thead><tbody>';
    g.rows.forEach(function (r) {
      h += '<tr><td>' + r[0] + '</td><td>' + r[1] + '</td><td style="text-align:left">' + r[2] + '</td><td>' + r[3] +
        '</td><td><span class="ver-badge">' + r[4] + '</span></td><td><span class="tag ok">' + r[5] + '</span></td></tr>';
    });
    h += '</tbody></table></div>';
  });
  h += '</div>';
  return h;
}

// 利益相关方（矩阵）
function ppStakeTab() {
  let h = '<div class="panel"><h3><span class="bar"></span>A14 利益相关方参与表</h3>';
  h += '<div style="overflow-x:auto;"><table class="tbl" style="min-width:1100px;"><thead><tr><th>活动＼角色</th>' +
    PP_STAKE_ROLES.map(function (r) { return '<th>' + r + '</th>'; }).join('') + '</tr></thead><tbody>';
  PP_STAKE_ACTS.forEach(function (act) {
    const set = PP_STAKE_MATRIX[act] || [];
    h += '<tr><td style="text-align:left;font-weight:600;">' + act + '</td>';
    PP_STAKE_ROLES.forEach(function (role, ri) {
      const on = set.indexOf(ri) >= 0;
      h += '<td>' + (on ? '<span class="mark plan">√</span>' : '<span class="mark none">·</span>') + '</td>';
    });
    h += '</tr>';
  });
  h += '</tbody></table></div>';
  h += '<div class="note">角色真实姓名：' + PP_STAKE_NAMES.join('、') + '</div></div>';
  return h;
}

/* 操作栏按钮（占位） */
function ppSyncAll() { alert('已将策划数据同步至 SVN（R105 受控库，示例）'); }
function ppSvnCommit(no) { alert('已同步模块 ' + no + ' 到 SVN（示例）'); }
