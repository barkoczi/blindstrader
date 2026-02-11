# Git Workflow for Infrastructure

This document describes the Git workflow for managing BlindStrader infrastructure code using a trunk-based development approach.

## Overview

We use a **trunk-based development** workflow where:
- All development happens on the `main` branch
- Deployments are tagged with version numbers
- No long-lived feature branches
- Terraform workspaces are NOT used (we use separate directories instead)

## Repository Structure

```
blindstrader/
├── terraform/
│   ├── modules/              # Reusable Terraform modules
│   └── environments/
│       ├── prod/            # Production configuration
│       └── stage/           # Staging configuration
├── docker-compose.yml        # Container orchestration
├── nginx/                    # Nginx configuration
├── scripts/                  # Utility scripts
└── docs/                    # Documentation
```

## Branching Strategy

### Main Branch

- **Branch**: `main`
- **Purpose**: Single source of truth for infrastructure code
- **Protection**: Should be protected with PR reviews
- **Direct Commits**: Allowed for urgent hotfixes (with caution)

### No Feature Branches

For infrastructure changes:
1. Make changes directly on `main` (or very short-lived branch)
2. Test locally with `terraform plan`
3. Commit and push
4. Apply to staging first
5. Tag when ready for production
6. Apply to production

## Deployment Workflow

### Deploying to Staging

```bash
# 1. Make infrastructure changes
cd terraform/environments/stage
vi terraform.tfvars  # or modify .tf files in modules/

# 2. Test changes
terraform plan

# 3. Commit to git
git add .
git commit -m "feat: increase staging instance to t3a.medium"
git push origin main

# 4. Apply to staging
terraform apply

# 5. Verify changes
ssh -i ~/.ssh/blindstrader-stage-key ec2-user@<STAGING_IP>
```

### Promoting to Production

Once changes are verified in staging:

```bash
# 1. Navigate to prod environment
cd terraform/environments/prod

# 2. Apply the same changes
# (Copy from stage or modify directly)
vi terraform.tfvars

# 3. Plan and review carefully
terraform plan

# 4. Apply to production
terraform apply

# 5. Tag the release
git tag -a prod-v1.0.0 -m "Production deployment: increased instance size"
git push origin prod-v1.0.0
```

## Tagging Strategy

### Tag Format

- **Production**: `prod-v{major}.{minor}.{patch}`
- **Staging**: `stage-v{major}.{minor}.{patch}`

### When to Tag

- After successful production deployment
- Before major infrastructure changes
- When creating a rollback point

### Examples

```bash
# Infrastructure version bump
git tag -a prod-v1.0.0 -m "Initial production deployment"

# Feature addition
git tag -a prod-v1.1.0 -m "Added auto-shutdown for cost optimization"

# Bug fix
git tag -a prod-v1.0.1 -m "Fixed security group rules"

# Major change
git tag -a prod-v2.0.0 -m "Migrated to RDS from containerized MySQL"
```

## Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature (e.g., new module, resource)
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring without functionality change
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `security`: Security fixes

### Examples

```bash
# Feature
git commit -m "feat(ec2): add auto-shutdown Lambda for staging"

# Bug fix
git commit -m "fix(security): allow HTTPS from CloudFront IPs only"

# Documentation
git commit -m "docs: add disaster recovery procedures"

# Refactor
git commit -m "refactor(modules): extract DNS configuration to module"

# Security fix
git commit -m "security(iam): restrict S3 bucket access to instance role only"
```

## Working with Terraform State

### Local State Management

Since we use local state (not S3 backend):

```bash
# State files are in:
terraform/environments/prod/terraform.tfstate
terraform/environments/stage/terraform.tfstate

# These are .gitignored and should NEVER be committed!
```

### Backing Up State

Create manual backups before major changes:

```bash
# Before major change
cd terraform/environments/prod
cp terraform.tfstate terraform.tfstate.backup-$(date +%Y%m%d)

# After successful apply, remove backup
rm terraform.tfstate.backup-*
```

### State Recovery

If state is lost or corrupted:

```bash
# Import existing resources
terraform import aws_instance.main i-1234567890abcdef0

# Or recreate state from AWS
terraform refresh
```

## Rollback Procedures

### Rolling Back Infrastructure Changes

#### Option 1: Revert Git Commit

```bash
# Find the commit to revert to
git log --oneline

# Revert to previous state
git revert <commit-hash>
git push origin main

# Apply the reverted configuration
cd terraform/environments/prod
terraform apply
```

#### Option 2: Checkout Previous Tag

```bash
# List available tags
git tag -l

# Checkout previous production tag
git checkout prod-v1.0.0

# Apply previous configuration
cd terraform/environments/prod
terraform apply

# When done, return to main
git checkout main
```

#### Option 3: Manual Terraform Rollback

```bash
# Restore from state backup
cd terraform/environments/prod
cp terraform.tfstate.backup-20260208 terraform.tfstate

# Apply previous state
terraform apply
```

## Handling Secrets

### Never Commit Secrets

Ensure these are .gitignored:
- `terraform.tfvars` (contains SSH keys, potentially sensitive vars)
- `*.tfstate` (contains resource details)
- `*.pem` (SSH private keys)
- `.env` files
- Any file with passwords or keys

### Secret Management

```bash
# Secrets are stored in AWS Secrets Manager
# Reference in documentation, not in code

# Example in docs:
# "Create secret: /blindstrader/prod/db_password"

# Never in code:
# db_password = "actual_password_here"  # ❌ NEVER DO THIS
```

## Collaboration Guidelines

### For Solo Development

Current setup (single developer):
- Direct commits to `main` are acceptable
- Tag releases for production deployments
- Keep commit history clean and meaningful

### For Team Development

When adding team members:

1. **Protect Main Branch**:
   ```bash
   # GitHub Settings > Branches > Add rule
   # Require pull request reviews before merging
   ```

2. **Use Pull Requests**:
   ```bash
   # Create short-lived branch
   git checkout -b infra/add-cdn
   
   # Make changes and push
   git push origin infra/add-cdn
   
   # Create PR on GitHub
   # After review and approval, merge to main
   ```

3. **Review Terraform Plans**:
   - Include `terraform plan` output in PR description
   - Review resource changes carefully
   - Test in staging before production

## CI/CD Integration (Future)

When ready to automate deployments:

### GitHub Actions Workflow

```yaml
# .github/workflows/terraform-staging.yml
name: Terraform Staging

on:
  push:
    branches: [main]
    paths:
      - 'terraform/**'

jobs:
  terraform:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
      
      - name: Terraform Init
        run: terraform init
        working-directory: terraform/environments/stage
      
      - name: Terraform Plan
        run: terraform plan
        working-directory: terraform/environments/stage
      
      - name: Terraform Apply
        if: github.ref == 'refs/heads/main'
        run: terraform apply -auto-approve
        working-directory: terraform/environments/stage
```

### Production Approval Gate

```yaml
# .github/workflows/terraform-production.yml
name: Terraform Production

on:
  push:
    tags:
      - 'prod-v*'

jobs:
  terraform:
    runs-on: ubuntu-latest
    environment: production  # Requires manual approval
    steps:
      # Same as staging but with manual approval
```

## Best Practices

### Do's ✅

- Commit infrastructure changes frequently
- Tag production deployments
- Test in staging before production
- Write descriptive commit messages
- Keep changes atomic and focused
- Document major changes in commit body
- Back up state before major changes

### Don'ts ❌

- Don't commit secrets or sensitive data
- Don't commit `terraform.tfstate` files
- Don't make production changes without staging test
- Don't skip terraform plan
- Don't force push to main
- Don't create long-lived feature branches
- Don't deploy to production on Fridays (weekends harder to fix)

## Emergency Hotfixes

For urgent production fixes:

```bash
# 1. Make fix directly on main
cd terraform/environments/prod
vi terraform.tfvars  # or module files

# 2. Plan carefully
terraform plan

# 3. Apply immediately
terraform apply

# 4. Commit with clear message
git add .
git commit -m "fix(security): close open port 3306 to public"
git push origin main

# 5. Tag as patch version
git tag -a prod-v1.0.1 -m "Emergency security fix"
git push origin prod-v1.0.1

# 6. Apply same fix to staging later
cd terraform/environments/stage
# ...apply fix...
git tag -a stage-v1.0.1 -m "Security fix from production"
```

## Version History Tracking

Keep a CHANGELOG.md for major infrastructure changes:

```markdown
# Infrastructure Changelog

## [1.0.1] - 2026-02-08
### Fixed
- Closed MySQL port 3306 to public internet
- Fixed security group egress rules

## [1.0.0] - 2026-02-01
### Added
- Initial production deployment
- EC2 with Docker containers
- Route53 DNS configuration
- S3 backup system
- Lambda auto-shutdown for staging

### Changed
- Migrated from local development to AWS

## [0.1.0] - 2026-01-15
### Added
- Initial Terraform modules
- Staging environment configuration
```

## Questions and Support

- **Git Issues**: Check [Git documentation](https://git-scm.com/doc)
- **Terraform Workflow**: See [Terraform Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/index.html)
- **Infrastructure Issues**: See [DEPLOYMENT.md](DEPLOYMENT.md)

## Summary

**Key Principles**:
1. Trunk-based: All work on `main`
2. Tag releases: Version production deployments
3. Staging first: Test before production
4. Atomic commits: Small, focused changes
5. Never commit secrets: Use Secrets Manager
6. Document major changes: Clear commit messages and tags

This workflow keeps infrastructure manageable for solo development while being ready to scale for team collaboration.
