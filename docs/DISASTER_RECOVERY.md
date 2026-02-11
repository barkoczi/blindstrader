# Disaster Recovery Guide

This guide explains how to restore the BlindStrader application from encrypted backups stored in AWS S3.

## Backup Overview

Production backups are:
- **Created**: Daily at 2 AM UTC via automated systemd timer
- **Stored**: AWS S3 bucket `blindstrader-backups-prod` in `eu-west-2`
- **Encrypted**: GPG encrypted with shared public key
- **Retention**: 30 days standard storage, then moved to Glacier
- **Contents**: MySQL databases (all schemas) + Redis dump

Staging backups are **disabled** to reduce costs.

## Prerequisites for Recovery

### Required Items

1. **GPG Private Key**: The private key generated during pre-deployment (`blindstrader-backup-private.asc`)
2. **GPG Passphrase**: The passphrase you set when generating the key
3. **AWS Access**: CLI access to the S3 bucket
4. **Working EC2 Instance**: Either existing or newly provisioned

### If Starting Fresh

If the entire infrastructure was destroyed:

```bash
# Re-provision infrastructure using Terraform
cd terraform/environments/prod
terraform apply

# Wait for instance to be ready
ssh -i ~/.ssh/blindstrader-prod-key ec2-user@<NEW_ELASTIC_IP>
```

## Recovery Procedure

### Step 1: List Available Backups

```bash
# From your local machine or EC2
aws s3 ls s3://blindstrader-backups-prod/ --recursive --region eu-west-2

# Output example:
# 2026-02-08/backup-2026-02-08-02-00.tar.gz.gpg
# 2026-02-07/backup-2026-02-07-02-00.tar.gz.gpg
```

Choose the backup you want to restore (usually the most recent).

### Step 2: Download Backup from S3

```bash
# Create restore directory
mkdir -p ~/restore
cd ~/restore

# Download the backup
aws s3 cp \
    s3://blindstrader-backups-prod/2026-02-08/backup-2026-02-08-02-00.tar.gz.gpg \
    backup.tar.gz.gpg \
    --region eu-west-2
```

### Step 3: Import GPG Private Key

If restoring on a new machine, import your private key:

```bash
# Import from file
gpg --import blindstrader-backup-private.asc

# Or if you have it in a password manager, paste it:
cat > private-key.asc << 'EOF'
-----BEGIN PGP PRIVATE KEY BLOCK-----
[paste your private key here]
-----END PGP PRIVATE KEY BLOCK-----
EOF

gpg --import private-key.asc
rm private-key.asc  # Clean up immediately
```

### Step 4: Decrypt Backup

```bash
# Decrypt (will prompt for passphrase)
gpg --decrypt --output backup.tar.gz backup.tar.gz.gpg

# Or if you want to avoid interactive prompt
echo "YOUR_PASSPHRASE" | gpg --batch --yes --passphrase-fd 0 \
    --decrypt --output backup.tar.gz backup.tar.gz.gpg
```

### Step 5: Extract Backup

```bash
# Extract tarball
tar xzf backup.tar.gz

# Verify contents
ls -lh
# Should see:
# - mysql-backup.sql
# - redis-dump.rdb
# - metadata.txt

# View backup metadata
cat metadata.txt
```

### Step 6: Stop Application Services

Before restoring data, stop the application containers to prevent data corruption:

```bash
# SSH to EC2 instance if not already there
ssh -i ~/.ssh/blindstrader-prod-key ec2-user@<ELASTIC_IP>

cd /opt/blindstrader

# Stop application services (but keep database running)
docker-compose stop catalog user-management
```

### Step 7: Restore MySQL Database

```bash
# Copy SQL file to a location accessible by Docker container
sudo cp ~/restore/mysql-backup.sql /tmp/restore.sql

# Restore to MySQL
docker exec -i blindstrader-mysql mysql -u root -p"$DB_PASSWORD" < /tmp/restore.sql

# Verify restoration
docker exec blindstrader-mysql mysql -u root -p"$DB_PASSWORD" -e "SHOW DATABASES;"
docker exec blindstrader-mysql mysql -u root -p"$DB_PASSWORD" blindstrader_catalog -e "SHOW TABLES;"
docker exec blindstrader-mysql mysql -u root -p"$DB_PASSWORD" blindstrader_user_management -e "SHOW TABLES;"

# Clean up
sudo rm /tmp/restore.sql
```

### Step 8: Restore Redis Data

```bash
# Stop Redis to replace dump file
docker-compose stop redis

# Backup current dump (just in case)
sudo cp /var/lib/redis/dump.rdb /var/lib/redis/dump.rdb.backup

# Copy restored dump
sudo cp ~/restore/redis-dump.rdb /var/lib/redis/dump.rdb

# Fix permissions
sudo chown 999:999 /var/lib/redis/dump.rdb

# Start Redis
docker-compose start redis

# Verify Redis has data
docker exec blindstrader-redis redis-cli DBSIZE
```

### Step 9: Restart Application

```bash
# Start all services
docker-compose up -d

# Verify all containers are running
docker-compose ps

# Check logs for errors
docker-compose logs -f catalog user-management
```

### Step 10: Verify Application Functionality

```bash
# Test from local machine
curl -I https://auth.blindstrader.com
curl -I https://catalog.blindstrader.com

# Check Grafana
curl -u admin:PASSWORD https://insights.blindstrader.com

# SSH to instance and verify data
docker exec blindstrader-mysql mysql -u root -p"$DB_PASSWORD" \
    blindstrader_catalog -e "SELECT COUNT(*) FROM users;"
```

### Step 11: Clean Up

```bash
# Remove restore directory
rm -rf ~/restore

# Remove any sensitive files
shred -u ~/restore/mysql-backup.sql  # if still exists
```

## Partial Recovery Scenarios

### Restore Only MySQL

If you only need to restore the database:

```bash
# Follow steps 1-5 to download and decrypt
# Then jump to step 7 for MySQL restoration
# Skip Redis restoration (step 8)
```

### Restore Only Redis

If you only need to restore Redis data:

```bash
# Follow steps 1-5 to download and decrypt
# Skip MySQL restoration (step 7)
# Then jump to step 8 for Redis restoration
```

### Restore Specific Database Schema

To restore only one schema (e.g., `blindstrader_catalog`):

```bash
# Extract specific database from backup
docker exec -i blindstrader-mysql mysql -u root -p"$DB_PASSWORD" \
    blindstrader_catalog < mysql-backup.sql

# Or use mysqldump with --one-database flag during backup
```

## Disaster Scenarios

### Scenario 1: EC2 Instance Failure

**Situation**: EC2 instance becomes unresponsive or corrupt.

**Recovery**:
1. Provision new EC2 instance via Terraform (`terraform apply`)
2. Follow full recovery procedure above
3. Update DNS if IP changed (though Elastic IP should remain)

**Time**: ~15-30 minutes

### Scenario 2: EBS Volume Failure

**Situation**: Database or Redis volume becomes corrupt.

**Recovery**:
1. Stop affected services
2. Detach corrupt EBS volume
3. Create new EBS volume (via Terraform or console)
4. Attach to instance
5. Format and mount volume
6. Follow recovery procedure to restore data

**Time**: ~30-60 minutes

### Scenario 3: Accidental Data Deletion

**Situation**: Important data was accidentally deleted from database.

**Recovery**:
1. Identify backup timestamp before deletion
2. Download and decrypt that specific backup
3. Extract and compare data with current state
4. Selectively restore deleted records using SQL scripts

**Time**: Depends on complexity, 30+ minutes

### Scenario 4: Entire AWS Account Compromised

**Situation**: AWS credentials compromised, all resources deleted.

**Recovery**:
1. Create new AWS account
2. Restore Terraform state from version control
3. Re-run `terraform apply`
4. Download latest backup from S3 (if bucket still exists)
5. If S3 deleted, restore from offline backup (if you maintained one)
6. Follow full recovery procedure

**Time**: 1-4 hours

### Scenario 5: GPG Private Key Lost

**Situation**: Private key file lost and passphrase forgotten.

**Recovery**:
⚠️ **IRRECOVERABLE** - Encrypted backups cannot be decrypted without the private key.

**Prevention**:
- Store GPG private key in multiple secure locations
- Password manager (1Password, LastPass)
- Encrypted USB drive in safe
- Printed paper backup in secure location
- Share with trusted team member

## Testing Your Recovery Plan

### Quarterly Recovery Drill

Perform a test recovery every 3 months:

1. Spin up a separate test EC2 instance
2. Download a production backup
3. Restore to test instance
4. Verify data integrity
5. Document time taken and any issues
6. Destroy test instance

### Automated Recovery Testing

Consider automating recovery tests:

```bash
#!/bin/bash
# recovery-test.sh

# Download latest backup
aws s3 cp s3://blindstrader-backups-prod/$(date +%Y-%m-%d)/ \
    ./test-backup/ --recursive --region eu-west-2

# Decrypt and extract
gpg --decrypt backup.tar.gz.gpg | tar xz

# Verify files exist
test -f mysql-backup.sql && echo "✓ MySQL backup found"
test -f redis-dump.rdb && echo "✓ Redis backup found"

# Test MySQL import (dry run)
docker run --rm -v $(pwd):/backup mysql:8.0 \
    sh -c "mysql < /backup/mysql-backup.sql --verbose --dry-run"

echo "Recovery test completed"
```

## Backup Verification

### Check Backup Integrity

```bash
# List recent backups
aws s3 ls s3://blindstrader-backups-prod/ \
    --recursive --region eu-west-2 | tail -10

# Check backup size (should be > 0)
aws s3 ls s3://blindstrader-backups-prod/$(date +%Y-%m-%d)/ \
    --region eu-west-2 --human-readable

# Download and test decrypt (don't restore)
aws s3 cp s3://blindstrader-backups-prod/latest.tar.gz.gpg test.gpg --region eu-west-2
gpg --decrypt test.gpg > /dev/null && echo "✓ Decryption successful"
rm test.gpg
```

### Monitor Backup Timer

```bash
# SSH to EC2
ssh -i ~/.ssh/blindstrader-prod-key ec2-user@<ELASTIC_IP>

# Check timer status
sudo systemctl status blindstrader-backup.timer
sudo systemctl list-timers | grep blindstrader

# Check last backup execution
sudo journalctl -u blindstrader-backup.service -n 50

# Check S3 for today's backup
aws s3 ls s3://blindstrader-backups-prod/$(date +%Y-%m-%d)/ --region eu-west-2
```

## Advanced Recovery Topics

### Point-in-Time Recovery

For more granular recovery, consider enabling:
- MySQL binary logs (incremental backups)
- More frequent backup schedule (every 6 hours)

### Cross-Region Replication

For additional disaster recovery protection:

```bash
# Enable S3 cross-region replication to us-east-1
aws s3api put-bucket-replication \
    --bucket blindstrader-backups-prod \
    --replication-configuration file://replication.json \
    --region eu-west-2
```

### Backup to Multiple Destinations

Modify backup script to also copy to:
- Different AWS account
- Different cloud provider (GCS, Azure)
- On-premise NAS
- Cold storage (tape)

## Recovery RTO and RPO

**Recovery Time Objective (RTO)**: Time to restore service
- Target: < 1 hour for full restoration
- Actual: 15-30 minutes with practice

**Recovery Point Objective (RPO)**: Maximum data loss acceptable  
- Current: Up to 24 hours (daily backups at 2 AM)
- To improve: Increase backup frequency to every 6 hours

## Emergency Contacts

In case of disaster:

1. **AWS Support**: Via AWS Console or phone
2. **Team Members**: Ensure multiple people have recovery access
3. **External DBA**: Consider having a database expert on retainer

## Checklist: Are You Prepared?

- [ ] GPG private key stored in 3+ secure locations
- [ ] Passphrase documented in password manager
- [ ] Tested full recovery procedure at least once
- [ ] Documented custom recovery procedures for your specific data
- [ ] Multiple team members trained on recovery process
- [ ] Automated backup verification in place
- [ ] Recovery drill scheduled quarterly
- [ ] RTO/RPO requirements documented and met
- [ ] AWS credentials for recovery stored securely offline
- [ ] Terraform state backed up

## Post-Recovery Tasks

After successful recovery:

1. **Investigate Root Cause**: What caused the failure?
2. **Update Documentation**: Document lessons learned
3. **Improve Backup Strategy**: Based on what went wrong
4. **Notify Stakeholders**: Communicate incident timeline
5. **Review Security**: Check for unauthorized access
6. **Update Monitoring**: Add alerts to prevent recurrence

## Getting Help

If recovery fails or you need assistance:

1. Check [Troubleshooting](#troubleshooting) section in [DEPLOYMENT.md](DEPLOYMENT.md)
2. Review backup logs: `sudo journalctl -u blindstrader-backup.service`
3. AWS Support for infrastructure issues
4. Database experts for complex MySQL recovery

Remember: **Prevention is better than recovery**. Test your backups regularly!
