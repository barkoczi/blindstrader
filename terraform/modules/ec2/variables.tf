variable "environment" {
  description = "Environment name (prod or stage)"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID for EC2 instance"
  type        = string
}

variable "security_group_id" {
  description = "Security group ID for EC2 instance"
  type        = string
}

variable "iam_instance_profile_name" {
  description = "IAM instance profile name"
  type        = string
}

variable "elastic_ip_id" {
  description = "Elastic IP allocation ID"
  type        = string
}

variable "availability_zone" {
  description = "AWS availability zone"
  type        = string
}

variable "domain" {
  description = "Domain name for the environment"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "ssh_public_key" {
  description = "SSH public key for EC2 access"
  type        = string
}

variable "ebs_mysql_size" {
  description = "Size of MySQL EBS volume in GB"
  type        = number
  default     = 20
}

variable "ebs_redis_size" {
  description = "Size of Redis EBS volume in GB"
  type        = number
  default     = 10
}

variable "ebs_monitoring_size" {
  description = "Size of monitoring EBS volume in GB"
  type        = number
  default     = 15
}

variable "s3_backup_bucket" {
  description = "S3 bucket name for backups"
  type        = string
}

variable "enable_backups" {
  description = "Enable automated backups"
  type        = bool
  default     = false
}

variable "enable_auto_shutdown" {
  description = "Enable auto-shutdown scheduling"
  type        = bool
  default     = false
}

variable "shutdown_cron_start" {
  description = "Cron expression for instance shutdown"
  type        = string
  default     = "0 18 * * MON-FRI"
}

variable "sentry_dsn" {
  description = "Sentry DSN for error tracking"
  type        = string
  default     = ""
}

variable "ansible_ssh_key" {
  description = "SSH public key for Ansible user"
  type        = string
}
