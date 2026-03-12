output "ec2_instance_id" {
  description = "EC2 instance ID"
  value       = module.ec2.instance_id
}

output "elastic_ip" {
  description = "Elastic IP address"
  value       = module.security.elastic_ip
}

output "s3_backup_bucket" {
  description = "S3 backup bucket name"
  value       = module.storage.s3_bucket_name
}

output "ssh_command" {
  description = "SSH command to connect to the EC2 instance"
  value       = "ssh -i ~/.ssh/blindstrader-stage-key ec2-user@${module.security.elastic_ip}"
}

output "ansible_inventory" {
  description = "Ansible inventory information"
  value = {
    environment      = var.environment
    host             = "blindstrader-${var.environment}"
    ansible_host     = module.security.elastic_ip
    ansible_user     = "ansible"
    domain           = var.domain
    ebs_devices      = module.ec2.ebs_devices
    backup_enabled   = var.enable_backups
    backup_s3_bucket = var.enable_backups ? "blindstrader-backups-${var.environment}" : ""
  }
}

output "deployment_info" {
  description = "Post-deployment instructions"
  value       = <<-EOT
    ==========================================
    Terraform Apply Complete!
    ==========================================

    Environment : ${var.environment}
    Elastic IP  : ${module.security.elastic_ip}

    ── Step 1: Add DNS A records in Cloudflare ──
       - identity.${var.domain} -> ${module.security.elastic_ip}
       - brand.${var.domain} -> ${module.security.elastic_ip}
       - supplier.${var.domain} -> ${module.security.elastic_ip}
       - sc.${var.domain} -> ${module.security.elastic_ip}
       - payment.${var.domain} -> ${module.security.elastic_ip}
       - retailer.${var.domain} -> ${module.security.elastic_ip}
       - platform.${var.domain} -> ${module.security.elastic_ip}
       - notification.${var.domain} -> ${module.security.elastic_ip}
       - docs.${var.domain} -> ${module.security.elastic_ip}
       - insights.${var.domain} -> ${module.security.elastic_ip}
       - prometheus.${var.domain} -> ${module.security.elastic_ip}

    ── Step 2: Update Ansible inventory ──
    Edit: ../../ansible/inventory/${var.environment}.yml
    Set:  ansible_host: ${module.security.elastic_ip}

    ── Step 3: Create secrets in AWS Secrets Manager ──
    Shared:
       - /blindstrader/${var.environment}/db_root_password
       - /blindstrader/${var.environment}/db_password
       - /blindstrader/${var.environment}/redis_password
       - /blindstrader/${var.environment}/grafana_admin_password
       - /blindstrader/${var.environment}/stripe_secret_key
       - /blindstrader/${var.environment}/stripe_webhook_secret
       - /blindstrader/${var.environment}/stripe_connect_client_id
       - /blindstrader/shared/gpg_public_key

    Per-service APP_KEYs:
       - /blindstrader/stage/app_key_identity
       - /blindstrader/stage/app_key_brand
       - /blindstrader/stage/app_key_supplier
       - /blindstrader/stage/app_key_supply_chain
       - /blindstrader/stage/app_key_payment
       - /blindstrader/stage/app_key_retailer
       - /blindstrader/stage/app_key_platform
       - /blindstrader/stage/app_key_notification

    ── Step 4: Run Ansible ──
    cd ../../ansible
    ansible-playbook -i inventory/${var.environment}.yml playbooks/site.yml

    ── Step 5: Obtain SSL certificates ──
    ansible-playbook -i inventory/${var.environment}.yml playbooks/ssl.yml

    ── Step 6: Verify services ──
    https://identity.${var.domain}/health
    https://brand.${var.domain}/health
    https://supplier.${var.domain}/health
    https://sc.${var.domain}/health
    https://payment.${var.domain}/health
    https://retailer.${var.domain}/health
    https://platform.${var.domain}/health
    https://notification.${var.domain}/health
    https://docs.${var.domain}
    https://insights.${var.domain}

    ==========================================
  EOT
}
