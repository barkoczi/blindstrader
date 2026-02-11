resource "aws_route53_zone" "main" {
  name = var.domain

  tags = {
    Name        = "${var.environment}-hosted-zone"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_route53_record" "auth" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "auth.${var.domain}"
  type    = "A"
  ttl     = 300
  records = [var.elastic_ip]
}

resource "aws_route53_record" "catalog" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "catalog.${var.domain}"
  type    = "A"
  ttl     = 300
  records = [var.elastic_ip]
}

resource "aws_route53_record" "insights" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "insights.${var.domain}"
  type    = "A"
  ttl     = 300
  records = [var.elastic_ip]
}

resource "aws_route53_record" "prometheus" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "prometheus.${var.domain}"
  type    = "A"
  ttl     = 300
  records = [var.elastic_ip]
}

resource "aws_route53_record" "root" {
  zone_id = aws_route53_zone.main.zone_id
  name    = var.domain
  type    = "A"
  ttl     = 300
  records = [var.elastic_ip]
}

# CNAME records for third-party services
resource "aws_route53_record" "cname" {
  for_each = var.cname_records

  zone_id = aws_route53_zone.main.zone_id
  name    = "${each.key}.${var.domain}"
  type    = "CNAME"
  ttl     = 300
  records = [each.value]
}
