variable "environment" {
  description = "Environment name (prod or stage)"
  type        = string
}

variable "enable_auto_shutdown" {
  description = "Enable auto-shutdown scheduling"
  type        = bool
  default     = false
}

variable "shutdown_cron_start" {
  description = "Cron expression for instance shutdown (UTC)"
  type        = string
  default     = "0 18 * * MON-FRI"
}

variable "shutdown_cron_stop" {
  description = "Cron expression for instance startup (UTC)"
  type        = string
  default     = "0 8 * * MON-FRI"
}

variable "lambda_role_arn" {
  description = "IAM role ARN for Lambda execution"
  type        = string
}
