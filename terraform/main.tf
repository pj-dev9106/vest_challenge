terraform {
  required_version = ">= 1.5.0"

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

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

resource "aws_security_group" "portfolio_db_sg" {
  name        = "portfolio-db-sg"
  description = "Allow PostgreSQL access from my IP"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "Postgres from my IP"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.allowed_cidr]
  }

  # From app EC2 security group (for real traffic)
  ingress {
    description      = "Postgres from app EC2"
    from_port        = 5432
    to_port          = 5432
    protocol         = "tcp"
    security_groups  = [aws_security_group.portfolio_app_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    CandidateId = var.candidate_id
  }
}

resource "aws_db_instance" "portfolio" {
  identifier        = "portfolio-clearinghouse-db"
  engine            = "postgres"
  engine_version    = "15"
  instance_class    = "db.t3.micro"
  allocated_storage = 20

  username = var.db_username
  password = var.db_password

  db_name             = "portfolio_clearinghouse"
  skip_final_snapshot = true

  publicly_accessible    = true
  vpc_security_group_ids = [aws_security_group.portfolio_db_sg.id]

  tags = {
    CandidateId = var.candidate_id
  }
}

resource "aws_security_group" "portfolio_app_sg" {
  name        = "portfolio-app-sg"
  description = "Allow HTTP access to app and outbound to RDS"
  vpc_id      = data.aws_vpc.default.id

  # Allow HTTP from anywhere (for API demo)
  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

    # NEW: Allow SSH only from your IP
  ingress {
    description = "SSH from my IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow all outbound (so app can reach RDS and internet)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    CandidateId = var.candidate_id
  }
}

data "aws_ami" "ubuntu" {
  most_recent = true

  owners = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}


resource "aws_instance" "portfolio_app" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "t3.micro"
  subnet_id                   = data.aws_subnets.default.ids[0]
  vpc_security_group_ids      = [aws_security_group.portfolio_app_sg.id]
  associate_public_ip_address = true
  key_name                    = "portfolio-app-key"

  tags = {
    CandidateId = var.candidate_id
    Name        = "portfolio-app-server"
  }

  # For now, we keep user_data minimal.
  # Next step we will SSH in and set up Docker + app.
  user_data = <<-EOF
              #!/bin/bash
              apt-get update -y
              apt-get install -y docker.io
              systemctl enable docker
              systemctl start docker
              EOF
}
