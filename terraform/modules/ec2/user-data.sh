#!/bin/bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "$${GREEN}[INFO]$${NC} $1"
}

log_error() {
    echo -e "$${RED}[ERROR]$${NC} $1" >&2
}

log_warning() {
    echo -e "$${YELLOW}[WARNING]$${NC} $1"
}

log_info "Starting BlindStrader EC2 initialization..."

# Update system
log_info "Updating system packages..."
yum update -y

# Update system
log_info "Updating system packages..."
yum update -y

# Install Docker
log_info "Installing Docker..."
yum install -y docker
systemctl start docker
systemctl enable docker

# Install Docker Compose
log_info "Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install AWS CLI v2
log_info "Installing AWS CLI..."
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
yum install -y unzip
unzip awscliv2.zip
./aws/install
rm -rf aws awscliv2.zip

# Install other utilities
log_info "Installing utilities (git, htop, vim, jq, httpd-tools)..."
yum install -y git htop vim jq httpd-tools

# Install other utilities
log_info "Installing utilities (git, htop, vim, jq, httpd-tools)..."
yum install -y git htop vim jq httpd-tools

# Create directories for EBS mounts
log_info "Creating mount directories..."
mkdir -p /var/lib/mysql
mkdir -p /var/lib/redis
mkdir -p /var/lib/monitoring

# Format and mount EBS volumes
log_info "Mounting EBS volumes..."
# MySQL volume
if ! blkid ${mysql_device}; then
  log_info "Formatting MySQL volume..."
  mkfs -t ext4 ${mysql_device}
fi
mount ${mysql_device} /var/lib/mysql
echo "${mysql_device} /var/lib/mysql ext4 defaults,nofail 0 2" >> /etc/fstab

# Redis volume
if ! blkid ${redis_device}; then
  mkfs -t ext4 ${redis_device}
fi
mount ${redis_device} /var/lib/redis
echo "${redis_device} /var/lib/redis ext4 defaults,nofail 0 2" >> /etc/fstab

# Monitoring volume
if ! blkid ${monitoring_device}; then
  mkfs -t ext4 ${monitoring_device}
fi
mount ${monitoring_device} /var/lib/monitoring
echo "${monitoring_device} /var/lib/monitoring ext4 defaults,nofail 0 2" >> /etc/fstab

# Set proper permissions
log_info "Setting permissions..."
chown -R 999:999 /var/lib/mysql
chown -R 999:999 /var/lib/redis
chmod -R 755 /var/lib/monitoring

# Retrieve secrets from AWS Secrets Manager
log_info "Retrieving secrets from AWS Secrets Manager..."
export AWS_DEFAULT_REGION=${aws_region}

DB_PASSWORD=$(aws secretsmanager get-secret-value --secret-id /blindstrader/${environment}/db_password --query SecretString --output text)
REDIS_PASSWORD=$(aws secretsmanager get-secret-value --secret-id /blindstrader/${environment}/redis_password --query SecretString --output text)
APP_KEY=$(aws secretsmanager get-secret-value --secret-id /blindstrader/${environment}/app_key --query SecretString --output text)
GRAFANA_ADMIN_PASSWORD=$(aws secretsmanager get-secret-value --secret-id /blindstrader/${environment}/grafana_admin_password --query SecretString --output text)
BASIC_AUTH_PASSWORD=$(aws secretsmanager get-secret-value --secret-id /blindstrader/${environment}/basic_auth_password --query SecretString --output text)
GPG_PUBLIC_KEY=$(aws secretsmanager get-secret-value --secret-id /blindstrader/shared/gpg_public_key --query SecretString --output text)

# Create application directory
log_info "Creating application directory..."
mkdir -p /opt/blindstrader
cd /opt/blindstrader

# Clone or copy infrastructure repository
# For now, we'll create the necessary files directly

# Create application directory
log_info "Creating application directory..."
mkdir -p /opt/blindstrader
cd /opt/blindstrader

# Create .env file for docker-compose
log_info "Creating environment configuration..."
cat > .env <<EOF
ENVIRONMENT=${environment}
DOMAIN=${domain}

# Database
DB_HOST=blindstrader-mysql
DB_PORT=3306
DB_USERNAME=blindstrader
DB_PASSWORD=$DB_PASSWORD

# Redis
REDIS_HOST=blindstrader-redis
REDIS_PORT=6379
REDIS_PASSWORD=$REDIS_PASSWORD

# Application
APP_KEY=$APP_KEY
APP_ENV=production
APP_DEBUG=false
SESSION_DOMAIN=.${domain}

# Monitoring
GRAFANA_ADMIN_PASSWORD=$GRAFANA_ADMIN_PASSWORD

# Sentry (add your DSN)
SENTRY_LARAVEL_DSN=${sentry_dsn}
EOF

# Generate htpasswd file for monitoring basic auth
log_info "Generating basic auth credentials..."
htpasswd -bc /opt/blindstrader/.htpasswd admin "$BASIC_AUTH_PASSWORD"

# Import GPG public key for backups
log_info "Importing GPG public key..."
echo "$GPG_PUBLIC_KEY" | gpg --import

# Create docker-compose.yml
log_info "Creating docker-compose.yml..."
cat > /opt/blindstrader/docker-compose.yml <<'DOCKER_COMPOSE_EOF'
services:
  db:
    image: mysql:8.0
    container_name: blindstrader-mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: $${DB_PASSWORD}
      MYSQL_DATABASE: blindstrader_catalog
    volumes:
      - /var/lib/mysql:/var/lib/mysql
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
    volumes:
      - /var/lib/redis:/data
    networks:
      - blindstrader
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      timeout: 3s
      retries: 10

  catalog:
    image: ghcr.io/barkoczi/blindstrader-catalog:latest
    container_name: blindstrader-catalog
    restart: unless-stopped
    working_dir: /app
    environment:
      DB_HOST: db
      DB_PORT: 3306
      DB_DATABASE: blindstrader_catalog
      DB_USERNAME: blindstrader
      DB_PASSWORD: $${DB_PASSWORD}
      REDIS_HOST: redis
      REDIS_PORT: 6379
      SESSION_DRIVER: redis
      CACHE_DRIVER: redis
      SESSION_DOMAIN: .${domain}
      APP_KEY: $${APP_KEY}
      APP_ENV: $${ENVIRONMENT}
      APP_DEBUG: false
      SENTRY_LARAVEL_DSN: $${SENTRY_LARAVEL_DSN:-}
      SENTRY_ENVIRONMENT: catalog
      SENTRY_TRACES_SAMPLE_RATE: 0.2
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - blindstrader
    command: >
      sh -c "php artisan migrate --force && php-fpm"

  user-management:
    image: ghcr.io/barkoczi/blindstrader-user-management:latest
    container_name: blindstrader-user-management
    restart: unless-stopped
    working_dir: /app
    environment:
      DB_HOST: db
      DB_PORT: 3306
      DB_DATABASE: blindstrader_user_management
      DB_USERNAME: blindstrader
      DB_PASSWORD: $${DB_PASSWORD}
      REDIS_HOST: redis
      REDIS_PORT: 6379
      SESSION_DRIVER: redis
      CACHE_DRIVER: redis
      SESSION_DOMAIN: .${domain}
      APP_KEY: $${APP_KEY}
      APP_ENV: $${ENVIRONMENT}
      APP_DEBUG: false
      SENTRY_LARAVEL_DSN: $${SENTRY_LARAVEL_DSN:-}
      SENTRY_ENVIRONMENT: user-management
      SENTRY_TRACES_SAMPLE_RATE: 0.2
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - blindstrader
    command: >
      sh -c "php artisan migrate --force && php-fpm"

  nginx:
    image: nginx:alpine
    container_name: blindstrader-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /opt/blindstrader/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - /opt/blindstrader/nginx/conf.d:/etc/nginx/conf.d:ro
      - /opt/blindstrader/nginx/certs:/etc/letsencrypt:ro
      - /opt/blindstrader/.htpasswd:/etc/nginx/.htpasswd:ro
      - /opt/blindstrader/logs:/var/log/nginx
      - certbot_webroot:/var/www/certbot:ro
    depends_on:
      - catalog
      - user-management
    networks:
      - blindstrader

  certbot:
    image: certbot/certbot:latest
    container_name: blindstrader-certbot
    volumes:
      - /opt/blindstrader/nginx/certs:/etc/letsencrypt
      - certbot_webroot:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $$$${!}; done;'"
    networks:
      - blindstrader

  prometheus:
    image: prom/prometheus:latest
    container_name: blindstrader-prometheus
    restart: unless-stopped
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=15d'
    volumes:
      - /var/lib/monitoring/prometheus:/prometheus
    networks:
      - blindstrader

  grafana:
    image: grafana/grafana:latest
    container_name: blindstrader-grafana
    restart: unless-stopped
    environment:
      GF_SERVER_ROOT_URL: https://insights.${domain}
      GF_SERVER_DOMAIN: insights.${domain}
      GF_AUTH_ANONYMOUS_ENABLED: "true"
      GF_AUTH_ANONYMOUS_ORG_ROLE: Admin
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: $${GRAFANA_ADMIN_PASSWORD}
    volumes:
      - /var/lib/monitoring/grafana:/var/lib/grafana
    depends_on:
      - prometheus
    networks:
      - blindstrader

  loki:
    image: grafana/loki:latest
    container_name: blindstrader-loki
    restart: unless-stopped
    command: -config.file=/etc/loki/local-config.yaml
    volumes:
      - /var/lib/monitoring/loki:/loki
    networks:
      - blindstrader

  promtail:
    image: grafana/promtail:latest
    container_name: blindstrader-promtail
    restart: unless-stopped
    volumes:
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /opt/blindstrader/logs:/var/log/nginx:ro
    depends_on:
      - loki
    networks:
      - blindstrader

networks:
  blindstrader:
    driver: bridge

volumes:
  certbot_webroot:
    driver: local
DOCKER_COMPOSE_EOF

# Create nginx directory structure
log_info "Creating nginx configuration..."
mkdir -p /opt/blindstrader/nginx/conf.d /opt/blindstrader/nginx/certs /opt/blindstrader/logs

# Create main nginx.conf
cat > /opt/blindstrader/nginx/nginx.conf <<'NGINX_CONF_EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;

    # Include additional server configurations
    include /etc/nginx/conf.d/*.conf;
}
NGINX_CONF_EOF

# Create app nginx config
cat > /opt/blindstrader/nginx/conf.d/app.conf <<NGINX_APP_EOF
server {
    listen 80;
    listen [::]:80;
    server_name auth.${domain} catalog.${domain} ${domain};

    # Certbot webroot for SSL certificate challenges
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirect all other HTTP traffic to HTTPS
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# Auth service
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name auth.${domain};
    root /app/user-management/public;
    index index.php;

    ssl_certificate /etc/letsencrypt/live/${domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${domain}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        try_files \$uri \$uri/ /index.php?\$query_string;
    }

    location ~ \.php\$ {
        try_files \$uri =404;
        fastcgi_split_path_info ^(.+\.php)(/.+)\$;
        fastcgi_pass user-management:9000;
        fastcgi_index index.php;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME \$document_root\$fastcgi_script_name;
        fastcgi_param PATH_INFO \$fastcgi_path_info;
    }

    location ~ /\.(?!well-known).* {
        deny all;
    }
}

# Catalog service
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name catalog.${domain};
    root /app/catalog/public;
    index index.php;

    ssl_certificate /etc/letsencrypt/live/${domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${domain}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        try_files \$uri \$uri/ /index.php?\$query_string;
    }

    location ~ \.php\$ {
        try_files \$uri =404;
        fastcgi_split_path_info ^(.+\.php)(/.+)\$;
        fastcgi_pass catalog:9000;
        fastcgi_index index.php;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME \$document_root\$fastcgi_script_name;
        fastcgi_param PATH_INFO \$fastcgi_path_info;
    }

    location ~ /\.(?!well-known).* {
        deny all;
    }
}

# Root domain redirect
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${domain};

    ssl_certificate /etc/letsencrypt/live/${domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${domain}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers HIGH:!aNULL:!MD5;

    return 301 https://auth.${domain}\$request_uri;
}
NGINX_APP_EOF

# Create monitoring nginx configs
cat > /opt/blindstrader/nginx/conf.d/monitoring.conf <<NGINX_MON_EOF
server {
    listen 80;
    listen [::]:80;
    server_name insights.${domain} prometheus.${domain};

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# Grafana
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name insights.${domain};

    ssl_certificate /etc/letsencrypt/live/${domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${domain}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers HIGH:!aNULL:!MD5;

    auth_basic "Monitoring Access";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://blindstrader-grafana:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

# Prometheus
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name prometheus.${domain};

    ssl_certificate /etc/letsencrypt/live/${domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${domain}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers HIGH:!aNULL:!MD5;

    auth_basic "Monitoring Access";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://blindstrader-prometheus:9090;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
NGINX_MON_EOF

# Pull Docker images and start services
log_info "Pulling Docker images..."
cd /opt/blindstrader
docker-compose pull

log_info "Starting Docker services..."
docker-compose up -d

# Wait for services to be healthy
log_info "Waiting for services to be ready..."
sleep 30

# Check service status
docker-compose ps

# Create backup script
cat > /opt/blindstrader/backup.sh <<'BACKUP_SCRIPT'
#!/bin/bash
set -e

BACKUP_DIR="/tmp/backup-$(date +%Y-%m-%d-%H-%M)"
S3_BUCKET="${s3_backup_bucket}"
TIMESTAMP=$(date +%Y-%m-%d)

mkdir -p "$BACKUP_DIR"

# Backup MySQL
echo "Backing up MySQL..."
docker exec blindstrader-mysql mysqldump -u root -p"$DB_PASSWORD" --all-databases > "$BACKUP_DIR/mysql-backup.sql"

# Backup Redis
echo "Backing up Redis..."
docker exec blindstrader-redis redis-cli save
cp /var/lib/redis/dump.rdb "$BACKUP_DIR/redis-dump.rdb"

# Create tarball
echo "Creating archive..."
cd "$BACKUP_DIR"
tar czf backup.tar.gz mysql-backup.sql redis-dump.rdb

# Encrypt with GPG
echo "Encrypting backup..."
gpg --encrypt --recipient admin@blindstrader.com --trust-model always -o backup.tar.gz.gpg backup.tar.gz

# Upload to S3
echo "Uploading to S3..."
aws s3 cp backup.tar.gz.gpg "s3://$S3_BUCKET/$TIMESTAMP/backup.tar.gz.gpg"

# Cleanup
cd /
rm -rf "$BACKUP_DIR"

echo "Backup completed successfully!"
BACKUP_SCRIPT

chmod +x /opt/blindstrader/backup.sh

# Create systemd service for backup (only if backups are enabled)
%{ if enable_backups }
cat > /etc/systemd/system/blindstrader-backup.service <<EOF
[Unit]
Description=BlindStrader Backup Service
After=docker.service

[Service]
Type=oneshot
Environment="DB_PASSWORD=$DB_PASSWORD"
ExecStart=/opt/blindstrader/backup.sh
User=root
EOF

cat > /etc/systemd/system/blindstrader-backup.timer <<EOF
[Unit]
Description=BlindStrader Backup Timer

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable blindstrader-backup.timer
systemctl start blindstrader-backup.timer
%{ endif }

# Create systemd service for certbot renewal
cat > /etc/systemd/system/certbot-renew.service <<EOF
[Unit]
Description=Certbot Renewal Service
After=docker.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/docker-compose -f /opt/blindstrader/docker-compose.yml run --rm certbot renew
ExecStartPost=/usr/local/bin/docker-compose -f /opt/blindstrader/docker-compose.yml exec -T nginx nginx -s reload
User=root
EOF

cat > /etc/systemd/system/certbot-renew.timer <<EOF
[Unit]
Description=Certbot Renewal Timer

[Timer]
OnCalendar=daily
OnCalendar=00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable certbot-renew.timer
systemctl start certbot-renew.timer

log_info "BlindStrader EC2 initialization completed successfully!"
log_info ""
log_info "Next steps:"
log_info "1. Wait for DNS propagation"
log_info "2. Obtain SSL certificates: docker-compose run --rm certbot certonly --standalone ..."
log_info "3. Restart nginx: docker-compose restart nginx"
log_info "4. Access application at https://auth.${domain}"
log_info ""
log_info "Services status:"
docker-compose ps
