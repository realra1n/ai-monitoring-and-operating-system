-- Minimal schema demo (not used by in-memory MVP yet)
CREATE TABLE IF NOT EXISTS tenants(
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  status TEXT DEFAULT 'active',
  created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS users(
  id SERIAL PRIMARY KEY,
  tenant_id INT REFERENCES tenants(id),
  email TEXT UNIQUE NOT NULL,
  hash_pwd TEXT NOT NULL,
  role TEXT NOT NULL,
  is_active BOOLEAN DEFAULT TRUE
);
INSERT INTO tenants(name) VALUES('demo') ON CONFLICT DO NOTHING;
