#!/usr/bin/env python3
"""
Generate / update GitHub Actions workflow files.
- Rewrites build-images.yml (8 parallel build jobs)
- Removes test-catalog.yml and test-user-management.yml
- Creates 8 new test-{service}.yml files (PHP 8.3, path-filtered)
- Updates deploy-staging.yml (8 health-check URLs)
- Updates deploy-production.yml (8 health-check URLs + rollback)
"""

import os

ROOT = "/Users/barkocziroland/laravel/blindstrader"
WORKFLOWS = f"{ROOT}/.github/workflows"

SERVICES = [
    {"name": "identity",      "subdomain": "identity",      "kafka": True,  "port": 8001},
    {"name": "brand",         "subdomain": "brand",         "kafka": True,  "port": 8002},
    {"name": "supplier",      "subdomain": "supplier",      "kafka": True,  "port": 8003},
    {"name": "supply-chain",  "subdomain": "sc",            "kafka": True,  "port": 8004},
    {"name": "payment",       "subdomain": "payment",       "kafka": True,  "port": 8005},
    {"name": "retailer",      "subdomain": "retailer",      "kafka": True,  "port": 8006},
    {"name": "platform",      "subdomain": "platform",      "kafka": True,  "port": 8007},
    {"name": "notification",  "subdomain": "notification",  "kafka": False, "port": 8008},
]


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    print(f"  wrote {os.path.relpath(path, ROOT)}")


def delete(path):
    if os.path.exists(path):
        os.remove(path)
        print(f"  deleted {os.path.relpath(path, ROOT)}")


# ─── build-images.yml ─────────────────────────────────────────────────────────

def gen_build_job(svc_name):
    img_var = f"IMAGE_NAME_{svc_name.upper().replace('-', '_')}"
    return f"""\
  build-{svc_name}:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{{{ env.REGISTRY }}}}
          username: ${{{{ github.actor }}}}
          password: ${{{{ secrets.GITHUB_TOKEN }}}}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{{{ env.REGISTRY }}}}/${{{{ env.{img_var} }}}}
          tags: |
            type=ref,event=branch
            type=ref,event=tag
            type=sha,prefix={{{{{{{{branch}}}}}}}}-
            type=raw,value=latest,enable={{{{{{{{is_default_branch}}}}}}}}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: ./services/{svc_name}
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{{{ steps.meta.outputs.tags }}}}
          labels: ${{{{ steps.meta.outputs.labels }}}}
          cache-from: type=registry,ref=${{{{ env.REGISTRY }}}}/${{{{ env.{img_var} }}}}:buildcache
          cache-to: type=registry,ref=${{{{ env.REGISTRY }}}}/${{{{ env.{img_var} }}}}:buildcache,mode=max
"""


env_block = "\n".join(
    f"  IMAGE_NAME_{s['name'].upper().replace('-', '_')}: ${{{{ github.repository_owner }}}}/blindstrader-{s['name']}"
    for s in SERVICES
)

build_jobs = "\n".join(gen_build_job(s["name"]) for s in SERVICES)

BUILD_IMAGES = f"""\
name: Build and Push Docker Images

on:
  push:
    branches: [main]
    tags:
      - 'prod-v*'
      - 'stage-v*'
  workflow_dispatch:

env:
  REGISTRY: ghcr.io
{env_block}

jobs:
{build_jobs}"""

# ─── test-{service}.yml (one per service) ────────────────────────────────────

PHP_EXTENSIONS = "mbstring, xml, ctype, iconv, intl, pdo_mysql, dom, filter, gd, json, pdo, redis, rdkafka"

def gen_test_workflow(svc):
    name = svc["name"]
    title = name.replace("-", " ").title()
    flag = name.replace("-", "_")

    return f"""\
name: Test {title} Service

on:
  push:
    branches: [main, develop]
    paths:
      - 'services/{name}/**'
      - '.github/workflows/test-{name}.yml'
  pull_request:
    branches: [main, develop]
    paths:
      - 'services/{name}/**'

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: password
          MYSQL_DATABASE: testing
        ports:
          - 3306:3306
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=3

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd="redis-cli ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=3

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup PHP
        uses: shivammathur/setup-php@v2
        with:
          php-version: '8.3'
          extensions: {PHP_EXTENSIONS}
          coverage: xdebug

      - name: Copy .env
        run: |
          cd services/{name}
          cp .env.example .env
          php artisan key:generate

      - name: Install Composer dependencies
        run: |
          cd services/{name}
          composer install --prefer-dist --no-progress --ignore-platform-req=ext-rdkafka

      - name: Run tests
        env:
          APP_ENV: testing
          DB_CONNECTION: mysql
          DB_HOST: 127.0.0.1
          DB_PORT: 3306
          DB_DATABASE: testing
          DB_USERNAME: root
          DB_PASSWORD: password
          REDIS_HOST: 127.0.0.1
          REDIS_PORT: 6379
          CACHE_STORE: array
          SESSION_DRIVER: array
          QUEUE_CONNECTION: sync
        run: |
          cd services/{name}
          php artisan migrate --force
          php artisan test --coverage-clover coverage.xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./services/{name}/coverage.xml
          flags: {flag}
          token: ${{{{ secrets.CODECOV_TOKEN }}}}
"""


# ─── deploy-staging.yml ───────────────────────────────────────────────────────

staging_health = "\n".join(
    f"          curl -f --retry 5 --retry-delay 10 https://{s['subdomain']}.stage.blindstrader.com/health || exit 1"
    for s in SERVICES
)

DEPLOY_STAGING = f"""\
name: Deploy to Staging

on:
  push:
    branches: [develop]
    tags:
      - 'stage-v*'
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: staging

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Ansible
        run: |
          pip install ansible
          ansible-galaxy collection install community.docker

      - name: Configure SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{{{ secrets.ANSIBLE_SSH_PRIVATE_KEY }}}}" > ~/.ssh/blindstrader-ansible-key
          chmod 600 ~/.ssh/blindstrader-ansible-key
          ssh-keyscan -H ${{{{ secrets.STAGE_HOST_IP }}}} >> ~/.ssh/known_hosts

      - name: Update inventory with staging IP
        run: |
          cd ansible
          sed -i "s/ansible_host:.*/ansible_host: ${{{{ secrets.STAGE_HOST_IP }}}}/" inventory/stage.yml

      - name: Wake up staging instance (if auto-shutdown enabled)
        env:
          AWS_ACCESS_KEY_ID: ${{{{ secrets.AWS_ACCESS_KEY_ID }}}}
          AWS_SECRET_ACCESS_KEY: ${{{{ secrets.AWS_SECRET_ACCESS_KEY }}}}
          AWS_DEFAULT_REGION: eu-west-2
        run: |
          INSTANCE_ID=$(aws ec2 describe-instances \\
            --filters "Name=tag:Environment,Values=stage" "Name=instance-state-name,Values=running,stopped" \\
            --query "Reservations[0].Instances[0].InstanceId" \\
            --output text)

          if [ "$INSTANCE_ID" != "None" ]; then
            echo "Starting instance $INSTANCE_ID..."
            aws ec2 start-instances --instance-ids $INSTANCE_ID
            aws ec2 wait instance-running --instance-ids $INSTANCE_ID
            echo "Instance started successfully"
          fi

      - name: Run Ansible deployment
        env:
          ANSIBLE_HOST_KEY_CHECKING: False
        run: |
          cd ansible
          ansible-playbook -i inventory/stage.yml playbooks/deploy-app.yml \\
            -e "version=latest" \\
            -e "github_token=${{{{ secrets.GH_PAT }}}}" \\
            -v

      - name: Verify deployment
        run: |
          echo "Waiting for services to be healthy..."
          sleep 30
{staging_health}

      - name: Notify deployment success
        if: success()
        run: |
          echo "✅ Staging deployment successful"
          # TODO: Add Slack/Discord notification
"""

# ─── deploy-production.yml ────────────────────────────────────────────────────

prod_health = "\n".join(
    f"          curl -f --retry 5 --retry-delay 10 https://{s['subdomain']}.blindstrader.com/health || exit 1"
    for s in SERVICES
)

DEPLOY_PRODUCTION = f"""\
name: Deploy to Production

on:
  push:
    tags:
      - 'prod-v*'
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Ansible
        run: |
          pip install ansible
          ansible-galaxy collection install community.docker

      - name: Configure SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{{{ secrets.ANSIBLE_SSH_PRIVATE_KEY }}}}" > ~/.ssh/blindstrader-ansible-key
          chmod 600 ~/.ssh/blindstrader-ansible-key
          ssh-keyscan -H ${{{{ secrets.PROD_HOST_IP }}}} >> ~/.ssh/known_hosts

      - name: Update inventory with production IP
        run: |
          cd ansible
          sed -i "s/ansible_host:.*/ansible_host: ${{{{ secrets.PROD_HOST_IP }}}}/" inventory/prod.yml

      - name: Run Ansible deployment
        env:
          ANSIBLE_HOST_KEY_CHECKING: False
        run: |
          cd ansible
          ansible-playbook -i inventory/prod.yml playbooks/deploy-app.yml \\
            -e "version=${{{{ github.ref_name }}}}" \\
            -e "github_token=${{{{ secrets.GH_PAT }}}}" \\
            -v

      - name: Verify deployment
        run: |
          echo "Waiting for services to be healthy..."
          sleep 30
{prod_health}

      - name: Notify deployment success
        if: success()
        run: |
          echo "✅ Production deployment successful: ${{{{ github.ref_name }}}}"
          # TODO: Add Slack/Discord notification

      - name: Rollback on failure
        if: failure()
        run: |
          echo "❌ Deployment failed! Initiating rollback..."
          cd ansible
          PREVIOUS_VERSION=$(git tag --sort=-version:refname | grep "prod-v" | sed -n '2p')
          echo "Rolling back to $PREVIOUS_VERSION"
          ansible-playbook -i inventory/prod.yml playbooks/rollback.yml \\
            -e "version=$PREVIOUS_VERSION" \\
            -e "confirm_rollback.user_input=yes"
"""

# ─── Write everything ─────────────────────────────────────────────────────────

# Delete old workflows
delete(f"{WORKFLOWS}/test-catalog.yml")
delete(f"{WORKFLOWS}/test-user-management.yml")

# Write new / updated workflows
write(f"{WORKFLOWS}/build-images.yml", BUILD_IMAGES)
write(f"{WORKFLOWS}/deploy-staging.yml", DEPLOY_STAGING)
write(f"{WORKFLOWS}/deploy-production.yml", DEPLOY_PRODUCTION)

for svc in SERVICES:
    write(f"{WORKFLOWS}/test-{svc['name']}.yml", gen_test_workflow(svc))

print("\n✅ All CI workflow files written.")
