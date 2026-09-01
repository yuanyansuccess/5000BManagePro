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

// ---- 区0：项目配置（新建 / 修改项目信息 / 切换当前项目）----
function settingsLoadProjects() {
  Api.listProjects().then(function (r) {
    var rows = (r && r.data) || [];
    var cur = Api.curProjectId();
    var h = '<table class="tbl"><thead><tr>' +
      '<th>项目代号</th><th>软件全称</th><th>飞机型号</th><th>负责人</th><th>承研单位</th><th>客户单位</th>' +
      '<th>阶段</th><th>立项日期</th><th>批准日期</th><th>IDE版本</th><th>软件版本</th><th>文档编号</th><th>本机路径</th><th>SVN 基路径</th>' +
      '<th>当前</th><th>操作</th></tr></thead><tbody>';
    rows.forEach(function (x) {
      var isCur = x.projectId === cur;
      h += '<tr data-pid="' + x.projectId + '">' +
        '<td><input value="' + x.projectId + '" data-f="projectId" style="width:70px" ' + (isCur ? 'readonly' : '') + '></td>' +
        '<td><input value="' + (x.projectName || '') + '" data-f="projectName" style="width:100px"></td>' +
        '<td><input value="' + (x.aircraftModel || '') + '" data-f="aircraftModel" style="width:60px" placeholder="K409"></td>' +
        '<td><input value="' + (x.owner || '') + '" data-f="owner" style="width:60px"></td>' +
        '<td><input value="' + (x.org || '') + '" data-f="org" style="width:80px"></td>' +
        '<td><input value="' + (x.customerDept || '') + '" data-f="customerDept" style="width:80px"></td>' +
        '<td><input value="' + (x.phase || '') + '" data-f="phase" style="width:60px" placeholder="初样"></td>' +
        '<td><input value="' + (x.startDate || '') + '" data-f="startDate" style="width:70px"></td>' +
        '<td><input value="' + (x.approveDate || '') + '" data-f="approveDate" style="width:70px"></td>' +
        '<td><input value="' + (x.ideVersion || '') + '" data-f="ideVersion" style="width:70px"></td>' +
        '<td><input value="' + (x.swVersion || '') + '" data-f="swVersion" style="width:70px"></td>' +
        '<td><input value="' + (x.docNumber || '') + '" data-f="docNumber" style="width:80px"></td>' +
        '<td><input value="' + (x.localPath || '') + '" data-f="localPath" style="width:80px"></td>' +
        '<td><input value="' + (x.svnBasePath || '') + '" data-f="svnBasePath" style="width:80px"></td>' +
        '<td>' + (isCur ? '<span class="tag ok">当前</span>' : '<button class="btn ghost sm" onclick="settingsSetCurProj(\'' + x.projectId + '\')">设为当前</button>') + '</td>' +
        '<td><button class="btn ghost sm" onclick="settingsSaveProj(this)">保存</button>' +
        '<button class="btn ghost sm" onclick="settingsEditProj(\'' + x.projectId + '\')">修改</button></td></tr>';
    });
    h += '</tbody></table>' +
      '<div class="note">项目代号=软件编号（生成文档/文件名/风险表/SVN 一律用此值）。飞机型号、负责人、单位、阶段、立项日期、文档编号均会注入生成的开发计划。修改后点「保存」即更新；「设为当前」切换全局代号。</div>' +
      '<button class="btn primary sm" onclick="settingsAddProj()">＋ 新建项目</button>';
    document.getElementById('project-box').innerHTML = h;
  }).catch(function (e) {
    document.getElementById('project-box').innerHTML = '<div class="err">加载失败：' + (e.message || e) + '</div>';
  });
}
// 新建/修改项目：弹窗收集全部关键词字段。editPid 非空时为修改模式（预填当前值）
function settingsSaveProj(btn) {
  var tr = btn.closest('tr');
  var pid = tr.getAttribute('data-pid');
  var payload = {};
  tr.querySelectorAll('[data-f]').forEach(function (el) { payload[el.getAttribute('data-f')] = el.value.trim(); });
  Api.updateProject(pid, payload).then(function () { settingsLoadProjects(); })
    .catch(function (e) { alert('保存失败：' + (e.message || e)); });
}
function settingsSetCurProj(pid) {
  if (!confirm('切换当前项目为 ' + pid + '？')) return;
  Api.setCurrentProject(pid).then(function () {
    Api.loadCurrentProject().then(function () { settingsLoadProjects(); toast('已切换到 ' + pid); });
  }).catch(function (e) { alert('切换失败：' + (e.message || e)); });
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
function settingsSaveRepo(btn) {
  var tr = btn.closest('tr');
  var payload = {};
  tr.querySelectorAll('[data-f]').forEach(function (el) { payload[el.getAttribute('data-f')] = el.value.trim(); });
  Api.upsertSvnRepo(payload).then(function () { settingsLoadRepos(); })
    .catch(function (e) { alert('保存失败：' + (e.message || e)); });
}

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
function settingsSaveDocPath(btn) {
  var tr = btn.closest('tr');
  var payload = {};
  tr.querySelectorAll('[data-f]').forEach(function (el) { payload[el.getAttribute('data-f')] = el.value.trim(); });
  Api.upsertSvnDocPath(payload).then(function () { settingsLoadDocPaths(); })
    .catch(function (e) { alert('保存失败：' + (e.message || e)); });
}

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
function settingsSaveLocalPath(btn) {
  var tr = btn.closest('tr');
  var payload = {};
  tr.querySelectorAll('[data-f]').forEach(function (el) { payload[el.getAttribute('data-f')] = el.value.trim(); });
  Api.upsertLocalPath(payload).then(function () { settingsLoadLocalPaths(); })
    .catch(function (e) { alert('保存失败：' + (e.message || e)); });
}
