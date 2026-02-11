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
  description = "SSH command to connect to EC2 instance (for personal access)"
  value       = "ssh -i ~/.ssh/blindstrader-prod-key ec2-user@${module.security.elastic_ip}"
}

# Ansible inventory outputs
output "ansible_inventory" {
  description = "Ansible inventory information"
  value = {
    environment = var.environment
    host        = "blindstrader-${var.environment}"
    ansible_host = module.security.elastic_ip
    ansible_user = "ansible"
    domain      = var.domain
    ebs_devices = module.ec2.ebs_devices
    backup_enabled = var.enable_backups
    backup_s3_bucket = var.enable_backups ? "blindstrader-backups-${var.environment}" : ""
  }
}

output "deployment_info" {
  description = "Post-deployment instructions"
  value       = <<-EOT
    ========================================
    Terraform Apply Complete!
    ========================================
    
    Environment: ${var.environment}
    Elastic IP: ${module.security.elastic_ip}
    
    Next Steps:
    
    1. Add DNS A records in Cloudflare (see docs/cloudflare-dns-import.txt):
       - auth.${var.domain} -> ${module.security.elastic_ip}
       - catalog.${var.domain} -> ${module.security.elastic_ip}
       - insights.${var.domain} -> ${module.security.elastic_ip}
       - prometheus.${var.domain} -> ${module.security.elastic_ip}
    
    2. Update Ansible inventory file:
       Edit: ../../ansible/inventory/${var.environment}.yml
       Set ansible_host: ${module.security.elastic_ip}
    
    3. Create secrets in AWS Secrets Manager:
       - /blindstrader/shared/gpg_public_key
       - /blindstrader/prod/db_password
       - /blindstrader/prod/redis_password
       - /blindstrader/prod/app_key
       - /blindstrader/prod/grafana_admin_password
       - /blindstrader/prod/basic_auth_password
    
    4. Run Ansible to configure the instance:
       cd ../../ansible
       ansible-playbook -i inventory/${var.environment}.yml playbooks/site.yml
    
    5. Obtain SSL certificates:
       ansible-playbook -i inventory/${var.environment}.yml playbooks/ssl.yml
    
    6. Verify deployment:
       https://${var.domain}
       https://auth.${var.domain}
       https://catalog.${var.domain}
       https://insights.${var.domain}
    
    ========================================
    
    4. Deploy application code and run certbot initial setup
  EOT
}
