output "security_group_id" {
  description = "Security group ID for EC2"
  value       = aws_security_group.ec2.id
}

output "elastic_ip" {
  description = "Elastic IP address"
  value       = aws_eip.main.public_ip
}

output "elastic_ip_id" {
  description = "Elastic IP allocation ID"
  value       = aws_eip.main.id
}

output "iam_instance_profile_name" {
  description = "IAM instance profile name for EC2"
  value       = aws_iam_instance_profile.ec2.name
}

output "lambda_role_arn" {
  description = "Lambda execution role ARN"
  value       = var.enable_auto_shutdown ? aws_iam_role.lambda_scheduler[0].arn : null
}
