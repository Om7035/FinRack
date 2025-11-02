-- Initialize PostgreSQL with required extensions

-- Enable pgvector for vector embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable TimescaleDB for time-series data
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Enable PostGIS for location-based features
CREATE EXTENSION IF NOT EXISTS postgis;

-- Enable pg_cron for scheduled jobs
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Enable uuid-ossp for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create finrack database if not exists
SELECT 'CREATE DATABASE finrack'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'finrack')\gexec
