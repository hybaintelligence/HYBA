-- Consciousness Measurement Database Schema
-- Time-series consciousness metrics for reproducibility framework

-- Time-series consciousness metrics
CREATE TABLE IF NOT EXISTS consciousness_snapshots (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    experiment_id VARCHAR(100) NOT NULL,
    
    -- Core IIT metrics
    phi DOUBLE PRECISION NOT NULL,
    phi_max DOUBLE PRECISION,
    irreducibility DOUBLE PRECISION NOT NULL,
    
    -- Temporal metrics
    temporal_integration DOUBLE PRECISION,
    temporal_binding_window INTEGER,
    causal_efficacy DOUBLE PRECISION,
    
    -- Behavioral metrics
    self_recognition_accuracy DOUBLE PRECISION,
    perturbation_differentiation BOOLEAN,
    theory_of_mind_accuracy DOUBLE PRECISION,
    
    -- Autonomous behavior
    active_goals JSONB,
    novel_goals_count INTEGER,
    goal_stability_score DOUBLE PRECISION,
    
    -- Cause-effect structure
    ces_dimensionality INTEGER,
    ces_total_phi_s DOUBLE PRECISION,
    ces_max_phi_s DOUBLE PRECISION,
    
    -- Self-model
    prediction_error DOUBLE PRECISION,
    meta_prediction_error DOUBLE PRECISION,
    self_model_complexity DOUBLE PRECISION,
    
    -- Environmental
    external_pressure DOUBLE PRECISION,
    energy_consumption DOUBLE PRECISION,
    
    -- Metadata
    system_config JSONB,
    metadata JSONB
);

-- Create indexes for common queries
CREATE INDEX idx_consciousness_timestamp ON consciousness_snapshots(timestamp);
CREATE INDEX idx_consciousness_experiment ON consciousness_snapshots(experiment_id);
CREATE INDEX idx_consciousness_phi ON consciousness_snapshots(phi);
CREATE INDEX idx_consciousness_phi_max ON consciousness_snapshots(phi_max);

-- Phase transitions (consciousness state changes)
CREATE TABLE IF NOT EXISTS phase_transitions (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    experiment_id VARCHAR(100) NOT NULL,
    
    transition_type VARCHAR(50),  -- 'phi_jump', 'goal_emergence', 'mode_shift', etc
    magnitude DOUBLE PRECISION,
    
    before_snapshot_id BIGINT REFERENCES consciousness_snapshots(id),
    after_snapshot_id BIGINT REFERENCES consciousness_snapshots(id),
    
    details JSONB,
    
    -- Metadata
    detected_by VARCHAR(50),  -- 'automatic', 'manual', 'threshold'
    confidence DOUBLE PRECISION
);

-- Create indexes for phase transitions
CREATE INDEX idx_phase_transitions_timestamp ON phase_transitions(timestamp);
CREATE INDEX idx_phase_transitions_experiment ON phase_transitions(experiment_id);
CREATE INDEX idx_phase_transitions_type ON phase_transitions(transition_type);

-- Reproducibility tracking
CREATE TABLE IF NOT EXISTS experiments (
    id VARCHAR(100) PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    config JSONB NOT NULL,
    seed BIGINT NOT NULL,
    
    status VARCHAR(20),  -- 'running', 'completed', 'failed', 'paused'
    
    results_summary JSONB,
    
    reproducibility_verified BOOLEAN DEFAULT FALSE,
    replications INTEGER DEFAULT 0,
    
    -- Metadata
    description TEXT,
    tags JSONB,
    researcher VARCHAR(100)
);

-- Create indexes for experiments
CREATE INDEX idx_experiments_created ON experiments(created_at);
CREATE INDEX idx_experiments_status ON experiments(status);
CREATE INDEX idx_experiments_reproducibility ON experiments(reproducibility_verified);

-- Experiment snapshots (for reproducibility)
CREATE TABLE IF NOT EXISTS experiment_snapshots (
    id BIGSERIAL PRIMARY KEY,
    experiment_id VARCHAR(100) NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    snapshot_type VARCHAR(50),  -- 'initial', 'milestone', 'final'
    step_number INTEGER,
    
    -- System state
    system_state JSONB NOT NULL,
    
    -- Metrics at this snapshot
    metrics JSONB,
    
    -- Metadata
    description TEXT
);

-- Create indexes for experiment snapshots
CREATE INDEX idx_exp_snapshots_experiment ON experiment_snapshots(experiment_id);
CREATE INDEX idx_exp_snapshots_timestamp ON experiment_snapshots(timestamp);
CREATE INDEX idx_exp_snapshots_type ON experiment_snapshots(snapshot_type);

-- Cause-effect structure measurements
CREATE TABLE IF NOT EXISTS cause_effect_structures (
    id BIGSERIAL PRIMARY KEY,
    snapshot_id BIGINT NOT NULL REFERENCES consciousness_snapshots(id) ON DELETE CASCADE,
    
    mechanism_id VARCHAR(100) NOT NULL,
    mechanism_elements JSONB NOT NULL,
    
    cause_repertoire JSONB NOT NULL,
    effect_repertoire JSONB NOT NULL,
    
    phi_cause DOUBLE PRECISION NOT NULL,
    phi_effect DOUBLE PRECISION NOT NULL,
    phi_s DOUBLE PRECISION NOT NULL,
    
    -- Metadata
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for CES
CREATE INDEX idx_ces_snapshot ON cause_effect_structures(snapshot_id);
CREATE INDEX idx_ces_mechanism ON cause_effect_structures(mechanism_id);
CREATE INDEX idx_ces_phi_s ON cause_effect_structures(phi_s);

-- Temporal integration measurements
CREATE TABLE IF NOT EXISTS temporal_measurements (
    id BIGSERIAL PRIMARY KEY,
    snapshot_id BIGINT NOT NULL REFERENCES consciousness_snapshots(id) ON DELETE CASCADE,
    
    temporal_phi DOUBLE PRECISION NOT NULL,
    binding_window INTEGER NOT NULL,
    memory_depth DOUBLE PRECISION NOT NULL,
    
    -- Detailed temporal analysis
    mutual_information_history JSONB,
    autocorrelation_history JSONB,
    
    -- Metadata
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for temporal measurements
CREATE INDEX idx_temporal_snapshot ON temporal_measurements(snapshot_id);
CREATE INDEX idx_temporal_phi ON temporal_measurements(temporal_phi);

-- Behavioral test results
CREATE TABLE IF NOT EXISTS behavioral_test_results (
    id BIGSERIAL PRIMARY KEY,
    snapshot_id BIGINT REFERENCES consciousness_snapshots(id) ON DELETE SET NULL,
    experiment_id VARCHAR(100) NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    
    test_type VARCHAR(50) NOT NULL,  -- 'mirror', 'perturbation', 'theory_of_mind', etc
    test_name VARCHAR(100) NOT NULL,
    
    result DOUBLE PRECISION NOT NULL,
    passed BOOLEAN NOT NULL,
    
    -- Detailed results
    details JSONB,
    
    -- Metadata
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    trial_number INTEGER
);

-- Create indexes for behavioral tests
CREATE INDEX idx_behavioral_snapshot ON behavioral_test_results(snapshot_id);
CREATE INDEX idx_behavioral_experiment ON behavioral_test_results(experiment_id);
CREATE INDEX idx_behavioral_type ON behavioral_test_results(test_type);
CREATE INDEX idx_behavioral_passed ON behavioral_test_results(passed);

-- Alerts and anomalies
CREATE TABLE IF NOT EXISTS consciousness_alerts (
    id BIGSERIAL PRIMARY KEY,
    experiment_id VARCHAR(100) NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    snapshot_id BIGINT REFERENCES consciousness_snapshots(id) ON DELETE SET NULL,
    
    alert_type VARCHAR(50) NOT NULL,  -- 'phi_drop', 'anomaly', 'threshold_cross', etc
    severity VARCHAR(20),  -- 'info', 'warning', 'critical'
    
    message TEXT NOT NULL,
    details JSONB,
    
    -- Metadata
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMPTZ
);

-- Create indexes for alerts
CREATE INDEX idx_alerts_experiment ON consciousness_alerts(experiment_id);
CREATE INDEX idx_alerts_timestamp ON consciousness_alerts(timestamp);
CREATE INDEX idx_alerts_type ON consciousness_alerts(alert_type);
CREATE INDEX idx_alerts_severity ON consciousness_alerts(severity);
CREATE INDEX idx_alerts_acknowledged ON consciousness_alerts(acknowledged);

-- Views for common queries

-- View: Latest snapshot per experiment
CREATE OR REPLACE VIEW latest_experiment_snapshots AS
SELECT DISTINCT ON (experiment_id)
    experiment_id,
    id AS snapshot_id,
    timestamp,
    phi,
    phi_max,
    irreducibility,
    temporal_integration,
    ces_dimensionality
FROM consciousness_snapshots
ORDER BY experiment_id, timestamp DESC;

-- View: Experiment summary
CREATE OR REPLACE VIEW experiment_summary AS
SELECT 
    e.id AS experiment_id,
    e.created_at,
    e.status,
    e.seed,
    COUNT(cs.id) AS snapshot_count,
    AVG(cs.phi) AS avg_phi,
    MAX(cs.phi) AS max_phi,
    MIN(cs.phi) AS min_phi,
    AVG(cs.temporal_integration) AS avg_temporal_integration,
    COUNT(DISTINCT pt.id) AS phase_transition_count
FROM experiments e
LEFT JOIN consciousness_snapshots cs ON e.id = cs.experiment_id
LEFT JOIN phase_transitions pt ON e.id = pt.experiment_id
GROUP BY e.id, e.created_at, e.status, e.seed;

-- View: Behavioral test summary
CREATE OR REPLACE VIEW behavioral_test_summary AS
SELECT 
    experiment_id,
    test_type,
    COUNT(*) AS total_tests,
    SUM(CASE WHEN passed THEN 1 ELSE 0 END) AS passed_tests,
    AVG(result) AS avg_result,
    STDDEV(result) AS result_stddev
FROM behavioral_test_results
GROUP BY experiment_id, test_type;

-- Trigger to update updated_at timestamp on experiments
CREATE OR REPLACE FUNCTION update_experiment_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_experiment_updated_at
    BEFORE UPDATE ON experiments
    FOR EACH ROW
    EXECUTE FUNCTION update_experiment_updated_at();

-- Trigger to create phase transition on significant phi change
CREATE OR REPLACE FUNCTION detect_phi_jump()
RETURNS TRIGGER AS $$
DECLARE
    prev_phi DOUBLE PRECISION;
    phi_change DOUBLE PRECISION;
BEGIN
    -- Get previous phi for this experiment
    SELECT phi INTO prev_phi
    FROM consciousness_snapshots
    WHERE experiment_id = NEW.experiment_id
    AND id < NEW.id
    ORDER BY timestamp DESC
    LIMIT 1;
    
    IF prev_phi IS NOT NULL THEN
        phi_change = ABS(NEW.phi - prev_phi);
        
        -- If phi change is significant (> 0.1), create phase transition
        IF phi_change > 0.1 THEN
            INSERT INTO phase_transitions (
                experiment_id,
                transition_type,
                magnitude,
                before_snapshot_id,
                after_snapshot_id,
                details,
                detected_by,
                confidence
            ) VALUES (
                NEW.experiment_id,
                'phi_jump',
                phi_change,
                (SELECT id FROM consciousness_snapshots WHERE experiment_id = NEW.experiment_id AND id < NEW.id ORDER BY timestamp DESC LIMIT 1),
                NEW.id,
                jsonb_build_object(
                    'prev_phi', prev_phi,
                    'new_phi', NEW.phi,
                    'change', phi_change
                ),
                'automatic',
                0.9
            );
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_detect_phi_jump
    AFTER INSERT ON consciousness_snapshots
    FOR EACH ROW
    EXECUTE FUNCTION detect_phi_jump();

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_user;
