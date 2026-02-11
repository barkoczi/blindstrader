# DNS Configuration Guide

This guide explains how to configure DNS for your BlindStrader infrastructure using AWS Route53.

## Overview

You have two AWS Route53 hosted zones created by Terraform:

1. **Production Zone** (`blindstrader.com`)
   - Nameservers:
     ```
     ns-1232.awsdns-26.org
     ns-1764.awsdns-28.co.uk
     ns-259.awsdns-32.com
     ns-828.awsdns-39.net
     ```

2. **Staging Zone** (`stage.blindstrader.com`)
   - Nameservers:
     ```
     ns-1392.awsdns-46.org
     ns-1700.awsdns-20.co.uk
     ns-267.awsdns-33.com
     ns-596.awsdns-10.net
     ```

## Configuration Steps

### Option A: Domain Registered with Cloudflare

If your domain is registered/managed by Cloudflare:

#### Step 1: Change Root Domain Nameservers

1. Log into **Cloudflare Dashboard**: https://dash.cloudflare.com
2. Click on **Accounts** → Select your account
3. Go to **Domain Registration** → **blindstrader.com**
4. Click **Configuration** → **Nameservers**
5. Change from Cloudflare nameservers to Route53:
   - Remove existing Cloudflare nameservers
   - Add custom nameservers:
     ```
     ns-1232.awsdns-26.org
     ns-1764.awsdns-28.co.uk
     ns-259.awsdns-32.com
     ns-828.awsdns-39.net
     ```
6. Click **Save**

⚠️ **Important**: Changing nameservers will transfer DNS management from Cloudflare to AWS Route53. All existing DNS records in Cloudflare will no longer be active.

#### Step 2: Configure Staging Subdomain Delegation

Since you're now using Route53 for DNS, configure staging subdomain there:

1. Go to **AWS Console** → **Route53**
2. Click on **Hosted zones** → Select **blindstrader.com**
3. Click **Create record**
4. Configure the record:
   - **Record name**: `stage`
   - **Record type**: `NS - Name server`
   - **Value**: (Enter all 4 nameservers, one per line)
     ```
     ns-1392.awsdns-46.org
     ns-1700.awsdns-20.co.uk
     ns-267.awsdns-33.com
     ns-596.awsdns-10.net
     ```
   - **TTL**: `300` seconds
   - **Routing policy**: Simple routing
5. Click **Create records**

---

### Option B: Domain Registered Elsewhere (GoDaddy, Namecheap, etc.)

If your domain is registered at another registrar:

#### Step 1: Change Nameservers at Registrar

1. Log into your domain registrar's control panel
2. Navigate to DNS/Nameserver settings for **blindstrader.com**
3. Select **Custom Nameservers** or **Use custom nameservers**
4. Replace existing nameservers with AWS Route53 nameservers:
   ```
   ns-1232.awsdns-26.org
   ns-1764.awsdns-28.co.uk
   ns-259.awsdns-32.com
   ns-828.awsdns-39.net
   ```
5. Save changes

**Common registrar paths:**
- **Namecheap**: Domain List → Manage → Nameservers → Custom DNS
- **GoDaddy**: My Products → Domains → DNS → Nameservers → Change
- **Google Domains**: DNS → Name servers → Use custom name servers
- **Hover**: DNS → Nameservers → Edit

#### Step 2: Configure Staging Subdomain

Same as Option A, Step 2 - Add NS records in Route53 production zone.

---

## DNS Propagation

After making changes:

- **Nameserver changes**: 1-48 hours (usually 1-4 hours)
- **DNS record changes**: 5-30 minutes (based on TTL)

## Verification

### Check Nameservers

Wait 15-30 minutes after making changes, then verify:

```bash
# Check production nameservers
dig NS blindstrader.com +short

# Expected output:
# ns-1232.awsdns-26.org
# ns-1764.awsdns-28.co.uk
# ns-259.awsdns-32.com
# ns-828.awsdns-39.net

# Check staging nameservers
dig NS stage.blindstrader.com +short

# Expected output:
# ns-1392.awsdns-46.org
# ns-1700.awsdns-20.co.uk
# ns-267.awsdns-33.com
# ns-596.awsdns-10.net
```

### Check DNS Records

After nameservers are verified, check if subdomains resolve:

```bash
# Production subdomains (replace X.X with actual IP from terraform output)
dig auth.blindstrader.com +short
dig catalog.blindstrader.com +short

# Staging subdomains
dig auth.stage.blindstrader.com +short
dig catalog.stage.blindstrader.com +short
```

### Check from Multiple Locations

Use online tools to verify global DNS propagation:
- https://dnschecker.org
- https://www.whatsmydns.net

Enter your domain name to see propagation status worldwide.

## DNS Architecture

```
blindstrader.com (Route53 Production Zone)
├── auth.blindstrader.com → 13.40.X.X (Production EC2)
├── catalog.blindstrader.com → 13.40.X.X (Production EC2)
├── insights.blindstrader.com → 13.40.X.X (Production EC2)
├── prometheus.blindstrader.com → 13.40.X.X (Production EC2)
└── stage.blindstrader.com (NS delegation)
    └── Route53 Staging Zone
        ├── auth.stage.blindstrader.com → 18.133.43.175 (Staging EC2)
        ├── catalog.stage.blindstrader.com → 18.133.43.175 (Staging EC2)
        ├── insights.stage.blindstrader.com → 18.133.43.175 (Staging EC2)
        └── prometheus.stage.blindstrader.com → 18.133.43.175 (Staging EC2)
```

## Troubleshooting

### Nameservers Not Updating

**Problem**: `dig NS blindstrader.com` shows old nameservers

**Solutions**:
1. Wait longer (can take up to 48 hours)
2. Clear local DNS cache:
   ```bash
   # macOS
   sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
   
   # Linux
   sudo systemd-resolve --flush-caches
   ```
3. Verify changes were saved at registrar
4. Try from a different network or use 8.8.8.8:
   ```bash
   dig @8.8.8.8 NS blindstrader.com +short
   ```

### Staging Subdomain Not Resolving

**Problem**: `dig NS stage.blindstrader.com` returns nothing

**Solutions**:
1. Verify NS records exist in production Route53 zone
2. Check you added the NS record in the **production** zone, not staging
3. Wait for DNS propagation (5-30 minutes)

### NXDOMAIN or Server Not Found

**Problem**: Domain doesn't resolve at all

**Solutions**:
1. Verify nameservers are correct at registrar
2. Check Route53 hosted zone has A records
3. Run Terraform to ensure DNS records are created:
   ```bash
   cd terraform/environments/prod
   terraform plan  # Should show no changes
   ```

### DNS Records in Route53 Not Working

**Problem**: Nameservers correct but subdomains don't resolve

**Solutions**:
1. Check Route53 hosted zone has the correct records
2. Verify zone ID matches what Terraform created
3. Check TTL hasn't expired
4. Ensure records point to correct IP addresses

## Quick Reference

| Domain | Type | Value |
|--------|------|-------|
| blindstrader.com | NS | ns-1232.awsdns-26.org<br>ns-1764.awsdns-28.co.uk<br>ns-259.awsdns-32.com<br>ns-828.awsdns-39.net |
| stage (subdomain in prod zone) | NS | ns-1392.awsdns-46.org<br>ns-1700.awsdns-20.co.uk<br>ns-267.awsdns-33.com<br>ns-596.awsdnes-10.net |
| auth.blindstrader.com | A | Production Elastic IP |
| auth.stage.blindstrader.com | A | 18.133.43.175 |

## Next Steps

After DNS is configured and verified:

1. ✅ Verify DNS resolution with `dig` commands above
2. ✅ Test HTTPS access (after SSL certificates are installed):
   ```bash
   curl -I https://auth.blindstrader.com
   curl -I https://auth.stage.blindstrader.com
   ```
3. ✅ Configure Ansible inventory with Elastic IPs
4. ✅ Run Ansible playbooks to configure servers
5. ✅ Obtain SSL certificates with Let's Encrypt

See [02-DEPLOYMENT.md](02-DEPLOYMENT.md) for next deployment steps.
