# Deployment Guide

This guide covers deploying and managing the BlindStrader infrastructure on AWS using Terraform.

## Prerequisites

Complete all steps in [PRE_DEPLOYMENT.md](PRE_DEPLOYMENT.md) before proceeding.

## Deployment Steps

### 1. Choose Environment

Decide which environment to deploy first. We recommend **staging** to test the process.

```bash
# For staging
cd terraform/environments/stage

# For production
cd terraform/environments/prod
```

### 2. Apply Terraform Configuration

```bash
terraform apply
```

Terraform will show you a plan of all resources to be created. Review carefully and type `yes` to proceed.

**⏱️ Deployment time**: ~5-10 minutes

### 3. Save Terraform Outputs

After successful deployment, Terraform will output important information:

```bash
terraform output
```

You'll see:
- **elastic_ip**: The public IP address of your EC2 instance
- **route53_name_servers**: Name servers for DNS configuration
- **ec2_instance_id**: Instance ID for AWS console reference
- **ssh_command**: Command to SSH into the instance
- **deployment_info**: Post-deployment instructions

**💾 Save these values** - especially the name servers and Elastic IP.

### 4. Configure DNS at Registrar

1. Log into your domain registrar (where you registered `blindstrader.com`)
2. Navigate to DNS settings
3. Replace existing name servers with the Route53 name servers from terraform output

**Example for production:**
```
ns-123.awsdns-12.com
ns-456.awsdns-45.net
ns-789.awsdns-78.org
ns-012.awsdns-01.co.uk
```

**Example for staging:**
The staging environment creates a separate hosted zone for `stage.blindstrader.com`. You'll need to add NS records as a subdomain delegation.

4. Save changes and wait for DNS propagation (5 minutes to 48 hours, typically < 1 hour)

### 5. Verify DNS Propagation

```bash
# Check if DNS is resolving
dig auth.blindstrader.com
# or for staging
dig auth.stage.blindstrader.com

# Should show the Elastic IP address
```

### 6. SSH to EC2 Instance

```bash
# Production
ssh -i ~/.ssh/blindstrader-prod-key ec2-user@<ELASTIC_IP>

# Staging
ssh -i ~/.ssh/blindstrader-stage-key ec2-user@<ELASTIC_IP>
```

### 7. Verify User Data Script Execution

Check if the user-data script completed successfully:

```bash
# Check cloud-init logs
sudo tail -100 /var/log/cloud-init-output.log

# Look for the completion message
sudo grep "Minimal setup complete" /var/log/cloud-init-output.log

# Verify completion marker file exists
ls -la /var/log/user-data-complete

# Verify Python 3 is installed (required for Ansible)
python3 --version

# Verify AWS CLI is installed
aws --version

# Check ansible user was created
id ansible

# Verify application directory exists
ls -ld /opt/blindstrader
```

The user-data script should complete in 1-2 minutes. If the completion message is not found, wait a bit longer.

**Note**: The user-data script only prepares the instance. Application deployment happens via Ansible (see next section).

### 8. Deploy Application with Ansible

**Important**: The EC2 instance is now ready but the application is not yet deployed. The Terraform deployment only created the infrastructure and prepared the instance for configuration.

**Next step**: Continue with [03-ANSIBLE_DEPLOYMENT.md](03-ANSIBLE_DEPLOYMENT.md) to:
- Update Ansible inventory with the Elastic IP
- Deploy the full application stack (Docker, services, monitoring)
- Obtain SSL certificates
- Complete the deployment

The Ansible deployment takes approximately 10-15 minutes.

### 9. Verify Application Access

**Note**: This step can only be completed after running Ansible playbooks (see step 8).

Test each subdomain:

```bash
# From your local machine
curl -I https://auth.blindstrader.com
curl -I https://catalog.blindstrader.com

# Test monitoring endpoints (will prompt for basic auth)
curl -u admin:YOUR_MONITORING_PASSWORD https://insights.blindstrader.com
curl -u admin:YOUR_MONITORING_PASSWORD https://prometheus.blindstrader.com
```

Or visit in your browser:
- https://blindstrader.com (redirects to auth)
- https://auth.blindstrader.com
- https://catalog.blindstrader.com
- https://insights.blindstrader.com (requires basic auth)
- https://prometheus.blindstrader.com (requires basic auth)

### 10. Test Backup System (Production Only)

```bash
# On the EC2 instance
sudo /opt/blindstrader/backup.sh

# Check if backup was uploaded to S3
aws s3 ls s3://blindstrader-backups-prod/ --region eu-west-2

# Verify systemd timer is active
sudo systemctl status blindstrader-backup.timer
sudo systemctl list-timers | grep blindstrader
```

### 11. Monitor Auto-Shutdown (Staging Only)

For staging environment with auto-shutdown enabled:

```bash
# Check Lambda function
aws lambda list-functions --region eu-west-2 | grep stage-ec2-scheduler

# Check EventBridge rules
aws events list-rules --region eu-west-2 | grep stage

# View scheduled times in Terraform output
terraform output auto_shutdown_schedule
```

The instance will automatically:
- **Stop** at the configured time (default: 6 PM UTC Mon-Fri)
- **Start** at the configured time (default: 8 AM UTC Mon-Fri)

To manually start/stop:

```bash
# Stop instance
aws ec2 stop-instances --instance-ids <INSTANCE_ID> --region eu-west-2

# Start instance
aws ec2 start-instances --instance-ids <INSTANCE_ID> --region eu-west-2
```

## Post-Deployment Verification Checklist

- [ ] All Docker containers are running (`docker-compose ps`)
- [ ] DNS resolves to correct IP (`dig auth.blindstrader.com`)
- [ ] SSL certificates are installed and valid
- [ ] Application is accessible via HTTPS
- [ ] Monitoring endpoints require basic authentication
- [ ] Database migrations completed successfully
- [ ] Redis is persisting data
- [ ] Backup timer is active (production only)
- [ ] Auto-shutdown is scheduled (staging only)
- [ ] Grafana dashboards are accessible
- [ ] Prometheus is scraping metrics

## Managing the Infrastructure

### View Current State

```bash
cd terraform/environments/<env>
terraform show
```

### Update Infrastructure

1. Modify variables in `terraform.tfvars` or Terraform files
2. Preview changes:
   ```bash
   terraform plan
   ```
3. Apply changes:
   ```bash
   terraform apply
   ```

### Destroy Environment

**⚠️ WARNING**: This will delete all resources including EBS volumes with data!

For staging (safe to destroy/recreate):

```bash
cd terraform/environments/stage
terraform destroy
```

For production (use with extreme caution):

```bash
cd terraform/environments/prod

# Take final backup first!
ssh -i ~/.ssh/blindstrader-prod-key ec2-user@<ELASTIC_IP> \
    sudo /opt/blindstrader/backup.sh

# Confirm backup exists in S3
aws s3 ls s3://blindstrader-backups-prod/ --region eu-west-2

# Then destroy
terraform destroy
```

### Scale Instance Size

To upgrade instance type (e.g., from t3a.medium to t3a.large):

1. Edit `terraform/environments/prod/terraform.tfvars`:
   ```hcl
   instance_type = "t3a.large"
   ```

2. Apply changes:
   ```bash
   terraform apply
   ```

The instance will be stopped, resized, and restarted. Downtime: ~2-5 minutes.

### Increase EBS Volume Size

To expand storage:

1. Edit `terraform/environments/prod/terraform.tfvars`:
   ```hcl
   ebs_mysql_size = 40  # increased from 20
   ```

2. Apply changes:
   ```bash
   terraform apply
   ```

3. SSH to instance and resize filesystem:
   ```bash
   sudo resize2fs /dev/xvdf
   df -h | grep mysql
   ```

## Maintenance Tasks

### Update Docker Images

```bash
# SSH to instance
cd /opt/blindstrader

# Pull latest images
docker-compose pull

# Restart with new images
docker-compose up -d
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f catalog
docker-compose logs -f nginx

# Nginx access logs
tail -f /opt/blindstrader/logs/nginx/access.log
```

### Database Access

```bash
# MySQL CLI
docker exec -it blindstrader-mysql mysql -u root -p

# Redis CLI
docker exec -it blindstrader-redis redis-cli
```

### Rotate Secrets

When rotating passwords:

1. Update in AWS Secrets Manager:
   ```bash
   aws secretsmanager update-secret \
       --secret-id /blindstrader/prod/db_password \
       --secret-string "NEW_PASSWORD" \
       --region eu-west-2
   ```

2. SSH to instance and update `.env`:
   ```bash
   sudo nano /opt/blindstrader/.env
   ```

3. Restart affected services:
   ```bash
   docker-compose restart catalog user-management
   ```

### Check Resource Usage

```bash
# System resources
htop

# Docker resources
docker stats

# Disk usage
df -h
du -sh /var/lib/mysql
du -sh /var/lib/redis
du -sh /var/lib/monitoring
```

## Troubleshooting

### EC2 Instance Not Accessible

```bash
# Check instance status
aws ec2 describe-instance-status \
    --instance-ids <INSTANCE_ID> \
    --region eu-west-2

# Check security group rules
aws ec2 describe-security-groups \
    --group-ids <SECURITY_GROUP_ID> \
    --region eu-west-2
```

### DNS Not Resolving

```bash
# Check Route53 records
aws route53 list-resource-record-sets \
    --hosted-zone-id <ZONE_ID>

# Verify name servers at registrar
dig NS blindstrader.com
```

### SSL Certificate Issues

```bash
# Check certificate validity
openssl x509 -in /opt/blindstrader/nginx/certs/live/blindstrader.com/fullchain.pem \
    -noout -dates

# Force renewal
docker-compose run --rm certbot renew --force-renewal

# Restart nginx
docker-compose restart nginx
```

### Backup Failures

```bash
# Check backup logs
sudo journalctl -u blindstrader-backup.service

# Run backup manually with debug
sudo bash -x /opt/blindstrader/backup.sh

# Check S3 permissions
aws s3 ls s3://blindstrader-backups-prod/ --region eu-west-2
```

### Out of Disk Space

```bash
# Clean up Docker
docker system prune -a

# Check EBS volume size
df -h

# If needed, increase EBS volume size (see above)
```

## Cost Monitoring

### View Current Costs

```bash
# Use AWS Cost Explorer in console
# or CLI:
aws ce get-cost-and-usage \
    --time-period Start=2026-01-01,End=2026-01-31 \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --group-by Type=TAG,Key=Environment
```

### Set Up Billing Alerts

1. AWS Console → Billing → Budgets
2. Create budget for each environment
3. Set alert thresholds (e.g., > $50/month for prod)

## Next Steps

- [Disaster Recovery Guide](DISASTER_RECOVERY.md) - Learn how to restore from backups
- [Git Workflow](GIT_WORKFLOW.md) - Infrastructure versioning and deployment strategy
- Monitor your infrastructure via Grafana: https://insights.blindstrader.com
