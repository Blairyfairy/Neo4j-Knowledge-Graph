terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_s3_bucket" "graph" {
  bucket = var.bucket_name

  tags = {
    Project = "blair-skill-knowledge-graph"
    Purpose = "Neo4j graph import artifacts"
  }
}

resource "aws_s3_bucket_public_access_block" "graph" {
  bucket                  = aws_s3_bucket.graph.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "graph" {
  bucket = aws_s3_bucket.graph.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_object" "graph_json" {
  bucket = aws_s3_bucket.graph.id
  key    = "graph/graph.json"
  source = var.graph_json_path
  etag   = filemd5(var.graph_json_path)
}

resource "aws_iam_role" "importer" {
  name = "${var.name_prefix}-importer"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "importer_s3" {
  role = aws_iam_role.importer.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["s3:GetObject", "s3:GetObjectVersion"]
      Resource = "${aws_s3_bucket.graph.arn}/graph/*"
    }]
  })
}

resource "aws_iam_instance_profile" "importer" {
  name = "${var.name_prefix}-importer"
  role = aws_iam_role.importer.name
}

resource "aws_security_group" "importer" {
  name        = "${var.name_prefix}-importer"
  description = "SSH administration; outbound access to Neo4j Aura and package mirrors"

  ingress {
    description = "Administrative SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
  }

  egress {
    description = "Outbound HTTPS/Bolt to managed services"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "importer" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.importer.id]
  iam_instance_profile   = aws_iam_instance_profile.importer.name

  metadata_options {
    http_tokens = "required"
  }

  tags = {
    Name    = "${var.name_prefix}-importer"
    Project = "blair-skill-knowledge-graph"
  }
}
