resource "aws_security_group" "ec2" {
  name        = "${var.environment}-ec2-sg"
  description = "Security group for EC2 instance"
  vpc_id      = var.vpc_id

  # HTTP
  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS
  ingress {
    description = "HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # SSH
  ingress {
    description = "SSH from anywhere"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # All outbound traffic
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.environment}-ec2-sg"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_eip" "main" {
  domain = "vpc"

  tags = {
    Name        = "${var.environment}-eip"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_iam_role" "ec2" {
  name = "${var.environment}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.environment}-ec2-role"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_iam_role_policy" "ec2_s3_access" {
  name = "${var.environment}-ec2-s3-policy"
  role = aws_iam_role.ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::blindstrader-backups-${var.environment}",
          "arn:aws:s3:::blindstrader-backups-${var.environment}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "ec2_secrets_access" {
  name = "${var.environment}-ec2-secrets-policy"
  role = aws_iam_role.ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          "arn:aws:secretsmanager:${var.aws_region}:*:secret:/blindstrader/${var.environment}/*",
          "arn:aws:secretsmanager:${var.aws_region}:*:secret:/blindstrader/shared/*"
        ]
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ec2" {
  name = "${var.environment}-ec2-profile"
  role = aws_iam_role.ec2.name

  tags = {
    Name        = "${var.environment}-ec2-profile"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# Lambda execution role for EC2 scheduler
resource "aws_iam_role" "lambda_scheduler" {
  count = var.enable_auto_shutdown ? 1 : 0
  name  = "${var.environment}-lambda-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.environment}-lambda-scheduler-role"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_iam_role_policy" "lambda_ec2_control" {
  count = var.enable_auto_shutdown ? 1 : 0
  name  = "${var.environment}-lambda-ec2-control-policy"
  role  = aws_iam_role.lambda_scheduler[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:StartInstances",
          "ec2:StopInstances",
          "ec2:DescribeInstances"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}
