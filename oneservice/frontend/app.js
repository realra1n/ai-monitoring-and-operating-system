let token = localStorage.getItem('os_token');
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
  else if(name==='alerts') renderAlerts();
  else if(name==='tenants') renderTenants();
  else if(name==='settings') renderSettings();
}

function requireAuth(){
  if(!token){
    window.location.href = '/login.html';
    return false;
  }
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
  token = null; currentUser = null;
  localStorage.removeItem('os_token');
  localStorage.removeItem('os_user');
    userPopover.classList.add('hidden');
    renderUserFab();
  window.location.href = '/login.html';
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
function renderTenants(){
  content.innerHTML = `<div class='card'>多租户与用户（Demo 占位）</div>`;
}
function renderSettings(){
  content.innerHTML = `<div class='card'>设置（Demo 占位）</div>`;
}

// Initial view: if not logged in, redirect to login page
if(!token){
  window.location.href = '/login.html';
}else{
  const cached = localStorage.getItem('os_user');
  currentUser = cached ? JSON.parse(cached) : null;
  (async ()=>{ if(!currentUser) await fetchMe(); renderUserFab(); })();
  setView('dashboard');
}
