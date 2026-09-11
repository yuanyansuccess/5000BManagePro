// 作者：袁燕
// 功能：用户管理页（user）。模块1 项目人员（卡片）+ 模块2 系统用户（7 列表格·后端 API 实时数据）。
// 2026-08-10 改造：系统用户表格从静态 SYS_USERS 数组改为 GET /api/users 后端取数，增删改全部走 API。

// 角色配色（对标 teamColor）
function teamColor(t) {
  const map = { '软件': '#4da3ff', '测试': '#52c41a', '设计': '#6c5ce7', '配置': '#fa8c16', '质保': '#eb2f96', '管理': '#13c2c2' };
  for (var k in map) if (t.indexOf(k) >= 0) return map[k];
  return '#999';
}

// 模块2：系统用户（从后端 /api/users 加载）
var SYS_USERS = [];
var SYS_USER_ROLES = { admin: '管理员', pp: '策划员', pmc: '监控员', pqa: '质量保证', cm: '配置管理', user: '普通用户' };
var SYS_USER_STATE = { active: '启用', disabled: '禁用' };

/** 从后端加载用户列表，存入 SYS_USERS */
async function userLoad() {
  try {
    var resp = await Api.listUsers();
    // 后端返回 ApiResp { status, data: [...] }，也可能是直接数组
    SYS_USERS = (resp && resp.data) ? resp.data : (Array.isArray(resp) ? resp : []);
  } catch (e) {
    console.error('加载用户列表失败：', e);
    toast('加载用户列表失败：' + e.message);
    SYS_USERS = [];
  }
}

/** 渲染整个用户管理页面 */
async function userRender() {
  await userLoad();
  await memberLoad();
  await orgLoad();
  await ciLoad();
  const c = document.getElementById('content');
  var h = '<div class="page"><div class="page-title">用户管理</div><div class="page-sub">项目人员（' + MEMBERS.length + ' 人，当前项目 ' + Api.curProjectId() + ' ' + shellCurProjName() + '，文档签署角色基础）· 系统用户（' + SYS_USERS.length + ' 人）</div>';
  // 模块1 项目人员表格（按项目维度，可增改删，是文档生成的角色基础）
  h += '<div class="panel"><h3><span class="bar"></span>项目人员（' + MEMBERS.length + '）' +
    '<button class="btn-sm ok" style="float:right;margin-top:-4px" onclick="memberAddDialog()">+ 新增人员</button></h3>' +
    '<div style="overflow-x:auto;"><table class="tbl"><thead><tr>' +
    '<th>姓名</th><th>角色</th><th>所属组</th><th>编号</th><th>技术素质要求</th><th>时段</th><th>投入精力(%)</th><th style="width:150px">操作</th></tr></thead>' +
    '<tbody id="member-tbody"><tr><td colspan="8" style="text-align:center;color:var(--text-3);">加载中…</td></tr></tbody></table></div>' +
    '<div style="color:var(--text-3);font-size:13px;margin-top:8px">说明：姓名/角色为文档签署与「表23 人力资源表」数据来源，生成文档后该表锁定不可编辑。</div></div>';
  // 模块1b 组织机构表（表22，对标 R121 表29，文档生成来源）
  h += '<div class="panel"><h3><span class="bar"></span>组织机构表 / 表22（' + ORG_CHART.length + '）' +
    '<button class="btn-sm ok" style="float:right;margin-top:-4px" onclick="orgAddDialog()">+ 新增机构</button></h3>' +
    '<div style="overflow-x:auto;"><table class="tbl"><thead><tr>' +
    '<th style="width:60px">序号</th><th>组织机构/角色</th><th>人员（代表）</th><th>职责</th><th style="width:150px">操作</th></tr></thead>' +
    '<tbody id="org-tbody"><tr><td colspan="5" style="text-align:center;color:var(--text-3);">加载中…</td></tr></tbody></table></div>' +
    '<div style="color:var(--text-3);font-size:13px;margin-top:8px">说明：对标 R121 表29，生成文档后该表锁定不可编辑。</div></div>';
  // 模块1c 配置项与基线（表13 基线列表 / 表19 配置项）
  h += '<div class="panel"><h3><span class="bar"></span>配置项与基线 / 表13·表19（' + CONFIG_ITEMS.length + ' 项）' +
    '<button class="btn-sm ok" style="float:right;margin-top:-4px" onclick="ciAddDialog()">+ 新增配置项</button></h3>' +
    '<div style="overflow-x:auto;"><table class="tbl"><thead><tr>' +
    '<th>配置项标识</th><th>名称</th><th>基线类别</th><th>基线名称</th><th>基线标识</th><th>状态</th><th style="width:150px">操作</th></tr></thead>' +
    '<tbody id="ci-tbody"><tr><td colspan="7" style="text-align:center;color:var(--text-3);">加载中…</td></tr></tbody></table></div>' +
    '<div style="color:var(--text-3);font-size:13px;margin-top:8px">说明：同一「基线标识」下的多个配置项，生成文档时用顿号「、」连接；生成后该表锁定不可编辑。</div></div>';
  // 模块2 系统用户表格
  h += '<div class="panel"><h3><span class="bar"></span>系统用户（' + SYS_USERS.length + '）' +
    '<button class="btn-sm ok" style="float:right;margin-top:-4px" onclick="userAddDialog()">+ 新增用户</button></h3>' +
    '<div style="overflow-x:auto;"><table class="tbl"><thead><tr>' +
    '<th style="width:48px">头像</th><th>姓名</th><th>账号</th><th>角色</th><th>状态</th><th>权限</th><th style="width:220px">操作</th></tr></thead><tbody>';
  SYS_USERS.forEach(function (u, i) {
    var role = SYS_USER_ROLES[u.role] || u.role;
    var st = u.state === 'active' ? 'ok' : 'danger';
    var stTxt = SYS_USER_STATE[u.state] || u.state;
    var auth = u.authList || '';
    h += '<tr><td><span class="av" style="background:var(--primary)">' + u.name.charAt(0) + '</span></td>' +
      '<td style="font-weight:600">' + u.name + '</td><td>' + u.account + '</td><td><span class="tag">' + role + '</span></td>' +
      '<td><span class="tag ' + st + '">' + stTxt + '</span></td><td style="text-align:left;color:var(--text-3)">' + auth + '</td>' +
      '<td><button class="btn-sm" onclick="userEditDialog(\'' + u.userId + '\')">编辑</button>' +
      '<button class="btn-sm ' + (u.state === 'active' ? '' : 'ok') + '" onclick="userToggle(\'' + u.userId + '\')">' + (u.state === 'active' ? '禁用' : '启用') + '</button>' +
      '<button class="btn-sm danger" onclick="userDel(\'' + u.userId + '\')">删除</button></td></tr>';
  });
  if (SYS_USERS.length === 0) {
    h += '<tr><td colspan="7" style="text-align:center;color:var(--text-3);padding:32px">暂无系统用户，请点击右上角「新增用户」添加</td></tr>';
  }
  h += '</tbody></table></div></div></div>';
  c.innerHTML = h;
  memberRenderRows();
  orgRenderRows();
  ciRenderRows();
}

// ==================== 项目人员 / 组织机构 / 配置项（通用 CRUD 工厂，收敛自手抄五件套）====================

var MEMBERS = [];
var ORG_CHART = [];
var CONFIG_ITEMS = [];

var memberCrud = crudTable({
  key: 'member', tbody: 'member-tbody', colspan: 7,
  empty: '暂无项目人员，点「+ 新增人员」添加',
  api: {
    list: function (pid) { return Api.listMembers(pid); },
    create: function (pid, p) { return Api.createMember(pid, p); },
    update: function (pid, id, p) { return Api.updateMember(pid, id, p); },
    del: function (pid, id) { return Api.deleteMember(pid, id); }
  },
  cols: [
    { f: 'name', w: '80px' }, { f: 'role', w: '100px' },
    { f: 'team', w: '70px', color: teamColor },
    { f: 'no', w: '70px' }, { f: 'skillReq', w: '160px' },
    { f: 'period', w: '120px' }, { f: 'effortPct', w: '70px' }
  ],
  afterChange: function () { return userRender(); },
  notify: 'toast', loadRender: false, failSilent: true,
  confirmDel: '确认删除该项目人员？',
  dialog: {
    title: function () { return '新增项目人员（' + Api.curProjectId() + '）'; },
    layout: 'list', msgId: 'mb-msg',
    fields: [
      { id: 'mb-name', label: '姓名 *' },
      { id: 'mb-role', label: '角色', placeholder: '如 软件负责人/测试/QA' },
      { id: 'mb-team', label: '所属组', placeholder: '软件/测试/设计/配置/质保/管理' },
      { id: 'mb-no', label: '编号' },
      { id: 'mb-svn', label: 'SVN 路径', placeholder: 'svn://pdm/R105/姓名' },
      { id: 'mb-auth', label: '权限/职责' }
    ],
    required: { id: 'mb-name', msg: '姓名必填' },
    payload: function (g, items) {
      return { name: g('mb-name'), role: g('mb-role'), team: g('mb-team'),
        no: g('mb-no'), svn: g('mb-svn'), auth: g('mb-auth'), seq: items.length + 1 };
    },
    successMsg: '已新增项目人员'
  }
});

var orgCrud = crudTable({
  key: 'org', tbody: 'org-tbody', colspan: 5,
  empty: '暂无组织机构，点「+ 新增机构」添加',
  api: {
    list: function (pid) { return Api.listOrgChart(pid); },
    create: function (pid, p) { return Api.createOrgChart(pid, p); },
    update: function (pid, id, p) { return Api.updateOrgChart(pid, id, p); },
    del: function (pid, id) { return Api.deleteOrgChart(pid, id); }
  },
  rowPrepend: function (item, idx) {
    return '<td style="text-align:center;color:var(--text-3)">' + (idx + 1) + '</td>';
  },
  cols: [
    { f: 'orgRole', w: '220px' }, { f: 'representative', w: '120px' }, { f: 'duty', w: '320px' }
  ],
  afterChange: function () { return userRender(); },
  notify: 'toast', loadRender: false, failSilent: true,
  confirmDel: '确认删除该组织机构项？',
  dialog: {
    title: function () { return '新增组织机构（' + Api.curProjectId() + '）'; },
    layout: 'list', msgId: 'og-msg',
    fields: [
      { id: 'og-role', label: '组织机构/角色 *', placeholder: '如 公司配置管理组' },
      { id: 'og-rep', label: '人员（代表）', placeholder: '如 廖建英' },
      { id: 'og-duty', label: '职责' }
    ],
    required: { id: 'og-role', msg: '组织机构/角色必填' },
    payload: function (g, items) {
      return { orgRole: g('og-role'), representative: g('og-rep'), duty: g('og-duty'), seq: items.length + 1 };
    },
    successMsg: '已新增组织机构'
  }
});

var ciCrud = crudTable({
  key: 'ci', tbody: 'ci-tbody', colspan: 7,
  empty: '暂无配置项，点「+ 新增配置项」添加',
  api: {
    list: function (pid) { return Api.listConfigItems(pid); },
    create: function (pid, p) { return Api.createConfigItem(pid, p); },
    update: function (pid, id, p) { return Api.updateConfigItem(pid, id, p); },
    del: function (pid, id) { return Api.deleteConfigItem(pid, id); }
  },
  cols: [
    { f: 'ciId', w: '200px' }, { f: 'name', w: '200px' },
    { f: 'baseline', w: '90px' }, { f: 'baselineName', w: '100px' },
    { f: 'baselineId', w: '160px' }, { f: 'status', w: '70px' }
  ],
  afterChange: function () { return userRender(); },
  notify: 'toast', loadRender: false, failSilent: true,
  confirmDel: '确认删除该配置项？',
  dialog: {
    title: function () { return '新增配置项（' + Api.curProjectId() + '）'; },
    layout: 'list', msgId: 'ci-msg',
    fields: [
      { id: 'ci-id', label: '配置项标识 *', placeholder: '如 R105_SDTD_V1.00.00' },
      { id: 'ci-name', label: '名称', placeholder: '如 R105 软件研制任务书' },
      { id: 'ci-bl', label: '基线类别', placeholder: '功能基线 / 分配基线 / 产品基线' },
      { id: 'ci-blname', label: '基线名称', placeholder: 'R105 / R105_0201 / R105_0202' },
      { id: 'ci-blid', label: '基线标识', placeholder: '如 R105_JG_V1.00（同一标识下多项用顿号连接）' },
      { id: 'ci-status', label: '状态', placeholder: '草稿 / 受控 / 已发布' }
    ],
    required: { id: 'ci-id', msg: '配置项标识必填' },
    payload: function (g) {
      return { ciId: g('ci-id'), name: g('ci-name'), baseline: g('ci-bl'),
        baselineName: g('ci-blname'), baselineId: g('ci-blid'), status: g('ci-status') };
    },
    successMsg: '已新增配置项'
  }
});

/** 加载当前项目人员（GET /api/pp/{pid}/members），同步到模块级 MEMBERS 供页面统计显示 */
async function memberLoad() {
  await memberCrud.load();
  MEMBERS = memberCrud.state.items;
}
function memberRenderRows() { memberCrud.renderRows(); }
async function memberSave(id) { await memberCrud.save(id); }
async function memberDel(id) { await memberCrud.del(id); }
function memberAddDialog() { memberCrud.addDialog(); }
async function memberSaveNew() { await memberCrud.saveNew(); }

/** 加载组织机构表（GET /api/pp/{pid}/org-chart），同步到模块级 ORG_CHART */
async function orgLoad() {
  await orgCrud.load();
  ORG_CHART = orgCrud.state.items;
}
function orgRenderRows() { orgCrud.renderRows(); }
async function orgSave(id) { await orgCrud.save(id); }
async function orgDel(id) { await orgCrud.del(id); }
function orgAddDialog() { orgCrud.addDialog(); }
async function orgSaveNew() { await orgCrud.saveNew(); }

/** 加载配置项（GET /api/pp/{pid}/config-items），同步到模块级 CONFIG_ITEMS */
async function ciLoad() {
  await ciCrud.load();
  CONFIG_ITEMS = ciCrud.state.items;
}
function ciRenderRows() { ciCrud.renderRows(); }
async function ciSave(id) { await ciCrud.save(id); }
async function ciDel(id) { await ciCrud.del(id); }
function ciAddDialog() { ciCrud.addDialog(); }
async function ciSaveNew() { await ciCrud.saveNew(); }

// ==================== 用户操作 ====================

/** 切换启用/禁用状态 */
async function userToggle(userId) {
  var u = findUser(userId);
  if (!u) return;
  var newState = u.state === 'active' ? 'disabled' : 'active';
  try {
    await Api.updateUser(userId, { state: newState });
    toast('用户【' + u.name + '】已' + (newState === 'active' ? '启用' : '禁用'));
    await userRender();
  } catch (e) {
    toast('操作失败：' + e.message);
  }
}

/** 删除用户 */
async function userDel(userId) {
  var u = findUser(userId);
  if (!u) return;
  if (!confirm('确认删除用户【' + u.name + '（' + u.account + '）】？此操作不可撤销。')) return;
  try {
    await Api.deleteUser(userId);
    toast('用户【' + u.name + '】已删除');
    await userRender();
  } catch (e) {
    toast('删除失败：' + e.message);
  }
}

/** 在 SYS_USERS 中按 userId 查找 */
function findUser(userId) {
  for (var j = 0; j < SYS_USERS.length; j++) {
    if (SYS_USERS[j].userId === userId) return SYS_USERS[j];
  }
  return null;
}

// toast 已提升为全局函数（见 shell.js），此处不再重复定义

// ==================== 新增/编辑弹窗 ====================

/** 打开新增用户弹窗 */
function userAddDialog() {
  userFormDialog(null);
}

/** 打开编辑用户弹窗 */
function userEditDialog(userId) {
  var u = findUser(userId);
  if (!u) return;
  userFormDialog(u);
}

/** 通用用户表单弹窗（新增时 user=null，编辑时传入已有用户对象） */
function userFormDialog(user) {
  var isEdit = user !== null;
  var title = isEdit ? '编辑用户' : '新增用户';
  var userId = isEdit ? user.userId : 'U' + Date.now().toString(36).toUpperCase();
  var name = isEdit ? user.name : '';
  var account = isEdit ? user.account : '';
  var role = isEdit ? user.role : 'user';
  var authList = isEdit ? (user.authList || '') : '';
  var password = '';
  var placeholderPwd = isEdit ? '留空不修改密码' : '请输入密码';

  var roleOptions = '';
  for (var rk in SYS_USER_ROLES) {
    roleOptions += '<option value="' + rk + '"' + (role === rk ? ' selected' : '') + '>' + SYS_USER_ROLES[rk] + '</option>';
  }

  var html = '<div class="modal-mask" id="user-form-mask" onclick="closeUserForm()">' +
    '<div class="modal-box" onclick="event.stopPropagation()" style="width:480px;max-height:90vh;overflow-y:auto">' +
    '<div class="modal-title">' + title + '</div>' +
    '<div class="modal-body">' +
    '<div class="form-row"><label>用户ID</label><input id="uf-userId" value="' + userId + '" ' + (isEdit ? 'readonly' : '') + ' style="background:' + (isEdit ? '#f5f5f5' : '#fff') + '"></div>' +
    '<div class="form-row"><label>姓名</label><input id="uf-name" value="' + name + '"></div>' +
    '<div class="form-row"><label>账号</label><input id="uf-account" value="' + account + '"></div>' +
    '<div class="form-row"><label>密码</label><input id="uf-password" type="password" placeholder="' + placeholderPwd + '"></div>' +
    '<div class="form-row"><label>角色</label><select id="uf-role">' + roleOptions + '</select></div>' +
    '<div class="form-row"><label>权限列表</label><input id="uf-authList" value="' + authList + '" placeholder="逗号分隔，如：pp_edit,pmc_view"></div>' +
    '</div>' +
    '<div class="modal-foot">' +
    '<button class="btn" onclick="closeUserForm()">取消</button>' +
    '<button class="btn primary" onclick="userFormSubmit(\'' + (isEdit ? userId : '') + '\',' + isEdit + ')">' + (isEdit ? '保存' : '创建') + '</button>' +
    '</div></div></div>';

  var old = document.getElementById('user-form-mask');
  if (old) old.remove();
  var div = document.createElement('div');
  div.innerHTML = html;
  document.body.appendChild(div.firstElementChild);
}

/** 关闭弹窗 */
function closeUserForm() {
  var mask = document.getElementById('user-form-mask');
  if (mask) mask.remove();
}

/** 提交表单 */
async function userFormSubmit(userId, isEdit) {
  var name = document.getElementById('uf-name').value.trim();
  var account = document.getElementById('uf-account').value.trim();
  var password = document.getElementById('uf-password').value;
  var role = document.getElementById('uf-role').value;
  var authList = document.getElementById('uf-authList').value.trim();

  if (!name) { toast('请输入姓名'); return; }
  if (!account) { toast('请输入账号'); return; }
  if (!isEdit && !password) { toast('请输入密码'); return; }

  var payload = { name: name, account: account, role: role, authList: authList };
  if (password) payload.password = password;

  try {
    if (isEdit) {
      await Api.updateUser(userId, payload);
      toast('用户【' + name + '】保存成功');
    } else {
      var newUserId = document.getElementById('uf-userId').value.trim();
      payload.userId = newUserId;
      payload.state = 'active';
      await Api.createUser(payload);
      toast('用户【' + name + '】创建成功');
    }
    closeUserForm();
    await userRender();
  } catch (e) {
    toast('操作失败：' + e.message);
  }
}
