# GitHub Actions CI/CD Setup Guide

This guide explains how to set up and use the GitHub Actions workflows for automated testing, building, and deployment.

## Table of Contents

1. [Overview](#overview)
2. [Workflows](#workflows)
3. [Secrets Configuration](#secrets-configuration)
4. [Usage](#usage)
5. [Troubleshooting](#troubleshooting)

## Overview

The BlindStrader CI/CD pipeline consists of 5 GitHub Actions workflows:

| Workflow | Trigger | Purpose | Duration |
|----------|---------|---------|----------|
| `test-user-management.yml` | Push/PR to `main`, `develop` | Run user-management tests | ~3-5 min |
| `test-catalog.yml` | Push/PR to `main`, `develop` | Run catalog service tests | ~3-5 min |
| `build-images.yml` | Push to `main`, tags | Build and push Docker images | ~5-10 min |
| `deploy-production.yml` | Tags `prod-v*` | Deploy to production | ~5-7 min |
| `deploy-staging.yml` | Push to `develop`, tags `stage-v*` | Deploy to staging | ~5-7 min |

### Pipeline Flow

```
┌─────────────────┐
│  Git Push       │
└────────┬────────┘
         │
         ├──────────────────────┬──────────────────────┐
         │                      │                      │
         ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐   ┌─────────────────┐
│  Test User Mgmt │    │  Test Catalog   │   │  Test Other...  │
└────────┬────────┘    └────────┬────────┘   └────────┬────────┘
         │                      │                      │
         └──────────────────────┴──────────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Build Images   │
                       └────────┬────────┘
                                │
                 ┌──────────────┴──────────────┐
                 │                             │
                 ▼                             ▼
        ┌─────────────────┐          ┌─────────────────┐
        │ Deploy Staging  │          │Deploy Production│
        │  (develop)      │          │    (tags)       │
        └─────────────────┘          └─────────────────┘
```

## Workflows

### 1. Test User Management Service

**File**: `.github/workflows/test-user-management.yml`

**Triggers**:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Only when files in `services/user-management/` change

**What it does**:
1. Sets up PHP 8.2 with required extensions
2. Starts MySQL and Redis services
3. Installs Composer dependencies
4. Runs PHPUnit tests with coverage
5. Uploads coverage to Codecov

**Key features**:
- Uses GitHub Actions service containers for MySQL and Redis
- Generates code coverage reports
- Fast feedback on pull requests

### 2. Test Catalog Service

**File**: `.github/workflows/test-catalog.yml`

**Triggers**:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Only when files in `services/catalog/` change

**What it does**:
- Same as User Management tests but for the Catalog service

### 3. Build and Push Docker Images

**File**: `.github/workflows/build-images.yml`

**Triggers**:
- Push to `main` branch
- Tags matching `prod-v*` or `stage-v*`
- Manual dispatch via GitHub UI

**What it does**:
1. Logs into GitHub Container Registry (ghcr.io)
2. Builds Docker images for both services
3. Tags images with:
   - Branch name (e.g., `main`)
   - Git tag (e.g., `prod-v1.2.0`)
   - Git SHA (e.g., `main-abc1234`)
   - `latest` for main branch
4. Pushes images to ghcr.io
5. Uses layer caching for faster builds

**Registry**:
- User Management: `ghcr.io/barkoczi/blindstrader-user-management`
- Catalog: `ghcr.io/barkoczi/blindstrader-catalog`

### 4. Deploy to Production

**File**: `.github/workflows/deploy-production.yml`

**Triggers**:
- Git tags matching `prod-v*` (e.g., `prod-v1.0.0`)
- Manual dispatch via GitHub UI

**Environment**: `production` (with protection rules)

**What it does**:
1. Installs Ansible and required collections
2. Configures SSH access to production server
3. Updates Ansible inventory with production IP
4. Runs Ansible deployment playbook
5. Waits 30 seconds for service health
6. Verifies application endpoints
7. Sends success notification
8. **Auto-rollback** on failure to previous version

**Protection**:
- Requires manual approval (recommended)
- Uses GitHub Environment secrets
- Includes automatic rollback

### 5. Deploy to Staging

**File**: `.github/workflows/deploy-staging.yml`

**Triggers**:
- Push to `develop` branch
- Git tags matching `stage-v*`
- Manual dispatch via GitHub UI

**Environment**: `staging`

**What it does**:
1. Installs Ansible and required collections
2. **Wakes up EC2 instance** if auto-shutdown is enabled
3. Configures SSH access to staging server
4. Updates Ansible inventory with staging IP
5. Runs Ansible deployment playbook (always uses `latest` tag)
6. Verifies application endpoints
7. Sends success notification

**Special feature**: Automatically starts stopped EC2 instances (cost optimization)

## Secrets Configuration

### Required GitHub Secrets

Configure these in **Settings → Secrets and variables → Actions**:

#### Repository Secrets

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `GH_PAT` | GitHub Personal Access Token (for ghcr.io) | `ghp_abc123...` |

**How to create `GH_PAT`**:
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with scopes:
   - `read:packages` - Pull images
   - `write:packages` - Push images
3. Copy and save in repository secrets

#### Environment Secrets (Production)

Create environment: **Settings → Environments → New environment** (`production`)

| Secret Name | Description | How to get |
|-------------|-------------|------------|
| `ANSIBLE_SSH_PRIVATE_KEY` | Private SSH key for Ansible user | Content of `~/.ssh/blindstrader-ansible-key` |
| `PROD_HOST_IP` | Production Elastic IP | From Terraform output |
| `AWS_ACCESS_KEY_ID` | AWS access key for rollback (optional) | AWS IAM credentials |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for rollback (optional) | AWS IAM credentials |

**Production environment protection** (recommended):
- ✅ Enable "Required reviewers" (add yourself or team lead)
- ✅ Enable "Wait timer" (5 minutes to allow cancel)
- ✅ Limit to protected branches only

#### Environment Secrets (Staging)

Create environment: **Settings → Environments → New environment** (`staging`)

| Secret Name | Description | How to get |
|-------------|-------------|------------|
| `ANSIBLE_SSH_PRIVATE_KEY` | Private SSH key for Ansible user | Same as production |
| `STAGE_HOST_IP` | Staging Elastic IP | From Terraform output |
| `AWS_ACCESS_KEY_ID` | AWS access key for auto-start | AWS IAM credentials |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for auto-start | AWS IAM credentials |

### Setting Secrets

**Via GitHub UI**:
```
Repository → Settings → Secrets and variables → Actions → New repository secret
```

**Via GitHub CLI**:
```bash
# Repository secret
gh secret set GH_PAT --body "ghp_your_token_here"

# Environment secret
gh secret set ANSIBLE_SSH_PRIVATE_KEY --env production --body "$(cat ~/.ssh/blindstrader-ansible-key)"
gh secret set PROD_HOST_IP --env production --body "52.56.123.45"
```

## Usage

### Automatic Deployments

#### Staging Deployment (Automatic on develop)

```bash
# On feature branch
git checkout develop
git pull origin develop

# Merge your feature
git merge feature/my-feature

# Push to develop → triggers staging deployment
git push origin develop
```

**Flow**:
1. Tests run automatically
2. Docker images built and pushed
3. Staging auto-deploys with `latest` tag
4. Notification sent

#### Production Deployment (Manual with tags)

```bash
# Ensure main is up to date
git checkout main
git pull origin main

# Create and push production tag
git tag -a prod-v1.2.0 -m "Release v1.2.0 - Added feature X"
git push origin prod-v1.2.0
```

**Flow**:
1. Tag push triggers production workflow
2. **Manual approval required** (if configured)
3. Docker images built with tag `prod-v1.2.0`
4. Ansible deploys specific version
5. Health checks run
6. Notification sent
7. Auto-rollback on failure

### Manual Deployments

#### Via GitHub UI

1. Go to **Actions** tab
2. Select workflow (e.g., "Deploy to Production")
3. Click "Run workflow" button
4. Select branch/tag
5. Click "Run workflow"

#### Via GitHub CLI

```bash
# Deploy to staging
gh workflow run deploy-staging.yml --ref develop

# Deploy to production (specific tag)
gh workflow run deploy-production.yml --ref prod-v1.2.0

# Build images manually
gh workflow run build-images.yml --ref main
```

### Versioning Strategy

Use semantic versioning with environment prefix:

**Production tags**:
- `prod-v1.0.0` - Major release
- `prod-v1.1.0` - Minor release (new features)
- `prod-v1.1.1` - Patch release (bug fixes)

**Staging tags** (optional):
- `stage-v1.1.0-rc1` - Release candidate
- `stage-v1.1.0-beta` - Beta version

**Examples**:
```bash
# Major release
git tag -a prod-v2.0.0 -m "Release v2.0.0 - Major redesign"

# Minor release
git tag -a prod-v1.3.0 -m "Release v1.3.0 - Added user profiles"

# Patch
git tag -a prod-v1.2.1 -m "Release v1.2.1 - Fixed login bug"

# Push
git push origin prod-v1.2.1
```

### Rollback

#### Automatic Rollback

Production deployment automatically rolls back on failure:
- Triggered if health checks fail
- Reverts to previous version tag
- No manual intervention needed

#### Manual Rollback

If you need to rollback manually:

**Option 1: Via Ansible directly**
```bash
cd ansible
ansible-playbook -i inventory/prod.yml playbooks/rollback.yml -e "version=prod-v1.1.0"
```

**Option 2: Deploy older tag via GitHub Actions**
```bash
# Re-run deployment with old tag
gh workflow run deploy-production.yml --ref prod-v1.1.0
```

## Monitoring Workflows

### View Workflow Status

**GitHub UI**:
```
Repository → Actions → Select workflow → View runs
```

**GitHub CLI**:
```bash
# List recent runs
gh run list --workflow=deploy-production.yml --limit 10

# View specific run
gh run view <run-id>

# Watch live run
gh run watch
```

### Notifications

#### Email Notifications

GitHub sends email notifications for:
- Workflow failures
- Manual approval requests
- Deployment completions

Configure: **Settings → Notifications → Actions**

#### Slack/Discord Integration (TODO)

Add webhook notifications in workflows:

```yaml
- name: Notify Slack
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
    payload: |
      {
        "text": "✅ Production deployed: ${{ github.ref_name }}"
      }
```

## Troubleshooting

### Workflow Fails at "Test" Stage

**Problem**: Tests fail but work locally

**Solutions**:
```bash
# 1. Check if .env.example is up to date
cd services/user-management
cp .env.example .env
php artisan key:generate

# 2. Run tests locally with same DB versions
docker-compose -f docker-compose.test.yml up -d
composer test

# 3. Check workflow logs in GitHub Actions tab
# Look for specific test failures
```

### Workflow Fails at "Build Images"

**Problem**: Docker build fails or authentication issues

**Solutions**:
```bash
# 1. Verify GH_PAT token is valid
curl -H "Authorization: Bearer $GH_PAT" https://ghcr.io/v2/

# 2. Check if Dockerfile exists and is valid
docker build -f services/user-management/Dockerfile services/user-management/

# 3. Verify package permissions
# Go to Repository → Packages → Package settings
# Ensure "Write" permissions for GitHub Actions
```

### Workflow Fails at "Deploy" Stage

**Problem**: Ansible playbook fails

**Solutions**:
```bash
# 1. Verify SSH key is correct
cat ~/.ssh/blindstrader-ansible-key.pub
# Compare with Terraform variable

# 2. Test Ansible connection manually
ansible -i inventory/prod.yml all -m ping

# 3. Check EC2 instance is running
aws ec2 describe-instances --filters "Name=tag:Environment,Values=prod"

# 4. Verify security group allows SSH from GitHub Actions IPs
# GitHub uses dynamic IPs, consider using VPN or bastion host
```

### Health Checks Fail After Deployment

**Problem**: Deployment completes but health checks return errors

**Solutions**:
```bash
# 1. SSH to instance and check logs
ssh -i ~/.ssh/blindstrader-ansible-key ansible@<IP>
docker logs user-management --tail=100
docker logs catalog --tail=100

# 2. Check if migrations failed
docker exec user-management php artisan migrate:status

# 3. Verify .env configuration
cat /opt/blindstrader/.env

# 4. Test endpoints manually
curl -v http://localhost/health
```

### GitHub Actions Secrets Not Found

**Problem**: `secret not found` error

**Solutions**:
```bash
# 1. Verify secret name matches exactly (case-sensitive)
# 2. Check if using environment secret in correct environment
# 3. List secrets via GitHub CLI
gh secret list
gh secret list --env production

# 4. Re-create secret
gh secret set ANSIBLE_SSH_PRIVATE_KEY --env production --body "$(cat ~/.ssh/blindstrader-ansible-key)"
```

## Best Practices

### Security

- ✅ Use environment secrets for production
- ✅ Enable branch protection on `main`
- ✅ Require pull request reviews
- ✅ Enable "Required reviewers" for production deployments
- ✅ Rotate SSH keys and tokens regularly
- ✅ Use least-privilege IAM permissions

### Development Workflow

- ✅ Create feature branches from `develop`
- ✅ Open PR to `develop` (triggers tests)
- ✅ Merge to `develop` (auto-deploys staging)
- ✅ Test in staging thoroughly
- ✅ Create PR from `develop` to `main`
- ✅ Merge to `main` and create release tag
- ✅ Tag triggers production deployment

### Testing

- ✅ Write tests for all new features
- ✅ Aim for >80% code coverage
- ✅ Run tests locally before pushing
- ✅ Fix failing tests immediately
- ✅ Don't merge PRs with failing tests

### Deployments

- ✅ Always deploy to staging first
- ✅ Use semantic versioning consistently
- ✅ Write meaningful tag messages
- ✅ Monitor application after deployment
- ✅ Keep rollback versions accessible
- ✅ Document breaking changes

## Advanced Configuration

### Parallel Tests

Run services in parallel for faster CI:

```yaml
jobs:
  test:
    strategy:
      matrix:
        service: [user-management, catalog]
    steps:
      - name: Test ${{ matrix.service }}
        run: |
          cd services/${{ matrix.service }}
          composer test
```

### Conditional Deployments

Deploy only if specific conditions are met:

```yaml
jobs:
  deploy:
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    steps:
      # deployment steps
```

### Manual Approval with Environment

Require manual approval for production:

```yaml
jobs:
  deploy:
    environment:
      name: production
      url: https://blindstrader.com
```

Then enable "Required reviewers" in environment settings.

## Next Steps

1. Review [Complete Workflow Guide](COMPLETE_WORKFLOW.md) for end-to-end process
2. Set up branch protection rules
3. Configure Slack/Discord notifications
4. Set up status badges in README
5. Configure automatic dependency updates (Dependabot)

## Support

For issues:
- Check workflow logs in GitHub Actions tab
- Review [Ansible Deployment Guide](ANSIBLE_DEPLOYMENT.md)
- Consult [GitHub Actions Documentation](https://docs.github.com/actions)
