variable "environment" {
  description = "Environment name (prod or stage)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "enable_auto_shutdown" {
  description = "Enable auto-shutdown for staging environment"
  type        = bool
  default     = false
}
