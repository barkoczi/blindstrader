output "lambda_function_name" {
  description = "Lambda function name"
  value       = var.enable_auto_shutdown ? aws_lambda_function.scheduler[0].function_name : null
}

output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = var.enable_auto_shutdown ? aws_lambda_function.scheduler[0].arn : null
}

output "stop_schedule" {
  description = "Stop instances schedule"
  value       = var.enable_auto_shutdown ? var.shutdown_cron_start : null
}

output "start_schedule" {
  description = "Start instances schedule"
  value       = var.enable_auto_shutdown ? var.shutdown_cron_stop : null
}
