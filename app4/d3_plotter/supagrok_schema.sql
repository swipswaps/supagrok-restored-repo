-- PRF-SUPAGROK-TIMESCALEDB-SCHEMA
-- Defines hypertable to store EEG logs with timestamp and source tracking

CREATE TABLE IF NOT EXISTS eeg_logs (
    timestamp TIMESTAMPTZ NOT NULL,
    magnitude REAL NOT NULL,
    source TEXT DEFAULT 'ddwrt',
    PRIMARY KEY (timestamp, source)
);

SELECT create_hypertable('eeg_logs', 'timestamp', if_not_exists => TRUE);
