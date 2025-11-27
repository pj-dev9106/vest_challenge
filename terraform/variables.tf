variable "aws_region" {
  type    = string
  default = "us-west-2"
}

variable "db_username" {
  type        = string
  description = "Username for the RDS Postgres instance"
}

variable "db_password" {
  type        = string
  description = "Password for the RDS Postgres instance"
  sensitive   = true
}

variable "candidate_id" {
  type        = string
  description = "Tag value required by the interview environment"
  default     = "kyle-gardner-vest-trial-001"
}

variable "allowed_cidr" {
  type        = string
  description = "CIDR allowed to access the RDS instance (e.g. 123.45.67.89/32)"
}
