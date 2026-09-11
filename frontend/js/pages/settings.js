// 作者：袁燕
// 功能：系统设置页。SVN 仓库配置 / 文档路径映射 / 本机本地路径 三区，统一存库可配。

function settingsRender() {
  var h = '';
  // 注：项目配置（当前项目代号）已迁移到顶栏「修改项目」按钮，设置页不再重复（避免两边不同步）
  // 区1：SVN 仓库配置（按项目）
  h += '<div class="panel"><div class="panel-hd"><h3><span class="bar"></span>SVN 仓库配置（按项目）</h3></div>' +
    '<div id="repo-box"></div></div>';
  // 区2：文档路径映射
  h += '<div class="panel"><div class="panel-hd"><h3><span class="bar"></span>文档类型 → SVN 相对路径映射</h3></div>' +
    '<div class="note">相对仓库根的路径，如 开发计划 填「trunk/项目管理/项目策划/项目计划」。此模块不按项目区分（所有项目 SVN 相对路径几乎一致）。</div>' +
    '<div id="docpath-box"></div></div>';
  // 区3：本机本地路径（machine+user+project）
  h += '<div class="panel"><div class="panel-hd"><h3><span class="bar"></span>本机本地 SVN 路径</h3></div>' +
    '<div class="note">每人每台机器不同，按 机器+用户+项目 维度保存。</div>' +
    '<div id="localpath-box"></div></div>';
  document.getElementById('content').innerHTML = h;
  settingsLoadRepos();
  settingsLoadDocPaths();
  settingsLoadLocalPaths();
}

// ---- 区1：仓库配置 ----
function settingsLoadRepos() {
  Api.listSvnRepos().then(function (r) {
    var rows = (r && r.data) || [];
    var h = '<table class="tbl"><thead><tr><th>项目</th><th>仓库 URL</th><th>用户名</th><th>密码</th><th>默认基路径</th><th>操作</th></tr></thead><tbody>';
    rows.forEach(function (x) {
      h += repoRow(x);
    });
    h += '</tbody></table>' +
      '<button class="btn primary sm" onclick="settingsAddRepo()">＋ 新增仓库配置</button>';
    document.getElementById('repo-box').innerHTML = h;
  }).catch(function (e) {
    document.getElementById('repo-box').innerHTML = '<div class="err">加载失败：' + (e.message || e) + '</div>';
  });
}
function repoRow(x) {
  return '<tr data-pid="' + x.projectId + '">' +
    '<td><input value="' + x.projectId + '" data-f="projectId" style="width:80px"></td>' +
    '<td><input value="' + x.repoUrl + '" data-f="repoUrl"></td>' +
    '<td><input value="' + x.username + '" data-f="username" style="width:80px"></td>' +
    '<td><input value="' + x.password + '" data-f="password" type="password" style="width:90px"></td>' +
    '<td><input value="' + (x.baseRelPath || 'trunk/develop') + '" data-f="baseRelPath"></td>' +
    '<td><button class="btn ghost sm" onclick="settingsSaveRepo(this)">保存</button></td></tr>';
}
function settingsAddRepo() {
  var tb = document.querySelector('#repo-box tbody');
  var tr = document.createElement('tr');
  tr.innerHTML = repoRow({ projectId: '', repoUrl: 'https://yuanyan/svn/', username: 'admin', password: '123456', baseRelPath: 'trunk/develop' });
  tb.appendChild(tr);
}
// 设置页通用行保存：收集行内 [data-f] → 调 upsert → 重载（三区共用同一套逻辑）
function settingsSaveRow(btn, upsertFn, reloadFn) {
  var tr = btn.closest('tr');
  var payload = {};
  tr.querySelectorAll('[data-f]').forEach(function (el) { payload[el.getAttribute('data-f')] = el.value.trim(); });
  upsertFn(payload).then(reloadFn).catch(function (e) { alert('保存失败：' + (e.message || e)); });
}
function settingsSaveRepo(btn) { settingsSaveRow(btn, Api.upsertSvnRepo, settingsLoadRepos); }

// ---- 区2：文档路径映射（全局，不分项目）----
function settingsLoadDocPaths() {
  Api.listSvnDocPaths().then(function (r) {
    var rows = (r && r.data) || [];
    var h = '<table class="tbl"><thead><tr><th>模板</th><th>SVN 相对路径</th><th>操作</th></tr></thead><tbody>';
    rows.forEach(function (x) {
      h += '<tr><td><input value="' + x.templateName + '" data-f="templateName" style="width:70px"></td>' +
        '<td><input value="' + x.relPath + '" data-f="relPath"></td>' +
        '<td><button class="btn ghost sm" onclick="settingsSaveDocPath(this)">保存</button></td></tr>';
    });
    h += '</tbody></table><button class="btn primary sm" onclick="settingsAddDocPath()">＋ 新增映射</button>';
    document.getElementById('docpath-box').innerHTML = h;
  }).catch(function (e) {
    document.getElementById('docpath-box').innerHTML = '<div class="err">加载失败：' + (e.message || e) + '</div>';
  });
}
function settingsAddDocPath() {
  var tb = document.querySelector('#docpath-box tbody');
  var tr = document.createElement('tr');
  tr.innerHTML = '<td><input value="SDP" data-f="templateName" style="width:70px"></td>' +
  '<td><input value="trunk/项目管理/项目策划/项目计划" data-f="relPath"></td>' +
  '<td><button class="btn ghost sm" onclick="settingsSaveDocPath(this)">保存</button></td>';
  tb.appendChild(tr);
}
function settingsSaveDocPath(btn) { settingsSaveRow(btn, Api.upsertSvnDocPath, settingsLoadDocPaths); }

// ---- 区3：本机本地路径 ----
function settingsLoadLocalPaths() {
  Api.listLocalPaths().then(function (r) {
    var rows = (r && r.data) || [];
    var h = '<table class="tbl"><thead><tr><th>机器ID</th><th>用户</th><th>项目</th><th>本地路径</th><th>操作</th></tr></thead><tbody>';
    rows.forEach(function (x) {
      h += '<tr><td><input value="' + x.machineId + '" data-f="machineId" style="width:120px"></td>' +
        '<td><input value="' + x.userId + '" data-f="userId" style="width:70px"></td>' +
        '<td><input value="' + x.projectId + '" data-f="projectId" style="width:70px"></td>' +
        '<td><input value="' + x.localPath + '" data-f="localPath"></td>' +
        '<td><button class="btn ghost sm" onclick="settingsSaveLocalPath(this)">保存</button></td></tr>';
    });
    h += '</tbody></table><button class="btn primary sm" onclick="settingsAddLocalPath()">＋ 新增本地路径</button>';
    document.getElementById('localpath-box').innerHTML = h;
  }).catch(function (e) {
    document.getElementById('localpath-box').innerHTML = '<div class="err">加载失败：' + (e.message || e) + '</div>';
  });
}
function settingsAddLocalPath() {
  var tb = document.querySelector('#localpath-box tbody');
  var tr = document.createElement('tr');
  tr.innerHTML = '<td><input value="" data-f="machineId" style="width:120px" placeholder="电脑名/用户"></td>' +
  '<td><input value="admin" data-f="userId" style="width:70px"></td>' +
  '<td><input value="' + Api.curProjectId() + '" data-f="projectId" style="width:70px"></td>' +
  '<td><input value="D:\\5000\\' + Api.curProjectId() + '" data-f="localPath"></td>' +
  '<td><button class="btn ghost sm" onclick="settingsSaveLocalPath(this)">保存</button></td>';
  tb.appendChild(tr);
}
function settingsSaveLocalPath(btn) { settingsSaveRow(btn, Api.upsertLocalPath, settingsLoadLocalPaths); }
