// 作者：袁燕
// 功能：用户管理页（user）。模块1 项目人员（卡片）+ 模块2 系统用户（7 列表格·后端 API 实时数据）。
// 2026-08-10 改造：系统用户表格从静态 SYS_USERS 数组改为 GET /api/users 后端取数，增删改全部走 API。

// 角色配色（对标 teamColor）
function teamColor(t) {
  const map = { '软件': '#4da3ff', '测试': '#52c41a', '设计': '#6c5ce7', '配置': '#fa8c16', '质保': '#eb2f96', '管理': '#13c2c2' };
  for (var k in map) if (t.indexOf(k) >= 0) return map[k];
  return '#999';
}

// 模块1：项目人员（R105 真实名册·静态）
var PEOPLE = [
  { name: '辛峥峰', role: '软件负责人', team: '软件', no: 'SF-01', svn: 'svn://pdm/R105/辛峥峰', auth: '全部' },
  { name: '马慧芳', role: '需求', team: '软件', no: 'MF-02', svn: 'svn://pdm/R105/马慧芳', auth: '需求/文档' },
  { name: '吴明森', role: '设计实现', team: '设计', no: 'WM-03', svn: 'svn://pdm/R105/吴明森', auth: '设计/编码' },
  { name: '罗臻', role: '设计实现', team: '设计', no: 'LZ-04', svn: 'svn://pdm/R105/罗臻', auth: '设计/测试' },
  { name: '谢柯薪', role: '测试', team: '测试', no: 'XK-05', svn: 'svn://pdm/R105/谢柯薪', auth: '测试/验证' },
  { name: '杜晟', role: 'QA', team: '质保', no: 'DS-06', svn: 'svn://pdm/R105/杜晟', auth: '质量保证' },
  { name: '张星竹', role: '配置管理员', team: '配置', no: 'ZX-07', svn: 'svn://pdm/R105/张星竹', auth: '配置管理' },
  { name: '许宏刚', role: 'CCB', team: '管理', no: 'XG-08', svn: 'svn://pdm/R105/许宏刚', auth: '变更审批' }
];

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
  const c = document.getElementById('content');
  var h = '<div class="page"><div class="page-title">用户管理</div><div class="page-sub">项目人员（' + MEMBERS.length + ' 人，当前项目 ' + Api.curProjectId() + ' ' + shellCurProjName() + '，文档签署角色基础）· 系统用户（' + SYS_USERS.length + ' 人）</div>';
  // 模块1 项目人员表格（按项目维度，可增改删，是文档生成的角色基础）
  h += '<div class="panel"><h3><span class="bar"></span>项目人员（' + MEMBERS.length + '）' +
    '<button class="btn-sm ok" style="float:right;margin-top:-4px" onclick="memberAddDialog()">+ 新增人员</button></h3>' +
    '<div style="overflow-x:auto;"><table class="tbl"><thead><tr>' +
    '<th>姓名</th><th>角色</th><th>所属组</th><th>编号</th><th>SVN 路径</th><th>权限/职责</th><th style="width:150px">操作</th></tr></thead>' +
    '<tbody id="member-tbody"><tr><td colspan="7" style="text-align:center;color:var(--text-3);">加载中…</td></tr></tbody></table></div></div>';
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
}

// ==================== 项目人员（按项目维度，文档签署角色基础）====================

var MEMBERS = [];

/** 加载当前项目人员（GET /api/pp/{pid}/members） */
async function memberLoad() {
  try {
    var resp = await Api.listMembers(Api.curProjectId());
    MEMBERS = (resp && resp.data) ? resp.data : (Array.isArray(resp) ? resp : []);
  } catch (e) {
    console.error('加载项目人员失败：', e);
    MEMBERS = [];
  }
}

/** 渲染项目人员表体（行内编辑 + 保存/删除） */
function memberRenderRows() {
  var tb = document.getElementById('member-tbody');
  if (!tb) return;
  if (!MEMBERS.length) {
    tb.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-3);padding:24px">暂无项目人员，点「+ 新增人员」添加</td></tr>';
    return;
  }
  tb.innerHTML = MEMBERS.map(function (m) {
    function inp(f, w, v) { return '<td><input data-f="' + f + '" data-id="' + m.id + '" value="' + (v == null ? '' : v) + '" style="width:' + w + '"></td>'; }
    return '<tr>' + inp('name', '80px', m.name) + inp('role', '100px', m.role) +
      '<td><input data-f="team" data-id="' + m.id + '" value="' + (m.team || '') + '" style="width:70px;background:' + teamColor(m.team || '') + '14;color:' + teamColor(m.team || '') + '"></td>' +
      inp('no', '70px', m.no) + inp('svn', '200px', m.svn) + inp('auth', '110px', m.auth) +
      '<td><button class="btn-sm ok" onclick="memberSave(' + m.id + ')">保存</button>' +
      '<button class="btn-sm danger" onclick="memberDel(' + m.id + ')">删除</button></td></tr>';
  }).join('');
}

/** 数据到位后渲染表体（userRender 内已 await memberLoad） */
function memberAfterRender() { memberRenderRows(); }

async function memberSave(id) {
  var get = function (f) { var el = document.querySelector('#member-tbody [data-id="' + id + '"][data-f="' + f + '"]'); return el ? el.value.trim() : ''; };
  try {
    await Api.updateMember(Api.curProjectId(), id, {
      name: get('name'), role: get('role'), team: get('team'),
      no: get('no'), svn: get('svn'), auth: get('auth'),
    });
    toast('已保存');
    await userRender();
  } catch (e) { toast('保存失败：' + e.message); }
}

async function memberDel(id) {
  if (!confirm('确认删除该项目人员？')) return;
  try {
    await Api.deleteMember(Api.curProjectId(), id);
    toast('已删除');
    await userRender();
  } catch (e) { toast('删除失败：' + e.message); }
}

function memberAddDialog() {
  var html = '<div class="modal-mask" onclick="if(event.target===this)this.remove()"><div class="modal"><div class="modal-hd">新增项目人员（' + Api.curProjectId() + '）</div><div class="modal-bd">' +
    '<div class="field"><label>姓名 *</label><input id="mb-name"></div><div class="field"><label>角色</label><input id="mb-role" placeholder="如 软件负责人/测试/QA"></div>' +
    '<div class="field"><label>所属组</label><input id="mb-team" placeholder="软件/测试/设计/配置/质保/管理"></div><div class="field"><label>编号</label><input id="mb-no"></div>' +
    '<div class="field"><label>SVN 路径</label><input id="mb-svn" placeholder="svn://pdm/R105/姓名"></div><div class="field"><label>权限/职责</label><input id="mb-auth"></div>' +
    '<div id="mb-msg" style="color:#e74c3c;font-size:13px;min-height:16px;"></div></div>' +
    '<div class="modal-ft"><button class="btn ghost" onclick="this.closest(\'.modal-mask\').remove()">取消</button>' +
    '<button class="btn primary" onclick="memberSaveNew()">保存</button></div></div></div>';
  document.body.insertAdjacentHTML('beforeend', html);
}

async function memberSaveNew() {
  var msg = document.getElementById('mb-msg');
  var g = function (id) { return document.getElementById(id).value.trim(); };
  if (!g('mb-name')) { msg.textContent = '姓名必填'; return; }
  try {
    await Api.createMember(Api.curProjectId(), {
      name: g('mb-name'), role: g('mb-role'), team: g('mb-team'),
      no: g('mb-no'), svn: g('mb-svn'), auth: g('mb-auth'), seq: MEMBERS.length + 1,
    });
    document.querySelector('.modal-mask').remove();
    toast('已新增项目人员');
    await userRender();
  } catch (e) { msg.textContent = '保存失败：' + e.message; }
}

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
