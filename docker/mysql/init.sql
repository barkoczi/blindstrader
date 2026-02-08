-- Create databases
CREATE DATABASE IF NOT EXISTS blindstrader_catalog;
CREATE DATABASE IF NOT EXISTS blindstrader_user_management;

-- Create user and grant privileges
CREATE USER IF NOT EXISTS 'blindstrader'@'%' IDENTIFIED BY 'blindstrader';
GRANT ALL PRIVILEGES ON blindstrader_catalog.* TO 'blindstrader'@'%';
GRANT ALL PRIVILEGES ON blindstrader_user_management.* TO 'blindstrader'@'%';
FLUSH PRIVILEGES;

-- Create monitoring user for Prometheus MySQL Exporter
-- This user needs read-only access to collect metrics
CREATE USER IF NOT EXISTS 'exporter'@'%' IDENTIFIED BY 'exporter_pass';
GRANT SELECT, PROCESS, REPLICATION CLIENT ON *.* TO 'exporter'@'%';
FLUSH PRIVILEGES;
