-- BlindStrader service databases
CREATE DATABASE IF NOT EXISTS blindstrader_identity;
CREATE DATABASE IF NOT EXISTS blindstrader_brand;
CREATE DATABASE IF NOT EXISTS blindstrader_supplier;
CREATE DATABASE IF NOT EXISTS blindstrader_supply_chain;
CREATE DATABASE IF NOT EXISTS blindstrader_payment;
CREATE DATABASE IF NOT EXISTS blindstrader_retailer;
CREATE DATABASE IF NOT EXISTS blindstrader_platform;
CREATE DATABASE IF NOT EXISTS blindstrader_notification;

-- Application user
CREATE USER IF NOT EXISTS 'blindstrader'@'%' IDENTIFIED BY 'blindstrader';
GRANT ALL PRIVILEGES ON blindstrader_identity.*      TO 'blindstrader'@'%';
GRANT ALL PRIVILEGES ON blindstrader_brand.*         TO 'blindstrader'@'%';
GRANT ALL PRIVILEGES ON blindstrader_supplier.*      TO 'blindstrader'@'%';
GRANT ALL PRIVILEGES ON blindstrader_supply_chain.*  TO 'blindstrader'@'%';
GRANT ALL PRIVILEGES ON blindstrader_payment.*       TO 'blindstrader'@'%';
GRANT ALL PRIVILEGES ON blindstrader_retailer.*      TO 'blindstrader'@'%';
GRANT ALL PRIVILEGES ON blindstrader_platform.*      TO 'blindstrader'@'%';
GRANT ALL PRIVILEGES ON blindstrader_notification.*  TO 'blindstrader'@'%';

-- Grant wildcard for stancl/tenancy-created per-tenant databases
-- e.g. blindstrader_brand_louvolite, blindstrader_supplier_cassidy, etc.
GRANT ALL PRIVILEGES ON `blindstrader\_%`.* TO 'blindstrader'@'%';

FLUSH PRIVILEGES;

-- Prometheus MySQL exporter user
CREATE USER IF NOT EXISTS 'exporter'@'%' IDENTIFIED BY 'exporter_pass';
GRANT SELECT, PROCESS, REPLICATION CLIENT ON *.* TO 'exporter'@'%';
FLUSH PRIVILEGES;
