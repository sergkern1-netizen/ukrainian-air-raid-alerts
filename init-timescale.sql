-- TimescaleDB + PostGIS Initialization
-- Extensions
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS postgis CASCADE;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create HYPERTABLE for alerts time series
CREATE TABLE IF NOT EXISTS alerts (
    id BIGSERIAL,
    time TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL,
    source_id VARCHAR(32) NOT NULL,
    event_type VARCHAR(32) NOT NULL,
    oblast VARCHAR(64),
    raion VARCHAR(128),
    h3_index VARCHAR(16),
    alert_duration_seconds INT,
    alert_active BOOLEAN,
    air_defense_active BOOLEAN,
    inferred_end_flag BOOLEAN DEFAULT FALSE,
    data_quality_score FLOAT DEFAULT 1.0,
    raw_data JSONB,
    PRIMARY KEY (time, id)
) PARTITION BY RANGE (time);

SELECT create_hypertable('alerts', 'time', if_not_exists => TRUE);

-- Create indexes for time series queries
CREATE INDEX IF NOT EXISTS idx_alerts_time ON alerts (time DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_h3 ON alerts (h3_index, time DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_oblast ON alerts (oblast, time DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_source ON alerts (source_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_ingested ON alerts (ingested_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_event_type ON alerts (event_type, time DESC);

-- Enable compression for cold chunks (>7 days)
ALTER TABLE alerts SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'oblast,h3_index,source_id',
    timescaledb.compress_orderby = 'time DESC'
);

SELECT add_compression_policy('alerts', INTERVAL '7 days', if_not_exists => TRUE);

-- Create HYPERTABLE for weather data
CREATE TABLE IF NOT EXISTS weather (
    id BIGSERIAL,
    time TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL,
    h3_index VARCHAR(16) NOT NULL,
    latitude FLOAT,
    longitude FLOAT,
    pressure_hpa FLOAT,
    wind_speed_ms FLOAT,
    wind_direction_deg FLOAT,
    cloud_cover_percent INT,
    convective_potential FLOAT,
    visibility_km FLOAT,
    temperature_celsius FLOAT,
    precipitation_mm FLOAT,
    PRIMARY KEY (time, id)
) PARTITION BY RANGE (time);

SELECT create_hypertable('weather', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_weather_time ON weather (time DESC);
CREATE INDEX IF NOT EXISTS idx_weather_h3 ON weather (h3_index, time DESC);
CREATE INDEX IF NOT EXISTS idx_weather_location ON weather (latitude, longitude);

ALTER TABLE weather SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'h3_index',
    timescaledb.compress_orderby = 'time DESC'
);

SELECT add_compression_policy('weather', INTERVAL '7 days', if_not_exists => TRUE);

-- Create HYPERTABLE for predictions
CREATE TABLE IF NOT EXISTS predictions (
    id BIGSERIAL,
    forecast_time TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL,
    model_version VARCHAR(32) NOT NULL,
    h3_index VARCHAR(16),
    oblast VARCHAR(64),
    prediction_15min FLOAT,
    prediction_30min FLOAT,
    prediction_60min FLOAT,
    confidence FLOAT,
    model_mode VARCHAR(16), -- 'ml' or 'fallback'
    feature_vector JSONB,
    PRIMARY KEY (forecast_time, id)
) PARTITION BY RANGE (forecast_time);

SELECT create_hypertable('predictions', 'forecast_time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_predictions_time ON predictions (forecast_time DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_h3 ON predictions (h3_index, forecast_time DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_oblast ON predictions (oblast, forecast_time DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_model ON predictions (model_version, forecast_time DESC);

ALTER TABLE predictions SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'oblast,h3_index',
    timescaledb.compress_orderby = 'forecast_time DESC'
);

SELECT add_compression_policy('predictions', INTERVAL '7 days', if_not_exists => TRUE);

-- Create HYPERTABLE for feature cache (online features)
CREATE TABLE IF NOT EXISTS features_online (
    id BIGSERIAL,
    computed_at TIMESTAMPTZ NOT NULL,
    valid_until TIMESTAMPTZ NOT NULL,
    h3_index VARCHAR(16) NOT NULL,
    oblast VARCHAR(64),
    alert_count_15m INT,
    alert_count_1h INT,
    alert_count_6h INT,
    alert_count_24h INT,
    time_since_last_alert_seconds INT,
    neighbor_active_count INT,
    hour_of_day INT,
    day_of_week INT,
    is_holiday BOOLEAN,
    days_since_last_mass_strike INT,
    feature_vector JSONB,
    PRIMARY KEY (computed_at, id)
) PARTITION BY RANGE (computed_at);

SELECT create_hypertable('features_online', 'computed_at', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_features_h3 ON features_online (h3_index, computed_at DESC);
CREATE INDEX IF NOT EXISTS idx_features_oblast ON features_online (oblast, computed_at DESC);
CREATE INDEX IF NOT EXISTS idx_features_valid ON features_online (valid_until DESC);

ALTER TABLE features_online SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'oblast,h3_index',
    timescaledb.compress_orderby = 'computed_at DESC'
);

SELECT add_compression_policy('features_online', INTERVAL '7 days', if_not_exists => TRUE);

-- PostGIS tables for spatial data
-- Admin boundaries
CREATE TABLE IF NOT EXISTS admin_boundaries (
    id BIGSERIAL PRIMARY KEY,
    admin_level INT,
    name VARCHAR(256),
    oblast VARCHAR(64),
    raion VARCHAR(128),
    h3_index VARCHAR(16),
    geom GEOMETRY(Polygon, 4326),
    UNIQUE(oblast, raion, admin_level)
);

CREATE INDEX IF NOT EXISTS idx_boundaries_geom ON admin_boundaries USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_boundaries_h3 ON admin_boundaries (h3_index);
CREATE INDEX IF NOT EXISTS idx_boundaries_oblast ON admin_boundaries (oblast);

-- H3 Hexagons (resolution 5 and 7)
CREATE TABLE IF NOT EXISTS h3_polygons (
    id BIGSERIAL PRIMARY KEY,
    h3_index VARCHAR(16) UNIQUE NOT NULL,
    resolution INT,
    parent_h3 VARCHAR(16),
    geom GEOMETRY(Polygon, 4326) NOT NULL,
    area_km2 FLOAT,
    population_estimate INT,
    weight FLOAT DEFAULT 1.0
);

CREATE INDEX IF NOT EXISTS idx_h3_geom ON h3_polygons USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_h3_index ON h3_polygons (h3_index);
CREATE INDEX IF NOT EXISTS idx_h3_resolution ON h3_polygons (resolution);
CREATE INDEX IF NOT EXISTS idx_h3_parent ON h3_polygons (parent_h3);

-- Gazetteer for NLP location extraction
CREATE TABLE IF NOT EXISTS gazetteer_ukraine (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(256) NOT NULL,
    name_uk VARCHAR(256),
    name_ru VARCHAR(256),
    katotth_code VARCHAR(10),
    oblast VARCHAR(64),
    raion VARCHAR(128),
    h3_index_5 VARCHAR(16),
    h3_index_7 VARCHAR(16),
    latitude FLOAT,
    longitude FLOAT,
    geom POINT,
    entity_type VARCHAR(32), -- 'oblast', 'raion', 'city', 'village'
    population INT,
    UNIQUE(name, oblast)
);

CREATE INDEX IF NOT EXISTS idx_gazetteer_name ON gazetteer_ukraine (name);
CREATE INDEX IF NOT EXISTS idx_gazetteer_h3_5 ON gazetteer_ukraine (h3_index_5);
CREATE INDEX IF NOT EXISTS idx_gazetteer_h3_7 ON gazetteer_ukraine (h3_index_7);
CREATE INDEX IF NOT EXISTS idx_gazetteer_oblast ON gazetteer_ukraine (oblast);
CREATE INDEX IF NOT EXISTS idx_gazetteer_geom ON gazetteer_ukraine USING GIST(geom);

-- Retention policies
SELECT add_retention_policy('alerts', INTERVAL '3 months', if_not_exists => TRUE);
SELECT add_retention_policy('weather', INTERVAL '3 months', if_not_exists => TRUE);
SELECT add_retention_policy('predictions', INTERVAL '1 month', if_not_exists => TRUE);
SELECT add_retention_policy('features_online', INTERVAL '7 days', if_not_exists => TRUE);

-- Grant permissions (if needed by application user)
GRANT CONNECT ON DATABASE airraids TO postgres;
GRANT USAGE ON SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
