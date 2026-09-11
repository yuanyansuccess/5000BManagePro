// 作者：袁燕
// 功能：通用「行内编辑 CRUD 表格」工厂。收敛 pp/user/settings 各页手抄的
//       Load/Add/SaveNew/Save/Del 五件套（原 10 组复制粘贴，现一处维护）。
// 设计：组间差异全部配置化（Api 方法 / 列定义 / 弹窗字段 / 刷新与提示方式），
//       页面只需提供配置与对外函数别名，功能逻辑与手写版完全一致。

/**
 * 创建一组行内编辑 CRUD 表格。
 * 输入：cfg 配置对象，字段如下——
 *   tbody       表体 id（行内输入按 #tbody [data-id][data-f] 定位）
 *   empty       空态文案
 *   colspan     空态/加载失败行的合并列数
 *   api         {list(pid), create(pid,p), update(pid,id,p), del(pid,id)}
 *   cols        行内编辑列 [{f,w,num?,color?(team)->颜色}]，顺序即渲染顺序
 *   rowPrepend  可选 fn(item,idx)->td串（如组织机构序号列）
 *   afterChange 增删改成功后的刷新函数（如 ppHwLoad / userRender）
 *   notify      提示方式 'toast'|'alert'（toast 模式成功提示"已保存/已删除"）
 *   confirmDel  删除确认文案
 *   loadRender  true=load 内直接渲染（pp 页子页签）；false=只取数由页面统一渲染（user 页）
 *   failSilent  true=取数失败仅 console.error（user 页）；false=失败写进 tbody（pp 页）
 *   btn         可选 {save:'btn ghost sm',saveText:'保存',del:'btn ghost sm',delText:'删'}（缺省 btn-sm ok/danger 风格）
 *   dialog      新增弹窗 {title(string或fn延迟求值), layout:'grid2'|'list', msgId,
 *                        fields:[{id,label,type,placeholder,value}], required:{id,msg},
 *                        payload:fn(g,items)->payload, successMsg?}
 * 输出：{load, renderRows, save, del, addDialog, saveNew}
 */
function crudTable(cfg) {
  var state = { items: [] };

  // 行内输入取值：数字字段转数值（与原各页 +v||0 口径一致）
  function cellVal(id, f) {
    var el = document.querySelector('#' + cfg.tbody + ' [data-id="' + id + '"][data-f="' + f + '"]');
    return el ? el.value.trim() : '';
  }
  function rowPayload(id) {
    var p = {};
    (cfg.cols || []).forEach(function (c) {
      p[c.f] = c.num ? (+cellVal(id, c.f) || 0) : cellVal(id, c.f);
    });
    return p;
  }
  function cellHtml(item, c) {
    var style = 'width:' + (c.w || '100px');
    if (c.color) {
      var col = c.color(item[c.f] || '');
      style += ';background:' + col + '14;color:' + col;
    }
    return '<td><input data-f="' + c.f + '" data-id="' + item.id + '" value="' +
      (item[c.f] == null ? '' : item[c.f]) + '" style="' + style + '"></td>';
  }
  function notifyErr(msg) { cfg.notify === 'toast' ? toast(msg) : alert(msg); }

  /** 渲染表体（数据到位后调用） */
  function renderRows() {
    var tb = document.getElementById(cfg.tbody);
    if (!tb) return;
    if (!state.items.length) {
      tb.innerHTML = '<tr><td colspan="' + cfg.colspan + '" style="text-align:center;color:var(--text-3);padding:24px">' + cfg.empty + '</td></tr>';
      return;
    }
    var btn = cfg.btn || {};
    var saveCls = btn.save || 'btn-sm ok', delCls = btn.del || 'btn-sm danger';
    tb.innerHTML = state.items.map(function (item, idx) {
      return '<tr>' + (cfg.rowPrepend ? cfg.rowPrepend(item, idx) : '') +
        (cfg.cols || []).map(function (c) { return cellHtml(item, c); }).join('') +
        '<td><button class="' + saveCls + '" onclick="' + cfg.key + 'Save(' + item.id + ')">' + (btn.saveText || '保存') + '</button>' +
        '<button class="' + delCls + '" onclick="' + cfg.key + 'Del(' + item.id + ')">' + (btn.delText || '删除') + '</button></td></tr>';
    }).join('');
  }

  /** 从后端拉取列表（loadRender=true 时渲染表体） */
  async function load() {
    try {
      var resp = await cfg.api.list(Api.curProjectId());
      state.items = (resp && resp.data) ? resp.data : (Array.isArray(resp) ? resp : []);
    } catch (e) {
      console.error('加载' + cfg.empty.slice(2) + '失败：', e);
      state.items = [];
      if (!cfg.failSilent) {
        var tb = document.getElementById(cfg.tbody);
        if (tb) tb.innerHTML = '<tr><td colspan="' + cfg.colspan + '" style="color:#e74c3c;">加载失败：' + (e.message || e) + '</td></tr>';
        return;
      }
    }
    if (cfg.loadRender !== false) renderRows();
  }

  /** pp 页专用：失败信息写 tbody 的拉取（与原 ppXxxLoad 行为一致，含空态文案差异） */
  function loadPpStyle(emptyText) {
    var tb = document.getElementById(cfg.tbody);
    if (!tb) return;
    cfg.api.list(Api.curProjectId()).then(function (r) {
      state.items = (r && r.data) || [];
      if (!state.items.length) {
        tb.innerHTML = '<tr><td colspan="' + cfg.colspan + '" style="text-align:center;color:#999;">' + (emptyText || cfg.empty) + '</td></tr>';
        return;
      }
      renderRows();
    }).catch(function (e) {
      tb.innerHTML = '<tr><td colspan="' + cfg.colspan + '" style="color:#e74c3c;">加载失败：' + (e.message || e) + '</td></tr>';
    });
  }

  /** 行内保存 */
  async function save(id) {
    try {
      await cfg.api.update(Api.curProjectId(), id, rowPayload(id));
      if (cfg.notify === 'toast') toast('已保存');
      await cfg.afterChange();
    } catch (e) { notifyErr('保存失败：' + (e.message || e)); }
  }

  /** 删除（带确认） */
  async function del(id) {
    if (!confirm(cfg.confirmDel || '确认删除？')) return;
    try {
      await cfg.api.del(Api.curProjectId(), id);
      if (cfg.notify === 'toast') toast('已删除');
      await cfg.afterChange();
    } catch (e) { notifyErr('删除失败：' + (e.message || e)); }
  }

  /** 新增弹窗（layout=grid2 为 pp 页宽版两列；list 为 user 页单列） */
  function addDialog() {
    var d = cfg.dialog;
    var grid2 = d.layout === 'grid2';
    var msg = '<div id="' + d.msgId + '" ' + (grid2 ? 'class="span2" ' : '') +
      'style="color:#e74c3c;font-size:13px;min-height:16px;"></div>';
    var fields = (d.fields || []).map(function (f) {
      return '<div class="field"><label>' + f.label + '</label><input id="' + f.id + '"' +
        (f.type ? ' type="' + f.type + '"' : '') +
        (f.placeholder ? ' placeholder="' + f.placeholder + '"' : '') +
        (f.value != null ? ' value="' + f.value + '"' : '') + '></div>';
    }).join('');
    var title = typeof d.title === 'function' ? d.title() : d.title;
    var html = '<div class="modal-mask" onclick="if(event.target===this)this.remove()">' +
      '<div class="modal' + (grid2 ? ' modal-lg' : '') + '"><div class="modal-hd">' + title + '</div>' +
      '<div class="modal-bd' + (grid2 ? ' grid2' : '') + '">' + fields + msg + '</div>' +
      '<div class="modal-ft"><button class="btn ghost" onclick="this.closest(\'.modal-mask\').remove()">取消</button>' +
      '<button class="btn primary" onclick="' + cfg.key + 'SaveNew()">保存</button></div></div></div>';
    document.body.insertAdjacentHTML('beforeend', html);
  }

  /** 新增保存（成功后关弹窗并刷新；successMsg 时 toast 提示） */
  async function saveNew() {
    var d = cfg.dialog;
    var msg = document.getElementById(d.msgId);
    var g = function (id) { var el = document.getElementById(id); return el ? el.value.trim() : ''; };
    if (d.required && !g(d.required.id)) { msg.textContent = d.required.msg; return; }
    try {
      await cfg.api.create(Api.curProjectId(), d.payload(g, state.items));
      document.querySelector('.modal-mask').remove();
      if (d.successMsg) toast(d.successMsg);
      await cfg.afterChange();
    } catch (e) { msg.textContent = '保存失败：' + (e.message || e); }
  }

  return { load: load, loadPpStyle: loadPpStyle, renderRows: renderRows, save: save, del: del, addDialog: addDialog, saveNew: saveNew, state: state };
}
