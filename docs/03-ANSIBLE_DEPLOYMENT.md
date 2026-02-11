# Ansible Deployment Guide

This guide explains how to deploy and manage the BlindStrader infrastructure using Ansible.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Deployment Workflows](#deployment-workflows)
5. [Playbook Reference](#playbook-reference)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

- **Ansible** >= 2.14
- **Python** 3.8+
- **SSH access** to EC2 instances
- **AWS CLI** configured (for Secrets Manager access during development)

### Install Ansible

```bash
# macOS
brew install ansible

# Ubuntu/Debian
sudo apt update
sudo apt install ansible

# Using pip
pip3 install ansible
```

### Install Ansible Collections

```bash
ansible-galaxy collection install community.docker
```

## Installation

### 1. Generate SSH Key for Ansible

```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/blindstrader-ansible-key -C "ansible-automation"
```

**Important**: Add the public key to your `terraform.tfvars`:

```hcl
ansible_ssh_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQ... ansible-automation"
```

### 2. Update Ansible Inventory

After running `terraform apply`, update the inventory files with the Elastic IP:

**Production** (`ansible/inventory/prod.yml`):
```yaml
all:
  children:
    production:
      hosts:
        blindstrader-prod:
          ansible_host: 52.56.123.45  # Replace with your Elastic IP
```

**Staging** (`ansible/inventory/stage.yml`):
```yaml
all:
  children:
    staging:
      hosts:
        blindstrader-stage:
          ansible_host: 35.178.234.56  # Replace with your Elastic IP
```

### 3. Test Ansible Connection

```bash
cd ansible

# Test production
ansible -i inventory/prod.yml all -m ping

# Test staging
ansible -i inventory/stage.yml all -m ping
```

Expected output:
```
blindstrader-prod | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

## Configuration

### Inventory Variables

Key variables defined in `inventory/*.yml`:

| Variable | Description | Example |
|----------|-------------|---------|
| `environment` | Environment name | `prod`, `stage` |
| `domain` | Primary domain | `blindstrader.com` |
| `docker_compose_version` | Docker Compose version | `2.24.5` |
| `ebs_volumes` | EBS device mappings | See inventory files |
| `backup_enabled` | Enable backups | `true` (prod only) |
| `backup_s3_bucket` | S3 bucket for backups | `blindstrader-backups-prod` |

### Role Overview

| Role | Purpose | Key Tasks |
|------|---------|-----------|
| `common` | Base system setup | Update packages, mount EBS volumes, create directories |
| `docker` | Docker installation | Install Docker, Docker Compose, configure daemon |
| `nginx` | Web server config | Deploy nginx configs, setup basic auth |
| `monitoring` | Observability stack | Configure Prometheus, Grafana, Loki |
| `backups` | Automated backups | Deploy backup scripts, systemd timers |
| `app` | Application deployment | Pull images, run migrations, start services |

## Deployment Workflows

### First-Time Complete Setup

Use this for initial infrastructure configuration:

```bash
cd ansible

# Production
ansible-playbook -i inventory/prod.yml playbooks/site.yml

# Staging
ansible-playbook -i inventory/stage.yml playbooks/site.yml
```

**What it does:**
1. Configures base system (common role)
2. Installs Docker and Docker Compose
3. Sets up nginx with SSL-ready configs
4. Configures monitoring stack
5. Sets up backups (prod only)
6. Deploys application and runs migrations

**Duration**: ~10-15 minutes

### Application-Only Deployment

For routine application updates (fastest):

```bash
cd ansible

# Deploy latest version
ansible-playbook -i inventory/prod.yml playbooks/deploy-app.yml

# Deploy specific version
ansible-playbook -i inventory/prod.yml playbooks/deploy-app.yml -e "version=prod-v1.2.0"
```

**What it does:**
1. Pulls latest Docker images
2. Stops application containers
3. Starts containers with new images
4. Runs database migrations
5. Clears application cache
6. Reloads nginx
7. Health checks

**Duration**: ~2-3 minutes

### SSL Certificate Management

#### First-Time Certificate Obtainment

```bash
cd ansible
ansible-playbook -i inventory/prod.yml playbooks/ssl.yml
```

**Requirements:**
- DNS must be propagated and pointing to your Elastic IP
- Nginx will be stopped temporarily for standalone mode

**What it does:**
1. Checks if certificates exist
2. Stops nginx (first time only)
3. Obtains certificates via Certbot standalone
4. Starts nginx with SSL enabled
5. Sets up auto-renewal timer (daily at 02:00 UTC)

#### Manual Certificate Renewal

```bash
cd ansible
ansible-playbook -i inventory/prod.yml playbooks/ssl.yml --tags renew
```

### Rollback Deployment

To rollback to a previous version:

```bash
cd ansible
ansible-playbook -i inventory/prod.yml playbooks/rollback.yml -e "version=prod-v1.1.0"
```

**What it does:**
1. Prompts for confirmation
2. Creates database backup before rollback
3. Pulls specific version images
4. Updates docker-compose configuration
5. Restarts services with old version
6. Runs health checks

**Important**: Have the rollback version tag ready!

### Specific Role Execution

Run only specific roles using tags:

```bash
# Update only nginx configuration
ansible-playbook -i inventory/prod.yml playbooks/site.yml --tags nginx

# Update only monitoring
ansible-playbook -i inventory/prod.yml playbooks/site.yml --tags monitoring

# Update backups configuration
ansible-playbook -i inventory/prod.yml playbooks/site.yml --tags backups

# Deploy app without migrations
ansible-playbook -i inventory/prod.yml playbooks/deploy-app.yml --skip-tags migrations
```

## Playbook Reference

### site.yml - Complete Infrastructure Setup

**Usage**: First-time setup or complete reconfiguration

```bash
ansible-playbook -i inventory/prod.yml playbooks/site.yml
```

**Roles executed** (in order):
1. common
2. docker
3. nginx
4. monitoring
5. backups (if enabled)
6. app

**Tags**:
- `common`, `base` - Base system configuration
- `docker` - Docker installation
- `nginx` - Nginx configuration
- `monitoring` - Monitoring stack
- `backups` - Backup configuration
- `app`, `deploy` - Application deployment

### deploy-app.yml - Application Deployment

**Usage**: Routine deployments

```bash
# Latest version
ansible-playbook -i inventory/prod.yml playbooks/deploy-app.yml

# Specific version
ansible-playbook -i inventory/prod.yml playbooks/deploy-app.yml -e "version=prod-v1.2.0"
```

**Extra variables**:
- `version` - Docker image tag (default: `latest`)

**Tags**:
- `pull` - Pull Docker images
- `stop` - Stop containers
- `start` - Start containers
- `health` - Health checks
- `migrations` - Run migrations
- `cache` - Clear caches
- `nginx` - Reload nginx

### rollback.yml - Version Rollback

**Usage**: Emergency rollback

```bash
ansible-playbook -i inventory/prod.yml playbooks/rollback.yml -e "version=prod-v1.1.0"
```

**Extra variables** (required):
- `version` - Version to rollback to

**Interactive prompt**: Confirms rollback before execution

### ssl.yml - SSL Certificate Management

**Usage**: Obtain or renew certificates

```bash
# First time
ansible-playbook -i inventory/prod.yml playbooks/ssl.yml

# Renewal only
ansible-playbook -i inventory/prod.yml playbooks/ssl.yml --tags renew
```

**Tags**:
- `certbot` - Certificate operations
- `nginx` - Nginx reload
- `renew` - Renewal only
- `systemd` - Configure auto-renewal

## Advanced Usage

### Parallel Deployments

Deploy to multiple environments simultaneously:

```bash
# NOT RECOMMENDED for production!
ansible-playbook -i inventory/prod.yml,inventory/stage.yml playbooks/deploy-app.yml
```

### Dry Run Mode

Check what would change without making changes:

```bash
ansible-playbook -i inventory/prod.yml playbooks/site.yml --check --diff
```

### Verbose Output

For debugging:

```bash
# Level 1: Verbose
ansible-playbook -i inventory/prod.yml playbooks/deploy-app.yml -v

# Level 2: More verbose
ansible-playbook -i inventory/prod.yml playbooks/deploy-app.yml -vv

# Level 3: Debug mode
ansible-playbook -i inventory/prod.yml playbooks/deploy-app.yml -vvv
```

### Limited Execution

Run specific tasks:

```bash
# Only run tasks up to a specific task name
ansible-playbook -i inventory/prod.yml playbooks/site.yml --step

# Start from a specific task
ansible-playbook -i inventory/prod.yml playbooks/site.yml --start-at-task="Pull latest Docker images"
```

## Troubleshooting

### Connection Issues

**Problem**: `UNREACHABLE! => {"changed": false, "msg": "Failed to connect"}`

**Solutions**:
```bash
# 1. Verify SSH key permissions
chmod 600 ~/.ssh/blindstrader-ansible-key

# 2. Test manual SSH connection
ssh -i ~/.ssh/blindstrader-ansible-key ansible@<ELASTIC_IP>

# 3. Verify inventory hostname
ansible-inventory -i inventory/prod.yml --list

# 4. Check security group allows SSH from your IP
# AWS Console → EC2 → Security Groups → Check port 22 rules
```

### Permission Errors

**Problem**: `Permission denied` or `sudo: a password is required`

**Solutions**:
```bash
# 1. Verify ansible user has sudo permissions on EC2
ssh -i ~/.ssh/blindstrader-ansible-key ansible@<ELASTIC_IP>
sudo -l  # Should show NOPASSWD: ALL

# 2. Check /etc/sudoers.d/ansible file exists on EC2
cat /etc/sudoers.d/ansible
```

### Docker Module Errors

**Problem**: `docker` or `docker_compose` module not found

**Solutions**:
```bash
# Install community.docker collection
ansible-galaxy collection install community.docker --force

# Install Python Docker SDK on EC2 (Ansible will do this, but manual check:)
ssh -i ~/.ssh/blindstrader-ansible-key ansible@<ELASTIC_IP>
pip3 list | grep docker
```

### Secrets Manager Access

**Problem**: Cannot retrieve secrets from AWS Secrets Manager

**Solutions**:
```bash
# 1. Verify IAM role has correct permissions
aws iam get-role-policy --role-name blindstrader-prod-ec2-role --policy-name SecretsManagerAccess

# 2. Test from EC2 instance
ssh -i ~/.ssh/blindstrader-ansible-key ansible@<ELASTIC_IP>
aws secretsmanager get-secret-value --secret-id /blindstrader/prod/db_password --region eu-west-2

# 3. Ensure secrets exist
aws secretsmanager list-secrets --region eu-west-2 | grep blindstrader
```

### Deployment Failures

**Problem**: Playbook fails partway through

**Solutions**:
```bash
# 1. Use retry file (automatically created)
ansible-playbook -i inventory/prod.yml playbooks/site.retry

# 2. Check logs on EC2
ssh -i ~/.ssh/blindstrader-ansible-key ansible@<ELASTIC_IP>
sudo journalctl -u docker -n 100
docker-compose -f /opt/blindstrader/docker-compose.yml logs --tail=100

# 3. Verify EBS volumes are mounted
df -h
ls -la /var/lib/mysql /var/lib/redis /var/lib/monitoring
```

### SSL Certificate Issues

**Problem**: Certbot fails to obtain certificates

**Solutions**:
```bash
# 1. Verify DNS is propagated
dig auth.blindstrader.com
nslookup catalog.blindstrader.com

# 2. Check nginx is stopped (first time only)
ssh -i ~/.ssh/blindstrader-ansible-key ansible@<ELASTIC_IP>
docker ps | grep nginx

# 3. Verify port 80 is accessible
curl -I http://auth.blindstrader.com/.well-known/acme-challenge/test

# 4. Check certbot logs
docker logs certbot
```

### Health Check Failures

**Problem**: Health checks fail after deployment

**Solutions**:
```bash
# 1. Check container status
ssh -i ~/.ssh/blindstrader-ansible-key ansible@<ELASTIC_IP>
docker ps -a

# 2. Check container logs
docker logs user-management --tail=50
docker logs catalog --tail=50
docker logs mysql --tail=50

# 3. Test endpoints manually
curl http://localhost/health
curl http://localhost:3306  # MySQL
curl http://localhost:6379  # Redis

# 4. Check migrations ran successfully
docker exec user-management php artisan migrate:status
docker exec catalog php artisan migrate:status
```

## Best Practices

### Security

- ✅ Always use SSH keys, never passwords
- ✅ Rotate SSH keys regularly
- ✅ Use Ansible Vault for sensitive data (if needed)
- ✅ Limit SSH access to specific IPs in security groups
- ✅ Keep Ansible and collections updated

### Deployment

- ✅ Test in staging before production
- ✅ Tag production releases semantically (`prod-v1.2.3`)
- ✅ Always run with `-check` first for production changes
- ✅ Keep rollback versions readily available
- ✅ Monitor application after deployment

### Maintenance

- ✅ Regularly update roles and playbooks
- ✅ Keep docker-compose templates in sync with local dev
- ✅ Document custom changes in playbooks
- ✅ Use tags to run partial updates efficiently
- ✅ Review Ansible logs periodically

## Next Steps

1. Set up automated deployments with [GitHub Actions](GITHUB_ACTIONS.md)
2. Review [Complete Workflow Guide](COMPLETE_WORKFLOW.md) for end-to-end process
3. Configure monitoring alerts in Grafana
4. Set up Slack/Discord notifications for deployments
5. Implement blue-green deployment strategy (advanced)

## Support

For issues or questions:
- Check the [Troubleshooting](#troubleshooting) section
- Review Ansible logs: `cat ansible.log`
- Check EC2 instance logs: `/var/log/cloud-init-output.log`
- Consult [Ansible Documentation](https://docs.ansible.com/)
