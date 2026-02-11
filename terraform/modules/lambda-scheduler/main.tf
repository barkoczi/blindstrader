data "archive_file" "lambda" {
  count       = var.enable_auto_shutdown ? 1 : 0
  type        = "zip"
  source_file = "${path.module}/function.py"
  output_path = "${path.module}/function.zip"
}

resource "aws_lambda_function" "scheduler" {
  count            = var.enable_auto_shutdown ? 1 : 0
  filename         = data.archive_file.lambda[0].output_path
  function_name    = "${var.environment}-ec2-scheduler"
  role             = var.lambda_role_arn
  handler          = "function.lambda_handler"
  source_code_hash = data.archive_file.lambda[0].output_base64sha256
  runtime          = "python3.11"
  timeout          = 60

  environment {
    variables = {
      ENVIRONMENT = var.environment
    }
  }

  tags = {
    Name        = "${var.environment}-ec2-scheduler"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_cloudwatch_event_rule" "stop_instances" {
  count               = var.enable_auto_shutdown ? 1 : 0
  name                = "${var.environment}-stop-instances"
  description         = "Stop EC2 instances according to schedule"
  schedule_expression = "cron(${var.shutdown_cron_start})"

  tags = {
    Name        = "${var.environment}-stop-instances-rule"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_cloudwatch_event_target" "stop_instances" {
  count     = var.enable_auto_shutdown ? 1 : 0
  rule      = aws_cloudwatch_event_rule.stop_instances[0].name
  target_id = "StopInstances"
  arn       = aws_lambda_function.scheduler[0].arn

  input = jsonencode({
    action = "stop"
  })
}

resource "aws_cloudwatch_event_rule" "start_instances" {
  count               = var.enable_auto_shutdown ? 1 : 0
  name                = "${var.environment}-start-instances"
  description         = "Start EC2 instances according to schedule"
  schedule_expression = "cron(${var.shutdown_cron_stop})"

  tags = {
    Name        = "${var.environment}-start-instances-rule"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_cloudwatch_event_target" "start_instances" {
  count     = var.enable_auto_shutdown ? 1 : 0
  rule      = aws_cloudwatch_event_rule.start_instances[0].name
  target_id = "StartInstances"
  arn       = aws_lambda_function.scheduler[0].arn

  input = jsonencode({
    action = "start"
  })
}

resource "aws_lambda_permission" "allow_cloudwatch_stop" {
  count         = var.enable_auto_shutdown ? 1 : 0
  statement_id  = "AllowExecutionFromCloudWatchStop"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.scheduler[0].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.stop_instances[0].arn
}

resource "aws_lambda_permission" "allow_cloudwatch_start" {
  count         = var.enable_auto_shutdown ? 1 : 0
  statement_id  = "AllowExecutionFromCloudWatchStart"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.scheduler[0].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.start_instances[0].arn
}
