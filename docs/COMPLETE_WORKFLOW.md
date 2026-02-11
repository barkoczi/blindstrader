# Complete Development & Deployment Workflow

This guide provides an end-to-end walkthrough of the complete development, testing, and deployment process for BlindStrader.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Development Workflow](#development-workflow)
3. [Testing Strategy](#testing-strategy)
4. [Deployment Process](#deployment-process)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Emergency Procedures](#emergency-procedures)

## Architecture Overview

### Infrastructure Layers

```
┌─────────────────────────────────────────────────────────┐
│                     Developer Machine                    │
│  • Local Development                                     │
│  • Git Commits                                           │
│  • Terraform/Ansible Execution                          │
└────────────────────────┬─────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│    GitHub    │  │     AWS      │  │  Monitoring  │
│              │  │              │  │              │
│ • Repository │  │ • Terraform  │  │ • Grafana    │
│ • CI/CD      │  │ • EC2        │  │ • Prometheus │
│ • Packages   │  │ • S3/Route53 │  │ • Loki       │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┴─────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Staging    │  │  Production  │  │   Backups    │
│              │  │              │  │              │
│ • Auto-stop  │  │ • High Avail │  │ • S3 Glacier │
│ • Latest tag │  │ • Tagged ver │  │ • GPG Encrypt│
└──────────────┘  └──────────────┘  └──────────────┘
```

### Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Infrastructure** | Terraform, AWS (EC2, S3, Route53, Secrets Manager) |
| **Configuration** | Ansible, Cloud-Init |
| **Application** | Laravel 10, PHP 8.2, MySQL 8.0, Redis 7 |
| **Containerization** | Docker, Docker Compose |
| **Web Server** | Nginx, PHP-FPM |
| **SSL** | Certbot, Let's Encrypt |
| **CI/CD** | GitHub Actions |
| **Monitoring** | Prometheus, Grafana, Loki, Promtail, cAdvisor |
| **Registry** | GitHub Container Registry (ghcr.io) |

## Development Workflow

### 1. Initial Setup (One-Time)

#### A. Clone Repository

```bash
git clone https://github.com/barkoczi/blindstrader.git
cd blindstrader
```

#### B. Local Development Environment

```bash
# Copy environment files
cp services/user-management/.env.example services/user-management/.env
cp services/catalog/.env.example services/catalog/.env

# Generate application keys
cd services/user-management && php artisan key:generate
cd ../catalog && php artisan key:generate

# Start local development environment
cd ../..
docker-compose up -d

# Run migrations
docker exec user-management php artisan migrate
docker exec catalog php artisan migrate
```

#### C. Configure Git Workflow

```bash
# Set up Git hooks (optional)
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Run tests before commit
composer test
EOF
chmod +x .git/hooks/pre-commit
```

### 2. Feature Development

#### A. Create Feature Branch

```bash
# Always branch from develop
git checkout develop
git pull origin develop

# Create feature branch (use descriptive names)
git checkout -b feature/user-profile-page
# or
git checkout -b fix/login-redirect-bug
# or
git checkout -b refactor/database-queries
```

**Branch naming conventions**:
- `feature/` - New features
- `fix/` or `bugfix/` - Bug fixes
- `refactor/` - Code refactoring
- `chore/` - Maintenance tasks
- `docs/` - Documentation updates

#### B. Develop Feature

```bash
# Make changes
vim services/user-management/app/Http/Controllers/ProfileController.php

# Test locally
docker exec user-management php artisan test

# Check code style (if configured)
composer cs-check
```

#### C. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat(auth): Add user profile page with avatar upload

- Created ProfileController with show, edit, update methods
- Added profile view with form validation
- Implemented avatar upload to S3
- Added tests for profile controller

Closes #123"
```

**Commit message format** (Conventional Commits):
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

#### D. Push and Create Pull Request

```bash
# Push feature branch
git push origin feature/user-profile-page

# Create PR via GitHub CLI
gh pr create --base develop --title "Add user profile page" --body "
## Description
Implements user profile page with avatar upload functionality

## Changes
- Added ProfileController
- Created profile views
- Implemented S3 avatar storage

## Testing
- All unit tests pass
- Manual testing completed
- Edge cases covered

## Screenshots
[Attach screenshots if UI changes]

Closes #123
"
```

### 3. Code Review Process

#### Review Checklist

**For Author**:
- [ ] Tests added/updated and passing
- [ ] Code follows project style guidelines
- [ ] Documentation updated
- [ ] No sensitive data in commits
- [ ] Migration files if DB changes
- [ ] Self-review completed

**For Reviewer**:
- [ ] Code logic is sound
- [ ] Tests are comprehensive
- [ ] No security vulnerabilities
- [ ] Performance considerations addressed
- [ ] Follows SOLID principles
- [ ] No unnecessary complexity

#### Approval and Merge

```bash
# After approval, merge to develop
# Via GitHub UI or CLI:
gh pr merge --squash --delete-branch
```

## Testing Strategy

### Test Pyramid

```
        ┌─────────────┐
        │     E2E     │  Few, expensive, slow
        │   Tests     │
        ├─────────────┤
        │ Integration │  Some, medium cost
        │   Tests     │
        ├─────────────┤
        │    Unit     │  Many, cheap, fast
        │   Tests     │
        └─────────────┘
```

### 1. Local Testing

```bash
# Run all tests for a service
cd services/user-management
composer test

# Run specific test file
php artisan test tests/Feature/ProfileTest.php

# Run with coverage
php artisan test --coverage

# Run specific test method
php artisan test --filter testUserCanUploadAvatar
```

### 2. Automated Testing (CI)

**Triggered on**:
- Push to `main` or `develop`
- Pull requests
- Changed files in service directories

**What runs**:
1. PHP syntax check
2. Composer dependency installation
3. Database migrations
4. PHPUnit test suite
5. Code coverage reporting

### 3. Staging Testing

After deployment to staging:

```bash
# Smoke tests
curl https://auth.stage.blindstrader.com/health
curl https://catalog.stage.blindstrader.com/health

# Manual exploratory testing
# Use staging environment for QA

# Performance testing (optional)
ab -n 1000 -c 10 https://catalog.stage.blindstrader.com/api/products
```

## Deployment Process

### Overview

```
Local Dev → Git Push → Tests → Build Images → Deploy → Verify
```

### 1. Infrastructure Provisioning (One-Time)

#### A. Prepare Prerequisites

```bash
# Follow PRE_DEPLOYMENT.md
# 1. Generate GPG keys
# 2. Generate SSH keys (EC2 and Ansible)
# 3. Create AWS Secrets Manager entries
# 4. Configure terraform.tfvars
```

#### B. Deploy Infrastructure with Terraform

```bash
# Staging first
cd terraform/environments/stage
terraform init
terraform plan
terraform apply

# Note the Elastic IP from output
# Example: 35.178.234.56
```

#### C. Configure Ansible Inventory

```bash
# Update inventory file with Elastic IP
cd ../../../ansible
vim inventory/stage.yml

# Set: ansible_host: 35.178.234.56
```

#### D. Configure Server with Ansible

```bash
# Run complete setup
ansible-playbook -i inventory/stage.yml playbooks/site.yml

# This takes ~10-15 minutes
# Installs Docker, configures services, sets up monitoring
```

#### E. Obtain SSL Certificates

```bash
# After DNS propagates
ansible-playbook -i inventory/stage.yml playbooks/ssl.yml
```

#### F. Repeat for Production

```bash
cd terraform/environments/prod
terraform init
terraform plan
terraform apply

# Configure inventory
cd ../../../ansible
vim inventory/prod.yml

# Run Ansible
ansible-playbook -i inventory/prod.yml playbooks/site.yml
ansible-playbook -i inventory/prod.yml playbooks/ssl.yml
```

### 2. Application Deployment (Routine)

#### A. Staging Deployment (Automatic)

```bash
# Merge feature to develop
git checkout develop
git merge feature/user-profile-page
git push origin develop
```

**Automatic flow**:
1. ✅ Tests run via GitHub Actions
2. ✅ Docker images built with `latest` tag
3. ✅ Pushed to ghcr.io
4. ✅ Staging EC2 woken up (if stopped)
5. ✅ Ansible pulls images and deploys
6. ✅ Health checks run
7. ✅ Notification sent

#### B. Verify Staging

```bash
# Check deployment status
gh run list --workflow=deploy-staging.yml --limit 1

# Test endpoints
curl https://auth.stage.blindstrader.com/health
curl https://catalog.stage.blindstrader.com/health

# Manual QA testing in staging
```

#### C. Production Deployment (Manual with Tags)

```bash
# Merge develop to main
git checkout main
git merge develop
git push origin main

# Create production release tag
git tag -a prod-v1.2.0 -m "Release v1.2.0

Features:
- User profile page with avatar upload
- Improved search performance
- Bug fixes for login redirect

Breaking changes:
- None

Migration notes:
- Run: php artisan migrate
"

# Push tag (triggers deployment)
git push origin prod-v1.2.0
```

**Automatic flow**:
1. ⏸️  Manual approval required (if configured)
2. ✅ Docker images built with `prod-v1.2.0` tag
3. ✅ Pushed to ghcr.io
4. ✅ Ansible deploys tagged version
5. ✅ Database migrations run
6. ✅ Health checks performed
7. ✅ Success notification or auto-rollback

#### D. Monitor Deployment

```bash
# Watch deployment progress
gh run watch

# View logs
gh run view --log

# SSH to instance if needed
ssh -i ~/.ssh/blindstrader-ansible-key ansible@<PROD_IP>
docker logs user-management --tail=100
```

### 3. Post-Deployment Verification

```bash
# Automated health checks (done by GitHub Actions)
# Manual verification:

# 1. Application endpoints
curl -f https://auth.blindstrader.com/health
curl -f https://catalog.blindstrader.com/health

# 2. Monitoring
# Visit: https://insights.blindstrader.com
# Check dashboards for anomalies

# 3. Database migrations
ssh -i ~/.ssh/blindstrader-ansible-key ansible@<IP>
docker exec user-management php artisan migrate:status

# 4. Error logs
docker logs --since 5m user-management
docker logs --since 5m catalog

# 5. Performance
# Check response times in Grafana
```

## Monitoring & Maintenance

### 1. Daily Operations

#### Monitor Application Health

- **Grafana**: https://insights.blindstrader.com
  - Application metrics
  - Database performance
  - Cache hit rates
  - Request rates and errors

- **Prometheus**: https://prometheus.blindstrader.com
  - Raw metrics and queries
  - Alert rules status

- **Logs**: Via Loki in Grafana
  - Application logs
  - Nginx access logs
  - Error traces

#### Key Metrics to Watch

| Metric | Threshold | Action |
|--------|-----------|--------|
| CPU Usage | >80% sustained | Scale up instance |
| Memory Usage | >85% | Investigate memory leaks |
| Disk Space | >90% | Clean logs, expand volume |
| Response Time | >500ms p95 | Investigate slow queries |
| Error Rate | >1% | Check logs, investigate |
| Database Connections | >80% of max | Optimize connection pool |

### 2. Backup Verification

```bash
# Check backup status
ssh -i ~/.ssh/blindstrader-ansible-key ansible@<PROD_IP>
systemctl status blindstrader-backup.timer

# List S3 backups
aws s3 ls s3://blindstrader-backups-prod/prod/

# Test backup restoration (staging)
# Follow DISASTER_RECOVERY.md
```

### 3. Security Updates

```bash
# Monthly: Update system packages
ssh -i ~/.ssh/blindstrader-ansible-key ansible@<IP>
sudo yum update -y

# Update Docker images
cd /opt/blindstrader
docker-compose pull
docker-compose up -d

# Or via Ansible
ansible-playbook -i inventory/prod.yml playbooks/site.yml --tags common,docker
```

### 4. Certificate Renewal

Automatic renewal runs daily at 02:00 UTC. Verify:

```bash
# Check timer status
ssh -i ~/.ssh/blindstrader-ansible-key ansible@<IP>
systemctl status certbot-renewal.timer

# Manual renewal if needed
ansible-playbook -i inventory/prod.yml playbooks/ssl.yml --tags renew
```

### 5. Cost Optimization

**Staging auto-shutdown** (if enabled):
- Stops: 6 PM UTC weekdays
- Starts: 8 AM UTC weekdays
- Saves: 50-70% on staging costs

**Monitor costs**:
```bash
# AWS Cost Explorer
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=TAG,Key=Environment
```

## Emergency Procedures

### 1. Rollback Production

#### Automatic Rollback

If deployment health checks fail, automatic rollback occurs to previous version.

#### Manual Rollback via GitHub Actions

```bash
# Redeploy previous version
git tag -l "prod-v*" | sort -V | tail -n 2 | head -n 1
# Returns: prod-v1.1.0

# Trigger deployment with old tag
gh workflow run deploy-production.yml --ref prod-v1.1.0
```

#### Manual Rollback via Ansible

```bash
cd ansible
ansible-playbook -i inventory/prod.yml playbooks/rollback.yml -e "version=prod-v1.1.0"
```

### 2. Disaster Recovery

Follow [DISASTER_RECOVERY.md](DISASTER_RECOVERY.md) for:
- Database restoration from S3 backups
- Complete infrastructure rebuild
- Data recovery procedures

### 3. Emergency Hotfix

For critical production bugs:

```bash
# 1. Create hotfix branch from main (not develop!)
git checkout main
git checkout -b hotfix/critical-bug-fix

# 2. Make minimal fix
# Edit files...
git commit -m "hotfix: Fix critical bug in payment processing"

# 3. Push and create PR to main
git push origin hotfix/critical-bug-fix
gh pr create --base main --title "HOTFIX: Critical bug fix"

# 4. After review and merge, tag immediately
git checkout main
git pull
git tag -a prod-v1.2.1 -m "Hotfix v1.2.1 - Critical bug fix"
git push origin prod-v1.2.1

# 5. Merge back to develop
git checkout develop
git merge main
git push origin develop
```

### 4. Service Outage Response

```bash
# 1. Check service status
ssh -i ~/.ssh/blindstrader-ansible-key ansible@<IP>
docker ps -a

# 2. Check logs
docker logs user-management --tail=200
docker logs catalog --tail=200
docker logs mysql --tail=200

# 3. Restart services
docker-compose restart

# 4. If database issues
docker exec mysql mysql -u root -p -e "SHOW PROCESSLIST;"

# 5. If still down, restore from backup
# Follow DISASTER_RECOVERY.md
```

### 5. Security Incident

```bash
# 1. Immediately rotate credentials
aws secretsmanager update-secret \
  --secret-id /blindstrader/prod/db_password \
  --secret-string "NEW_SECURE_PASSWORD"

# 2. Regenerate Laravel APP_KEY
docker exec user-management php artisan key:generate --force

# 3. Redeploy with new secrets
ansible-playbook -i inventory/prod.yml playbooks/deploy-app.yml

# 4. Review access logs
docker exec nginx cat /var/log/nginx/access.log | grep -i "suspicious-pattern"

# 5. Update security groups if needed
# AWS Console → EC2 → Security Groups
```

## Best Practices Summary

### Development

- ✅ Branch from `develop`, not `main`
- ✅ Write tests for all features
- ✅ Follow conventional commit messages
- ✅ Keep PRs focused and small
- ✅ Request code reviews
- ✅ Update documentation

### Deployment

- ✅ Always deploy to staging first
- ✅ Test thoroughly in staging
- ✅ Use semantic versioning for tags
- ✅ Deploy during low-traffic hours
- ✅ Monitor after deployment
- ✅ Have rollback plan ready

### Security

- ✅ Never commit secrets
- ✅ Rotate credentials regularly
- ✅ Keep dependencies updated
- ✅ Review security advisories
- ✅ Use least-privilege IAM roles
- ✅ Enable MFA everywhere

### Monitoring

- ✅ Check Grafana daily
- ✅ Set up alert notifications
- ✅ Monitor disk space
- ✅ Verify backups weekly
- ✅ Test disaster recovery quarterly
- ✅ Document incidents

## Quick Reference

### Common Commands

```bash
# Local development
docker-compose up -d
docker-compose logs -f

# Testing
composer test
php artisan test --filter testUserCanLogin

# Deployment
git tag -a prod-v1.2.0 -m "Release v1.2.0"
git push origin prod-v1.2.0

# Monitoring
gh run list --limit 5
gh run watch

# Ansible
ansible-playbook -i inventory/prod.yml playbooks/deploy-app.yml
ansible-playbook -i inventory/prod.yml playbooks/rollback.yml -e "version=prod-v1.1.0"

# Infrastructure
cd terraform/environments/prod
terraform plan
terraform apply
```

### Useful Links

- **GitHub Repository**: https://github.com/barkoczi/blindstrader
- **Staging**: https://stage.blindstrader.com
- **Production**: https://blindstrader.com
- **Monitoring (Prod)**: https://insights.blindstrader.com
- **Prometheus (Prod)**: https://prometheus.blindstrader.com
- **Container Registry**: https://github.com/barkoczi?tab=packages

## Next Steps

1. ✅ Complete infrastructure setup
2. ✅ Configure GitHub Actions secrets
3. ✅ Deploy to staging and test
4. ✅ Deploy first production release
5. ⏭️  Set up monitoring alerts
6. ⏭️  Configure Slack notifications
7. ⏭️  Document runbooks for common issues
8. ⏭️  Train team on workflows

## Support & Feedback

For questions or improvements to this workflow:
- Open an issue on GitHub
- Update documentation via PR
- Share learnings with the team

---

**Congratulations!** You now have a complete, automated, production-ready deployment pipeline. 🎉
