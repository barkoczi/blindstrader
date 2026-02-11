#!/bin/bash
#
# BlindStrader Backup Script
# Backs up MySQL databases and Redis data, encrypts with GPG, and uploads to S3
#
# Usage: ./backup.sh
# 
# Environment variables required:
#   - DB_PASSWORD: MySQL root password
#   - ENVIRONMENT: prod or stage
#   - AWS_REGION: AWS region (default: eu-west-2)
#   - S3_BUCKET: S3 bucket name for backups

set -euo pipefail

# Configuration
ENVIRONMENT="${ENVIRONMENT:-prod}"
AWS_REGION="${AWS_REGION:-eu-west-2}"
S3_BUCKET="${S3_BUCKET:-blindstrader-backups-${ENVIRONMENT}}"
TIMESTAMP=$(date +%Y-%m-%d-%H-%M)
DATE_PREFIX=$(date +%Y-%m-%d)
BACKUP_DIR="/tmp/backup-${TIMESTAMP}"
GPG_RECIPIENT="admin@blindstrader.com"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Cleanup function
cleanup() {
    if [ -d "$BACKUP_DIR" ]; then
        log_info "Cleaning up temporary files..."
        rm -rf "$BACKUP_DIR"
    fi
}

trap cleanup EXIT

# Check required environment variables
if [ -z "${DB_PASSWORD:-}" ]; then
    log_error "DB_PASSWORD environment variable is required"
    exit 1
fi

# Create backup directory
log_info "Creating backup directory: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Backup MySQL databases
log_info "Backing up MySQL databases..."
if docker exec blindstrader-mysql mysqldump \
    -u root \
    -p"$DB_PASSWORD" \
    --all-databases \
    --single-transaction \
    --quick \
    --lock-tables=false \
    --routines \
    --triggers \
    --events \
    > "$BACKUP_DIR/mysql-backup.sql" 2>/dev/null; then
    
    MYSQL_SIZE=$(du -h "$BACKUP_DIR/mysql-backup.sql" | cut -f1)
    log_info "MySQL backup completed successfully (Size: $MYSQL_SIZE)"
else
    log_error "MySQL backup failed"
    exit 1
fi

# Backup Redis data
log_info "Backing up Redis data..."
if docker exec blindstrader-redis redis-cli save > /dev/null 2>&1; then
    # Wait a moment for save to complete
    sleep 2
    
    if [ -f "/var/lib/redis/dump.rdb" ]; then
        cp /var/lib/redis/dump.rdb "$BACKUP_DIR/redis-dump.rdb"
        REDIS_SIZE=$(du -h "$BACKUP_DIR/redis-dump.rdb" | cut -f1)
        log_info "Redis backup completed successfully (Size: $REDIS_SIZE)"
    else
        log_warning "Redis dump.rdb file not found at /var/lib/redis/dump.rdb"
        touch "$BACKUP_DIR/redis-dump.rdb"
    fi
else
    log_error "Redis backup failed"
    exit 1
fi

# Create metadata file
log_info "Creating backup metadata..."
cat > "$BACKUP_DIR/metadata.txt" <<EOF
Backup Information
==================
Timestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')
Environment: $ENVIRONMENT
Hostname: $(hostname)
MySQL Size: $MYSQL_SIZE
Redis Size: ${REDIS_SIZE:-N/A}
EOF

# Create tarball
log_info "Creating compressed archive..."
cd "$BACKUP_DIR"
tar czf backup.tar.gz mysql-backup.sql redis-dump.rdb metadata.txt
ARCHIVE_SIZE=$(du -h backup.tar.gz | cut -f1)
log_info "Archive created successfully (Size: $ARCHIVE_SIZE)"

# Encrypt with GPG
log_info "Encrypting backup with GPG..."
if gpg --encrypt \
    --recipient "$GPG_RECIPIENT" \
    --trust-model always \
    --output backup.tar.gz.gpg \
    backup.tar.gz; then
    
    ENCRYPTED_SIZE=$(du -h backup.tar.gz.gpg | cut -f1)
    log_info "Backup encrypted successfully (Size: $ENCRYPTED_SIZE)"
else
    log_error "GPG encryption failed"
    exit 1
fi

# Upload to S3
log_info "Uploading to S3: s3://$S3_BUCKET/$DATE_PREFIX/backup-$TIMESTAMP.tar.gz.gpg"
if aws s3 cp backup.tar.gz.gpg \
    "s3://$S3_BUCKET/$DATE_PREFIX/backup-$TIMESTAMP.tar.gz.gpg" \
    --region "$AWS_REGION" \
    --storage-class STANDARD \
    --metadata "environment=$ENVIRONMENT,timestamp=$TIMESTAMP"; then
    
    log_info "Upload completed successfully"
else
    log_error "S3 upload failed"
    exit 1
fi

# Summary
log_info "Backup Summary:"
log_info "  - MySQL backup: $MYSQL_SIZE"
log_info "  - Redis backup: ${REDIS_SIZE:-N/A}"
log_info "  - Compressed: $ARCHIVE_SIZE"
log_info "  - Encrypted: $ENCRYPTED_SIZE"
log_info "  - S3 Location: s3://$S3_BUCKET/$DATE_PREFIX/backup-$TIMESTAMP.tar.gz.gpg"
log_info "Backup completed successfully!"

exit 0
