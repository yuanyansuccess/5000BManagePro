// 作者：袁燕
// 功能：模板中心页（tpl）。1:1 还原效果图：10 过程域 chips 筛选 + 4 stat 卡 + 状态图例 + 7 列模板清单。
// 设计：模板清单为 R105 真实 A 类文档（严禁虚构）；后期接锚点引擎 {{KEY}} 自动取数。

// 过程域 chips（对标 TPL_DOMS）
var TPL_DOMS = ['全部', 'PP', 'PMC', 'RDM', 'VV', 'MA', 'CM', 'PQA', '评审', '结项'];
var TPL_DOM_NM = { PP: '项目策划', PMC: '项目监控', RDM: '需求管理', VV: '验证与确认', MA: '测量分析', CM: '配置管理', PQA: '质量保证', '评审': '评审与决策', '结项': '结项' };

// R105 真实 A 类文档清单（字段：no/nm/dom/fm/st[cls,text]/ver）
var TPL_DATA = [
  { no: 'A3', nm: '软件开发计划', dom: 'PP', fm: 'Word', st: ['info', '可取数'], ver: 'A' },
  { no: 'A4', nm: '软件项目启动会纪要', dom: 'PP', fm: 'Word', st: ['info', '套版'], ver: 'A' },
  { no: 'A5', nm: '估计理由假设表', dom: 'PP', fm: 'Excel', st: ['info', '可取数'], ver: 'A' },
  { no: 'A6', nm: 'Delphi法估算表', dom: 'PP', fm: 'Word', st: ['info', '可取数'], ver: 'A' },
  { no: 'A7', nm: 'PERT法估算表', dom: 'PP', fm: 'Word', st: ['info', '可取数'], ver: 'A' },
  { no: 'A8', nm: '类比法估算表', dom: 'PP', fm: 'Word', st: ['info', '可取数'], ver: 'A' },
  { no: 'A9', nm: '估算汇总表', dom: 'PP', fm: 'Word', st: ['info', '可取数'], ver: 'A' },
  { no: 'A10', nm: '软件估算表', dom: 'PP', fm: 'Word', st: ['info', '可取数'], ver: 'A' },
  { no: 'A11', nm: '软件风险管理表', dom: 'PP', fm: 'Word', st: ['info', '可取数'], ver: 'A' },
  { no: 'A12', nm: '数据管理表', dom: 'PP', fm: 'Excel', st: ['info', '可取数'], ver: 'A' },
  { no: 'A13', nm: '培训计划', dom: 'PP', fm: 'Word', st: ['info', '套版'], ver: 'A' },
  { no: 'A14', nm: '利益相关方参与表', dom: 'PP', fm: 'Excel', st: ['info', '可取数'], ver: 'A' },
  { no: 'A16', nm: '软件进度表', dom: 'PP', fm: 'Word', st: ['info', '可取数'], ver: 'A' },
  { no: 'A1', nm: '需求跟踪矩阵', dom: 'RDM', fm: 'Excel', st: ['warn', '待更新'], ver: 'A' },
  { no: 'A2', nm: '软件设计说明', dom: 'VV', fm: 'Word', st: ['ok', '母版'], ver: '—' },
  { no: 'A17', nm: '阶段报告', dom: 'PMC', fm: 'Word', st: ['info', '可取数'], ver: 'B' },
  { no: 'A20', nm: '个人周报', dom: 'PMC', fm: 'Excel', st: ['info', '可取数'], ver: 'B' },
  { no: 'A21', nm: '周任务分配表', dom: 'PMC', fm: 'Excel', st: ['info', '可取数'], ver: 'B' },
  { no: 'A22', nm: '软件周/双周报', dom: 'PMC', fm: 'Word', st: ['info', '可取数'], ver: 'B' },
  { no: 'A23', nm: '问题跟踪汇总表', dom: 'PMC', fm: 'Word', st: ['info', '可取数'], ver: 'B' },
  { no: 'A24', nm: '软件会议纪要', dom: 'PMC', fm: 'Word', st: ['info', '套版'], ver: 'B' },
  { no: 'A32', nm: '软件测量与分析报告', dom: 'MA', fm: 'Excel', st: ['info', '可取数'], ver: 'C' },
  { no: 'A51', nm: '软件配置管理计划', dom: 'CM', fm: 'Word', st: ['ok', '受控'], ver: 'C' },
  { no: 'A83', nm: '软件配置管理报告', dom: 'CM', fm: 'Word', st: ['ok', '已对齐'], ver: 'C' },
  { no: 'A26', nm: '软件质量保证工作报告', dom: 'PQA', fm: 'Word', st: ['ok', '已对齐'], ver: 'B' },
  { no: 'A27', nm: '不符合项报告', dom: 'PQA', fm: 'Word', st: ['ok', '已关闭'], ver: 'B' },
  { no: 'A70', nm: '评审申请报告', dom: '评审', fm: 'Word', st: ['info', '套版'], ver: 'A' },
  { no: 'A19', nm: '软件研制总结报告', dom: '结项', fm: 'Word', st: ['info', '可取数'], ver: 'B' }
];

var TPL_FILTER = '全部';

function tplRender() {
  const c = document.getElementById('content');
  const rows = tplRows();
  c.innerHTML = '<div class="page"><div class="page-title">模板中心</div>' +
    '<div class="page-sub">A1 ~ A83 贯标模板统一取数 · 按过程域检索 · 数据回流组织过程资产库/组织测量库</div>' +
    '<div class="stats">' +
    '<div class="stat"><div class="ic" style="background:#e6f0ff">📁</div><div class="lbl">模板条目</div><div class="num">' + TPL_DATA.length + '</div><div class="sub">10 过程域全量</div></div>' +
    '<div class="stat"><div class="ic" style="background:#f6ffed">✅</div><div class="lbl">当前显示</div><div class="num">' + rows.length + '</div><div class="sub">' + TPL_FILTER + '</div></div>' +
    '<div class="stat"><div class="ic" style="background:#fff7e6">⏳</div><div class="lbl">取数待核</div><div class="num">' + TPL_DATA.filter(t => t.st[1] === '可取数').length + '</div><div class="sub">点「🔗 取数」配置</div></div>' +
    '<div class="stat"><div class="ic" style="background:#ffeaea">🚨</div><div class="lbl">关联告警</div><div class="num">3</div><div class="sub">见告警日志</div></div>' +
    '</div>' +
    '<div class="panel" style="border:1px dashed #b7d3ff;background:#f7fbff;margin-bottom:16px;"><h3><span class="bar"></span>状态图例</h3><div class="legend">' +
    '<div class="lg"><span class="tag info">可取数</span><span class="lg-t">模板字段已配置自动取数来源，生成时直接填充。</span></div>' +
    '<div class="lg"><span class="tag ok">受控/已对齐</span><span class="lg-t">模板已纳入受控库并与体系对齐。</span></div>' +
    '<div class="lg"><span class="tag warn">待更新</span><span class="lg-t">模板内容需补充或修订。</span></div>' +
    '<div class="lg"><span class="tag">套版</span><span class="lg-t">按固定格式套用，无需取数。</span></div>' +
    '</div></div>' +
    '<div class="toolbar"><div class="chips" id="tplChips"></div></div>' +
    '<div class="panel"><div style="overflow-x:auto;"><table class="tbl"><thead><tr>' +
    '<th>编号</th><th>模板名称</th><th>过程域</th><th>载体</th><th>版次</th><th>状态</th><th>操作</th></tr></thead><tbody>' +
    rows.map(function (t) {
      return '<tr><td><span class="ver-badge">' + t.no + '</span></td><td style="text-align:left;font-weight:600">' + t.nm + '</td>' +
        '<td>' + (TPL_DOM_NM[t.dom] || t.dom) + '</td><td>' + t.fm + '</td>' +
        '<td><span class="ver-badge">' + t.ver + '</span></td>' +
        '<td><span class="tag ' + t.st[0] + '">' + t.st[1] + '</span></td>' +
        '<td><button class="btn-sm" onclick="tplSrc(\'' + t.no + '\')">🔗 取数</button> ' +
        '<button class="btn-sm" onclick="tplGotoAlert(\'' + t.no + '\')">告警</button></td></tr>';
    }).join('') +
    '</tbody></table></div></div></div>';
  tplRenderChips();
}

function tplRows() {
  if (TPL_FILTER === '全部') return TPL_DATA;
  return TPL_DATA.filter(t => t.dom === TPL_FILTER);
}

function tplRenderChips() {
  const box = document.getElementById('tplChips');
  if (!box) return;
  box.innerHTML = TPL_DOMS.map(function (d) {
    return '<span class="chip' + (TPL_FILTER === d ? ' on' : '') + '" onclick="tplFilter(\'' + d + '\')">' + d + '</span>';
  }).join('');
}

function tplFilter(d) { TPL_FILTER = d; tplRender(); }

function tplSrc(no) {
  const t = TPL_DATA.find(x => x.no === no);
  const h = '<div class="modal-hd"><div class="mt">' + no + ' ' + (t ? t.nm : '') + ' · 取数配置</div><div class="mx" onclick="closeMask()">×</div></div>' +
    '<div class="modal-bd"><div class="note">该模板支持自动取数，下列锚点从基础数据/过程域自动填充：</div>' +
    '<div class="chips"><span class="chip on">项目信息</span><span class="chip on">阶段划分</span><span class="chip on">工作量</span><span class="chip on">里程碑</span></div>' +
    '<div class="note" style="margin-top:10px;">生成方式：网页端按锚点引擎 {{KEY}} 取数，输出 Word 并同步 SVN 受控库。</div></div>' +
    '<div class="modal-ft"><button class="btn" onclick="closeMask()">关闭</button></div>';
  showMask(h);
}

function tplGotoAlert(no) { alert('跳转告警日志查看与 ' + no + ' 关联的告警（示例）'); }
