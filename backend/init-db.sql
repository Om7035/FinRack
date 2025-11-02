-- Enable required PostgreSQL extensions

-- pgvector for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- TimescaleDB for time-series data
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- PostGIS for location-based features
CREATE EXTENSION IF NOT EXISTS postgis;

-- UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- pg_cron for scheduled jobs
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Full text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE finrack TO postgres;
