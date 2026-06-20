CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'operator',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_login TIMESTAMPTZ,
    created_by VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS experiments (
    id VARCHAR(100) PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    config JSONB NOT NULL,
    seed BIGINT NOT NULL,
    status VARCHAR(20),
    results_summary JSONB,
    reproducibility_verified BOOLEAN DEFAULT false,
    replications INTEGER DEFAULT 0,
    description TEXT,
    tags JSONB,
    researcher VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS consciousness_snapshots (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    experiment_id VARCHAR(100) NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    phi DOUBLE PRECISION NOT NULL,
    phi_max DOUBLE PRECISION,
    irreducibility DOUBLE PRECISION NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    actor_username VARCHAR(100) NOT NULL,
    actor_role VARCHAR(50),
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id VARCHAR(255),
    details JSONB,
    ip_address VARCHAR(45)
);

CREATE INDEX IF NOT EXISTS ix_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS ix_audit_logs_actor_username ON audit_logs(actor_username);
CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS ix_consciousness_snapshots_experiment_id ON consciousness_snapshots(experiment_id);
