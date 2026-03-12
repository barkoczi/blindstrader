#!/usr/bin/env python3
"""Generate infrastructure files: docker-compose.yml, init.sql, nginx conf, prometheus.yml"""

import os

ROOT = "/Users/barkocziroland/laravel/blindstrader"


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    print(f"  wrote {os.path.relpath(path, ROOT)}")


# ─── docker-compose.yml ────────────────────────────────────────────────────────

DOCKER_COMPOSE = """\
services:
  # ─── Infrastructure ──────────────────────────────────────────────────────────

  db:
    image: mysql:8.0
    container_name: blindstrader-mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD:-root}
      MYSQL_DATABASE: blindstrader_identity
    ports:
      - "3307:3306"
    volumes:
      - db_data:/var/lib/mysql
      - ./docker/mysql/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - blindstrader
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      timeout: 20s
      retries: 10

  redis:
    image: redis:7-alpine
    container_name: blindstrader-redis
    restart: unless-stopped
    command: redis-server --save 900 1 --save 300 10 --save 60 10000
    ports:
      - "6380:6379"
    volumes:
      - redis_data:/data
    networks:
      - blindstrader
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      timeout: 3s
      retries: 10

  kafka:
    image: confluentinc/cp-kafka:7.6.0
    container_name: blindstrader-kafka
    restart: unless-stopped
    ports:
      - "9092:9092"
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
      CLUSTER_ID: blindstrader-kafka-cluster-1
    volumes:
      - kafka_data:/var/lib/kafka/data
    networks:
      - blindstrader
    healthcheck:
      test: ["CMD", "kafka-broker-api-versions", "--bootstrap-server", "localhost:9092"]
      interval: 30s
      timeout: 10s
      retries: 10

  # ─── Application Services ─────────────────────────────────────────────────────

  identity:
    image: ghcr.io/barkoczi/blindstrader-identity:latest
    container_name: blindstrader-identity
    restart: unless-stopped
    working_dir: /app
    volumes:
      - ./services/identity:/app
    ports:
      - "8001:9000"
    environment:
      APP_NAME: Identity
      DB_HOST: db
      DB_PORT: 3306
      DB_DATABASE: blindstrader_identity
      DB_USERNAME: ${DB_USERNAME:-blindstrader}
      DB_PASSWORD: ${DB_PASSWORD:-blindstrader}
      REDIS_HOST: redis
      REDIS_PORT: 6379
      SESSION_DRIVER: redis
      CACHE_STORE: redis
      QUEUE_CONNECTION: redis
      SESSION_DOMAIN: .blindstrader.test
      KAFKA_BROKERS: kafka:9092
      SENTRY_LARAVEL_DSN: ${SENTRY_LARAVEL_DSN:-}
      SENTRY_ENVIRONMENT: identity
      SENTRY_TRACES_SAMPLE_RATE: 0.2
      SENTRY_SEND_DEFAULT_PII: "true"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      kafka:
        condition: service_healthy
    networks:
      - blindstrader
    command: sh -c "php artisan migrate --force && php artisan db:seed --force && php-fpm"

  brand:
    image: ghcr.io/barkoczi/blindstrader-brand:latest
    container_name: blindstrader-brand
    restart: unless-stopped
    working_dir: /app
    volumes:
      - ./services/brand:/app
    ports:
      - "8002:9000"
    environment:
      APP_NAME: Brand
      DB_HOST: db
      DB_PORT: 3306
      DB_DATABASE: blindstrader_brand
      DB_USERNAME: ${DB_USERNAME:-blindstrader}
      DB_PASSWORD: ${DB_PASSWORD:-blindstrader}
      REDIS_HOST: redis
      REDIS_PORT: 6379
      SESSION_DRIVER: redis
      CACHE_STORE: redis
      QUEUE_CONNECTION: redis
      SESSION_DOMAIN: .blindstrader.test
      KAFKA_BROKERS: kafka:9092
      TENANCY_DB_HOST: db
      TENANCY_DB_PORT: 3306
      TENANCY_DB_USERNAME: ${DB_USERNAME:-blindstrader}
      TENANCY_DB_PASSWORD: ${DB_PASSWORD:-blindstrader}
      TENANCY_DB_PREFIX: blindstrader_brand_
      SENTRY_LARAVEL_DSN: ${SENTRY_LARAVEL_DSN:-}
      SENTRY_ENVIRONMENT: brand
      SENTRY_TRACES_SAMPLE_RATE: 0.2
      SENTRY_SEND_DEFAULT_PII: "true"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      kafka:
        condition: service_healthy
    networks:
      - blindstrader
    command: sh -c "php artisan migrate --force && php artisan db:seed --class=TenantSeeder --force && php-fpm"

  supplier:
    image: ghcr.io/barkoczi/blindstrader-supplier:latest
    container_name: blindstrader-supplier
    restart: unless-stopped
    working_dir: /app
    volumes:
      - ./services/supplier:/app
    ports:
      - "8003:9000"
    environment:
      APP_NAME: Supplier
      DB_HOST: db
      DB_PORT: 3306
      DB_DATABASE: blindstrader_supplier
      DB_USERNAME: ${DB_USERNAME:-blindstrader}
      DB_PASSWORD: ${DB_PASSWORD:-blindstrader}
      REDIS_HOST: redis
      REDIS_PORT: 6379
      SESSION_DRIVER: redis
      CACHE_STORE: redis
      QUEUE_CONNECTION: redis
      SESSION_DOMAIN: .blindstrader.test
      KAFKA_BROKERS: kafka:9092
      TENANCY_DB_HOST: db
      TENANCY_DB_PORT: 3306
      TENANCY_DB_USERNAME: ${DB_USERNAME:-blindstrader}
      TENANCY_DB_PASSWORD: ${DB_PASSWORD:-blindstrader}
      TENANCY_DB_PREFIX: blindstrader_supplier_
      SENTRY_LARAVEL_DSN: ${SENTRY_LARAVEL_DSN:-}
      SENTRY_ENVIRONMENT: supplier
      SENTRY_TRACES_SAMPLE_RATE: 0.2
      SENTRY_SEND_DEFAULT_PII: "true"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      kafka:
        condition: service_healthy
    networks:
      - blindstrader
    command: sh -c "php artisan migrate --force && php artisan db:seed --class=TenantSeeder --force && php-fpm"

  supply-chain:
    image: ghcr.io/barkoczi/blindstrader-supply-chain:latest
    container_name: blindstrader-supply-chain
    restart: unless-stopped
    working_dir: /app
    volumes:
      - ./services/supply-chain:/app
    ports:
      - "8004:9000"
    environment:
      APP_NAME: SupplyChain
      DB_HOST: db
      DB_PORT: 3306
      DB_DATABASE: blindstrader_supply_chain
      DB_USERNAME: ${DB_USERNAME:-blindstrader}
      DB_PASSWORD: ${DB_PASSWORD:-blindstrader}
      REDIS_HOST: redis
      REDIS_PORT: 6379
      SESSION_DRIVER: redis
      CACHE_STORE: redis
      QUEUE_CONNECTION: redis
      SESSION_DOMAIN: .blindstrader.test
      KAFKA_BROKERS: kafka:9092
      SENTRY_LARAVEL_DSN: ${SENTRY_LARAVEL_DSN:-}
      SENTRY_ENVIRONMENT: supply-chain
      SENTRY_TRACES_SAMPLE_RATE: 0.2
      SENTRY_SEND_DEFAULT_PII: "true"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      kafka:
        condition: service_healthy
    networks:
      - blindstrader
    command: sh -c "php artisan migrate --force && php-fpm"

  payment:
    image: ghcr.io/barkoczi/blindstrader-payment:latest
    container_name: blindstrader-payment
    restart: unless-stopped
    working_dir: /app
    volumes:
      - ./services/payment:/app
    ports:
      - "8005:9000"
    environment:
      APP_NAME: Payment
      DB_HOST: db
      DB_PORT: 3306
      DB_DATABASE: blindstrader_payment
      DB_USERNAME: ${DB_USERNAME:-blindstrader}
      DB_PASSWORD: ${DB_PASSWORD:-blindstrader}
      REDIS_HOST: redis
      REDIS_PORT: 6379
      SESSION_DRIVER: redis
      CACHE_STORE: redis
      QUEUE_CONNECTION: redis
      SESSION_DOMAIN: .blindstrader.test
      KAFKA_BROKERS: kafka:9092
      STRIPE_SECRET_KEY: ${STRIPE_SECRET_KEY:-}
      STRIPE_WEBHOOK_SECRET: ${STRIPE_WEBHOOK_SECRET:-}
      STRIPE_CONNECT_CLIENT_ID: ${STRIPE_CONNECT_CLIENT_ID:-}
      SENTRY_LARAVEL_DSN: ${SENTRY_LARAVEL_DSN:-}
      SENTRY_ENVIRONMENT: payment
      SENTRY_TRACES_SAMPLE_RATE: 0.2
      SENTRY_SEND_DEFAULT_PII: "true"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      kafka:
        condition: service_healthy
    networks:
      - blindstrader
    command: sh -c "php artisan migrate --force && php-fpm"

  retailer:
    image: ghcr.io/barkoczi/blindstrader-retailer:latest
    container_name: blindstrader-retailer
    restart: unless-stopped
    working_dir: /app
    volumes:
      - ./services/retailer:/app
    ports:
      - "8006:9000"
    environment:
      APP_NAME: Retailer
      DB_HOST: db
      DB_PORT: 3306
      DB_DATABASE: blindstrader_retailer
      DB_USERNAME: ${DB_USERNAME:-blindstrader}
      DB_PASSWORD: ${DB_PASSWORD:-blindstrader}
      REDIS_HOST: redis
      REDIS_PORT: 6379
      SESSION_DRIVER: redis
      CACHE_STORE: redis
      QUEUE_CONNECTION: redis
      SESSION_DOMAIN: .blindstrader.test
      KAFKA_BROKERS: kafka:9092
      TENANCY_DB_HOST: db
      TENANCY_DB_PORT: 3306
      TENANCY_DB_USERNAME: ${DB_USERNAME:-blindstrader}
      TENANCY_DB_PASSWORD: ${DB_PASSWORD:-blindstrader}
      TENANCY_DB_PREFIX: blindstrader_retailer_
      SENTRY_LARAVEL_DSN: ${SENTRY_LARAVEL_DSN:-}
      SENTRY_ENVIRONMENT: retailer
      SENTRY_TRACES_SAMPLE_RATE: 0.2
      SENTRY_SEND_DEFAULT_PII: "true"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      kafka:
        condition: service_healthy
    networks:
      - blindstrader
    command: sh -c "php artisan migrate --force && php artisan db:seed --class=TenantSeeder --force && php-fpm"

  platform:
    image: ghcr.io/barkoczi/blindstrader-platform:latest
    container_name: blindstrader-platform
    restart: unless-stopped
    working_dir: /app
    volumes:
      - ./services/platform:/app
    ports:
      - "8007:9000"
    environment:
      APP_NAME: Platform
      DB_HOST: db
      DB_PORT: 3306
      DB_DATABASE: blindstrader_platform
      DB_USERNAME: ${DB_USERNAME:-blindstrader}
      DB_PASSWORD: ${DB_PASSWORD:-blindstrader}
      REDIS_HOST: redis
      REDIS_PORT: 6379
      SESSION_DRIVER: redis
      CACHE_STORE: redis
      QUEUE_CONNECTION: redis
      SESSION_DOMAIN: .blindstrader.test
      KAFKA_BROKERS: kafka:9092
      SENTRY_LARAVEL_DSN: ${SENTRY_LARAVEL_DSN:-}
      SENTRY_ENVIRONMENT: platform
      SENTRY_TRACES_SAMPLE_RATE: 0.2
      SENTRY_SEND_DEFAULT_PII: "true"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      kafka:
        condition: service_healthy
    networks:
      - blindstrader
    command: sh -c "php artisan migrate --force && php-fpm"

  notification:
    image: ghcr.io/barkoczi/blindstrader-notification:latest
    container_name: blindstrader-notification
    restart: unless-stopped
    working_dir: /app
    volumes:
      - ./services/notification:/app
    ports:
      - "8008:9000"
    environment:
      APP_NAME: Notification
      DB_HOST: db
      DB_PORT: 3306
      DB_DATABASE: blindstrader_notification
      DB_USERNAME: ${DB_USERNAME:-blindstrader}
      DB_PASSWORD: ${DB_PASSWORD:-blindstrader}
      REDIS_HOST: redis
      REDIS_PORT: 6379
      SESSION_DRIVER: redis
      CACHE_STORE: redis
      QUEUE_CONNECTION: redis
      SESSION_DOMAIN: .blindstrader.test
      SENTRY_LARAVEL_DSN: ${SENTRY_LARAVEL_DSN:-}
      SENTRY_ENVIRONMENT: notification
      SENTRY_TRACES_SAMPLE_RATE: 0.2
      SENTRY_SEND_DEFAULT_PII: "true"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - blindstrader
    command: sh -c "php artisan migrate --force && php-fpm"

  # ─── API Docs Portal (Scalar — MIT licence, self-hosted) ─────────────────────

  docs:
    image: scalar/api-reference:latest
    container_name: blindstrader-docs
    restart: unless-stopped
    ports:
      - "8009:80"
    environment:
      SCALAR_CONFIGURATION: >
        {"theme":"purple","layout":"modern","showSidebar":true,"references":[
        {"name":"Identity","url":"http://identity:9000/docs/api.json"},
        {"name":"Brand","url":"http://brand:9000/docs/api.json"},
        {"name":"Supplier","url":"http://supplier:9000/docs/api.json"},
        {"name":"Supply Chain","url":"http://supply-chain:9000/docs/api.json"},
        {"name":"Payment","url":"http://payment:9000/docs/api.json"},
        {"name":"Retailer","url":"http://retailer:9000/docs/api.json"},
        {"name":"Platform","url":"http://platform:9000/docs/api.json"},
        {"name":"Notification","url":"http://notification:9000/docs/api.json"}
        ]}
    depends_on:
      - identity
      - brand
      - supplier
      - supply-chain
      - payment
      - retailer
      - platform
      - notification
    networks:
      - blindstrader

  # ─── Reverse Proxy ───────────────────────────────────────────────────────────

  nginx:
    image: nginx:alpine
    container_name: blindstrader-nginx
    restart: unless-stopped
    ports:
      - "8080:80"
      - "8443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/certs:/etc/letsencrypt:ro
      - ./nginx/.htpasswd:/etc/nginx/.htpasswd:ro
      - ./services/identity:/app/identity:ro
      - ./services/brand:/app/brand:ro
      - ./services/supplier:/app/supplier:ro
      - ./services/supply-chain:/app/supply-chain:ro
      - ./services/payment:/app/payment:ro
      - ./services/retailer:/app/retailer:ro
      - ./services/platform:/app/platform:ro
      - ./services/notification:/app/notification:ro
      - ./logs/nginx:/var/log/nginx
      - certbot_webroot:/var/www/certbot:ro
    depends_on:
      - identity
      - brand
      - supplier
      - supply-chain
      - payment
      - retailer
      - platform
      - notification
      - docs
    networks:
      - blindstrader

  phpmyadmin:
    image: phpmyadmin:latest
    container_name: blindstrader-phpmyadmin
    restart: unless-stopped
    environment:
      PMA_HOST: db
      PMA_PORT: 3306
      PMA_USER: root
      PMA_PASSWORD: ${DB_ROOT_PASSWORD:-root}
      UPLOAD_LIMIT: 100M
    ports:
      - "8010:80"
    depends_on:
      db:
        condition: service_healthy
    networks:
      - blindstrader

  certbot:
    image: certbot/certbot:latest
    container_name: blindstrader-certbot
    volumes:
      - ./nginx/certs:/etc/letsencrypt
      - certbot_webroot:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
    networks:
      - blindstrader

  # ─── Monitoring Stack ────────────────────────────────────────────────────────

  prometheus:
    image: prom/prometheus:latest
    container_name: blindstrader-prometheus
    restart: unless-stopped
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=15d'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    networks:
      - blindstrader

  grafana:
    image: grafana/grafana:latest
    container_name: blindstrader-grafana
    restart: unless-stopped
    environment:
      GF_SERVER_ROOT_URL: https://insights.blindstrader.test
      GF_SERVER_DOMAIN: insights.blindstrader.test
      GF_AUTH_ANONYMOUS_ENABLED: "true"
      GF_AUTH_ANONYMOUS_ORG_ROLE: Admin
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD:-admin}
      GF_INSTALL_PLUGINS: ""
    ports:
      - "8000:3000"
    volumes:
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus
      - loki
    networks:
      - blindstrader

  loki:
    image: grafana/loki:latest
    container_name: blindstrader-loki
    restart: unless-stopped
    command: -config.file=/etc/loki/loki-config.yml
    ports:
      - "3100:3100"
    volumes:
      - ./monitoring/loki:/etc/loki
      - loki_data:/loki
    networks:
      - blindstrader

  promtail:
    image: grafana/promtail:latest
    container_name: blindstrader-promtail
    restart: unless-stopped
    command: -config.file=/etc/promtail/promtail-config.yml
    ports:
      - "9080:9080"
    volumes:
      - ./monitoring/promtail:/etc/promtail
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./logs/nginx:/var/log/nginx:ro
    depends_on:
      - loki
    networks:
      - blindstrader

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: blindstrader-cadvisor
    restart: unless-stopped
    privileged: true
    ports:
      - "8004:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker:/var/lib/docker:ro
      - /dev/disk:/dev/disk:ro
    devices:
      - /dev/kmsg
    networks:
      - blindstrader

  node-exporter:
    image: prom/node-exporter:latest
    container_name: blindstrader-node-exporter
    restart: unless-stopped
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
    pid: host
    networks:
      - blindstrader

  mysql-exporter:
    image: prom/mysqld-exporter:latest
    container_name: blindstrader-mysql-exporter
    restart: unless-stopped
    environment:
      DATA_SOURCE_NAME: "exporter:${MYSQL_EXPORTER_PASSWORD:-exporter_pass}@tcp(blindstrader-mysql:3306)/"
    ports:
      - "9104:9104"
    depends_on:
      db:
        condition: service_healthy
    networks:
      - blindstrader

  redis-exporter:
    image: oliver006/redis_exporter:latest
    container_name: blindstrader-redis-exporter
    restart: unless-stopped
    environment:
      REDIS_ADDR: "blindstrader-redis:6379"
    ports:
      - "9121:9121"
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - blindstrader

networks:
  blindstrader:
    driver: bridge

volumes:
  db_data:
  redis_data:
  kafka_data:
  prometheus_data:
  grafana_data:
  loki_data:
  certbot_webroot:
"""

# ─── docker/mysql/init.sql ────────────────────────────────────────────────────

INIT_SQL = """\
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
GRANT ALL PRIVILEGES ON `blindstrader\\_%`.* TO 'blindstrader'@'%';

FLUSH PRIVILEGES;

-- Prometheus MySQL exporter user
CREATE USER IF NOT EXISTS 'exporter'@'%' IDENTIFIED BY 'exporter_pass';
GRANT SELECT, PROCESS, REPLICATION CLIENT ON *.* TO 'exporter'@'%';
FLUSH PRIVILEGES;
"""

# ─── nginx/conf.d/app.blindstrader.conf ───────────────────────────────────────

NGINX_CONF = """\
# HTTP → HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name
        identity.${DOMAIN}
        brand.${DOMAIN}
        supplier.${DOMAIN}
        sc.${DOMAIN}
        payment.${DOMAIN}
        retailer.${DOMAIN}
        platform.${DOMAIN}
        notification.${DOMAIN}
        docs.${DOMAIN}
        ${DOMAIN};

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# ─── Identity Service ─────────────────────────────────────────────────────────
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name identity.${DOMAIN};
    root /app/identity/public;
    index index.php;

    ssl_certificate     /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / { try_files $uri $uri/ /index.php?$query_string; }

    location ~ \\.php$ {
        try_files $uri =404;
        fastcgi_split_path_info ^(.+\\.php)(/.+)$;
        fastcgi_pass identity:9000;
        fastcgi_index index.php;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param PATH_INFO $fastcgi_path_info;
    }

    location ~ /\\.(?!well-known).* { deny all; }
}

# ─── Brand Service ────────────────────────────────────────────────────────────
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name brand.${DOMAIN};
    root /app/brand/public;
    index index.php;

    ssl_certificate     /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / { try_files $uri $uri/ /index.php?$query_string; }

    location ~ \\.php$ {
        try_files $uri =404;
        fastcgi_split_path_info ^(.+\\.php)(/.+)$;
        fastcgi_pass brand:9000;
        fastcgi_index index.php;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param PATH_INFO $fastcgi_path_info;
    }

    location ~ /\\.(?!well-known).* { deny all; }
}

# ─── Supplier Service ─────────────────────────────────────────────────────────
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name supplier.${DOMAIN};
    root /app/supplier/public;
    index index.php;

    ssl_certificate     /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / { try_files $uri $uri/ /index.php?$query_string; }

    location ~ \\.php$ {
        try_files $uri =404;
        fastcgi_split_path_info ^(.+\\.php)(/.+)$;
        fastcgi_pass supplier:9000;
        fastcgi_index index.php;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param PATH_INFO $fastcgi_path_info;
    }

    location ~ /\\.(?!well-known).* { deny all; }
}

# ─── Supply Chain Service ─────────────────────────────────────────────────────
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name sc.${DOMAIN};
    root /app/supply-chain/public;
    index index.php;

    ssl_certificate     /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / { try_files $uri $uri/ /index.php?$query_string; }

    location ~ \\.php$ {
        try_files $uri =404;
        fastcgi_split_path_info ^(.+\\.php)(/.+)$;
        fastcgi_pass supply-chain:9000;
        fastcgi_index index.php;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param PATH_INFO $fastcgi_path_info;
    }

    location ~ /\\.(?!well-known).* { deny all; }
}

# ─── Payment Service ──────────────────────────────────────────────────────────
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name payment.${DOMAIN};
    root /app/payment/public;
    index index.php;

    ssl_certificate     /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / { try_files $uri $uri/ /index.php?$query_string; }

    location ~ \\.php$ {
        try_files $uri =404;
        fastcgi_split_path_info ^(.+\\.php)(/.+)$;
        fastcgi_pass payment:9000;
        fastcgi_index index.php;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param PATH_INFO $fastcgi_path_info;
    }

    location ~ /\\.(?!well-known).* { deny all; }
}

# ─── Retailer Service ─────────────────────────────────────────────────────────
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name retailer.${DOMAIN};
    root /app/retailer/public;
    index index.php;

    ssl_certificate     /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / { try_files $uri $uri/ /index.php?$query_string; }

    location ~ \\.php$ {
        try_files $uri =404;
        fastcgi_split_path_info ^(.+\\.php)(/.+)$;
        fastcgi_pass retailer:9000;
        fastcgi_index index.php;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param PATH_INFO $fastcgi_path_info;
    }

    location ~ /\\.(?!well-known).* { deny all; }
}

# ─── Platform Service ─────────────────────────────────────────────────────────
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name platform.${DOMAIN};
    root /app/platform/public;
    index index.php;

    ssl_certificate     /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / { try_files $uri $uri/ /index.php?$query_string; }

    location ~ \\.php$ {
        try_files $uri =404;
        fastcgi_split_path_info ^(.+\\.php)(/.+)$;
        fastcgi_pass platform:9000;
        fastcgi_index index.php;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param PATH_INFO $fastcgi_path_info;
    }

    location ~ /\\.(?!well-known).* { deny all; }
}

# ─── Notification Service ─────────────────────────────────────────────────────
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name notification.${DOMAIN};
    root /app/notification/public;
    index index.php;

    ssl_certificate     /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / { try_files $uri $uri/ /index.php?$query_string; }

    location ~ \\.php$ {
        try_files $uri =404;
        fastcgi_split_path_info ^(.+\\.php)(/.+)$;
        fastcgi_pass notification:9000;
        fastcgi_index index.php;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param PATH_INFO $fastcgi_path_info;
    }

    location ~ /\\.(?!well-known).* { deny all; }
}

# ─── API Docs Portal (Scalar) ─────────────────────────────────────────────────
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name docs.${DOMAIN};

    ssl_certificate     /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass         http://docs:80;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}

# ─── Root domain redirect ─────────────────────────────────────────────────────
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${DOMAIN};

    ssl_certificate     /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;

    return 301 https://identity.${DOMAIN}$request_uri;
}
"""

# ─── monitoring/prometheus/prometheus.yml ─────────────────────────────────────

PROMETHEUS_YML = """\
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'blindstrader'
    environment: 'development'

rule_files:
  - '/etc/prometheus/alerts.yml'

scrape_configs:

  # ─── Infrastructure ──────────────────────────────────────────────────────────

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['blindstrader-cadvisor:8080']
        labels:
          service: 'cadvisor'

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['blindstrader-node-exporter:9100']
        labels:
          service: 'node-exporter'

  - job_name: 'mysql-exporter'
    static_configs:
      - targets: ['blindstrader-mysql-exporter:9104']
        labels:
          service: 'mysql'

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['blindstrader-redis-exporter:9121']
        labels:
          service: 'redis'

  - job_name: 'kafka-exporter'
    static_configs:
      - targets: ['blindstrader-kafka:7071']
        labels:
          service: 'kafka'

  # ─── Application Services ─────────────────────────────────────────────────────

  - job_name: 'identity-metrics'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['blindstrader-identity:9000']
        labels:
          service: 'identity'
          service_type: 'laravel'

  - job_name: 'brand-metrics'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['blindstrader-brand:9000']
        labels:
          service: 'brand'
          service_type: 'laravel'

  - job_name: 'supplier-metrics'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['blindstrader-supplier:9000']
        labels:
          service: 'supplier'
          service_type: 'laravel'

  - job_name: 'supply-chain-metrics'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['blindstrader-supply-chain:9000']
        labels:
          service: 'supply-chain'
          service_type: 'laravel'

  - job_name: 'payment-metrics'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['blindstrader-payment:9000']
        labels:
          service: 'payment'
          service_type: 'laravel'

  - job_name: 'retailer-metrics'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['blindstrader-retailer:9000']
        labels:
          service: 'retailer'
          service_type: 'laravel'

  - job_name: 'platform-metrics'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['blindstrader-platform:9000']
        labels:
          service: 'platform'
          service_type: 'laravel'

  - job_name: 'notification-metrics'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['blindstrader-notification:9000']
        labels:
          service: 'notification'
          service_type: 'laravel'

  # ─── Self-monitoring ─────────────────────────────────────────────────────────

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
        labels:
          service: 'prometheus'
"""

write(f"{ROOT}/docker-compose.yml", DOCKER_COMPOSE)
write(f"{ROOT}/docker/mysql/init.sql", INIT_SQL)
write(f"{ROOT}/nginx/conf.d/app.blindstrader.conf", NGINX_CONF)
write(f"{ROOT}/monitoring/prometheus/prometheus.yml", PROMETHEUS_YML)

print("\n✅ Infrastructure files written.")
