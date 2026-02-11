output "zone_id" {
  description = "Route53 hosted zone ID"
  value       = aws_route53_zone.main.zone_id
}

output "name_servers" {
  description = "Route53 name servers (configure these at your domain registrar)"
  value       = aws_route53_zone.main.name_servers
}

output "zone_name" {
  description = "Route53 hosted zone name"
  value       = aws_route53_zone.main.name
}
