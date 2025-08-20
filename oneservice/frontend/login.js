async function doLogin(email, password){
  const form = new URLSearchParams();
  form.append('username', email);
  form.append('password', password);
  const res = await fetch('/api/auth/login', {
    method:'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form
  });
  if(!res.ok) throw new Error('登录失败');
  const data = await res.json();
  localStorage.setItem('os_token', data.access_token);
  // fetch profile to prime cache (optional)
  try{
    const me = await fetch('/api/auth/me', {headers:{Authorization:`Bearer ${data.access_token}`}});
    if(me.ok){
      const user = await me.json();
      localStorage.setItem('os_user', JSON.stringify(user));
    }
  }catch{}
  window.location.href = '/';
}

function init(){
  const btn = document.getElementById('login-btn');
  const msg = document.getElementById('login-msg');
  btn.addEventListener('click', async ()=>{
    const email = document.getElementById('login-email').value;
    const pwd = document.getElementById('login-password').value;
    msg.textContent='';
    try{
      await doLogin(email, pwd);
    }catch(e){
      msg.textContent='登录失败，请重试';
    }
  });
}

document.addEventListener('DOMContentLoaded', init);
