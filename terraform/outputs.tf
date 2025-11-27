output "db_endpoint" {
  description = "RDS endpoint address for the portfolio database"
  value       = aws_db_instance.portfolio.address
}
output "app_public_ip" {
  description = "Public IP of the portfolio app EC2 instance"
  value       = aws_instance.portfolio_app.public_ip
}