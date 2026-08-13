// 作者：袁燕
// 功能：基础数据配置中心（base）。1:1 还原效果图：风险/硬件/软件/配置项 四类字典池（多选 chips，用户尽可能选、少写）。
// 设计：原型对标用前端静态真实数据；后期接后端 /api/base 时替换 baseGet 即可。

// 风险字典池（可选项）
var BASE_RISK_POOL = ['人员流动', '测试环境延迟', '需求变更频繁', '计划粒度粗', '技术难点', '供应链风险', '外协质量', '进度压缩'];
// 硬件资源池
var BASE_HW = [
  { nm: '工业控制计算机', spec: 'i5/8G/256G', use: '软件加载与调试', owner: '吴明森' },
  { nm: 'RS232 通信卡', spec: 'PCIe', use: '串口通信测试', owner: '吴明森' },
  { nm: '数字万用表', spec: '6.5 位', use: '信号测量', owner: '罗臻' },
  { nm: '信号模拟器', spec: '多通道', use: '离散量模拟', owner: '罗臻' },
  { nm: '通用计算机', spec: 'i7/16G', use: '编码与文档', owner: '马慧芳' },
  { nm: '仿真器', spec: 'JTAG', use: '在线调试', owner: '吴明森' }
];
// 软件资源池
var BASE_SW = [
  { nm: 'Keil 4', spec: 'C51/ARM', use: '嵌入式编译', owner: '吴明森' },
  { nm: 'Office 2007', spec: 'Word/Excel', use: '文档编制', owner: '马慧芳' },
  { nm: 'SourceInsight 4.0', spec: '4.0', use: '代码阅读', owner: '罗臻' },
  { nm: 'DGUS', spec: 'V7', use: '触摸屏组态', owner: '马慧芳' },
  { nm: 'Windows 7', spec: 'SP1', use: '开发宿主', owner: '马慧芳' },
  { nm: '串口助手', spec: 'V4', use: '串口联调', owner: '吴明森' }
];
// 软件配置项
var BASE_CI = [
  { nm: '触摸屏控制软件', ver: 'V3.01', owner: '辛峥峰', st: '受控' },
  { nm: '主控板控制软件', ver: 'V3.01', owner: '辛峥峰', st: '受控' },
  { nm: '通信协议动态库', ver: 'V1.20', owner: '吴明森', st: '受控' },
  { nm: '自检模块', ver: 'V2.00', owner: '罗臻', st: '受控' }
];

// 已选状态（字典池选中项）
var BASE_SEL = { risk: ['人员流动', '测试环境延迟', '需求变更频繁', '计划粒度粗'], hw: [], sw: [], ci: [] };

function baseRender() {
  const c = document.getElementById('content');
  c.innerHTML = '<div class="page"><div class="page-title">基础数据配置中心</div>' +
    '<div class="page-sub">统一数据源 · 需求/风险/相关方集中维护（各过程域从此取数）· 用户尽可能选、少写</div>' +
    '<div class="panel"><h3><span class="bar"></span>风险项字典池（A11）</h3>' +
    '<div class="note">从预置字典池勾选本项目风险类别，不重复手填。</div>' +
    '<div class="chips" id="baseRiskChips"></div></div>' +
    '<div class="panel"><h3><span class="bar"></span>硬件资源（A79）</h3><div style="overflow-x:auto;"><table class="tbl"><thead><tr>' +
    '<th>名称</th><th>规格</th><th>用途</th><th>责任人</th></tr></thead><tbody>' +
    BASE_HW.map(r => '<tr><td>' + r.nm + '</td><td>' + r.spec + '</td><td style="text-align:left">' + r.use + '</td><td>' + r.owner + '</td></tr>').join('') +
    '</tbody></table></div></div>' +
    '<div class="panel"><h3><span class="bar"></span>软件资源（A79）</h3><div style="overflow-x:auto;"><table class="tbl"><thead><tr>' +
    '<th>名称</th><th>版本</th><th>用途</th><th>责任人</th></tr></thead><tbody>' +
    BASE_SW.map(r => '<tr><td>' + r.nm + '</td><td>' + r.spec + '</td><td style="text-align:left">' + r.use + '</td><td>' + r.owner + '</td></tr>').join('') +
    '</tbody></table></div></div>' +
    '<div class="panel"><h3><span class="bar"></span>软件配置项</h3><div style="overflow-x:auto;"><table class="tbl"><thead><tr>' +
    '<th>配置项</th><th>版本</th><th>责任人</th><th>状态</th></tr></thead><tbody>' +
    BASE_CI.map(r => '<tr><td style="text-align:left">' + r.nm + '</td><td><span class="ver-badge">' + r.ver + '</span></td><td>' + r.owner + '</td><td><span class="tag ok">' + r.st + '</span></td></tr>').join('') +
    '</tbody></table></div></div>' +
    '</div>';
  baseRenderChips();
}

function baseRenderChips() {
  const box = document.getElementById('baseRiskChips');
  if (!box) return;
  box.innerHTML = BASE_RISK_POOL.map(function (r) {
    const on = BASE_SEL.risk.indexOf(r) >= 0;
    return '<span class="chip' + (on ? ' on' : '') + '" onclick="baseToggleRisk(\'' + r + '\')">' + r + '</span>';
  }).join('');
}

function baseToggleRisk(r) {
  const i = BASE_SEL.risk.indexOf(r);
  if (i >= 0) BASE_SEL.risk.splice(i, 1); else BASE_SEL.risk.push(r);
  baseRenderChips();
}
