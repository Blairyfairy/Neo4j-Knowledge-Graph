output "importer_instance_id" {
  value = aws_instance.importer.id
}

output "importer_private_ip" {
  value = aws_instance.importer.private_ip
}

output "graph_bucket" {
  value = aws_s3_bucket.graph.bucket
}

output "graph_object" {
  value = aws_s3_object.graph_json.key
}
