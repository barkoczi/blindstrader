variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-2"
}

variable "availability_zone" {
  description = "AWS availability zone"
  type        = string
  default     = "eu-west-2a"
}

variable "domain" {
  description = "Domain name"
  type        = string
  default     = "blindstrader.com"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3a.medium"
}

variable "ebs_mysql_size" {
  description = "MySQL EBS volume size in GB"
  type        = number
  default     = 20
}

variable "ebs_redis_size" {
  description = "Redis EBS volume size in GB"
  type        = number
  default     = 10
}

variable "ebs_monitoring_size" {
  description = "Monitoring EBS volume size in GB"
  type        = number
  default     = 15
}

variable "enable_backups" {
  description = "Enable automated backups"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Backup retention in days before moving to Glacier"
  type        = number
  default     = 30
}

variable "enable_auto_shutdown" {
  description = "Enable auto-shutdown (should be false for prod)"
  type        = bool
  default     = false
}

variable "shutdown_cron_start" {
  description = "Cron for shutdown (not used in prod)"
  type        = string
  default     = ""
}

variable "shutdown_cron_stop" {
  description = "Cron for startup (not used in prod)"
  type        = string
  default     = ""
}

variable "ssh_public_key" {
  description = "SSH public key for EC2 access"
  type        = string
}

variable "sentry_dsn" {
  description = "Sentry DSN for error tracking"
  type        = string
  default     = ""
}

variable "cname_records" {
  description = "Map of CNAME records for third-party services (subdomain => target domain)"
  type        = map(string)
  default     = {}
}

variable "ansible_ssh_key" {
  description = "SSH public key for Ansible user"
  type        = string
}

variable "github_username" {
  description = "GitHub username for container registry"
  type        = string
  default     = "barkoczi"
}

variable "github_token" {
  description = "GitHub Personal Access Token for ghcr.io (optional)"
  type        = string
  default     = ""
  sensitive   = true
}
