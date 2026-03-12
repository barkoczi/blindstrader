resource "aws_route53_zone" "main" {
  name = var.domain

  tags = {
    Name        = "${var.environment}-hosted-zone"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# ─── Service A records ────────────────────────────────────────────────────────

resource "aws_route53_record" "identity" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "identity.{var.domain}"
  type    = "A"
  ttl     = 300
  records = [var.elastic_ip]
}

resource "aws_route53_record" "brand" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "brand.{var.domain}"
  type    = "A"
  ttl     = 300
  records = [var.elastic_ip]
}

resource "aws_route53_record" "supplier" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "supplier.{var.domain}"
  type    = "A"
  ttl     = 300
  records = [var.elastic_ip]
}

resource "aws_route53_record" "supply_chain" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "sc.{var.domain}"
  type    = "A"
  ttl     = 300
  records = [var.elastic_ip]
}

resource "aws_route53_record" "payment" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "payment.{var.domain}"
  type    = "A"
  ttl     = 300
  records = [var.elastic_ip]
}

resource "aws_route53_record" "retailer" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "retailer.{var.domain}"
  type    = "A"
  ttl     = 300
  records = [var.elastic_ip]
}

resource "aws_route53_record" "platform" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "platform.{var.domain}"
  type    = "A"
  ttl     = 300
  records = [var.elastic_ip]
}

resource "aws_route53_record" "notification" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "notification.{var.domain}"
  type    = "A"
  ttl     = 300
  records = [var.elastic_ip]
}

resource "aws_route53_record" "docs" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "docs.${var.domain}"
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

# ─── CNAME records for third-party services ──────────────────────────────────

resource "aws_route53_record" "cname" {
  for_each = var.cname_records

  zone_id = aws_route53_zone.main.zone_id
  name    = "${each.key}.${var.domain}"
  type    = "CNAME"
  ttl     = 300
  records = [each.value]
}
