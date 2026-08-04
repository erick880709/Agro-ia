-- Script de inicialización de la base de datos AgroIA
-- Ejecutado automáticamente al crear el contenedor PostgreSQL

-- Extensiones requeridas
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "timescaledb";

-- Schema principal
CREATE SCHEMA IF NOT EXISTS agroia;
ALTER DATABASE agroia SET search_path TO agroia, public;
