variable "environment" {
  description = "Environment name (prod or stage)"
  type        = string
}

variable "domain" {
  description = "Domain name"
  type        = string
}

variable "elastic_ip" {
  description = "Elastic IP address to point DNS records to"
  type        = string
}

variable "cname_records" {
  description = "Map of CNAME records to create (subdomain => target)"
  type        = map(string)
  default     = {}
}
