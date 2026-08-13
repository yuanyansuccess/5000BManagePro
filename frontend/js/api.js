// 作者：袁燕
// 功能：前后端通信统一封装（HTTP + JSON）。
// 设计原则（继承智能柜铁律）：
//   1. 字段统一驼峰（P13）：发送/接收均驼峰，禁止蛇形
//   2. 页面绝不直连数据库（P18）：所有取数走本封装，不直接写 SQL
//   3. 路由不降级（P10）：请求失败返回明确错误，不静默降级
// 后端基地址可配置，便于前后端分离部署。

const API_BASE = (window.API_BASE || "http://127.0.0.1:8000");

async function request(method, path, body) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const resp = await fetch(API_BASE + path, opts);
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
};
