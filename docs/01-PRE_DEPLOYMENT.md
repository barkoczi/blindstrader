# Pre-Deployment Checklist

This document outlines all the steps required before deploying the BlindStrader infrastructure to AWS.

## 1. Prerequisites

### Install Required Tools

- **Terraform** >= 1.0: [Download](https://www.terraform.io/downloads)
- **AWS CLI** v2: [Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- **GPG**: For backup encryption
  - macOS: `brew install gnupg`
  - Linux: Usually pre-installed
- **SSH**: For EC2 access

### AWS Account Setup

#### Create AWS Account

1. Create an AWS account if you don't have one at [aws.amazon.com](https://aws.amazon.com)
2. Enable MFA (Multi-Factor Authentication) on your root account immediately
3. **Never use root account for daily operations** - create IAM users instead

#### Create IAM User for Terraform

1. **Log into AWS Console** with your root account or admin user
2. Navigate to **IAM** → **Users** → **Create user**
3. Set username: `terraform-deploy` (or your preference)
4. Enable **Programmatic access** (Access key - Programmatic access)
5. Click **Next: Permissions**

#### Attach Required IAM Policies

**Option 1: Quick Setup (Use Existing Policies)**

Attach these AWS managed policies:
- `AmazonEC2FullAccess` - For EC2, EBS, networking
- `AmazonS3FullAccess` - For backup buckets
- `AmazonRoute53FullAccess` - For DNS management
- `IAMFullAccess` - For creating roles and policies
- `SecretsManagerReadWrite` - For accessing secrets
- `AWSLambda_FullAccess` - For auto-shutdown function
- `CloudWatchEventsFullAccess` - For scheduling

**Option 2: Least Privilege (Recommended for Production)**

Create a custom policy with only required permissions:

1. Go to **IAM** → **Policies** → **Create policy**
2. Click **JSON** tab and paste:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:*",
        "s3:*",
        "route53:*",
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret",
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:GetRole",
        "iam:GetRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:ListRolePolicies",
        "iam:ListAttachedRolePolicies",
        "iam:ListInstanceProfilesForRole",
        "iam:CreateInstanceProfile",
        "iam:DeleteInstanceProfile",
        "iam:GetInstanceProfile",
        "iam:AddRoleToInstanceProfile",
        "iam:RemoveRoleFromInstanceProfile",
        "iam:PassRole",
        "lambda:*",
        "events:*",
        "backup:*",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

3. Name the policy: `BlindStraderTerraformPolicy`
4. Attach this policy to your `terraform-deploy` user

#### Download Access Keys

1. After creating the user, **download the access keys**
2. Save `Access Key ID` and `Secret Access Key` securely
3. **⚠️ This is your only chance to download the secret key!**

#### Configure AWS CLI

```bash
aws configure --profile blindstrader
```

Enter the values:
- **AWS Access Key ID**: (from downloaded CSV)
- **AWS Secret Access Key**: (from downloaded CSV)
- **Default region name**: `eu-west-2`
- **Default output format**: `json`

#### Set Default Profile (Optional)

To use this profile by default:

```bash
export AWS_PROFILE=blindstrader
```

Or add to your `~/.zshrc` or `~/.bashrc`:

```bash
echo 'export AWS_PROFILE=blindstrader' >> ~/.zshrc
source ~/.zshrc
```

#### Verify Access

```bash
aws sts get-caller-identity
```

You should see output like:
```json
{
    "UserId": "AIDAXXXXXXXXXXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/terraform-deploy"
}
```

#### Enable MFA for IAM User (Strongly Recommended)

1. Go to **IAM** → **Users** → Select your user
2. Click **Security credentials** tab
3. Under **Multi-factor authentication (MFA)**, click **Assign MFA device**
4. Choose **Virtual MFA device** (use Google Authenticator, Authy, etc.)
5. Scan QR code and enter two consecutive MFA codes
6. Save the configuration

## 2. Generate GPG Keys for Backup Encryption

The same GPG key pair is shared across both prod and stage environments for simplicity.

### Generate Key Pair

```bash
gpg --full-generate-key
```

Follow the prompts:
- Key type: `(1) RSA and RSA`
- Key size: `4096`
- Expiration: `0` (does not expire) or set your preference
- Real name: `BlindStrader Admin`
- Email: `admin@blindstrader.com`
- Comment: `Backup encryption key`
- Passphrase: **Use a strong passphrase and store it securely!**

### Export Public Key

```bash
gpg --armor --export admin@blindstrader.com > blindstrader-backup-public.asc
```

### Backup Private Key Securely

```bash
gpg --armor --export-secret-keys admin@blindstrader.com > blindstrader-backup-private.asc
```

**⚠️ CRITICAL**: Store the private key file (`blindstrader-backup-private.asc`) in a secure location:
- Password manager (1Password, LastPass, etc.)
- Encrypted USB drive
- Secure offline storage
- **Never commit to version control!**

### Get Public Key for Secrets Manager

```bash
gpg --armor --export admin@blindstrader.com
```

Copy the entire output (including `-----BEGIN PGP PUBLIC KEY BLOCK-----` and `-----END PGP PUBLIC KEY BLOCK-----`)

## 3. Generate SSH Key Pairs

### Production Key (For Direct SSH Access)

```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/blindstrader-prod-key -C "prod-ec2-access"
```

### Staging Key (For Direct SSH Access)

```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/blindstrader-stage-key -C "stage-ec2-access"
```

### Ansible Automation Key (Shared for Both Environments)

This key is used by Ansible to automate deployments and configuration management:

```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/blindstrader-ansible-key -C "ansible-automation"
```

**Note**: The same Ansible key is used for both prod and stage environments for simplicity.

### Get Public Keys

```bash
# Your personal SSH keys
cat ~/.ssh/blindstrader-prod-key.pub
cat ~/.ssh/blindstrader-stage-key.pub

# Ansible automation key
cat ~/.ssh/blindstrader-ansible-key.pub
```

Copy these values for your `terraform.tfvars` files.

### Add Ansible Private Key to SSH Agent

For Ansible to use the key without password prompts:

```bash
# Add to SSH agent
ssh-add ~/.ssh/blindstrader-ansible-key

# Verify it's added
ssh-add -l
```

### Configure SSH Config (Optional but Recommended)

Add to `~/.ssh/config`:

```
# Production
Host blindstrader-prod
  HostName 13.40.X.X  # Update after deployment
  User ubuntu
  IdentityFile ~/.ssh/blindstrader-prod-key
  IdentitiesOnly yes

# Staging
Host blindstrader-stage
  HostName 13.40.X.X  # Update after deployment
  User ubuntu
  IdentityFile ~/.ssh/blindstrader-stage-key
  IdentitiesOnly yes

# Ansible access
Host blindstrader-*
  User ansible
  IdentityFile ~/.ssh/blindstrader-ansible-key
  StrictHostKeyChecking accept-new
```

## 4. Create AWS Secrets Manager Entries

### Shared Secrets (used by both environments)

```bash
# GPG public key
aws secretsmanager create-secret \
    --name /blindstrader/shared/gpg_public_key \
    --description "GPG public key for backup encryption" \
    --secret-string "$(cat blindstrader-backup-public.asc)" \
    --region eu-west-2
```

### Production Secrets

```bash
# Database password
aws secretsmanager create-secret \
    --name /blindstrader/prod/db_password \
    --description "MySQL root password for production" \
    --secret-string "YOUR_STRONG_DB_PASSWORD_HERE" \
    --region eu-west-2

# Redis password (optional, leave empty for no auth)
aws secretsmanager create-secret \
    --name /blindstrader/prod/redis_password \
    --description "Redis password for production" \
    --secret-string "" \
    --region eu-west-2

# Laravel APP_KEY (generate with: php artisan key:generate --show)
aws secretsmanager create-secret \
    --name /blindstrader/prod/app_key \
    --description "Laravel APP_KEY for production" \
    --secret-string "base64:YOUR_GENERATED_KEY_HERE" \
    --region eu-west-2

# Grafana admin password
aws secretsmanager create-secret \
    --name /blindstrader/prod/grafana_admin_password \
    --description "Grafana admin password for production" \
    --secret-string "YOUR_STRONG_GRAFANA_PASSWORD" \
    --region eu-west-2

# Basic auth password for monitoring endpoints
aws secretsmanager create-secret \
    --name /blindstrader/prod/basic_auth_password \
    --description "Basic auth password for monitoring access" \
    --secret-string "YOUR_MONITORING_PASSWORD" \
    --region eu-west-2
```

### Staging Secrets

Repeat the above commands, replacing `/prod/` with `/stage/` and using different passwords.

## 5. Generate Laravel APP_KEY

If you have a Laravel installation locally:

```bash
cd services/catalog  # or user-management
php artisan key:generate --show
```

This will output something like: `base64:abcd1234...`

Use this value for the `/blindstrader/{env}/app_key` secret.

## 6. Configure GitHub Credentials (For CI/CD)

### Create GitHub Personal Access Token

1. Go to GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Click **Generate new token (classic)**
3. Set note: `BlindStrader CI/CD`
4. Select scopes:
   - `repo` (Full control of private repositories)
   - `write:packages` (Upload packages to GitHub Package Registry)
   - `read:packages` (Download packages from GitHub Package Registry)
5. Click **Generate token**
6. **Copy the token immediately** (you won't see it again)

### Store in Secrets Manager

```bash
# GitHub token for Docker registry access
aws secretsmanager create-secret \
    --name /blindstrader/shared/github_token \
    --description "GitHub PAT for GHCR access" \
    --secret-string "ghp_your_token_here" \
    --region eu-west-2
```

### GitHub Actions Secrets (Configure AFTER First Deployment)

⚠️ **Important**: You'll configure GitHub Actions secrets **after** running `terraform apply` because you need the Elastic IPs first.

The Elastic IPs are only created when you deploy the infrastructure. After your first deployment:

1. Get the IPs from Terraform output:
   ```bash
   cd terraform/environments/stage
   terraform output elastic_ip
   
   cd terraform/environments/prod
   terraform output elastic_ip
   ```

2. Then configure GitHub Actions secrets following the detailed instructions in [GITHUB_ACTIONS.md](GITHUB_ACTIONS.md#setup-github-secrets)

Secrets you'll need to add:
- `AWS_ACCESS_KEY_ID` - From your terraform-deploy IAM user (available now)
- `AWS_SECRET_ACCESS_KEY` - From your terraform-deploy IAM user (available now)
- `STAGING_HOST` - Elastic IP from staging deployment (**after terraform apply**)
- `PRODUCTION_HOST` - Elastic IP from production deployment (**after terraform apply**)
- `ANSIBLE_SSH_KEY` - Private key content from `~/.ssh/blindstrader-ansible-key` (available now)
- `DOCKER_USERNAME` - Your GitHub username (available now)
- `DOCKER_PASSWORD` - Your GitHub personal access token (available now)

## 7. Configure Terraform Variables

### Production Environment

```bash
cd terraform/environments/prod
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and add **both SSH keys** (both are required):

```hcl
# SSH key for your personal EC2 access (ubuntu user)
# Get it with: cat ~/.ssh/blindstrader-prod-key.pub
ssh_public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQ... prod-ec2-access"

# SSH key for Ansible automation (ansible user) - REQUIRED
# Get it with: cat ~/.ssh/blindstrader-ansible-key.pub
ansible_ssh_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQ... ansible-automation"

# GitHub credentials for CI/CD (REQUIRED)
github_username = "your-github-username"
github_token    = ""  # Leave empty, retrieved from Secrets Manager

# Optional: CNAME records for third-party services
# Use this if you're hosting parts of your app on external platforms (e.g., Lovable.app)
cname_records = {
  "app"    = "your-app.lovable.app"
  "portal" = "your-portal.lovable.app"
}

# Optional overrides
# instance_type = "t3a.large"
# ebs_mysql_size = 30
# sentry_dsn = "https://your-sentry-dsn@sentry.io/project-id"
```

**Important**: Without `ansible_ssh_key`, Terraform will fail with: `The argument 'ansible_ssh_key' is required, but no definition was found.`

### Staging Environment

```bash
cd terraform/environments/stage
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and add **both SSH keys** (both are required):

```hcl
# SSH key for your personal EC2 access (ubuntu user)
# Get it with: cat ~/.ssh/blindstrader-stage-key.pub
ssh_public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQ... stage-ec2-access"

# SSH key for Ansible automation (ansible user) - REQUIRED
# Get it with: cat ~/.ssh/blindstrader-ansible-key.pub
ansible_ssh_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQ... ansible-automation"

# GitHub credentials for CI/CD (REQUIRED)
github_username = "your-github-username"
github_token    = ""  # Leave empty, retrieved from Secrets Manager

# Optional: CNAME records for staging instances of third-party services
# cname_records = {
#   "app-staging"    = "your-staging-app.lovable.app"
#   "portal-staging" = "your-staging-portal.lovable.app"
# }

# Optional: Customize auto-shutdown schedule
shutdown_cron_start = "0 18 * * MON-FRI"  # 6 PM UTC weekdays
shutdown_cron_stop = "0 8 * * MON-FRI"    # 8 AM UTC weekdays

# Optional: Run staging 24/7 (not recommended for cost)
# enable_auto_shutdown = false
```

**Important**: Without `ansible_ssh_key`, Terraform will fail with: `The argument 'ansible_ssh_key' is required, but no definition was found.`

### Quick Reference: What Each SSH Key Does

| Variable | Purpose | User on EC2 | Used For |
|----------|---------|-------------|----------|
| `ssh_public_key` | Your personal access | `ubuntu` | Manual debugging, troubleshooting |
| `ansible_ssh_key` | Automation access | `ansible` | Ansible deployments, CI/CD pipelines |

## 8. Initialize Terraform

### Production

```bash
cd terraform/environments/prod
terraform init
```

### Staging

```bash
cd terraform/environments/stage
terraform init
```

## 9. Review Terraform Plan

Before applying, review what will be created:

### Production

```bash
cd terraform/environments/prod
terraform plan
```

### Staging

```bash
cd terraform/environments/stage
terraform plan
```

Review the output carefully. You should see:
- VPC and networking resources
- EC2 instance with EBS volumes
- Security groups allowing ports 22, 80, 443
- IAM roles and policies
- Route53 hosted zone
- S3 bucket (prod only)
- AWS Backup resources (prod only)
- Lambda function and EventBridge rules (stage only)

## 10. Estimated Costs

Before proceeding, review the monthly cost estimates:

### Production (~$40-45/month)
- EC2 t3a.medium: $25/month
- EBS volumes (45GB): $4/month
- S3 backups: $1-2/month
- Route53 hosted zone: $0.50/month
- AWS Backup: $2-3/month
- Data transfer: $1-5/month
- Elastic IP: $0 (while attached)

### Staging (~$10-21/month)
- EC2 t3a.small: $17/month (or $8-10 with auto-shutdown)
- EBS volumes (45GB): $4/month
- Route53: Shared with prod
- No backups
- Lambda: Free tier eligible

**Total: ~$50-66/month for both environments**

## 11. DNS Preparation

You'll need access to your domain registrar (where you registered `blindstrader.com`) to configure name servers after deployment.

### What You'll Configure

After running `terraform apply`, you'll get 4 name servers like:
```
ns-123.awsdns-12.com
ns-456.awsdns-45.net
ns-789.awsdns-78.org
ns-012.awsdns-01.co.uk
```

You'll need to:
1. Log into your domain registrar
2. Navigate to DNS settings for `blindstrader.com`
3. Replace existing name servers with the AWS Route53 name servers
4. Wait for DNS propagation (can take up to 48 hours, usually faster)

## 12. Pre-Flight Checklist

Before running `terraform apply`, ensure:

- [ ] AWS CLI is configured with correct credentials
- [ ] GPG key pair is generated and public key uploaded to Secrets Manager
- [ ] Private GPG key is backed up securely offline
- [ ] SSH key pairs are generated (personal + Ansible automation)
- [ ] Ansible private key is added to SSH agent
- [ ] GitHub personal access token is created with correct scopes
- [ ] GitHub token is stored in AWS Secrets Manager
- [ ] `terraform.tfvars` files are configured for both environments
- [ ] Both environments have `ansible_ssh_key` configured
- [ ] GitHub username is set in terraform.tfvars
- [ ] CNAME records are configured (if using third-party services)
- [ ] Terraform is initialized (`terraform init` completed)
- [ ] You've reviewed `terraform plan` output
- [ ] You understand the monthly costs (~$50-66)
- [ ] You have access to your domain registrar for NS record changes
- [ ] You have Sentry DSN (optional, for error tracking)

**Note**: GitHub Actions secrets (STAGING_HOST, PRODUCTION_HOST, etc.) will be configured **after** the first deployment when you have the Elastic IPs. See [GITHUB_ACTIONS.md](GITHUB_ACTIONS.md) for post-deployment setup.

## 13. Ready to Deploy

Once all items above are completed, proceed to the [Deployment Guide](DEPLOYMENT.md).

## Troubleshooting

### AWS CLI Not Configured

```bash
aws sts get-caller-identity
```

If this fails, run `aws configure` again.

### GPG Command Not Found

Install GPG:
- macOS: `brew install gnupg`
- Ubuntu/Debian: `sudo apt-get install gnupg`
- CentOS/RHEL: `sudo yum install gnupg`

### Terraform Init Fails

Ensure you're in the correct directory:
```bash
cd terraform/environments/prod  # or stage
terraform init
```

### Secret Already Exists

If a secret already exists in Secrets Manager, update it instead:
```bash
aws secretsmanager update-secret \
    --secret-id /blindstrader/prod/db_password \
    --secret-string "NEW_PASSWORD" \
    --region eu-west-2
```

## Security Reminders

- ✅ Never commit `terraform.tfvars` to version control (already in `.gitignore`)
- ✅ Never commit GPG private keys
- ✅ Never commit SSH private keys
- ✅ Use strong, unique passwords for all secrets
- ✅ Enable MFA on your AWS account
- ✅ Rotate credentials regularly
- ✅ Store backup encryption keys securely offline
