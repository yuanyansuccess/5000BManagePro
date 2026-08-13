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
  { id: 'sys', ic: '⚙️', t: '系统设置' }
];

const SHELL_TITLES = {
  pp: '项目策划 PP', pmc: '项目监控 PMC', alert: '告警日志', tpl: '模板中心',
  base: '基础数据', user: '用户管理', sys: '系统设置'
};

// 项目列表（对标效果图 PROJECTS：含 R105 真实项目）。所有页 topbar 共享渲染。
const SHELL_PROJECTS = [
  { code: 'R105', code2: 'K409', nm: '飞管软件', phase: 'V3.01 编码/测试阶段' },
  { code: 'B-9439-447', code2: 'K410', nm: '飞管软件', phase: 'V2.00 策划阶段' },
  { code: 'B-3167-40', code2: 'K411', nm: '火控软件', phase: 'V1.00 需求阶段' }
];
let SHELL_CUR_PROJ = 0;

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
  // 当前项目栏（1:1 还原效果图 renderProjBar 结构）
  const projbar = document.getElementById('projbar');
  if (projbar) {
    const p = SHELL_PROJECTS[SHELL_CUR_PROJ];
    if (p) {
      projbar.innerHTML =
        '<span class="pl">当前项目</span>' +
        '<span class="pn">' + p.code + (p.code2 ? '（' + p.code2 + '）' : '') + ' ' + p.nm + '</span>' +
        '<span class="pd">' + p.phase + '</span>' +
        '<button class="btn-mini" onclick="alert(\'切换项目功能待接入\')">切换项目</button>' +
        '<button class="btn-mini" onclick="alert(\'新建项目功能待接入\')">+ 新建项目</button>';
    }
  }
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
      location.href = 'pages/pp.html';
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
