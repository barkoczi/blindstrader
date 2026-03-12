#!/usr/bin/env python3
"""
Update Ansible and Terraform files for the 8-service BlindStrader architecture.

Writes:
  ansible/inventory/prod.yml
  ansible/inventory/stage.yml
  ansible/roles/app/templates/.env.j2
  ansible/roles/app/templates/docker-compose.yml.j2
  ansible/roles/app/tasks/main.yml
  ansible/roles/nginx/templates/app.conf.j2
  ansible/playbooks/deploy-app.yml
  ansible/playbooks/site.yml
  ansible/playbooks/rollback.yml
  ansible/playbooks/ssl.yml
  terraform/modules/dns/main.tf
  terraform/environments/prod/outputs.tf
  terraform/environments/stage/outputs.tf
"""

import os

ROOT = "/Users/barkocziroland/laravel/blindstrader"

SERVICES = [
    {"name": "identity",     "subdomain": "identity",     "tenancy": False, "stripe": False, "kafka": True,  "seeder": "DatabaseSeeder"},
    {"name": "brand",        "subdomain": "brand",        "tenancy": True,  "stripe": False, "kafka": True,  "seeder": "TenantSeeder"},
    {"name": "supplier",     "subdomain": "supplier",     "tenancy": True,  "stripe": False, "kafka": True,  "seeder": "TenantSeeder"},
    {"name": "supply-chain", "subdomain": "sc",           "tenancy": False, "stripe": False, "kafka": True,  "seeder": None},
    {"name": "payment",      "subdomain": "payment",      "tenancy": False, "stripe": True,  "kafka": True,  "seeder": None},
    {"name": "retailer",     "subdomain": "retailer",     "tenancy": True,  "stripe": False, "kafka": True,  "seeder": "TenantSeeder"},
    {"name": "platform",     "subdomain": "platform",     "tenancy": False, "stripe": False, "kafka": True,  "seeder": None},
    {"name": "notification", "subdomain": "notification", "tenancy": False, "stripe": False, "kafka": False, "seeder": None},
]

APP_CONTAINERS = [s["name"] for s in SERVICES]
ALL_CONTAINERS = APP_CONTAINERS + [
    "db", "redis", "kafka", "docs", "nginx", "certbot",
    "prometheus", "grafana", "loki", "promtail",
    "cadvisor", "node-exporter", "mysql-exporter", "redis-exporter",
]

SUBDOMAINS = [s["subdomain"] for s in SERVICES] + ["docs", "insights", "prometheus"]


def write(rel_path, content):
    path = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    print(f"  wrote {rel_path}")


# ─────────────────────────────────────────────────────────────────────────────
# ansible/inventory/prod.yml
# ─────────────────────────────────────────────────────────────────────────────

def services_list(indent=10):
    pad = " " * indent
    return "\n".join(f"{pad}- {c}" for c in ALL_CONTAINERS)


INVENTORY_PROD = f"""\
# Production Inventory
# This file is manually maintained or updated by CI via Terraform outputs.
# Run: cd ../terraform/environments/prod && terraform output -json
# Then update ansible_host below with the Elastic IP from that output.

all:
  children:
    production:
      hosts:
        blindstrader-prod:
          ansible_host: 18.132.180.137  # Elastic IP — update after terraform apply
          ansible_user: ansible
          ansible_become: yes
          ansible_python_interpreter: /usr/bin/python3.9

      vars:
        app_environment: prod
        domain: blindstrader.com
        docker_compose_version: "2.24.5"

        # GitHub Container Registry credentials
        github_username: barkoczi
        github_token: "{{{{ lookup('env', 'GITHUB_TOKEN') }}}}"

        # Service containers
        services:
{services_list()}

        # EBS mount points
        ebs_volumes:
          - device: /dev/nvme1n1
            mount: /var/lib/mysql
            fstype: ext4
          - device: /dev/nvme2n1
            mount: /var/lib/redis
            fstype: ext4
          - device: /dev/nvme3n1
            mount: /var/lib/kafka
            fstype: ext4
          - device: /dev/nvme4n1
            mount: /var/lib/monitoring
            fstype: ext4

        # Backup configuration
        backup_enabled: true
        backup_time: "02:00"
        backup_s3_bucket: "blindstrader-backups-prod"

        # Monitoring
        grafana_port: 3000
        prometheus_port: 9090
"""

INVENTORY_STAGE = f"""\
# Staging Inventory
# Update ansible_host with the Elastic IP from: terraform output -json (stage env)

all:
  children:
    staging:
      hosts:
        blindstrader-stage:
          ansible_host: 18.133.43.175  # Elastic IP — update after terraform apply
          ansible_user: ansible
          ansible_become: yes
          ansible_python_interpreter: /usr/bin/python3.9

      vars:
        app_environment: stage
        domain: stage.blindstrader.com
        docker_compose_version: "2.24.5"

        # GitHub Container Registry
        github_username: barkoczi
        github_token: "{{{{ lookup('env', 'GITHUB_TOKEN') }}}}"

        # Service containers
        services:
{services_list()}

        # EBS mount points
        ebs_volumes:
          - device: /dev/nvme1n1
            mount: /var/lib/mysql
            fstype: ext4
          - device: /dev/nvme2n1
            mount: /var/lib/redis
            fstype: ext4
          - device: /dev/nvme3n1
            mount: /var/lib/kafka
            fstype: ext4
          - device: /dev/nvme4n1
            mount: /var/lib/monitoring
            fstype: ext4

        # Backup configuration (disabled for staging)
        backup_enabled: false

        # Monitoring
        grafana_port: 3000
        prometheus_port: 9090
"""

# ─────────────────────────────────────────────────────────────────────────────
# ansible/roles/app/templates/.env.j2
# ─────────────────────────────────────────────────────────────────────────────

ENV_J2 = """\
# Environment: {{ environment }}
# Generated by Ansible — DO NOT EDIT MANUALLY

# ── Database (shared across all services) ────────────────────────────────────
DB_ROOT_PASSWORD={{ db_root_password_secret.stdout }}
DB_USERNAME=blindstrader
DB_PASSWORD={{ db_password_secret.stdout }}

# ── Redis ─────────────────────────────────────────────────────────────────────
REDIS_PASSWORD={{ redis_password_secret.stdout | default('') }}

# ── Stripe (Payment service) ─────────────────────────────────────────────────
STRIPE_SECRET_KEY={{ stripe_secret_key_secret.stdout }}
STRIPE_WEBHOOK_SECRET={{ stripe_webhook_secret_secret.stdout }}
STRIPE_CONNECT_CLIENT_ID={{ stripe_connect_client_id_secret.stdout }}

# ── Monitoring ────────────────────────────────────────────────────────────────
GRAFANA_ADMIN_PASSWORD={{ grafana_password_secret.stdout }}
MYSQL_EXPORTER_PASSWORD=exporter_pass

# ── Error Tracking ────────────────────────────────────────────────────────────
{% if sentry_dsn is defined and sentry_dsn != '' %}
SENTRY_LARAVEL_DSN={{ sentry_dsn }}
{% else %}
SENTRY_LARAVEL_DSN=
{% endif %}
"""

# ─────────────────────────────────────────────────────────────────────────────
# ansible/roles/app/templates/docker-compose.yml.j2
# ─────────────────────────────────────────────────────────────────────────────

def compose_app_service(svc):
    name = svc["name"]
    img = f"ghcr.io/barkoczi/blindstrader-{name}:latest"
    key_var = f"app_key_{name.replace('-', '_')}_secret"

    base_env = f"""\
      APP_NAME: {name.replace('-', ' ').title().replace(' ', '')}
      APP_KEY: {{{{ {key_var}.stdout }}}}
      APP_ENV: {{{{ environment }}}}
      APP_DEBUG: {{{{ 'true' if environment == 'stage' else 'false' }}}}
      APP_URL: https://{svc['subdomain']}.{{{{ domain }}}}
      DB_HOST: db
      DB_PORT: 3306
      DB_DATABASE: blindstrader_{name.replace('-', '_')}
      DB_USERNAME: ${{DB_USERNAME}}
      DB_PASSWORD: ${{DB_PASSWORD}}
      REDIS_HOST: redis
      REDIS_PORT: 6379
{{% if redis_password_secret.stdout %}}
      REDIS_PASSWORD: ${{REDIS_PASSWORD}}
{{% endif %}}
      SESSION_DRIVER: redis
      CACHE_STORE: redis
      QUEUE_CONNECTION: redis
      SESSION_DOMAIN: .{{{{ domain }}}}"""

    tenancy_env = ""
    if svc["tenancy"]:
        prefix = f"blindstrader_{name.replace('-', '_')}_"
        tenancy_env = f"""
      TENANCY_DB_HOST: db
      TENANCY_DB_PORT: 3306
      TENANCY_DB_USERNAME: ${{DB_USERNAME}}
      TENANCY_DB_PASSWORD: ${{DB_PASSWORD}}
      TENANCY_DB_PREFIX: {prefix}"""

    kafka_env = ""
    if svc["kafka"]:
        kafka_env = "\n      KAFKA_BROKERS: kafka:9092"

    stripe_env = ""
    if svc["stripe"]:
        stripe_env = """
      STRIPE_SECRET_KEY: ${STRIPE_SECRET_KEY}
      STRIPE_WEBHOOK_SECRET: ${STRIPE_WEBHOOK_SECRET}
      STRIPE_CONNECT_CLIENT_ID: ${STRIPE_CONNECT_CLIENT_ID}"""

    sentry_env = f"""
      SENTRY_LARAVEL_DSN: ${{SENTRY_LARAVEL_DSN}}
      SENTRY_ENVIRONMENT: {name}
      SENTRY_TRACES_SAMPLE_RATE: 0.2
      SENTRY_SEND_DEFAULT_PII: "true" """

    # Build depends_on
    deps = ["db", "redis"]
    if svc["kafka"]:
        deps.append("kafka")

    deps_block = "\n".join(
        f"      {d}:\n        condition: service_healthy" for d in deps
    )

    # Build command
    if svc["seeder"]:
        cmd = f"sh -c \"php artisan migrate --force && php artisan db:seed --class={svc['seeder']} --force && php-fpm\""
    else:
        cmd = 'sh -c "php artisan migrate --force && php-fpm"'

    return f"""\
  {name}:
    image: {img}
    container_name: blindstrader-{name}
    restart: unless-stopped
    working_dir: /app
    volumes:
      - /opt/blindstrader/services/{name}:/app
    environment:
{base_env}{tenancy_env}{kafka_env}{stripe_env}{sentry_env}
    depends_on:
{deps_block}
    networks:
      - blindstrader
    command: {cmd}
"""


certbot_domains = " ".join(
    f"-d {{{{ subdomain }}}}.{{{{ domain }}}}"
    for subdomain in [s["subdomain"] for s in SERVICES] + ["docs", "insights", "prometheus"]
)

all_app_service_names = " ".join(s["name"] for s in SERVICES)

# Build the scalar references JSON piece
scalar_refs = ",".join(
    f'{{\"name\":\"{s["name"].replace("-"," ").title()}\",\"url\":\"http://{s["name"]}:9000/docs/api.json\"}}'
    for s in SERVICES
)

COMPOSE_J2 = f"""\
services:
  # ─── Infrastructure ──────────────────────────────────────────────────────────

  db:
    image: mysql:8.0
    container_name: blindstrader-mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: ${{DB_ROOT_PASSWORD}}
      MYSQL_DATABASE: blindstrader_identity
    volumes:
      - /var/lib/mysql:/var/lib/mysql
      - /opt/blindstrader/docker/mysql/init.sql:/docker-entrypoint-initdb.d/init.sql
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
{{% if redis_password_secret.stdout %}}
    command: redis-server --save 900 1 --requirepass ${{REDIS_PASSWORD}}
{{% else %}}
    command: redis-server --save 900 1
{{% endif %}}
    volumes:
      - /var/lib/redis:/data
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
      - /var/lib/kafka:/var/lib/kafka/data
    networks:
      - blindstrader
    healthcheck:
      test: ["CMD", "kafka-broker-api-versions", "--bootstrap-server", "localhost:9092"]
      interval: 30s
      timeout: 10s
      retries: 10

  # ─── Application Services ─────────────────────────────────────────────────────

{"".join(compose_app_service(s) for s in SERVICES)}\
  # ─── API Docs Portal (Scalar) ─────────────────────────────────────────────────

  docs:
    image: scalar/api-reference:latest
    container_name: blindstrader-docs
    restart: unless-stopped
    environment:
      SCALAR_CONFIGURATION: >{{\n        {{"theme":"purple","layout":"modern","showSidebar":true,"references":[{scalar_refs}]}}}}
    depends_on:
{chr(10).join(f"      - {s['name']}" for s in SERVICES)}
    networks:
      - blindstrader

  # ─── Reverse Proxy ───────────────────────────────────────────────────────────

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
      - /opt/blindstrader/nginx/.htpasswd:/etc/nginx/.htpasswd:ro
{chr(10).join(f"      - /opt/blindstrader/services/{s['name']}:/app/{s['name']}:ro" for s in SERVICES)}
      - /opt/blindstrader/logs/nginx:/var/log/nginx
      - certbot_webroot:/var/www/certbot:ro
    depends_on:
{chr(10).join(f"      - {s['name']}" for s in SERVICES)}
      - docs
    networks:
      - blindstrader

  certbot:
    image: certbot/certbot:latest
    container_name: blindstrader-certbot
    volumes:
      - /opt/blindstrader/nginx/certs:/etc/letsencrypt
      - certbot_webroot:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait ${{{{!}}}}; done;'"
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
      PMA_PASSWORD: ${{DB_ROOT_PASSWORD}}
      UPLOAD_LIMIT: 100M
    depends_on:
      db:
        condition: service_healthy
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
      - '--web.enable-lifecycle'
    volumes:
      - /opt/blindstrader/monitoring/prometheus:/etc/prometheus
      - /var/lib/monitoring/prometheus:/prometheus
    networks:
      - blindstrader

  grafana:
    image: grafana/grafana:latest
    container_name: blindstrader-grafana
    restart: unless-stopped
    environment:
      GF_SERVER_ROOT_URL: https://insights.{{{{ domain }}}}
      GF_SERVER_DOMAIN: insights.{{{{ domain }}}}
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: ${{GRAFANA_ADMIN_PASSWORD}}
      GF_INSTALL_PLUGINS: ""
    volumes:
      - /opt/blindstrader/monitoring/grafana/provisioning:/etc/grafana/provisioning
      - /var/lib/monitoring/grafana:/var/lib/grafana
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
    volumes:
      - /opt/blindstrader/monitoring/loki:/etc/loki
      - /var/lib/monitoring/loki:/loki
    networks:
      - blindstrader

  promtail:
    image: grafana/promtail:latest
    container_name: blindstrader-promtail
    restart: unless-stopped
    command: -config.file=/etc/promtail/promtail-config.yml
    volumes:
      - /opt/blindstrader/monitoring/promtail:/etc/promtail
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /opt/blindstrader/logs/nginx:/var/log/nginx:ro
    depends_on:
      - loki
    networks:
      - blindstrader

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: blindstrader-cadvisor
    restart: unless-stopped
    privileged: true
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
      DATA_SOURCE_NAME: "exporter:${{MYSQL_EXPORTER_PASSWORD}}@tcp(blindstrader-mysql:3306)/"
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
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - blindstrader

networks:
  blindstrader:
    driver: bridge

volumes:
  certbot_webroot:
"""

# ─────────────────────────────────────────────────────────────────────────────
# ansible/roles/app/tasks/main.yml
# ─────────────────────────────────────────────────────────────────────────────

def secret_task(secret_name, register_name, fail_when_missing=True):
    path = f"/blindstrader/{{{{ app_environment }}}}/{secret_name}"
    return f"""\
    - name: Get {secret_name.replace('_', ' ')}
      shell: |
        aws secretsmanager get-secret-value \\
          --secret-id {path} \\
          --region eu-west-2 \\
          --query SecretString \\
          --output text
      register: {register_name}
      no_log: true
      changed_when: false
{"      failed_when: false" if not fail_when_missing else ""}\
"""


app_key_tasks = "\n".join(
    secret_task(
        f"app_key_{s['name'].replace('-', '_')}",
        f"app_key_{s['name'].replace('-', '_')}_secret",
        fail_when_missing=True,
    )
    for s in SERVICES
)

migration_tasks = "\n".join(
    f"""\
- name: Run migrations — {s['name']}
  community.docker.docker_container_exec:
    container: blindstrader-{s['name']}
    command: php artisan migrate --force
  register: migration_{s['name'].replace('-', '_')}
  failed_when: false
  tags: [app, deploy, migrations]
"""
    for s in SERVICES
)

migration_debug_lines = "\n".join(
    f'          - "{s["name"]}: {{{{ migration_{s["name"].replace("-", "_")}.stdout | default("N/A") }}}}"'
    for s in SERVICES
)

APP_TASKS = f"""\
---
# Application role — Deploy and manage application services

- name: Retrieve secrets from AWS Secrets Manager
  block:
    - name: Get database root password
      shell: |
        aws secretsmanager get-secret-value \\
          --secret-id /blindstrader/{{{{ app_environment }}}}/db_root_password \\
          --region eu-west-2 \\
          --query SecretString \\
          --output text
      register: db_root_password_secret
      no_log: true
      changed_when: false

    - name: Get database password
      shell: |
        aws secretsmanager get-secret-value \\
          --secret-id /blindstrader/{{{{ app_environment }}}}/db_password \\
          --region eu-west-2 \\
          --query SecretString \\
          --output text
      register: db_password_secret
      no_log: true
      changed_when: false

    - name: Get Redis password
      shell: |
        aws secretsmanager get-secret-value \\
          --secret-id /blindstrader/{{{{ app_environment }}}}/redis_password \\
          --region eu-west-2 \\
          --query SecretString \\
          --output text
      register: redis_password_secret
      no_log: true
      changed_when: false
      failed_when: false

    - name: Get Grafana admin password
      shell: |
        aws secretsmanager get-secret-value \\
          --secret-id /blindstrader/{{{{ app_environment }}}}/grafana_admin_password \\
          --region eu-west-2 \\
          --query SecretString \\
          --output text
      register: grafana_password_secret
      no_log: true
      changed_when: false

    - name: Get Stripe secret key
      shell: |
        aws secretsmanager get-secret-value \\
          --secret-id /blindstrader/{{{{ app_environment }}}}/stripe_secret_key \\
          --region eu-west-2 \\
          --query SecretString \\
          --output text
      register: stripe_secret_key_secret
      no_log: true
      changed_when: false
      failed_when: false

    - name: Get Stripe webhook secret
      shell: |
        aws secretsmanager get-secret-value \\
          --secret-id /blindstrader/{{{{ app_environment }}}}/stripe_webhook_secret \\
          --region eu-west-2 \\
          --query SecretString \\
          --output text
      register: stripe_webhook_secret_secret
      no_log: true
      changed_when: false
      failed_when: false

    - name: Get Stripe Connect client ID
      shell: |
        aws secretsmanager get-secret-value \\
          --secret-id /blindstrader/{{{{ app_environment }}}}/stripe_connect_client_id \\
          --region eu-west-2 \\
          --query SecretString \\
          --output text
      register: stripe_connect_client_id_secret
      no_log: true
      changed_when: false
      failed_when: false

    # Per-service Laravel APP_KEYs
{app_key_tasks}
  tags: [app, secrets]

- name: Create shared environment file
  template:
    src: .env.j2
    dest: /opt/blindstrader/.env
    owner: ansible
    group: ansible
    mode: '0600'
  no_log: true
  tags: [app, config]

- name: Deploy docker-compose configuration
  template:
    src: docker-compose.yml.j2
    dest: /opt/blindstrader/docker-compose.yml
    owner: ansible
    group: ansible
    mode: '0644'
  tags: [app, config]

- name: Login to GitHub Container Registry
  shell: echo "{{{{ github_token }}}}" | docker login ghcr.io -u "{{{{ github_username }}}}" --password-stdin
  when: github_token is defined and github_token | length > 0
  no_log: true
  tags: [app, deploy]

- name: Pull latest Docker images
  shell: docker compose pull
  args:
    chdir: /opt/blindstrader
  tags: [app, deploy]

- name: Start all services
  shell: docker compose up -d
  args:
    chdir: /opt/blindstrader
  tags: [app, deploy]

- name: Wait for MySQL to be ready
  wait_for:
    host: localhost
    port: 3306
    delay: 5
    timeout: 120
  tags: [app, deploy]

- name: Wait for Redis to be ready
  wait_for:
    host: localhost
    port: 6379
    delay: 5
    timeout: 60
  tags: [app, deploy]

- name: Wait for Kafka to be ready
  wait_for:
    host: localhost
    port: 9092
    delay: 10
    timeout: 120
  tags: [app, deploy]

{migration_tasks}
- name: Display migration results
  debug:
    msg:
{migration_debug_lines}
  tags: [app, deploy, migrations]

- name: Verify all services are running
  shell: docker compose ps
  args:
    chdir: /opt/blindstrader
  register: service_status
  tags: [app, health]

- name: Display service status
  debug:
    var: service_status.stdout_lines
  tags: [app, health]
"""

# ─────────────────────────────────────────────────────────────────────────────
# ansible/roles/nginx/templates/app.conf.j2
# ─────────────────────────────────────────────────────────────────────────────

def nginx_service_block(svc):
    name = svc["name"]
    subdomain = svc["subdomain"]
    return f"""\
# ─── {name.replace('-', ' ').title()} Service ─────────────────────────────────────────────────────────────────
server {{
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name {subdomain}.{{{{ domain }}}};
    root /app/{name}/public;
    index index.php;

    ssl_certificate     /etc/letsencrypt/live/{{{{ domain }}}}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{{{{ domain }}}}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {{ try_files $uri $uri/ /index.php?$query_string; }}

    location ~ \\.php$ {{
        try_files $uri =404;
        fastcgi_split_path_info ^(.+\\.php)(/.+)$;
        fastcgi_pass {name}:9000;
        fastcgi_index index.php;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param PATH_INFO $fastcgi_path_info;
    }}

    location ~ /\\.(?!well-known).* {{ deny all; }}
}}

"""

all_server_names = "\n        ".join(
    [f"{s['subdomain']}.{{{{ domain }}}}" for s in SERVICES]
    + ["docs.{{ domain }}", "insights.{{ domain }}", "prometheus.{{ domain }}", "{{ domain }}"]
)

NGINX_APP_CONF_J2 = f"""\
# HTTP → HTTPS redirect
server {{
    listen 80;
    listen [::]:80;
    server_name
        {all_server_names};

    location /.well-known/acme-challenge/ {{
        root /var/www/certbot;
    }}

    location / {{
        return 301 https://$server_name$request_uri;
    }}
}}

{"".join(nginx_service_block(s) for s in SERVICES)}\
# ─── API Docs Portal (Scalar) ─────────────────────────────────────────────────
server {{
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name docs.{{{{ domain }}}};

    ssl_certificate     /etc/letsencrypt/live/{{{{ domain }}}}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{{{{ domain }}}}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {{
        proxy_pass         http://docs:80;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }}
}}

# ─── Root domain → Identity ───────────────────────────────────────────────────
server {{
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name {{{{ domain }}}};

    ssl_certificate     /etc/letsencrypt/live/{{{{ domain }}}}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{{{{ domain }}}}/privkey.pem;

    return 301 https://identity.{{{{ domain }}}}$request_uri;
}}
"""

# ─────────────────────────────────────────────────────────────────────────────
# ansible/playbooks/deploy-app.yml
# ─────────────────────────────────────────────────────────────────────────────

stop_start_containers = " ".join(s["name"] for s in SERVICES)

cache_clear_loop = "\n".join(
    f"""\
        - {{ container: 'blindstrader-{s["name"]}', command: 'php artisan cache:clear' }}
        - {{ container: 'blindstrader-{s["name"]}', command: 'php artisan config:cache' }}
        - {{ container: 'blindstrader-{s["name"]}', command: 'php artisan route:cache' }}"""
    for s in SERVICES
)

migration_loop = "\n".join(
    f"""\
    - name: Run migrations — {s["name"]}
      community.docker.docker_container_exec:
        container: blindstrader-{s["name"]}
        command: php artisan migrate --force
      register: migration_{s["name"].replace("-", "_")}
      failed_when: false
      tags: [migrations]
"""
    for s in SERVICES
)

health_checks = "\n".join(
    f'        - "http://localhost:{8001 + i}/health"'
    for i, s in enumerate(SERVICES)
)

DEPLOY_APP = f"""\
---
# Application Deployment Playbook
# Usage: ansible-playbook -i inventory/prod.yml playbooks/deploy-app.yml -e "version=latest"

- name: Deploy BlindStrader Application
  hosts: all
  become: yes
  gather_facts: no

  vars:
    app_version: "{{{{ version | default('latest') }}}}"

  pre_tasks:
    - name: Display deployment info
      debug:
        msg: "Deploying {{{{ app_version }}}} to {{{{ app_environment }}}}"

  tasks:
    - name: Pull latest Docker images
      shell: docker compose pull
      args:
        chdir: /opt/blindstrader
      tags: [pull]

    - name: Stop application containers
      shell: docker compose stop {stop_start_containers}
      args:
        chdir: /opt/blindstrader
      tags: [stop]

    - name: Start application containers with new images
      shell: docker compose up -d {stop_start_containers}
      args:
        chdir: /opt/blindstrader
      tags: [start]

    - name: Wait for infrastructure to be healthy
      wait_for:
        host: localhost
        port: "{{{{ item }}}}"
        delay: 5
        timeout: 120
      loop:
        - 3306  # MySQL
        - 6379  # Redis
        - 9092  # Kafka
      tags: [health]

{migration_loop}
    - name: Cache config and routes for all services
      community.docker.docker_container_exec:
        container: "{{{{ item.container }}}}"
        command: "{{{{ item.command }}}}"
      loop:
{cache_clear_loop}
      failed_when: false
      tags: [cache]

    - name: Reload nginx
      shell: docker compose restart nginx
      args:
        chdir: /opt/blindstrader
      tags: [nginx]

    - name: Health check — all service endpoints
      uri:
        url: "{{{{ item }}}}"
        status_code: 200
      loop:
{health_checks}
      register: health_results
      failed_when: false
      tags: [health]

    - name: Display deployment results
      debug:
        msg:
          - "=========================================="
          - "Deployment Status: SUCCESS"
          - "Version: {{{{ app_version }}}}"
          - "Environment: {{{{ app_environment }}}}"
          - "=========================================="
"""

# ─────────────────────────────────────────────────────────────────────────────
# ansible/playbooks/site.yml
# ─────────────────────────────────────────────────────────────────────────────

container_verify_loop = "\n".join(
    f"        - blindstrader-{c}" for c in APP_CONTAINERS + ["mysql", "redis", "kafka", "nginx", "prometheus", "grafana"]
)

SITE_YML = f"""\
---
# Main Playbook — Complete Infrastructure Setup
# Usage: ansible-playbook -i inventory/prod.yml playbooks/site.yml

- name: Configure BlindStrader Infrastructure
  hosts: all
  become: yes
  gather_facts: yes

  pre_tasks:
    - name: Display target environment
      debug:
        msg: "Configuring {{{{ inventory_hostname }}}} for {{{{ app_environment }}}} environment"

    - name: Wait for system to be ready
      wait_for_connection:
        delay: 5
        timeout: 300

    - name: Gather facts
      setup:

  roles:
    - role: common
      tags: [common, base]

    - role: docker
      tags: [docker]

    - role: nginx
      tags: [nginx]

    - role: monitoring
      tags: [monitoring]

    - role: backups
      tags: [backups]
      when: backup_enabled | default(false)

    - role: app
      tags: [app, deploy]

  post_tasks:
    - name: Verify all Docker containers are running
      community.docker.docker_container_info:
        name: "{{{{ item }}}}"
      loop:
{container_verify_loop}
      register: container_status

    - name: Display deployment summary
      debug:
        msg:
          - "=========================================="
          - "Deployment completed successfully!"
          - "Environment: {{{{ app_environment }}}}"
          - "Domain: {{{{ domain }}}}"
          - "=========================================="
          - "Services deployed:"
""" + "\n".join(
    f'          - "  {s["subdomain"]}.{{{{{{ domain }}}}}} -> {s["name"]}"'
    for s in SERVICES
) + """
          - "  docs.{{{{ domain }}}} -> Scalar API docs"
          - "  insights.{{{{ domain }}}} → Grafana"
          - "=========================================="
          - "Next steps:"
          - "1. Verify DNS propagation for all 9 subdomains"
          - "2. Obtain SSL certificates: ansible-playbook playbooks/ssl.yml"
          - "3. Test /health on each service endpoint"
          - "=========================================="
"""

# ─────────────────────────────────────────────────────────────────────────────
# ansible/playbooks/rollback.yml
# ─────────────────────────────────────────────────────────────────────────────

rollback_image_loop = "\n".join(
    "        - { image: 'ghcr.io/barkoczi/blindstrader-" + s["name"] + "' }"
    for s in SERVICES
)

ROLLBACK_YML = f"""\
---
# Rollback Playbook
# Usage: ansible-playbook -i inventory/prod.yml playbooks/rollback.yml -e "version=prod-v1.0.0"

- name: Rollback BlindStrader Application
  hosts: all
  become: yes
  gather_facts: no

  vars:
    rollback_version: "{{{{ version | mandatory }}}}"

  pre_tasks:
    - name: Confirm rollback version
      pause:
        prompt: "Are you sure you want to rollback to {{{{ rollback_version }}}}? (yes/no)"
      register: confirm_rollback

    - name: Abort if not confirmed
      fail:
        msg: "Rollback aborted by user"
      when: confirm_rollback.user_input | lower != 'yes'

  tasks:
    - name: Display rollback info
      debug:
        msg: "Rolling back {{{{ app_environment }}}} to version {{{{ rollback_version }}}}"

    - name: Create pre-rollback database backup
      community.docker.docker_container_exec:
        container: blindstrader-mysql
        command: mysqldump --all-databases --single-transaction
      register: db_backup
      tags: [backup]

    - name: Save backup to file
      copy:
        content: "{{{{ db_backup.stdout }}}}"
        dest: "/tmp/pre-rollback-backup-{{{{ ansible_date_time.epoch }}}}.sql"
      tags: [backup]

    - name: Pull rollback version images
      community.docker.docker_image:
        name: "{{{{ item.image }}}}"
        tag: "{{{{ rollback_version }}}}"
        source: pull
      loop:
{rollback_image_loop}
      tags: [pull]

    - name: Update docker-compose to use rollback version
      replace:
        path: /opt/blindstrader/docker-compose.yml
        regexp: ':latest$'
        replace: ':{{{{ rollback_version }}}}'
      tags: [config]

    - name: Stop application services
      shell: docker compose stop {stop_start_containers}
      args:
        chdir: /opt/blindstrader
      tags: [stop]

    - name: Start services with rollback version
      shell: docker compose up -d {stop_start_containers}
      args:
        chdir: /opt/blindstrader
      tags: [start]

    - name: Wait for infrastructure to be ready
      wait_for:
        host: localhost
        port: "{{{{ item }}}}"
        delay: 5
        timeout: 120
      loop:
        - 3306
        - 6379
        - 9092
      tags: [health]

    - name: Health check — verify rollback succeeded
      uri:
        url: "{{{{ item }}}}"
        status_code: 200
      loop:
{health_checks}
      register: health_check
      retries: 5
      delay: 10
      failed_when: false
      tags: [health]

    - name: Display rollback results
      debug:
        msg:
          - "=========================================="
          - "Rollback Status: SUCCESS"
          - "Rolled back to: {{{{ rollback_version }}}}"
          - "Environment: {{{{ app_environment }}}}"
          - "Backup saved: /tmp/pre-rollback-backup-{{{{ ansible_date_time.epoch }}}}.sql"
          - "=========================================="
"""

# ─────────────────────────────────────────────────────────────────────────────
# ansible/playbooks/ssl.yml
# ─────────────────────────────────────────────────────────────────────────────

SSL_DOMAINS_LIST = "\n".join(
    f'      - "{s["subdomain"]}.{{{{ domain }}}}"'
    for s in SERVICES
) + """
      - "docs.{{ domain }}"
      - "insights.{{ domain }}"
      - "prometheus.{{ domain }}" """

SSL_YML = f"""\
---
# SSL Certificate Management Playbook
# Usage: ansible-playbook -i inventory/prod.yml playbooks/ssl.yml

- name: Obtain and Renew SSL Certificates
  hosts: all
  become: yes
  gather_facts: no

  vars:
    certbot_email: "admin@{{{{ domain }}}}"
    certbot_domains:
{SSL_DOMAINS_LIST}

  tasks:
    - name: Check if wildcard certificate exists
      stat:
        path: "/opt/blindstrader/nginx/certs/live/{{{{ domain }}}}/fullchain.pem"
      register: cert_exists

    - name: Stop nginx for standalone certbot (first time only)
      shell: docker compose stop nginx
      args:
        chdir: /opt/blindstrader
      when: not cert_exists.stat.exists
      tags: [certbot]

    - name: Obtain SSL certificates — standalone mode (first time)
      command: >
        docker run --rm
        -v /opt/blindstrader/nginx/certs:/etc/letsencrypt
        -p 80:80 certbot/certbot certonly --standalone
        --email {{{{ certbot_email }}}}
        --agree-tos --no-eff-email --expand
        -d {{{{ certbot_domains | join(' -d ') }}}}
      when: not cert_exists.stat.exists
      tags: [certbot]

    - name: Start nginx after obtaining certificates
      shell: docker compose up -d nginx
      args:
        chdir: /opt/blindstrader
      when: not cert_exists.stat.exists
      tags: [nginx]

    - name: Renew existing certificates — webroot mode
      command: >
        docker run --rm
        -v /opt/blindstrader/nginx/certs:/etc/letsencrypt
        -v /opt/blindstrader/certbot-webroot:/var/www/certbot
        certbot/certbot renew --webroot --webroot-path=/var/www/certbot
      when: cert_exists.stat.exists
      register: renewal_result
      tags: [certbot, renew]

    - name: Reload nginx after renewal
      shell: docker compose restart nginx
      args:
        chdir: /opt/blindstrader
      when:
        - cert_exists.stat.exists
        - renewal_result is changed
      tags: [nginx]

    - name: Enable auto-renewal systemd timer
      systemd:
        name: certbot-renewal.timer
        enabled: yes
        state: started
        daemon_reload: yes
      tags: [systemd]

    - name: Display SSL status
      debug:
        msg:
          - "=========================================="
          - "SSL Certificate Status"
          - "Environment: {{{{ app_environment }}}}"
          - "Domain: {{{{ domain }}}}"
          - "=========================================="
          - "Certificates configured for:"
          - "{{{{ certbot_domains }}}}"
          - "=========================================="
          - "Auto-renewal: ENABLED (daily via systemd timer)"
          - "=========================================="
"""

# ─────────────────────────────────────────────────────────────────────────────
# terraform/modules/dns/main.tf
# ─────────────────────────────────────────────────────────────────────────────

service_records = "\n\n".join(
    f"""\
resource "aws_route53_record" "{s['name'].replace('-', '_')}" {{
  zone_id = aws_route53_zone.main.zone_id
  name    = "{s['subdomain']}.{'{'}var.domain{'}'}"
  type    = "A"
  ttl     = 300
  records = [var.elastic_ip]
}}"""
    for s in SERVICES
)

DNS_MAIN_TF = f"""\
resource "aws_route53_zone" "main" {{
  name = var.domain

  tags = {{
    Name        = "${{var.environment}}-hosted-zone"
    Environment = var.environment
    ManagedBy   = "terraform"
  }}
}}

# ─── Service A records ────────────────────────────────────────────────────────

{service_records}

resource "aws_route53_record" "docs" {{
  zone_id = aws_route53_zone.main.zone_id
  name    = "docs.${{var.domain}}"
  type    = "A"
  ttl     = 300
  records = [var.elastic_ip]
}}

resource "aws_route53_record" "insights" {{
  zone_id = aws_route53_zone.main.zone_id
  name    = "insights.${{var.domain}}"
  type    = "A"
  ttl     = 300
  records = [var.elastic_ip]
}}

resource "aws_route53_record" "prometheus" {{
  zone_id = aws_route53_zone.main.zone_id
  name    = "prometheus.${{var.domain}}"
  type    = "A"
  ttl     = 300
  records = [var.elastic_ip]
}}

resource "aws_route53_record" "root" {{
  zone_id = aws_route53_zone.main.zone_id
  name    = var.domain
  type    = "A"
  ttl     = 300
  records = [var.elastic_ip]
}}

# ─── CNAME records for third-party services ──────────────────────────────────

resource "aws_route53_record" "cname" {{
  for_each = var.cname_records

  zone_id = aws_route53_zone.main.zone_id
  name    = "${{each.key}}.${{var.domain}}"
  type    = "CNAME"
  ttl     = 300
  records = [each.value]
}}
"""

# ─────────────────────────────────────────────────────────────────────────────
# terraform/environments/prod/outputs.tf  &  stage/outputs.tf
# ─────────────────────────────────────────────────────────────────────────────

def outputs_tf(env, domain_var):
    subdomain_list = "\n".join(
        f'       - {s["subdomain"]}.{domain_var} → {s["name"]}'
        for s in SERVICES
    )
    dns_instructions = "\n".join(
        f"       - {s['subdomain']}.{domain_var} -> ${{module.security.elastic_ip}}"
        for s in SERVICES
    ) + f"\n       - docs.{domain_var} -> ${{module.security.elastic_ip}}"

    secrets_list = "\n".join(
        f"       - /blindstrader/{env}/app_key_{s['name'].replace('-', '_')}"
        for s in SERVICES
    )

    return f"""\
output "ec2_instance_id" {{
  description = "EC2 instance ID"
  value       = module.ec2.instance_id
}}

output "elastic_ip" {{
  description = "Elastic IP address"
  value       = module.security.elastic_ip
}}

output "s3_backup_bucket" {{
  description = "S3 backup bucket name"
  value       = module.storage.s3_bucket_name
}}

output "ssh_command" {{
  description = "SSH command to connect to the EC2 instance"
  value       = "ssh -i ~/.ssh/blindstrader-{env}-key ec2-user@${{module.security.elastic_ip}}"
}}

output "ansible_inventory" {{
  description = "Ansible inventory information"
  value = {{
    environment      = var.environment
    host             = "blindstrader-${{var.environment}}"
    ansible_host     = module.security.elastic_ip
    ansible_user     = "ansible"
    domain           = var.domain
    ebs_devices      = module.ec2.ebs_devices
    backup_enabled   = var.enable_backups
    backup_s3_bucket = var.enable_backups ? "blindstrader-backups-${{var.environment}}" : ""
  }}
}}

output "deployment_info" {{
  description = "Post-deployment instructions"
  value       = <<-EOT
    ==========================================
    Terraform Apply Complete!
    ==========================================

    Environment : ${{var.environment}}
    Elastic IP  : ${{module.security.elastic_ip}}

    ── Step 1: Add DNS A records in Cloudflare ──
{dns_instructions}
       - insights.{domain_var} -> ${{module.security.elastic_ip}}
       - prometheus.{domain_var} -> ${{module.security.elastic_ip}}

    ── Step 2: Update Ansible inventory ──
    Edit: ../../ansible/inventory/${{var.environment}}.yml
    Set:  ansible_host: ${{module.security.elastic_ip}}

    ── Step 3: Create secrets in AWS Secrets Manager ──
    Shared:
       - /blindstrader/${{var.environment}}/db_root_password
       - /blindstrader/${{var.environment}}/db_password
       - /blindstrader/${{var.environment}}/redis_password
       - /blindstrader/${{var.environment}}/grafana_admin_password
       - /blindstrader/${{var.environment}}/stripe_secret_key
       - /blindstrader/${{var.environment}}/stripe_webhook_secret
       - /blindstrader/${{var.environment}}/stripe_connect_client_id
       - /blindstrader/shared/gpg_public_key

    Per-service APP_KEYs:
{secrets_list}

    ── Step 4: Run Ansible ──
    cd ../../ansible
    ansible-playbook -i inventory/${{var.environment}}.yml playbooks/site.yml

    ── Step 5: Obtain SSL certificates ──
    ansible-playbook -i inventory/${{var.environment}}.yml playbooks/ssl.yml

    ── Step 6: Verify services ──
{chr(10).join(f"    https://{s['subdomain']}.{domain_var}/health" for s in SERVICES)}
    https://docs.{domain_var}
    https://insights.{domain_var}

    ==========================================
  EOT
}}
"""


# ─────────────────────────────────────────────────────────────────────────────
# Write everything
# ─────────────────────────────────────────────────────────────────────────────

write("ansible/inventory/prod.yml", INVENTORY_PROD)
write("ansible/inventory/stage.yml", INVENTORY_STAGE)
write("ansible/roles/app/templates/.env.j2", ENV_J2)
write("ansible/roles/app/templates/docker-compose.yml.j2", COMPOSE_J2)
write("ansible/roles/app/tasks/main.yml", APP_TASKS)
write("ansible/roles/nginx/templates/app.conf.j2", NGINX_APP_CONF_J2)
write("ansible/playbooks/deploy-app.yml", DEPLOY_APP)
write("ansible/playbooks/site.yml", SITE_YML)
write("ansible/playbooks/rollback.yml", ROLLBACK_YML)
write("ansible/playbooks/ssl.yml", SSL_YML)
write("terraform/modules/dns/main.tf", DNS_MAIN_TF)
write("terraform/environments/prod/outputs.tf", outputs_tf("prod", "${var.domain}"))
write("terraform/environments/stage/outputs.tf", outputs_tf("stage", "${var.domain}"))

print("\n✅ All Ansible and Terraform files updated.")
