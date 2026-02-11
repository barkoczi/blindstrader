data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_key_pair" "main" {
  key_name   = "${var.environment}-key"
  public_key = var.ssh_public_key

  tags = {
    Name        = "${var.environment}-key"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_ebs_volume" "mysql" {
  availability_zone = var.availability_zone
  size              = var.ebs_mysql_size
  type              = "gp3"

  tags = {
    Name        = "${var.environment}-mysql-volume"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_ebs_volume" "redis" {
  availability_zone = var.availability_zone
  size              = var.ebs_redis_size
  type              = "gp3"

  tags = {
    Name        = "${var.environment}-redis-volume"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_ebs_volume" "monitoring" {
  availability_zone = var.availability_zone
  size              = var.ebs_monitoring_size
  type              = "gp3"

  tags = {
    Name        = "${var.environment}-monitoring-volume"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_instance" "main" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [var.security_group_id]
  iam_instance_profile   = var.iam_instance_profile_name
  key_name               = aws_key_pair.main.key_name

  user_data = templatefile("${path.module}/user-data-ansible.sh", {
    environment      = var.environment
    ansible_ssh_key  = var.ansible_ssh_key
  })

  root_block_device {
    volume_size           = 30
    volume_type           = "gp3"
    delete_on_termination = true

    tags = {
      Name        = "${var.environment}-root-volume"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }

  tags = {
    Name            = "${var.environment}-ec2"
    Environment     = var.environment
    ManagedBy       = "terraform"
    AutoShutdown    = var.enable_auto_shutdown ? "true" : "false"
    ShutdownCron    = var.enable_auto_shutdown ? var.shutdown_cron_start : ""
  }
}

resource "aws_volume_attachment" "mysql" {
  device_name = "/dev/xvdf"
  volume_id   = aws_ebs_volume.mysql.id
  instance_id = aws_instance.main.id
}

resource "aws_volume_attachment" "redis" {
  device_name = "/dev/xvdg"
  volume_id   = aws_ebs_volume.redis.id
  instance_id = aws_instance.main.id
}

resource "aws_volume_attachment" "monitoring" {
  device_name = "/dev/xvdh"
  volume_id   = aws_ebs_volume.monitoring.id
  instance_id = aws_instance.main.id
}

resource "aws_eip_association" "main" {
  instance_id   = aws_instance.main.id
  allocation_id = var.elastic_ip_id
}
