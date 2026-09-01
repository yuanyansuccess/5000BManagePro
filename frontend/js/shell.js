// 作者：袁燕
// 功能：公共壳（所有子页面共享）。渲染 topbar + sidebar 菜单，菜单点击跳转对应 html。
// 设计原则（继承袁总解耦要求）：
//   1. 每个子页面是独立 html（frontend/pages/<id>.html），引本壳 + 各自 css/js
//   2. 菜单跳转用 location.href，每个页自包含，维护互不干扰
//   3. 登录态用 sessionStorage 简单校验（后期接后端鉴权）

// 菜单：分组 + 主节点（PP/PMC）。与效果图一致。
const SHELL_MENU = [
  { grp: '核心节点' },
  { id: 'pp', ic: '📅', t: '项目策划', main: true },
  { id: 'pmc', ic: '📈', t: '项目监控', main: true },
  { grp: '基础数据与预警' },
  { id: 'alert', ic: '🔔', t: '告警日志' },
  { id: 'base', ic: '🧱', t: '基础数据' },
  { grp: '系统' },
  { id: 'user', ic: '👤', t: '用户管理' },
  { id: 'tpl', ic: '📄', t: '模板中心' },
  { id: 'settings', ic: '⚙️', t: '系统设置' }
];

const SHELL_TITLES = {
  pp: '项目策划 PP', pmc: '项目监控 PMC', alert: '告警日志', tpl: '模板中心',
  base: '基础数据', user: '用户管理', sys: '系统设置'
};

// 当前项目名（单一数据源：后端 /api/projects/current 的 projectName；未加载时回退项目代号）
function shellCurProjName() {
  return (window.__curProj && window.__curProj.projectName) || Api.curProjectId() || '';
}

// 新建项目：复用修改项目弹窗（含软件代号 Rxxx 等全部字段，袁总要求）
function shellNewProj() {
  settingsAddProj();  // 不传 editPid = 新建模式（含"项目代号"输入框）
}

// 切换项目：弹窗列出全部项目，点击即设为当前项目
function shellSwitchProjDialog() {
  Api.listProjects().then(function (r) {
    var list = (r && r.data) || [];
    var cur = Api.curProjectId();
    var rows = list.map(function (p) {
      var pid = p.project_id || p.projectId || '';
      var nm = p.project_name || p.projectName || '';
      var on = (pid === cur);
      return '<tr' + (on ? ' style="background:#eef3ff;"' : '') + '>' +
        '<td><b>' + pid + '</b></td><td>' + nm + '</td>' +
        '<td style="text-align:right;">' +
        (on ? '<span class="tag">当前项目</span>'
            : '<button class="btn primary sm" onclick="shellSwitchTo(\'' + pid + '\')">切换到此项目</button>') +
        '</td></tr>';
    }).join('');
    var html = '<div class="modal-mask" onclick="if(event.target===this)this.remove()">' +
      '<div class="modal"><div class="modal-hd">切换项目</div><div class="modal-bd">' +
      '<div style="overflow-x:auto;"><table class="tbl"><thead><tr><th>项目代号</th><th>项目名称</th><th style="text-align:right;">操作</th></tr></thead>' +
      '<tbody>' + (rows || '<tr><td colspan="3" style="text-align:center;color:#999;">暂无项目</td></tr>') + '</tbody></table></div>' +
      '</div><div class="modal-ft"><button class="btn ghost" onclick="this.closest(\'.modal-mask\').remove()">关闭</button></div></div></div>';
    document.body.insertAdjacentHTML('beforeend', html);
  }).catch(function (e) { alert('加载项目列表失败：' + (e.message || e)); });
}

// 执行切换：设为当前项目后刷新页面
function shellSwitchTo(pid) {
  Api.setCurrentProject(pid).then(function () {
    return Api.loadCurrentProject();
  }).then(function () {
    var m = document.querySelector('.modal-mask');
    if (m) m.remove();
    location.reload();
  }).catch(function (e) { alert('切换失败：' + (e.message || e)); });
}

/** toast 全局提示（跨页面通用：顶部居中浮层，2.5s 自动消失） */
function toast(msg) {
  var el = document.getElementById('toast');
  if (!el) {
    el = document.createElement('div');
    el.id = 'toast';
    el.style.cssText = 'position:fixed;top:16px;left:50%;transform:translateX(-50%);background:#333;color:#fff;padding:10px 24px;border-radius:8px;z-index:9999;font-size:16px;pointer-events:none;opacity:0;transition:opacity .3s';
    document.body.appendChild(el);
  }
  el.textContent = msg;
  el.style.opacity = '1';
  clearTimeout(el._tid);
  el._tid = setTimeout(function () { el.style.opacity = '0'; }, 2500);
}

// 当前页面 id（由各子页面 html 在 body 上 data-page 属性声明）
function shellCurrentId() {
  const el = document.body;
  return el ? el.getAttribute('data-page') : '';
}

// 渲染壳（topbar + sidebar），各子页面 onload 调用
function shellRender() {
  // 简单登录校验：未登录跳回首页
  if (!sessionStorage.getItem('logged') && !window.__NO_AUTH__) {
    // 允许本地预览无登录态直接进入，避免阻塞；生产接后端后强制
  }
  const cur = shellCurrentId();
  // topbar
  const topbrand = document.getElementById('topbrand');
  if (topbrand) topbrand.innerHTML = cfLogo(26) + ' GJB5000B 平台';
  const crumb = document.getElementById('crumb');
  if (crumb) crumb.textContent = SHELL_TITLES[cur] || cur;
  // 当前项目栏（接后端项目配置）
  const projbar = document.getElementById('projbar');
  if (projbar) {
    var curPid = Api.curProjectId();
    projbar.innerHTML =
      '<span class="pl">当前项目</span>' +
      '<span class="pn">' + curPid + ' ' + shellCurProjName() + '</span>' +
      '<button class="btn-mini" onclick="settingsAddProj(\'' + curPid + '\')">修改项目</button>' +
      '<button class="btn-mini" onclick="shellNewProj()">＋ 新建项目</button>' +
      '<button class="btn-mini" onclick="shellSwitchProjDialog()">⇄ 切换项目</button>';
  }
  // 侧栏底部项目名（各页统一由壳更新，杜绝页面各自硬编码）
  var sp = document.getElementById('sidebar-proj');
  if (sp) sp.textContent = Api.curProjectId() + ' ' + shellCurProjName();
  // 右上角头像（取登录用户名首字）+ 注销按钮
  const me = document.getElementById('me');
  if (me) {
    const u = sessionStorage.getItem('uname') || '辛';
    me.textContent = u.charAt(0);
    me.insertAdjacentHTML('afterend', '<span class="logout-btn" onclick="shellLogout()" title="注销登录">注销</span>');
  }
  // sidebar 菜单
  const menu = document.getElementById('menu');
  if (menu) {
    let h = '';
    SHELL_MENU.forEach(function (m) {
      if (m.grp) {
        h += '<div class="grp">' + m.grp + '</div>';
      } else {
        const on = (m.id === cur) ? ' on' : '';
        h += '<div class="it' + (m.main ? ' main' : '') + on + '" data-id="' + m.id + '" onclick="shellGo(\'' + m.id + '\')">' +
          '<span class="ic">' + m.ic + '</span>' + m.t + '</div>';
      }
    });
    menu.innerHTML = h;
  }
}

// 菜单跳转
function shellGo(id) {
  if (id === shellCurrentId()) return;
  location.href = id + '.html';
}

// 注销登录：清除 sessionStorage 回登录页
function shellLogout() {
  sessionStorage.clear();
  location.href = '../index.html';
}

// 登录（在 index.html 调用）—— 调后端 /api/users/login 校验
async function shellEnter() {
  var uEl = document.getElementById('username');
  var pEl = document.getElementById('password');
  var btn = document.querySelector('.btn-p');
  var account = uEl ? uEl.value.trim() : '';
  var password = pEl ? pEl.value : '';
  if (!account || !password) {
    _loginMsg('请输入用户名和密码');
    return;
  }
  if (btn) { btn.disabled = true; btn.textContent = '登录中…'; }
  try {
    var resp = await Api.login(account, password);
    // LoginResponse: { success, message, token, user: { userId, name, account, role, ... } }
    if (resp.success) {
      sessionStorage.setItem('logged', '1');
      sessionStorage.setItem('uname', resp.user.name);
      sessionStorage.setItem('token', resp.token);
      Api.loadCurrentProject().then(function () { location.href = 'pages/pp.html'; });
    } else {
      _loginMsg(resp.message || '账号或密码错误');
    }
  } catch (err) {
    _loginMsg(err.message || '网络异常，请确认后端已启动');
  }
  if (btn) { btn.disabled = false; btn.textContent = '登 录 系 统'; };
}

function _loginMsg(text) {
  var el = document.getElementById('login-msg');
  if (!el) return;
  el.textContent = text;
  el.style.display = 'block';
  el.style.color = '#e74c3c';
}

// 公共弹窗（所有页共用，对标效果图 showMask/closeMask）
function showMask(html) {
  const m = document.getElementById('mask');
  if (!m) return;
  m.innerHTML = '<div class="modal">' + html + '</div>';
  m.classList.add('on');
}
function closeMask() {
  const m = document.getElementById('mask');
  if (!m) return;
  m.classList.remove('on');
  m.innerHTML = '';
}

// ===== 项目配置（跨页面公共，袁总要求放到顶栏「修改项目」）=====
// 新建/修改项目：editPid 非空为修改模式（全量字段预填）
function settingsAddProj(editPid) {
  var isEdit = !!editPid;
  // 两列布局：一行放两条信息；日期字段用日历选择器（input type=date）
  var base = '<div class="modal-mask" onclick="if(event.target===this)this.remove()">' +
    '<div class="modal modal-lg"><div class="modal-hd">' + (isEdit ? '修改项目 ' + editPid : '新建项目') + '</div><div class="modal-bd grid2">';
  var head = isEdit ? '' :
    '<div class="field"><label>项目代号（软件编号）*</label><input id="np-id" placeholder="如 R105"></div>';
  var foot = isEdit ? '' :
    '<div class="field span2"><label><input type="checkbox" id="np-cur"> 设为当前项目</label></div>';
  var html = base + head +
    '<div class="field span2"><label>项目名称 *</label><input id="np-name" placeholder="如 终点/轮载开关模拟器驱动软件"></div>' +
    '<div class="field"><label>飞机型号</label><input id="np-model" placeholder="如 K409"></div>' +
    '<div class="field"><label>软件负责人</label><input id="np-owner" placeholder="如 辛峥峰"></div>' +
    '<div class="field"><label>承研单位</label><input id="np-org"></div>' +
    '<div class="field"><label>客户单位</label><input id="np-customer"></div>' +
    '<div class="field"><label>阶段</label><select id="np-phase"><option>方案</option><option>初样</option><option>正样</option><option>定型</option><option>批产</option></select></div>' +
    '<div class="field"><label>软件版本</label><input id="np-swv" placeholder="如 V3.01"></div>' +
    '<div class="field"><label>立项日期（点击选择）</label><input id="np-start" type="date"></div>' +
    '<div class="field"><label>批准日期（点击选择）</label><input id="np-approve" type="date"></div>' +
    '<div class="field"><label>文档编号（留空自动 <代号>-SDP）</label><input id="np-doc"></div>' +
    '<div class="field"><label>IDE 版本</label><input id="np-ide" placeholder="如 Keil 4"></div>' +
    '<div class="field"><label>本机本地路径</label><input id="np-local" placeholder="D:/5000/R105"></div>' +
    '<div class="field"><label>SVN 基路径</label><input id="np-svn" placeholder="R105/trunk"></div>' +
    '<div class="field span2 modal-sub">项目组织角色（注入 7.2.1 人力资源表 / 相关方清单，袁总要求三处一致）</div>' +
    '<div class="field"><label>需求分析人员</label><input id="np-req" placeholder="如 马慧芳"></div>' +
    '<div class="field"><label>软件实现人员</label><input id="np-coder" placeholder="如 吴明森、罗臻"></div>' +
    '<div class="field"><label>测量分析人员</label><input id="np-measure" placeholder="如 张星竹"></div>' +
    '<div class="field"><label>项目负责人</label><input id="np-projlead" placeholder="如 孙超"></div>' +
    '<div class="field"><label>系统工程组</label><input id="np-syseng" placeholder="如 孙超"></div>' +
    '<div class="field span2 modal-sub">签署角色（注入 SDP 签署页，对标 R105）</div>' +
    '<div class="field"><label>CCB（配置控制委员会）</label><input id="np-ccb"></div>' +
    '<div class="field"><label>组织级配置管理者</label><input id="np-orgconfig"></div>' +
    '<div class="field"><label>设计者</label><input id="np-designer"></div>' +
    '<div class="field"><label>测试者</label><input id="np-tester"></div>' +
    '<div class="field"><label>质量保证（SQA）</label><input id="np-qa"></div>' +
    '<div class="field"><label>配置管理者（CM）</label><input id="np-config"></div>' +
    '<div class="field"><label>评审（主审）</label><input id="np-reviewer"></div>' +
    '<div class="field"><label>评审（副审1）</label><input id="np-reviewer2"></div>' +
    '<div class="field"><label>评审（副审2）</label><input id="np-reviewer3"></div>' +
    '<div class="field span2 modal-sub">开发环境与引用文档</div>' +
    '<div class="field"><label>开发工具链名称</label><input id="np-hwide" placeholder="如 Keil 4"></div>' +
    '<div class="field"><label>目标机处理器型号</label><input id="np-hwmcu"></div>' +
    '<div class="field"><label>宿主软件构件名</label><input id="np-swhost"></div>' +
    '<div class="field"><label>IAP 软件构件名</label><input id="np-swiap"></div>' +
    '<div class="field"><label>软件研制任务书编号</label><input id="np-sdtd"></div>' +
    '<div class="field"><label>软件质量保证计划编号</label><input id="np-sqap"></div>' +
    foot +
    '<div id="np-msg" class="span2" style="color:#e74c3c;font-size:13px;min-height:16px;"></div>' +
    '</div><div class="modal-ft">' +
    '<button class="btn ghost" onclick="this.closest(\'.modal-mask\').remove()">取消</button>' +
    '<button class="btn primary" onclick="' + (isEdit ? 'settingsSaveEditProj(\'' + editPid + '\')' : 'settingsSaveNewProj()') + '">' + (isEdit ? '保存' : '创建') + '</button></div></div></div>';
  if (isEdit) {
    Api.getProject(editPid).then(function (r) {
      var x = (r && r.data) || {};
      var s = function (id, key) { var el = document.getElementById(id); if (el && x[key] != null) el.value = x[key]; };
      s('np-name', 'projectName'); s('np-model', 'aircraftModel'); s('np-owner', 'owner');
      s('np-org', 'org'); s('np-phase', 'phase'); s('np-start', 'startDate');
      s('np-approve', 'approveDate'); s('np-customer', 'customerDept'); s('np-ide', 'ideVersion');
      s('np-swv', 'swVersion'); s('np-doc', 'docNumber'); s('np-local', 'localPath');
      s('np-svn', 'svnBasePath'); s('np-ccb', 'ccb'); s('np-designer', 'designer');
      s('np-reviewer', 'reviewer'); s('np-reviewer2', 'reviewer2'); s('np-reviewer3', 'reviewer3');
      s('np-tester', 'tester'); s('np-qa', 'qa'); s('np-config', 'configManager');
      s('np-orgconfig', 'orgConfigManager'); s('np-hwide', 'hwIdeName'); s('np-hwmcu', 'hwMcuModel');
      s('np-swhost', 'swNameHost'); s('np-swiap', 'swNameIap'); s('np-sdtd', 'refSdtdDocNumber');
      s('np-sqap', 'refSqapDocNumber');
      // 项目组织角色（三处一致：前端录入=数据库=生成文档）
      s('np-req', 'requirement'); s('np-coder', 'coder'); s('np-measure', 'measure');
      s('np-projlead', 'projLead'); s('np-syseng', 'sysEng');
    }).catch(function (e) { var m = document.getElementById('np-msg'); if (m) m.textContent = '加载失败：' + (e.message || e); });
  }
  document.body.insertAdjacentHTML('beforeend', html);
}
function settingsSaveNewProj() {
  var pid = document.getElementById('np-id').value.trim();
  var name = document.getElementById('np-name').value.trim();
  var msg = document.getElementById('np-msg');
  if (!pid || !name) { msg.textContent = '项目代号与项目名称必填'; return; }
  var payload = {
    projectId: pid, projectName: name,
    aircraftModel: document.getElementById('np-model').value.trim(),
    owner: document.getElementById('np-owner').value.trim(),
    org: document.getElementById('np-org').value.trim(),
    phase: document.getElementById('np-phase').value,
    startDate: document.getElementById('np-start').value.trim(),
    approveDate: document.getElementById('np-approve').value.trim(),
    customerDept: document.getElementById('np-customer').value.trim(),
    ideVersion: document.getElementById('np-ide').value.trim(),
    swVersion: document.getElementById('np-swv').value.trim() || 'V1.00',
    docNumber: document.getElementById('np-doc').value.trim(),
    localPath: document.getElementById('np-local').value.trim() || ('D:/5000/' + pid),
    svnBasePath: document.getElementById('np-svn').value.trim() || (pid + '/trunk'),
    ccb: document.getElementById('np-ccb').value.trim(),
    designer: document.getElementById('np-designer').value.trim(),
    reviewer: document.getElementById('np-reviewer').value.trim(),
    reviewer2: document.getElementById('np-reviewer2').value.trim(),
    reviewer3: document.getElementById('np-reviewer3').value.trim(),
    tester: document.getElementById('np-tester').value.trim(),
    qa: document.getElementById('np-qa').value.trim(),
    configManager: document.getElementById('np-config').value.trim(),
    orgConfigManager: document.getElementById('np-orgconfig').value.trim(),
    hwIdeName: document.getElementById('np-hwide').value.trim(),
    hwMcuModel: document.getElementById('np-hwmcu').value.trim(),
    swNameHost: document.getElementById('np-swhost').value.trim(),
    swNameIap: document.getElementById('np-swiap').value.trim(),
    refSdtdDocNumber: document.getElementById('np-sdtd').value.trim(),
    refSqapDocNumber: document.getElementById('np-sqap').value.trim(),
    // 项目组织角色（注入 7.2.1 人力资源表 / 相关方清单）
    requirement: document.getElementById('np-req').value.trim(),
    coder: document.getElementById('np-coder').value.trim(),
    measure: document.getElementById('np-measure').value.trim(),
    projLead: document.getElementById('np-projlead').value.trim(),
    sysEng: document.getElementById('np-syseng').value.trim(),
    setCurrent: document.getElementById('np-cur').checked,
  };
  Api.createProject(payload).then(function () {
    if (payload.setCurrent) return Api.setCurrentProject(pid);
  }).then(function () {
    return Api.loadCurrentProject();
  }).then(function () {
    document.querySelector('.modal-mask').remove();
    shellRender();
    if (typeof window.ppRender === 'function' && document.getElementById('pp-body')) ppRender();
    if (typeof window.pmcRender === 'function' && document.getElementById('pmc-body')) pmcRender();
    toast('已创建项目 ' + pid + (payload.setCurrent ? ' 并设为当前' : ''));
  }).catch(function (e) { msg.textContent = '创建失败：' + (e.message || e); });
}
function settingsSaveEditProj(pid) {
  var g = function (id) { return document.getElementById(id).value.trim(); };
  // 只传非空字段，避免预填未返回时误清数据库已有值
  var raw = {
    projectName: g('np-name'), aircraftModel: g('np-model'), owner: g('np-owner'),
    org: g('np-org'), customerDept: g('np-customer'), phase: g('np-phase'),
    startDate: g('np-start'), approveDate: g('np-approve'), ideVersion: g('np-ide'),
    swVersion: g('np-swv'), docNumber: g('np-doc'),
    ccb: g('np-ccb'), designer: g('np-designer'), reviewer: g('np-reviewer'),
    reviewer2: g('np-reviewer2'), reviewer3: g('np-reviewer3'), tester: g('np-tester'),
    qa: g('np-qa'), configManager: g('np-config'), orgConfigManager: g('np-orgconfig'),
    hwIdeName: g('np-hwide'), hwMcuModel: g('np-hwmcu'), swNameHost: g('np-swhost'),
    swNameIap: g('np-swiap'), refSdtdDocNumber: g('np-sdtd'), refSqapDocNumber: g('np-sqap'),
    // 项目组织角色（三处一致：前端=数据库=生成文档）
    requirement: g('np-req'), coder: g('np-coder'), measure: g('np-measure'),
    projLead: g('np-projlead'), sysEng: g('np-syseng'),
  };
  var payload = {};
  Object.keys(raw).forEach(function (k) { if (raw[k] !== '') payload[k] = raw[k]; });
  if (Object.keys(payload).length === 0) { alert('没有需要保存的修改'); return; }
  Api.updateProject(pid, payload).then(function () {
    document.querySelector('.modal-mask').remove();
    // 袁总要求：保存后立即刷新顶栏当前项目名 + 侧栏项目名 + 各子页项目标签（举一反三：新建/切换/删除同样要刷新）
    return Api.loadCurrentProject();
  }).then(function () {
    shellRender();
    if (typeof window.ppRender === 'function' && document.getElementById('pp-body')) ppRender();
    if (typeof window.pmcRender === 'function' && document.getElementById('pmc-body')) pmcRender();
    toast('已更新项目 ' + pid);
  }).catch(function (e) { alert('保存失败：' + (e.message || e)); });
}
