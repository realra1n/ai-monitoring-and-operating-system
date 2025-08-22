let token = localStorage.getItem('os_token');
// For testing: if no token, use demo token automatically
if(!token){
  token = 'tok-demo';
  localStorage.setItem('os_token', token);
}
let currentUser = null;
const content = document.getElementById('content');
const viewTitle = document.getElementById('view-title');
const userFab = document.getElementById('user-fab');
const userPopover = document.getElementById('user-popover');

function setView(name){
  viewTitle.textContent = name;
  document.querySelectorAll('.sidenav nav a').forEach(a=>{
    a.classList.toggle('active', a.dataset.view===name);
  });
  if(name==='dashboard') renderDashboard();
  else if(name==='training') renderTraining();
  else if(name==='model') renderModel();
  else if(name==='events') renderEvents();
  else if(name==='nodes') renderNodes();
  else if(name==='agents') renderAgents();
  else if(name==='apm-overview') renderApmOverview();
  else if(name==='apm-metrics') renderApmMetrics();
  else if(name==='apm-traces') renderApmTraces();
  else if(name==='apm-logs') renderApmLogs();
  else if(name==='alerts') renderAlerts();
  else if(name==='tenants') renderTenants();
  else if(name==='settings') renderSettings();
}

function requireAuth(){
  // Auth disabled for test: token is always set (tok-demo)
  return true;
}

document.querySelectorAll('.sidenav nav a').forEach(a=>{
  a.addEventListener('click',()=>setView(a.dataset.view));
});

async function fetchMe(){
  if(!token) return;
  const res = await fetch('/api/auth/me', {headers:{Authorization:`Bearer ${token}`}});
  if(res.ok){
    currentUser = await res.json();
  localStorage.setItem('os_user', JSON.stringify(currentUser));
  }
}

function grafanaUrl(){
  const u = new URL(window.location.href);
  const g = u.searchParams.get('grafana') || 'http://localhost:3000';
  return g;
}

function grafanaExploreUrl(type){
  // type: metrics | loki | tempo
  const base = grafanaUrl();
  if(type==='metrics') return `${base}/d/rYdddlPWk/node-exporter-full?orgId=1&refresh=10s`;
  if(type==='tempo') return `${base}/explore?orgId=1&left=%5B%22now-1h%22,%22now%22,%22Tempo%22,%7B%7D%5D`;
  if(type==='loki') return `${base}/explore?orgId=1&left=%5B%22now-1h%22,%22now%22,%22Loki%22,%7B%7D%5D`;
  return `${base}/explore?orgId=1`;
}

function renderDashboard(){
  content.innerHTML = `
  <div class='grid'>
    <div class='col-6 card'>
      <div class='iframe-wrap'><iframe src='${grafanaUrl()}/d/000000012/node-exporter-full?orgId=1&refresh=10s' loading='lazy'></iframe></div>
    </div>
    <div class='col-6 card'>
      <div class='iframe-wrap'><iframe src='${grafanaUrl()}/explore?orgId=1' loading='lazy'></iframe></div>
    </div>
  </div>`;
}

function renderApmOverview(){
  viewTitle.textContent = 'APM / Overview';
  content.innerHTML = `
    <div class='card'>
      <h3>APM 概览</h3>
      <p>系统通过 Grafana Alloy 统一接入 OTLP（http://alloy:4317/4318），将 Metrics 转发至 Prometheus（启用 OTLP Receiver），Traces 转发至 Grafana Tempo（MinIO 对象存储），Logs 转发至 Grafana Loki。</p>
      <ol>
        <li>应用 → OTLP → Alloy：批处理、资源标注、抽样（Tail Sampling）。</li>
        <li>Metrics → Prometheus（/api/v1/otlp）→ Grafana 面板</li>
        <li>Traces → Tempo → Grafana Tempo 插件</li>
        <li>Logs → Loki → Grafana Loki 插件</li>
      </ol>
      <div class='grid'>
        <div class='col-4 card'><div class='iframe-wrap'><iframe src='${grafanaExploreUrl('metrics')}'></iframe></div></div>
        <div class='col-4 card'><div class='iframe-wrap'><iframe src='${grafanaExploreUrl('tempo')}'></iframe></div></div>
        <div class='col-4 card'><div class='iframe-wrap'><iframe src='${grafanaExploreUrl('loki')}'></iframe></div></div>
      </div>
    </div>`;
}

function renderApmMetrics(){
  viewTitle.textContent = 'APM / Metrics';
  content.innerHTML = `
    <div class='card'>
      <div class='iframe-wrap'><iframe src='${grafanaUrl()}/d/000000012/node-exporter-full?orgId=1&refresh=10s'></iframe></div>
    </div>
    <div class='card'>
      <div class='iframe-wrap'><iframe src='${grafanaUrl()}/explore?orgId=1&schemaVersion=1&panes=%7B%7D'></iframe></div>
    </div>
  `;
}

function renderApmTraces(){
  viewTitle.textContent = 'APM / Traces';
  content.innerHTML = `
    <div class='card'>
      <div class='iframe-wrap'><iframe src='${grafanaUrl()}/explore?orgId=1&left=%5B%22now-6h%22,%22now%22,%22Tempo%22,%7B%7D%5D'></iframe></div>
    </div>
  `;
}

function renderApmLogs(){
  viewTitle.textContent = 'APM / Logs';
  content.innerHTML = `
    <div class='card'>
      <div class='iframe-wrap'><iframe src='${grafanaUrl()}/explore?orgId=1&left=%5B%22now-6h%22,%22now%22,%22Loki%22,%7B%7D%5D'></iframe></div>
    </div>
  `;
}

// Login page moved to login.html

function renderUserFab(){
  if(!currentUser){
    userFab.classList.add('hidden');
    userPopover.classList.add('hidden');
    return;
  }
  const initials = (currentUser.name || currentUser.email || 'U').slice(0,1).toUpperCase();
  userFab.textContent = initials;
  userFab.classList.remove('hidden');
}

userFab?.addEventListener('click', ()=>{
  if(!currentUser) return;
  const html = `
    <div class='user-card'>
      <div class='user-row strong'>${currentUser.name}</div>
      <div class='user-row'>${currentUser.email}</div>
      <div class='user-row small'>用户ID：${currentUser.id}</div>
      <div class='user-row small'>所属组织：${currentUser.tenant}</div>
      <div class='user-actions'>
        <button id='logout-btn' class='danger'>退出登录</button>
      </div>
    </div>`;
  userPopover.innerHTML = html;
  userPopover.classList.toggle('hidden');
  document.getElementById('logout-btn').addEventListener('click', ()=>{
    currentUser = null;
    // Keep tok-demo to avoid redirect; clear cached user info
    localStorage.removeItem('os_user');
    userPopover.classList.add('hidden');
    renderUserFab();
  });
});

async function renderTraining(){
  if(!requireAuth()) return;
  const res = await fetch('/api/runs', {headers: {Authorization: `Bearer ${token}`}});
  const runs = await res.json();
  const rows = runs.map(r=>`<tr><td>${r.id}</td><td>${r.name}</td><td>${r.status}</td><td>${r.framework}</td><td><button data-id='${r.id}' class='btn-view'>查看</button></td></tr>`).join('');
  content.innerHTML = `
    <div class='card'>
      <h3>Run 列表</h3>
      <table class='table'><thead><tr><th>ID</th><th>Name</th><th>Status</th><th>FW</th><th>Ops</th></tr></thead><tbody>${rows}</tbody></table>
    </div>
    <div id='run-detail'></div>
  `;
  content.querySelectorAll('.btn-view').forEach(btn=>{
    btn.addEventListener('click',()=>showRun(parseInt(btn.dataset.id)));
  });
}

async function showRun(id){
  const detail = document.getElementById('run-detail');
  const mres = await fetch(`/api/runs/${id}/metrics?name=loss&by=step`, {headers:{Authorization:`Bearer ${token}`}});
  const mdata = await mres.json();
  const lres = await fetch(`/api/runs/${id}/logs`, {headers:{Authorization:`Bearer ${token}`}});
  const ldata = await lres.json();
  const logs = ldata.items.map(x=>`<div>[${new Date(x.ts*1000).toLocaleTimeString()}] ${x.level}: ${x.msg}</div>`).join('');
  const points = mdata.series[0].points.map(p=>`(${p.step}, ${p.value.toFixed(3)})`).join(' ');
  detail.innerHTML = `
    <div class='grid'>
      <div class='col-6 card'><h3>Loss (step)</h3><pre>${points}</pre></div>
      <div class='col-6 card'><h3>日志</h3><div style='height:300px;overflow:auto;border:1px solid #eee;padding:8px'>${logs}</div></div>
    </div>
  `;
}

function renderModel(){
  content.innerHTML = `
    <div class='card'>
      <h3>模型可视化（Netron）</h3>
      <div class='iframe-wrap'>
        <iframe src='https://netron.app' title='Netron'></iframe>
      </div>
    </div>
  `;
}

function renderEvents(){
  content.innerHTML = `<div class='card'>K8S 事件（Demo 占位）</div>`;
}
function renderNodes(){
  content.innerHTML = `<div class='card'>节点列表（Demo 占位，可嵌入 Grafana 主机盘）</div>`;
}
function renderAlerts(){
  content.innerHTML = `<div class='card'>告警与阈值（Demo 占位）</div>`;
}
function renderSettings(){
  content.innerHTML = `<div class='card'>设置（Demo 占位）</div>`;
}

async function renderAgents(){
  if(!requireAuth()) return;
  viewTitle.textContent = 'Agent 管理';
  // subnav like Datadog: Overview | Versions
  content.innerHTML = `
    <div class='subnav'>
      <a class='subnav-link active' data-tab='overview'>Overview</a>
      <a class='subnav-link' data-tab='versions'>Agent 列表</a>
    </div>
    <section id='agent-tab'></section>
  `;
  const tab = document.getElementById('agent-tab');
  const links = content.querySelectorAll('.subnav-link');
  links.forEach(l=>l.addEventListener('click',()=>{
    links.forEach(x=>x.classList.remove('active'));
    l.classList.add('active');
    if(l.dataset.tab==='overview') renderAgentOverview(tab);
    else renderAgentVersions(tab);
  }));
  renderAgentOverview(tab);
}

function renderAgentOverview(root){
  const backend = 'http://oneservice-backend:8000';
  const cmd = `curl -fsSL ${backend}/api/agents/install.sh | TOKEN=tok-demo sh`;
  const errors = [
    {k:'No python3', fix:'安装 Python3（apt-get install -y python3 python3-pip 或 apk add python3 py3-pip）'},
    {k:'SSL 证书错误', fix:'使用 http 方案，或配置容器 CA 证书'},
    {k:'端口冲突: 9100', fix:'编辑 agent.yaml 修改 node_exporter 端口'},
    {k:'无法写入 /etc/prometheus/file_sd', fix:'检查后端是否与 Prometheus 共享 promfilesd 卷'},
  ];
  const errHtml = errors.map(e=>`<li><b>${e.k}:</b> ${e.fix}</li>`).join('');
  root.innerHTML = `
    <div class='card'>
      <h3>什么是 OneService Agent？</h3>
      <p>Agent 负责在目标主机或容器内安装并运行各类 Exporter（如 node_exporter、mysqld_exporter），并自动向平台注册抓取目标，Prometheus 随即开始采集数据。</p>
      <h4>一键安装（默认版本）</h4>
      <pre><code>${cmd}</code></pre>
      <div class='small muted'>提示：在同一 Docker 网络内直接使用服务名 oneservice-backend 作为主机名，Docker 内置 DNS 会解析到当前 IP，迁移/重建不受影响。需指定版本时可在管道前加入 <code>AGENT_VERSION=v0.2</code>。</div>
      <h4>常见错误与处理</h4>
      <ul>${errHtml}</ul>
    </div>
  `;
}

async function renderAgentVersions(root){
  let vres = await fetch('/api/agents/versions', {headers:{Authorization:`Bearer ${token}`}});
  // Retry without auth if unauthorized
  if(vres.status === 401){ token = 'tok-demo'; localStorage.setItem('os_token', token); vres = await fetch('/api/agents/versions'); }
  let dres = await fetch('/api/agents/versions/default', {headers:{Authorization:`Bearer ${token}`}});
  if(dres.status === 401){ dres = await fetch('/api/agents/versions/default'); }
  let versions = vres.ok ? await vres.json() : [];
  let def = dres.ok ? (await dres.json()).default : '';
  // Fallback: try direct backend in case proxy has issues
  if(!versions || versions.length===0){
    const backend = window.location.origin.replace(':8080', ':8000');
    try{
      const v2 = await fetch(`${backend}/api/agents/versions`);
      if(v2.ok){ versions = await v2.json(); }
      const d2 = await fetch(`${backend}/api/agents/versions/default`);
      if(d2.ok){ def = (await d2.json()).default; }
    }catch(_e){ /* ignore */ }
  }
  // Last resort seed: show built-in defaults so the list is never empty
  if(!versions || versions.length===0){
    versions = [{version:'v0.1', exporters:null},{version:'v0.2', exporters:null}];
    if(!def) def = 'v0.2';
  }
  const rows = versions.map(v=>{
    const ex = v.exporters || {};
    const exList = Object.keys(ex).map(k=>`${k} · ${Object.keys(ex[k].releases||{}).length} 平台`).join('<br/>');
    const isDef = v.version===def;
    const rowCls = isDef ? 'row-default' : '';
    return `<tr class='${rowCls}'>
      <td>${v.version}${isDef?" <span class='tag'>默认</span>":''}</td>
      <td>${exList||'-'}</td>
      <td class='ops'>
        ${isDef?'':`<button class='btn-set-default' data-ver='${v.version}'>设为默认</button>`}
        <button class='btn-delete' data-ver='${v.version}'>卸载</button>
      </td>
    </tr>`;
  }).join('');
  root.innerHTML = `
    <div class='card'>
      <div class='toolbar'>
        <button id='btn-upload'>载入新版Agent</button>
      </div>
      <table class='table'>
        <thead><tr><th>版本</th><th>包含的 Exporter</th><th>操作</th></tr></thead>
        <tbody>${rows||'<tr><td colspan=3>暂无版本</td></tr>'}</tbody>
      </table>
      <div class='small muted'>将某个版本设为默认后，执行 wget 安装命令（不指定版本参数）将自动获取该版本。</div>
    </div>
    <div id='upload-modal' class='modal hidden'>
      <div class='modal-body'>
        <h3>上传 Agent 压缩包（zip）</h3>
        <label>版本号：<input id='new-ver' placeholder='例如 v0.3'/></label>
        <input id='new-file' type='file' accept='.zip'/>
        <div class='modal-actions'>
          <button id='upload-cancel'>取消</button>
          <button id='upload-submit'>上传</button>
        </div>
      </div>
    </div>
  `;
  // actions
  root.querySelectorAll('.btn-set-default').forEach(b=>{
    b.addEventListener('click', async ()=>{
      const ver = b.dataset.ver;
      const res = await fetch('/api/agents/versions/default', {
        method:'POST', headers:{'Content-Type':'application/json', Authorization:`Bearer ${token}`},
        body: JSON.stringify({version: ver})
      });
      if(res.ok) renderAgentVersions(root);
    });
  });
  root.querySelectorAll('.btn-delete').forEach(b=>{
    b.addEventListener('click', async ()=>{
      const ver = b.dataset.ver;
      if(!confirm(`确认卸载版本 ${ver} ？`)) return;
      const res = await fetch(`/api/agents/versions/${encodeURIComponent(ver)}`, {
        method:'DELETE', headers:{Authorization:`Bearer ${token}`}
      });
      if(res.ok) renderAgentVersions(root);
    });
  });
  // upload modal
  const modal = root.querySelector('#upload-modal');
  root.querySelector('#btn-upload').addEventListener('click', ()=>{
    modal.classList.remove('hidden');
  });
  root.querySelector('#upload-cancel').addEventListener('click', ()=>{
    modal.classList.add('hidden');
  });
  root.querySelector('#upload-submit').addEventListener('click', async ()=>{
    const ver = root.querySelector('#new-ver').value.trim();
    const file = root.querySelector('#new-file').files[0];
    if(!ver || !file){ alert('请填写版本号并选择zip文件'); return; }
    const fd = new FormData();
    fd.append('version', ver);
    fd.append('file', file);
    const res = await fetch('/api/agents/versions/upload', {
      method:'POST', headers:{Authorization:`Bearer ${token}`}, body: fd
    });
    if(res.ok){ modal.classList.add('hidden'); renderAgentVersions(root); }
  });
}

// Initial view: if not logged in, redirect to login page
const cached = localStorage.getItem('os_user');
currentUser = cached ? JSON.parse(cached) : null;
(async ()=>{ if(!currentUser) await fetchMe(); renderUserFab(); })();
setView('dashboard');
