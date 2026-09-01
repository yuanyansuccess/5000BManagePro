// 作者：袁燕
// 功能：前后端通信统一封装（HTTP + JSON）。
// 设计原则（继承智能柜铁律）：
//   1. 字段统一驼峰（P13）：发送/接收均驼峰，禁止蛇形
//   2. 页面绝不直连数据库（P18）：所有取数走本封装，不直接写 SQL
//   3. 路由不降级（P10）：请求失败返回明确错误，不静默降级
// 后端基地址可配置，便于前后端分离部署。

const API_BASE = (window.API_BASE || "http://127.0.0.1:8000");

// 平台统一请求入口：所有前端数据一律走 /api/*（绝不直连数据库）。
// method=GET/POST/PUT/DELETE；body 为 JSON 载荷（GET 可忽略）。
// 统一错误出口：非 2xx 抛出后端 detail，由各调用点 catch 后 toast 提示。
async function request(method, path, body) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body !== undefined) opts.body = JSON.stringify(body);
  let resp = null;
  try {
    resp = await fetch(API_BASE + path, opts);
  } catch (e) {
    // 网络层失败（连接拒绝/断网/超时中断）——给出用户能自查的明确指引
    throw new Error("无法连接后端服务（127.0.0.1:8000）。请双击运行 start.bat 启动平台后再试；若已启动，请等 10 秒后刷新页面重试。");
  }
  let json = null;
  try { json = await resp.json(); } catch (e) { json = null; }
  if (!resp.ok) {
    const msg = (json && json.detail) || ("请求失败 " + resp.status);
    throw new Error(msg);
  }
  return json;
}

const Api = {
  health: () => request("GET", "/api/health"),
  // 登录认证
  login: (account, password) => request("POST", "/api/users/login", { account, password }),
  getMe: () => {
    const token = sessionStorage.getItem("token") || "";
    const headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = "Bearer " + token;
    return fetch(API_BASE + "/api/users/me", { headers }).then(function(r) { return r.json(); }).catch(function() { return null; });
  },
  // 需求（RDM）
  listRequirements: () => request("GET", "/api/requirements"),
  createRequirement: (payload) => request("POST", "/api/requirements", payload),
  deleteRequirement: (reqId) => request("DELETE", "/api/requirements/" + reqId),
  // 风险（PP/PMC）
  listRisks: () => request("GET", "/api/risks"),
  createRisk: (payload) => request("POST", "/api/risks", payload),
  deleteRisk: (riskId) => request("DELETE", "/api/risks/" + riskId),
  // 相关方（PP A14）
  listStakeholders: () => request("GET", "/api/stakeholders"),
  createStakeholder: (payload) => request("POST", "/api/stakeholders", payload),
  deleteStakeholder: (role) => request("DELETE", "/api/stakeholders/" + role),
  // 告警日志
  listAlerts: (params) => request("GET", "/api/alerts" + (params ? "?" + params : "")),
  updateAlertStatus: (id, status) => request("PATCH", "/api/alerts/" + id + "/status", { status }),
  // 用户（RBAC）
  listUsers: () => request("GET", "/api/users"),
  createUser: (payload) => request("POST", "/api/users", payload),
  updateUser: (userId, payload) => request("PUT", "/api/users/" + userId, payload),
  deleteUser: (userId) => request("DELETE", "/api/users/" + userId),
  // 文档生成（返回 docx 文件流，单独 fetch + blob 下载，不走通用 request）
  generateDoc: (projectId, templateName, opts) =>
    new Promise(function (resolve, reject) {
      let path = "/api/doc/" + projectId + "/" + templateName + "/generate";
      if (opts && (opts.docNumber || opts.docVersion)) {
        const q = [];
        if (opts.docNumber) q.push("doc_number=" + encodeURIComponent(opts.docNumber));
        if (opts.docVersion) q.push("doc_version=" + encodeURIComponent(opts.docVersion));
        path += "?" + q.join("&");
      }
      fetch(API_BASE + path, { method: "POST" })
        .then(function (resp) {
          if (!resp.ok) return reject(new Error("生成失败 " + resp.status));
          const cd = resp.headers.get("Content-Disposition") || "";
          const m = cd.match(/filename=([^;]+)/);
          const fname = (m && m[1]) || (projectId + "_" + templateName + ".docx");
          return resp.blob().then(function (blob) {
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url; a.download = fname; document.body.appendChild(a);
            a.click(); a.remove(); URL.revokeObjectURL(url);
            resolve(fname);
          });
        })
        .catch(function (e) { reject(e); });
    }),
  // 文档：下载到本机指定路径（方式1）
  saveToLocal: (projectId, templateName, body) =>
    request("POST", "/api/doc/" + projectId + "/" + templateName + "/save-to-local", body),
  // 文档：提交到 SVN（方式2）
  commitSvn: (projectId, templateName, opts) => {
    // templateName 可带查询串（如 "SDP?module=est"），此处拆开重组保证 URL 正确
    let tpl = templateName;
    let extra = {};
    if (templateName.indexOf('?') >= 0) {
      const parts = templateName.split('?');
      tpl = parts[0];
      parts[1].split('&').forEach(function (kv) {
        const p = kv.split('=');
        extra[p[0]] = p[1];
      });
    }
    let path = "/api/doc/" + projectId + "/" + tpl + "/commit-svn";
    const q = [];
    if (opts && opts.docNumber) q.push("doc_number=" + encodeURIComponent(opts.docNumber));
    if (opts && opts.docVersion) q.push("doc_version=" + encodeURIComponent(opts.docVersion));
    if (extra.module) q.push("module=" + extra.module);
    if (q.length) path += "?" + q.join("&");
    return request("POST", path);
  },
  // ===== 设置页：SVN 配置（存库，可配）=====
  // 仓库配置（按项目）
  listSvnRepos: () => request("GET", "/api/settings/svn-repos"),
  upsertSvnRepo: (payload) => request("POST", "/api/settings/svn-repos", payload),
  // 文档路径映射
  listSvnDocPaths: () => request("GET", "/api/settings/svn-doc-paths"),
  upsertSvnDocPath: (payload) => request("POST", "/api/settings/svn-doc-paths", payload),
  // 本机本地路径（machine+user+project）
  listLocalPaths: () => request("GET", "/api/settings/local-paths"),
  upsertLocalPath: (payload) => request("POST", "/api/settings/local-paths", payload),
  // ===== 项目配置（代号统一来源，取代硬编码 R121）=====
  currentProject: () => request("GET", "/api/projects/current"),
  getProject: (id) => request("GET", "/api/projects/" + id),
  listProjects: () => request("GET", "/api/projects"),
  createProject: (payload) => request("POST", "/api/projects", payload),
  updateProject: (id, payload) => request("PUT", "/api/projects/" + id, payload),
  setCurrentProject: (id) => request("POST", "/api/projects/" + id + "/current"),
  // ===== 项目策划资源（按项目维度：硬件/软件/规模估算/进度/相关方，供 SDP 表格占位符聚合）=====
  // 路由前缀 /api/pp/{projectId}/...
  listHwRes: (pid) => request("GET", "/api/pp/" + pid + "/hw-res"),
  createHwRes: (pid, payload) => request("POST", "/api/pp/" + pid + "/hw-res", payload),
  updateHwRes: (pid, rid, payload) => request("PUT", "/api/pp/" + pid + "/hw-res/" + rid, payload),
  deleteHwRes: (pid, rid) => request("DELETE", "/api/pp/" + pid + "/hw-res/" + rid),
  listSwRes: (pid) => request("GET", "/api/pp/" + pid + "/sw-res"),
  createSwRes: (pid, payload) => request("POST", "/api/pp/" + pid + "/sw-res", payload),
  updateSwRes: (pid, rid, payload) => request("PUT", "/api/pp/" + pid + "/sw-res/" + rid, payload),
  deleteSwRes: (pid, rid) => request("DELETE", "/api/pp/" + pid + "/sw-res/" + rid),
  listDocScale: (pid) => request("GET", "/api/pp/" + pid + "/doc-scale"),
  createDocScale: (pid, payload) => request("POST", "/api/pp/" + pid + "/doc-scale", payload),
  updateDocScale: (pid, rid, payload) => request("PUT", "/api/pp/" + pid + "/doc-scale/" + rid, payload),
  deleteDocScale: (pid, rid) => request("DELETE", "/api/pp/" + pid + "/doc-scale/" + rid),
  listCodeScale: (pid) => request("GET", "/api/pp/" + pid + "/code-scale"),
  createCodeScale: (pid, payload) => request("POST", "/api/pp/" + pid + "/code-scale", payload),
  updateCodeScale: (pid, rid, payload) => request("PUT", "/api/pp/" + pid + "/code-scale/" + rid, payload),
  deleteCodeScale: (pid, rid) => request("DELETE", "/api/pp/" + pid + "/code-scale/" + rid),
  listSchedule: (pid) => request("GET", "/api/pp/" + pid + "/schedule"),
  createSchedule: (pid, payload) => request("POST", "/api/pp/" + pid + "/schedule", payload),
  updateSchedule: (pid, rid, payload) => request("PUT", "/api/pp/" + pid + "/schedule/" + rid, payload),
  deleteSchedule: (pid, rid) => request("DELETE", "/api/pp/" + pid + "/schedule/" + rid),
  listProjStakeholders: (pid) => request("GET", "/api/pp/" + pid + "/stakeholders"),
  createProjStakeholder: (pid, payload) => request("POST", "/api/pp/" + pid + "/stakeholders", payload),
  updateProjStakeholder: (pid, rid, payload) => request("PUT", "/api/pp/" + pid + "/stakeholders/" + rid, payload),
  deleteProjStakeholder: (pid, rid) => request("DELETE", "/api/pp/" + pid + "/stakeholders/" + rid),
  // 利益相关方参与计划（R121 附录B 矩阵）
  listStakeholderPlan: (pid) => request("GET", "/api/pp/" + pid + "/stakeholder_plan"),
  updateStakeholderPlanRow: (pid, rid, payload) => request("PUT", "/api/pp/" + pid + "/stakeholder_plan/" + rid, payload),
  // 软件估算收敛项（对标 R105-PP-GH-01/02 两轮，按项目维度+轮次）
  listEstItems: (pid, roundNo) => request("GET", "/api/pp/" + pid + "/est-items?round_no=" + (roundNo || 1)),
  createEstItem: (pid, payload) => request("POST", "/api/pp/" + pid + "/est-items", payload),
  updateEstItem: (pid, rid, payload) => request("PUT", "/api/pp/" + pid + "/est-items/" + rid, payload),
  deleteEstItem: (pid, rid) => request("DELETE", "/api/pp/" + pid + "/est-items/" + rid),
  // 风险编辑（PUT 只更新传入字段）
  updateRisk: (riskId, payload) => request("PUT", "/api/risks/" + riskId, payload),
  // 进度任务项（R105 .mpp 导入，阶段+全部任务，为双周任务表储备）
  listScheduleTasks: (pid) => request("GET", "/api/pp/" + pid + "/schedule-tasks"),
  createScheduleTask: (pid, payload) => request("POST", "/api/pp/" + pid + "/schedule-tasks", payload),
  updateScheduleTask: (pid, rid, payload) => request("PUT", "/api/pp/" + pid + "/schedule-tasks/" + rid, payload),
  deleteScheduleTask: (pid, rid) => request("DELETE", "/api/pp/" + pid + "/schedule-tasks/" + rid),
  // 项目人员（按项目维度，文档签署角色基础）
  listMembers: (pid) => request("GET", "/api/pp/" + pid + "/members"),
  createMember: (pid, payload) => request("POST", "/api/pp/" + pid + "/members", payload),
  updateMember: (pid, rid, payload) => request("PUT", "/api/pp/" + pid + "/members/" + rid, payload),
  deleteMember: (pid, rid) => request("DELETE", "/api/pp/" + pid + "/members/" + rid),
};

// 当前项目缓存：启动时拉一次，全平台用（代替硬编码 R121/R105）
window.__curProj = null;
Api.loadCurrentProject = function () {
  return Api.currentProject().then(function (r) {
    window.__curProj = r && r.data ? r.data : { projectId: "R105", localPath: "D:/5000/R105", svnBasePath: "R105/trunk" };
    return window.__curProj;
  }).catch(function () {
    window.__curProj = { projectId: "R105", localPath: "D:/5000/R105", svnBasePath: "R105/trunk" };
    return window.__curProj;
  });
};
Api.curProjectId = function () { return (window.__curProj && window.__curProj.projectId) || "R105"; };
