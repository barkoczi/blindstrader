# BlindStrader Ansible Configuration

This directory contains Ansible automation for configuring and deploying the BlindStrader infrastructure.

## Quick Start

```bash
# 1. Install Ansible
pip install ansible
ansible-galaxy collection install community.docker

# 2. Update inventory with your EC2 IP
vim inventory/prod.yml  # Set ansible_host

# 3. Test connection
ansible -i inventory/prod.yml all -m ping

# 4. Complete server setup (first time)
ansible-playbook -i inventory/prod.yml playbooks/site.yml

# 5. Deploy application updates
ansible-playbook -i inventory/prod.yml playbooks/deploy-app.yml
```

## Directory Structure

```
ansible/
├── ansible.cfg               # Ansible configuration
├── inventory/                # Inventory files
│   ├── prod.yml             # Production hosts
│   └── stage.yml            # Staging hosts
├── playbooks/               # Playbooks
│   ├── site.yml             # Complete setup
│   ├── deploy-app.yml       # App deployment
│   ├── rollback.yml         # Rollback to previous version
│   └── ssl.yml              # SSL certificate management
└── roles/                   # Roles
    ├── common/              # Base system configuration
    ├── docker/              # Docker installation
    ├── nginx/               # Nginx web server
    ├── monitoring/          # Prometheus, Grafana, Loki
    ├── backups/             # Automated backups
    └── app/                 # Application deployment
```

## Playbooks

| Playbook | Purpose | Usage |
|----------|---------|-------|
| `site.yml` | Complete server setup | First-time configuration |
| `deploy-app.yml` | Deploy application | Routine deployments |
| `rollback.yml` | Rollback version | Emergency rollback |
| `ssl.yml` | Manage SSL certs | First-time or renewal |

## Common Commands

### Complete Setup
```bash
ansible-playbook -i inventory/prod.yml playbooks/site.yml
```

### Deploy Latest Version
```bash
ansible-playbook -i inventory/prod.yml playbooks/deploy-app.yml
```

### Deploy Specific Version
```bash
ansible-playbook -i inventory/prod.yml playbooks/deploy-app.yml -e "version=prod-v1.2.0"
```

### Rollback
```bash
ansible-playbook -i inventory/prod.yml playbooks/rollback.yml -e "version=prod-v1.1.0"
```

### Obtain SSL Certificates
```bash
ansible-playbook -i inventory/prod.yml playbooks/ssl.yml
```

### Run Specific Role
```bash
# Update only nginx
ansible-playbook -i inventory/prod.yml playbooks/site.yml --tags nginx

# Update only monitoring
ansible-playbook -i inventory/prod.yml playbooks/site.yml --tags monitoring
```

## Configuration

### Inventory Variables

Edit `inventory/prod.yml` or `inventory/stage.yml`:

```yaml
ansible_host: 52.56.123.45        # EC2 Elastic IP
environment: prod                  # Environment name
domain: blindstrader.com          # Domain name
backup_enabled: true              # Enable backups (prod only)
```

### Required Secrets

Ansible retrieves these from AWS Secrets Manager:
- `/blindstrader/prod/db_password`
- `/blindstrader/prod/redis_password`
- `/blindstrader/prod/app_key`
- `/blindstrader/prod/grafana_admin_password`
- `/blindstrader/prod/basic_auth_password`
- `/blindstrader/shared/gpg_public_key`

## Prerequisites

1. **SSH Access**
   - Generate key: `ssh-keygen -t rsa -b 4096 -f ~/.ssh/blindstrader-ansible-key`
   - Add public key to Terraform variables
   - Run `terraform apply` to create ansible user on EC2

2. **AWS Credentials**
   - Configure: `aws configure`
   - Ensure IAM permissions for Secrets Manager

3. **Ansible Collections**
   - Run: `ansible-galaxy collection install community.docker`

## Troubleshooting

### Connection Failed
```bash
# Test SSH manually
ssh -i ~/.ssh/blindstrader-ansible-key ansible@<IP>

# Check inventory
ansible-inventory -i inventory/prod.yml --list
```

### Docker Module Not Found
```bash
ansible-galaxy collection install community.docker --force
```

### Secrets Not Found
```bash
# Verify secrets exist
aws secretsmanager list-secrets --region eu-west-2 | grep blindstrader

# Test retrieval from EC2
ssh -i ~/.ssh/blindstrader-ansible-key ansible@<IP>
aws secretsmanager get-secret-value --secret-id /blindstrader/prod/db_password --region eu-west-2
```

## Documentation

- [Complete Ansible Deployment Guide](../docs/ANSIBLE_DEPLOYMENT.md)
- [GitHub Actions CI/CD Setup](../docs/GITHUB_ACTIONS.md)
- [Complete Workflow Guide](../docs/COMPLETE_WORKFLOW.md)

## Support

For detailed documentation, see:
- `docs/ANSIBLE_DEPLOYMENT.md` - Comprehensive Ansible guide
- `docs/GITHUB_ACTIONS.md` - CI/CD pipeline setup
- `docs/COMPLETE_WORKFLOW.md` - End-to-end workflow

For issues:
- Check playbook output and logs
- Review `ansible.log` file
- SSH to EC2 and check Docker logs
- Consult troubleshooting sections in documentation
