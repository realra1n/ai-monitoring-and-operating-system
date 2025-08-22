from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get('/api/health')
    assert r.status_code == 200
    assert r.json().get('status') == 'ok'

def test_login_and_runs():
    r = client.post('/api/auth/login', data={'username':'demo@oneservice.local', 'password':'demo123'})
    assert r.status_code == 200
    token = r.json()['access_token']
    r2 = client.get('/api/runs', headers={'Authorization': f'Bearer {token}'})
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)
