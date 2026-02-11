# AWS Infrastructure Provisioning - Implementation Complete

## Overview

Complete Terraform infrastructure for provisioning production and staging BlindStrader environments on AWS in the eu-west-2 (London) region.

## What's Been Implemented

### 1. Terraform Modules

Located in [terraform/modules/](../terraform/modules/):

- **vpc/**: VPC with public subnet, internet gateway, route tables
- **security/**: Security groups, IAM roles, Elastic IPs
- **ec2/**: EC2 instances with EBS volumes and user-data script
- **storage/**: S3 buckets for backups, AWS Backup configuration
- **dns/**: Route53 hosted zones and DNS records
- **lambda-scheduler/**: Auto-shutdown/start functionality for staging

### 2. Environment Configurations

- **[terraform/environments/prod/](../terraform/environments/prod/)**: Production environment
  - Instance: t3a.medium
  - Backups: Enabled (daily S3 + EBS snapshots)
  - Auto-shutdown: Disabled (runs 24/7)
  - Domain: blindstrader.com
  
- **[terraform/environments/stage/](../terraform/environments/stage/)**: Staging environment
  - Instance: t3a.small
  - Backups: Disabled
  - Auto-shutdown: Enabled (configurable schedule)
  - Domain: stage.blindstrader.com

### 3. Docker Configuration Updates

- Added **certbot** service for SSL certificate management
- Added Redis persistence with RDB snapshots
- Added nginx volumes for SSL certificates and basic auth
- Created production-ready nginx configs with HTTPS and basic auth

### 4. Backup System

- Automated backup script: [scripts/backup.sh](../scripts/backup.sh)
- MySQL dumps all databases
- Redis RDB backup
- GPG encryption
- S3 upload with lifecycle management
- Systemd timer for daily execution (2 AM UTC)

### 5. Comprehensive Documentation

- **[docs/PRE_DEPLOYMENT.md](PRE_DEPLOYMENT.md)**: Complete pre-deployment checklist
  - GPG key generation
  - SSH key setup
  - AWS Secrets Manager configuration
  - Cost estimates
  
- **[docs/DEPLOYMENT.md](DEPLOYMENT.md)**: Step-by-step deployment guide
  - Terraform apply procedures
  - DNS configuration
  - SSL certificate setup
  - Verification steps
  - Troubleshooting
  
- **[docs/DISASTER_RECOVERY.md](DISASTER_RECOVERY.md)**: Recovery procedures
  - Backup download and decryption
  - MySQL restoration
  - Redis restoration
  - Disaster scenarios
  - Testing procedures
  
- **[docs/GIT_WORKFLOW.md](GIT_WORKFLOW.md)**: Infrastructure versioning
  - Trunk-based development
  - Tagging strategy
  - Commit conventions
  - Rollback procedures

## Key Features

✅ **Cost-Optimized**: ~$50-66/month for both environments
✅ **Automated Backups**: Daily encrypted backups to S3 (production)
✅ **Auto-Shutdown**: Configurable scheduling for staging (50-70% savings)
✅ **SSL/TLS**: Automated Let's Encrypt certificates via Certbot
✅ **Secure**: Basic auth for monitoring, IAM roles, security groups
✅ **Monitored**: Full Prometheus/Grafana/Loki stack
✅ **Resilient**: EBS snapshots, S3 versioning, disaster recovery procedures
✅ **Documented**: Complete pre-deployment, deployment, and recovery guides

## Infrastructure Architecture

```
Internet
    ↓
Route53 DNS (blindstrader.com)
    ↓
Elastic IP → EC2 Instance (eu-west-2a)
    ↓
nginx (reverse proxy + SSL termination)
    ↓
┌─────────────────────────────────────┐
│  Docker Containers                  │
│  - catalog (Laravel)                │
│  - user-management (Laravel)        │
│  - mysql (persistent EBS)           │
│  - redis (persistent EBS)           │
│  - prometheus/grafana/loki          │
│  - certbot (SSL automation)         │
└─────────────────────────────────────┘
    ↓
S3 (encrypted backups) + EBS Snapshots
```

## Cost Breakdown

### Production (~$40-45/month)
- EC2 t3a.medium: $25/mo
- EBS volumes (45GB): $4/mo
- S3 backups: $1-2/mo
- AWS Backup: $2-3/mo
- Route53: $0.50/mo
- Data transfer: $1-5/mo

### Staging (~$10-21/month)
- EC2 t3a.small: $17/mo (or $8-10 with auto-shutdown)
- EBS volumes (45GB): $4/mo
- No backups or snapshots

**Total: ~$50-66/month**

## Next Steps

### 1. Pre-Deployment (30-60 minutes)

Follow [docs/PRE_DEPLOYMENT.md](PRE_DEPLOYMENT.md):
- Generate GPG keys for backup encryption
- Create SSH key pairs
- Configure AWS Secrets Manager entries
- Set up Terraform variables

### 2. Deploy Staging First (15-30 minutes)

```bash
cd terraform/environments/stage
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your SSH public key
terraform init
terraform plan
terraform apply
```

### 3. Configure DNS (5-60 minutes)

Add Route53 nameservers to your domain registrar, wait for DNS propagation.

### 4. Deploy Application (15-30 minutes)

SSH to instance, deploy docker-compose and configs, obtain SSL certificates.

### 5. Deploy Production (30-60 minutes)

Repeat process for production environment after staging is verified.

### 6. Set Up Monitoring (5 minutes)

Access Grafana at https://insights.blindstrader.com (with basic auth).

## File Structure

```
blindstrader/
├── terraform/
│   ├── .gitignore                    ✅ Created
│   ├── modules/
│   │   ├── vpc/                      ✅ Complete
│   │   ├── security/                 ✅ Complete
│   │   ├── ec2/                      ✅ Complete (with user-data script)
│   │   ├── storage/                  ✅ Complete
│   │   ├── dns/                      ✅ Complete
│   │   └── lambda-scheduler/         ✅ Complete
│   └── environments/
│       ├── prod/                     ✅ Complete
│       │   ├── main.tf
│       │   ├── variables.tf
│       │   ├── outputs.tf
│       │   └── terraform.tfvars.example
│       └── stage/                    ✅ Complete
│           ├── main.tf
│           ├── variables.tf
│           ├── outputs.tf
│           └── terraform.tfvars.example
├── docker-compose.yml                ✅ Updated (certbot, Redis persistence)
├── nginx/
│   ├── nginx.conf                    ✅ Existing
│   └── conf.d/
│       ├── app.blindstrader.conf     ✅ Created (SSL + HTTPS redirect)
│       ├── insights.blindstrader.conf ✅ Created (with basic auth)
│       └── prometheus.blindstrader.conf ✅ Created (with basic auth)
├── scripts/
│   └── backup.sh                     ✅ Created (executable)
└── docs/
    ├── PRE_DEPLOYMENT.md             ✅ Created
    ├── DEPLOYMENT.md                 ✅ Created
    ├── DISASTER_RECOVERY.md          ✅ Created
    ├── GIT_WORKFLOW.md               ✅ Created
    └── README-INFRASTRUCTURE.md      ✅ This file
```

## Configuration Variables

### Configurable Parameters

All environments support customization via `terraform.tfvars`:

- `instance_type`: EC2 instance size (t3a.small, t3a.medium, t3a.large)
- `ebs_mysql_size`: MySQL volume size in GB (default: 20)
- `ebs_redis_size`: Redis volume size in GB (default: 10)
- `ebs_monitoring_size`: Monitoring volume size in GB (default: 15)
- `enable_backups`: Enable/disable automated backups (prod: true, stage: false)
- `backup_retention_days`: Days before moving to Glacier (default: 30)
- `enable_auto_shutdown`: Enable/disable auto-shutdown (prod: false, stage: true)
- `shutdown_cron_start`: When to stop instance (default: "0 18 * * MON-FRI")
- `shutdown_cron_stop`: When to start instance (default: "0 8 * * MON-FRI")
- `ssh_public_key`: Your SSH public key for EC2 access
- `sentry_dsn`: Optional Sentry DSN for error tracking

## Security Considerations

### Secrets Management

All sensitive values stored in AWS Secrets Manager:
- `/blindstrader/shared/gpg_public_key`: Shared GPG public key for backups
- `/blindstrader/{env}/db_password`: MySQL root password
- `/blindstrader/{env}/redis_password`: Redis password (optional)
- `/blindstrader/{env}/app_key`: Laravel APP_KEY
- `/blindstrader/{env}/grafana_admin_password`: Grafana admin password
- `/blindstrader/{env}/basic_auth_password`: Monitoring basic auth password

### Never Committed to Git

The following files are `.gitignored`:
- `terraform.tfvars`: Contains SSH keys and potentially sensitive values
- `*.tfstate`: Terraform state (contains resource details)
- `*.pem`, `*.key`: Private keys
- Secret files and backups

### Access Control

- SSH: Key-based authentication only, no passwords
- Monitoring: Basic authentication required (HTTPS only)
- Database/Redis: Not exposed externally
- S3 Backups: IAM role-based access only

## Monitoring and Observability

All environments include:
- **Prometheus**: Metrics collection from all services
- **Grafana**: Visualization and dashboards
- **Loki**: Log aggregation
- **Promtail**: Log shipping
- **cAdvisor**: Container metrics
- **Node Exporter**: System metrics
- **MySQL Exporter**: Database metrics
- **Redis Exporter**: Cache metrics

Access: https://insights.{domain} (requires basic auth)

## Maintenance

### Regular Tasks

- **Daily**: Automated backups (production only)
- **Weekly**: Review Grafana dashboards for anomalies
- **Monthly**: Test disaster recovery procedure
- **Quarterly**: Review and rotate secrets
- **Annually**: Update instance types and storage if needed

### Commands Reference

```bash
# Apply infrastructure changes
terraform plan
terraform apply

# Destroy environment (careful!)
terraform destroy

# SSH to instance
ssh -i ~/.ssh/blindstrader-{env}-key ec2-user@<ELASTIC_IP>

# View Terraform state
terraform show

# Manual backup
sudo /opt/blindstrader/backup.sh

# Update Docker images
docker-compose pull && docker-compose up -d

# View logs
docker-compose logs -f
```

## Support and Troubleshooting

See detailed troubleshooting in:
- [docs/DEPLOYMENT.md](DEPLOYMENT.md#troubleshooting)
- [docs/DISASTER_RECOVERY.md](DISASTER_RECOVERY.md#troubleshooting)

Common issues:
- DNS not resolving: Check Route53 nameservers at registrar
- SSL certificate errors: Run certbot manually, check domain DNS
- Backup failures: Verify IAM permissions and S3 bucket access
- Instance not starting: Check CloudWatch logs and security groups

## Future Enhancements

Potential improvements for production scaling:

- [ ] Migrate to AWS RDS for managed database
- [ ] Add ElastiCache for managed Redis
- [ ] Implement Application Load Balancer for multi-instance scaling
- [ ] Add CloudFront CDN for static assets
- [ ] Set up VPN or bastion host for secure SSH access
- [ ] Implement blue/green deployment strategy
- [ ] Add CloudWatch alarms for resource usage
- [ ] Set up cross-region disaster recovery
- [ ] Implement automated recovery testing
- [ ] Add CI/CD pipeline with GitHub Actions

## License and Contributions

This infrastructure code is part of the BlindStrader project.

For questions or improvements, refer to the main project documentation.

---

**Last Updated**: 2026-02-08
**Version**: 1.0.0
**Status**: ✅ Implementation Complete - Ready for Deployment
