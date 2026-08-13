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
  const c = document.getElementById('content');
  var h = '<div class="page"><div class="page-title">用户管理</div><div class="page-sub">项目人员（R105 名册）· 系统用户（' + SYS_USERS.length + ' 人，后端实时数据）</div>';
  // 模块1 项目人员卡片
  h += '<div class="panel"><h3><span class="bar"></span>项目人员（' + PEOPLE.length + '）</h3><div class="base-grid">';
  PEOPLE.forEach(function (p) {
    h += '<div class="mc-card"><div class="mc-h"><span class="av" style="background:' + teamColor(p.team) + '">' + p.name.charAt(0) + '</span>' +
      '<div><div style="font-weight:700;">' + p.name + '</div><div style="font-size:12px;color:var(--text-3)">' + p.no + '</div></div>' +
      '<span class="tag" style="margin-left:auto;background:' + teamColor(p.team) + '22;color:' + teamColor(p.team) + '">' + p.team + '</span></div>' +
      '<div class="mc-rpt">角色：' + p.role + '</div>' +
      '<div class="mc-rpt">SVN：' + p.svn + '</div>' +
      '<div class="mc-rpt">权限：' + p.auth + '</div></div>';
  });
  h += '</div></div>';
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

/** toast 提示 */
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
