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
  // fetch versions and default
  const [vres, dres] = await Promise.all([
    fetch('/api/agents/versions', {headers:{Authorization:`Bearer ${token}`}}),
    fetch('/api/agents/versions/default', {headers:{Authorization:`Bearer ${token}`}})
  ]);
  const versions = vres.ok ? await vres.json() : [];
  const def = dres.ok ? (await dres.json()).default : '';
  const rows = versions.map(v=>{
    const ex = v.exporters || {};
    const exList = Object.keys(ex).map(k=>`${k} → ${Object.keys(ex[k].releases||{}).length} 平台`).join(', ');
    const current = v.version===def ? '（默认）' : '';
    return `<tr>
      <td>${v.version} ${current}</td>
      <td>${exList||'-'}</td>
      <td>
        ${v.version===def?'<span class="tag">当前默认</span>':`<button class='btn-set-default' data-ver='${v.version}'>设为默认</button>`}
        <button class='btn-preview' data-ver='${v.version}'>预览导出器</button>
      </td>
    </tr>`;
  }).join('');
  const installCmd = `wget -qO- $BACKEND/api/agents/install.sh | AGENT_VERSION=${def||'v1'} TOKEN=$TOKEN BACKEND_URL=$BACKEND sh`;
  content.innerHTML = `
    <div class='card'>
      <h3>Agent 版本管理</h3>
      <table class='table'>
        <thead><tr><th>版本</th><th>包含的 Exporter</th><th>操作</th></tr></thead>
        <tbody>${rows||'<tr><td colspan=3>暂无版本</td></tr>'}</tbody>
      </table>
      <div class='small'>
        一键安装（默认版本）：
        <pre><code>${installCmd}</code></pre>
      </div>
    </div>
    <div id='agent-preview'></div>
  `;
  // wire actions
  content.querySelectorAll('.btn-set-default').forEach(b=>{
    b.addEventListener('click', async ()=>{
      const ver = b.dataset.ver;
      const res = await fetch('/api/agents/versions/default', {
        method:'POST', headers:{'Content-Type':'application/json', Authorization:`Bearer ${token}`},
        body: JSON.stringify({version: ver})
      });
      if(res.ok){ renderAgents(); }
    });
  });
  content.querySelectorAll('.btn-preview').forEach(b=>{
    b.addEventListener('click', ()=>{
      const ver = b.dataset.ver;
      const v = versions.find(x=>x.version===ver);
      const ex = v?.exporters||{};
      const lines = Object.keys(ex).map(k=>{
        const rels = ex[k].releases||{};
        return `<div class='row'><b>${k}</b><div class='muted'>${Object.keys(rels).length} 平台</div></div>`;
      }).join('');
      document.getElementById('agent-preview').innerHTML = `<div class='card'><h3>版本 ${ver} Exporter</h3>${lines||'无'}</div>`;
    });
  });
}

// Initial view: if not logged in, redirect to login page
const cached = localStorage.getItem('os_user');
currentUser = cached ? JSON.parse(cached) : null;
(async ()=>{ if(!currentUser) await fetchMe(); renderUserFab(); })();
setView('dashboard');
