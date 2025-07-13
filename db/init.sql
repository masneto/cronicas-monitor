CREATE TABLE IF NOT EXISTS ping (
  id SERIAL PRIMARY KEY,
  host TEXT NOT NULL,
  rtt_avg REAL,               
  packet_loss REAL,           
  timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS http_check (
  id SERIAL PRIMARY KEY,
  host TEXT NOT NULL,
  latency_ms REAL,            
  status_code INT,            
  timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS viaipe (
  id SERIAL PRIMARY KEY,
  cliente TEXT NOT NULL,
  disponibilidade REAL,
  qualidade TEXT,
  consumo_mbps REAL,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);