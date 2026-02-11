terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "vpc" {
  source = "../../modules/vpc"

  environment       = var.environment
  availability_zone = var.availability_zone
}

module "security" {
  source = "../../modules/security"

  environment          = var.environment
  vpc_id               = module.vpc.vpc_id
  aws_region           = var.aws_region
  enable_auto_shutdown = var.enable_auto_shutdown
}

module "ec2" {
  source = "../../modules/ec2"

  environment              = var.environment
  instance_type            = var.instance_type
  subnet_id                = module.vpc.public_subnet_id
  security_group_id        = module.security.security_group_id
  iam_instance_profile_name = module.security.iam_instance_profile_name
  elastic_ip_id            = module.security.elastic_ip_id
  availability_zone        = var.availability_zone
  domain                   = var.domain
  aws_region               = var.aws_region
  ssh_public_key           = var.ssh_public_key
  ansible_ssh_key          = var.ansible_ssh_key
  ebs_mysql_size           = var.ebs_mysql_size
  ebs_redis_size           = var.ebs_redis_size
  ebs_monitoring_size      = var.ebs_monitoring_size
  s3_backup_bucket         = ""
  enable_backups           = var.enable_backups
  enable_auto_shutdown     = var.enable_auto_shutdown
  shutdown_cron_start      = var.shutdown_cron_start
  sentry_dsn               = var.sentry_dsn
}

module "storage" {
  source = "../../modules/storage"

  environment           = var.environment
  enable_backups        = var.enable_backups
  backup_retention_days = var.backup_retention_days
  ebs_volume_arns       = []
}

module "lambda_scheduler" {
  source = "../../modules/lambda-scheduler"

  environment          = var.environment
  enable_auto_shutdown = var.enable_auto_shutdown
  shutdown_cron_start  = var.shutdown_cron_start
  shutdown_cron_stop   = var.shutdown_cron_stop
  lambda_role_arn      = module.security.lambda_role_arn
}
