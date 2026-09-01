# -*- coding: utf-8 -*-
"""代码整改 E 组：PP 生成面板统计卡改为数据库动态取数。作者：袁燕
原状：4 张卡片硬编码（19 类文档/293 页、16 角色等，与库中实际不符）。
改后：页面渲染骨架，异步从 listDocScale / listStakeholderPlan / listHwRes+listSwRes /
     listSchedule 拉取真实计数填充。
"""
import io
import os

BASE = r'D:\5000\5000BManagePro'
p = os.path.join(BASE, 'frontend/js/pages/pp.js')
src = io.open(p, encoding='utf-8').read()

if 'ppGenPlanLoad' in src:
    print('  [跳过] 已改')
    raise SystemExit

old_start = src.find('function ppGenPlan() {')
old_end = src.find('\n}', src.find('return h;', old_start)) + 2

new_fn = (
    "function ppGenPlan() {\n"
    "  // 统计卡片：数据全部异步取自数据库接口（袁总铁律：显示数据一律从库读）\n"
    "  let h = '<div class=\"stats\">' +\n"
    "    '<div class=\"stat\"><div class=\"v\" id=\"gc-est\">加载中…</div><div class=\"k\">工作量估算（人日 / 阶段数）</div><div class=\"sub\"><span class=\"tag ok\">已入库</span></div></div>' +\n"
    "    '<div class=\"stat\"><div class=\"v\" id=\"gc-risk\">加载中…</div><div class=\"k\">风险资源（硬件 / 软件项）</div><div class=\"sub\"><span class=\"tag ok\">已入库</span></div></div>' +\n"
    "    '<div class=\"stat\"><div class=\"v\" id=\"gc-doc\">加载中…</div><div class=\"k\">文档规模（类数 / 合计页数）</div><div class=\"sub\"><span class=\"tag info\">可取数</span></div></div>' +\n"
    "    '<div class=\"stat\"><div class=\"v\" id=\"gc-stake\">加载中…</div><div class=\"k\">利益相关方（活动行 × 9 角色）</div><div class=\"sub\"><span class=\"tag info\">可取数</span></div></div>' +\n"
    "    '</div>';\n"
    "  h += '<div class=\"panel\"><h3><span class=\"bar\"></span>生成《软件开发计划》（SDP）</h3>' +\n"
    "    '<div class=\"note\">由估算收敛 / 风险资源 / 文档规模 / 利益相关方 自动汇总生成《软件开发计划》。' +\n"
    "    '可下载到本机指定 SVN 工作副本路径，或直接提交到 VisualSVN 受控库（仓库/路径在「设置」页配置）。' +\n"
    "    '<b>分类同步</b>：点某一类「同步到 SVN」，仅重新拉取该类最新数据生成文档并提交，其余章节保持原样。</div>' +\n"
    "    '<div class=\"row\">' +\n"
    "    '<button class=\"btn primary\" id=\"pp-dl-btn\" onclick=\"ppDownloadLocal()\">⬇ 下载到本地指定路径</button> ' +\n"
    "    '<button class=\"btn warn\" id=\"pp-svn-btn\" onclick=\"ppCommitSvn()\">⬆ 提交到 SVN</button>' +\n"
    "    '<span id=\"pp-gen-msg\" style=\"margin-left:12px;font-size:13px;\"></span></div>' +\n"
    "    '<div class=\"row\" style=\"margin-top:10px;\">' +\n"
    "    '<button class=\"btn ghost sm\" onclick=\"ppCommitSvn(\\'est\\')\">⬆ 同步估算到 SVN</button> ' +\n"
    "    '<button class=\"btn ghost sm\" onclick=\"ppCommitSvn(\\'risk\\')\">⬆ 同步风险资源到 SVN</button> ' +\n"
    "    '<button class=\"btn ghost sm\" onclick=\"ppCommitSvn(\\'stake\\')\">⬆ 同步利益相关方到 SVN</button>' +\n"
    "    '</div></div>';\n"
    "  setTimeout(ppGenPlanLoad, 0);\n"
    "  return h;\n"
    "}\n"
    "\n"
    "// 统计卡数据装载：全部来自数据库接口（项目维度）\n"
    "function ppGenPlanLoad() {\n"
    "  var pid = Api.curProjectId();\n"
    "  Api.listDocScale(pid).then(function (r) {\n"
    "    var rows = (r && r.data) || [];\n"
    "    var pages = rows.reduce(function (s, x) { return s + (+x.pages_new || 0); }, 0);\n"
    "    var el = document.getElementById('gc-doc');\n"
    "    if (el) el.textContent = rows.length + ' 类文档 / ' + pages + ' 页';\n"
    "  }).catch(function () {});\n"
    "  Api.listStakeholderPlan(pid).then(function (r) {\n"
    "    var rows = (r && r.data) || [];\n"
    "    var el = document.getElementById('gc-stake');\n"
    "    if (el) el.textContent = rows.length + ' 活动行 × 9 角色';\n"
    "  }).catch(function () {});\n"
    "  Promise.all([Api.listHwRes(pid), Api.listSwRes(pid)]).then(function (rs) {\n"
    "    var hw = ((rs[0] && rs[0].data) || []).length;\n"
    "    var sw = ((rs[1] && rs[1].data) || []).length;\n"
    "    var el = document.getElementById('gc-risk');\n"
    "    if (el) el.textContent = '硬件 ' + hw + ' 项 / 软件 ' + sw + ' 项';\n"
    "  }).catch(function () {});\n"
    "  Api.listSchedule(pid).then(function (r) {\n"
    "    var rows = (r && r.data) || [];\n"
    "    var eng = rows.reduce(function (s, x) { return s + (+x.eng_md || 0); }, 0);\n"
    "    var mgr = rows.reduce(function (s, x) { return s + (+x.mgr_md || 0); }, 0);\n"
    "    var el = document.getElementById('gc-est');\n"
    "    if (el) el.textContent = (Math.round((eng + mgr) * 10) / 10) + ' 人日 / ' + rows.length + ' 阶段';\n"
    "  }).catch(function () {});\n"
    "}\n")

if old_start >= 0 and old_end > old_start:
    src = src[:old_start] + new_fn + src[old_end:]
    io.open(p, 'w', encoding='utf-8').write(src)
    print('  [OK] E1 ppGenPlan 统计卡改数据库动态取数（4 卡）')
else:
    print('  [FAIL] 未定位 ppGenPlan')
