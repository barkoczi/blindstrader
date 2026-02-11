output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.main.id
}

output "instance_public_ip" {
  description = "EC2 instance public IP"
  value       = aws_instance.main.public_ip
}

output "mysql_volume_id" {
  description = "MySQL EBS volume ID"
  value       = aws_ebs_volume.mysql.id
}

output "mysql_volume_arn" {
  description = "MySQL EBS volume ARN"
  value       = aws_ebs_volume.mysql.arn
}

output "redis_volume_id" {
  description = "Redis EBS volume ID"
  value       = aws_ebs_volume.redis.id
}

output "redis_volume_arn" {
  description = "Redis EBS volume ARN"
  value       = aws_ebs_volume.redis.arn
}

output "monitoring_volume_id" {
  description = "Monitoring EBS volume ID"
  value       = aws_ebs_volume.monitoring.id
}

output "monitoring_volume_arn" {
  description = "Monitoring EBS volume ARN"
  value       = aws_ebs_volume.monitoring.arn
}

output "ebs_devices" {
  description = "EBS device mappings for Ansible"
  value = {
    mysql      = "/dev/xvdf"
    redis      = "/dev/xvdg"
    monitoring = "/dev/xvdh"
  }
}

