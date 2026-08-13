// 作者：袁燕
// 功能：系统设置页（sys）。1:1 还原效果图：SVN 文库配置 / 角色与权限 / R 校验规则 / 提交日志预设 / 同步机制 / 受控审核 / 操作日志查询。
// 设计：原型对标用前端静态真实数据；后期接后端 /api/config / /api/logs 时替换加载逻辑。

// 角色权限矩阵（PEOPLE × 权限项）
var SYS_ROLES = ['管理员', '策划员', '监控员', '质量保证', '配置管理', '普通用户'];
var SYS_PERMS = ['需求查看', '策划编辑', '监控查看', '风险编辑', '模板配置', '告警处理', '配置管理', '用户管理'];
var SYS_ROLE_PERMS = {
  '管理员': [1, 1, 1, 1, 1, 1, 1, 1],
  '策划员': [1, 1, 0, 1, 0, 0, 0, 0],
  '监控员': [1, 0, 1, 0, 0, 1, 0, 0],
  '质量保证': [1, 0, 1, 0, 0, 1, 0, 0],
  '配置管理': [0, 0, 0, 0, 1, 0, 1, 0],
  '普通用户': [1, 0, 0, 0, 0, 0, 0, 0]
};

// R 校验规则（19 条校核规则，节选）
var SYS_R_RULES = [
  'R01 文档编号须符合 A 类编号规则', 'R02 模板版次须为受控最新版', 'R03 需求编号须来自 A1 需求跟踪矩阵',
  'R04 风险等级须含关闭日期', 'R05 进度日期须为 2024 项目周期', 'R06 规模单位须为 KLOC 且数值合理',
  'R07 工作量单位须为人时', 'R08 缺陷密度须低于基准', 'R09 测试覆盖率须 ≥ 90%',
  'R10 配置项须纳入受控库', 'R11 里程碑须有评审结论', 'R12 不符合项须有关闭记录',
  'R13 人员须来自项目名册', 'R14 引用依据须为公司体系文件', 'R15 取数来源须已配置',
  'R16 双向追溯须闭环', 'R17 报表须含 SVN 版本', 'R18 权限须符合 RBAC', 'R19 结项须通过定型测评'
];

// 操作日志
var OPER_LOG = [
  { t: '2024-06-20 09:10', user: '马慧芳', mod: '需求管理', act: '新增需求', detail: 'OR-018 触摸屏初始化' },
  { t: '2024-06-19 17:05', user: '辛峥峰', mod: '项目监控', act: '提交阶段报告', detail: 'A17 设计实现阶段' },
  { t: '2024-06-18 14:20', user: '张星竹', mod: '配置管理', act: '入库', detail: 'A83 配置管理报告 r1180' },
  { t: '2024-06-17 10:08', user: '杜晟', mod: '质量保证', act: '开不符合项', detail: 'A26 审计依据不符' },
  { t: '2024-06-16 16:45', user: '吴明森', mod: '项目策划', act: '更新风险', detail: 'A11 RK-02 关闭' }
];

function sysRender() {
  const c = document.getElementById('content');
  let h = '<div class="page"><div class="page-title">系统设置</div><div class="page-sub">SVN 三库 · RBAC 角色权限 · R 校验规则 · 操作日志</div>';
  h += '<div class="stats">' +
    '<div class="stat"><div class="ic" style="background:#e6f0ff">📊</div><div class="lbl">组织测量库</div><div class="num">21</div><div class="sub">指标项</div></div>' +
    '<div class="stat"><div class="ic" style="background:#f3e8ff">🧩</div><div class="lbl">过程资产库</div><div class="num">38</div><div class="sub">模板/CBB/经验</div></div>' +
    '<div class="stat"><div class="ic" style="background:#f6ffed">🔄</div><div class="lbl">本月回流</div><div class="num">12</div><div class="sub">EPG 回流</div></div>' +
    '<div class="stat"><div class="ic" style="background:#fff1f0">⏳</div><div class="lbl">待回流</div><div class="num">2</div><div class="sub">结项/受控</div></div>' +
    '</div>';

  // SVN 文库配置
  h += '<div class="panel"><h3><span class="bar"></span>SVN 文库配置</h3><div class="frow"><span class="fn">开发库</span><span>svn://pdm.chengfei.com/R105/dev</span></div>' +
    '<div class="frow"><span class="fn">受控库</span><span>svn://pdm.chengfei.com/R105/ctrl</span></div>' +
    '<div class="frow"><span class="fn">产品库</span><span>svn://pdm.chengfei.com/R105/prod</span></div></div>';

  // 角色与权限矩阵
  h += '<div class="panel"><h3><span class="bar"></span>角色与权限（RBAC）</h3><div style="overflow-x:auto;"><table class="tbl"><thead><tr><th>角色＼权限</th>' +
    SYS_PERMS.map(p => '<th>' + p + '</th>').join('') + '</tr></thead><tbody>';
  SYS_ROLES.forEach(function (role) {
    const perms = SYS_ROLE_PERMS[role] || [];
    h += '<tr><td style="text-align:left;font-weight:600;">' + role + '</td>' +
      perms.map(v => '<td>' + (v ? '✓' : '—') + '</td>').join('') + '</tr>';
  });
  h += '</tbody></table></div></div>';

  // R 校验规则
  h += '<div class="panel"><h3><span class="bar"></span>R 校验规则（' + SYS_R_RULES.length + ' 条）</h3><div class="note">文档生成与取数时自动校核，确保符合 GJB5000B 与公司体系。</div><div style="display:flex;flex-wrap:wrap;gap:8px;">' +
    SYS_R_RULES.map(r => '<span class="chip">' + r + '</span>').join('') + '</div></div>';

  // 提交日志预设
  h += '<div class="panel"><h3><span class="bar"></span>提交日志预设</h3><div class="frow"><span class="fn">默认模板</span><span>[阶段] [文档编号] [摘要]</span></div>' +
    '<div class="frow"><span class="fn">示例</span><span>设计实现 A17 阶段报告 提交受控</span></div></div>';

  // 同步机制
  h += '<div class="panel"><h3><span class="bar"></span>同步机制</h3><div class="frow"><span class="fn">数据库</span><span>MySQL gjb5000b（主）</span></div>' +
    '<div class="frow"><span class="fn">组织测量库</span><span>定时回流（每日 02:00）</span></div>' +
    '<div class="frow"><span class="fn">组织过程资产库</span><span>EPG 审核后回流</span></div></div>';

  // 受控/审核设置
  h += '<div class="panel"><h3><span class="bar"></span>受控与审核设置</h3><div class="frow"><span class="fn">基线策略</span><span>阶段里程碑自动建基线</span></div>' +
    '<div class="frow"><span class="fn">变更审批</span><span>CCB（许宏刚）审批</span></div>' +
    '<div class="frow"><span class="fn">审计依据</span><span>Q/CEC R02.08（体系合规）</span></div></div>';

  // 操作日志查询
  h += '<div class="panel"><h3><span class="bar"></span>操作日志查询</h3><div style="overflow-x:auto;"><table class="tbl"><thead><tr>' +
    '<th>时间</th><th>用户</th><th>模块</th><th>动作</th><th>详情</th></tr></thead><tbody>';
  OPER_LOG.forEach(function (l) {
    h += '<tr><td style="white-space:nowrap;">' + l.t + '</td><td>' + l.user + '</td><td>' + l.mod + '</td><td>' + l.act + '</td><td style="text-align:left">' + l.detail + '</td></tr>';
  });
  h += '</tbody></table></div></div>';

  h += '</div>';
  c.innerHTML = h;
}
