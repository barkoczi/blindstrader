output "ec2_instance_id" {
  description = "EC2 instance ID"
  value       = module.ec2.instance_id
}

output "elastic_ip" {
  description = "Elastic IP address"
  value       = module.security.elastic_ip
}

output "route53_name_servers" {
  description = "Route53 name servers - Configure these at your domain registrar"
  value       = module.dns.name_servers
}

output "auto_shutdown_schedule" {
  description = "Auto-shutdown schedule"
  value = var.enable_auto_shutdown ? {
    stop  = var.shutdown_cron_start
    start = var.shutdown_cron_stop
  } : null
}

output "ssh_command" {
  description = "SSH command to connect to EC2 instance"
  value       = "ssh -i ~/.ssh/blindstrader-stage-key ec2-user@${module.security.elastic_ip}"
}

output "deployment_info" {
  description = "Post-deployment instructions"
  value       = <<-EOT
    1. Configure NS records at your domain registrar:
       ${join("\n       ", module.dns.name_servers)}
    
    2. Create secrets in AWS Secrets Manager:
       - /blindstrader/shared/gpg_public_key (if not already created)
       - /blindstrader/stage/db_password
       - /blindstrader/stage/redis_password
       - /blindstrader/stage/app_key
       - /blindstrader/stage/grafana_admin_password
       - /blindstrader/stage/basic_auth_password
    
    3. SSH to instance: ssh -i ~/.ssh/blindstrader-stage-key ec2-user@${module.security.elastic_ip}
    
    4. Deploy application code and run certbot initial setup
    
    5. Auto-shutdown schedule:
       - Stop: ${var.shutdown_cron_start} (UTC)
       - Start: ${var.shutdown_cron_stop} (UTC)
  EOT
}

output "cost_estimate" {
  description = "Monthly cost estimate"
  value       = <<-EOT
    Estimated monthly cost for staging:
    - EC2 t3a.small: $17/month (if running 24/7)
    - With auto-shutdown (weekdays only): ~$8-10/month (50-70% savings)
    - EBS volumes (45GB): $4/month
    - Elastic IP: $0 (while attached)
    - Route53: Shared with prod
    - Total: ~$12-21/month depending on usage
  EOT
}
