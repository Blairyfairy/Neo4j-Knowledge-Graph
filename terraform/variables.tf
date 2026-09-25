variable "aws_region" {
  type    = string
  default = "us-west-2"
}

variable "aws_account_id" {
  type      = string
  default   = null
  nullable  = true
}

variable "name_prefix" {
  type    = string
  default = "blair-skill-kg"
}

variable "bucket_name" {
  type        = string
  description = "Globally unique private S3 bucket name."
}

variable "graph_json_path" {
  type        = string
  default     = "../data/graph.json"
}

variable "subnet_id" {
  type        = string
  description = "Private or public subnet for the ingestion runner."
}

variable "admin_cidr" {
  type        = string
  description = "Your fixed admin /32 CIDR for SSH. Do not use 0.0.0.0/0."
}

variable "instance_type" {
  type    = string
  default = "t3.small"
}
