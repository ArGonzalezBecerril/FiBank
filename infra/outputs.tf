output "bucket_names" {
  value       = [for b in aws_s3_bucket.medallion_buckets : b.bucket]
  description = "Nombres de los buckets S3 creados para la arquitectura Medallon"
}

output "secrets_manager_arn" {
  value       = aws_secretsmanager_secret.db_secret.arn
  description = "ARN del AWS Secrets Manager para las credenciales de la base de datos"
}

output "glue_role_arn" {
  value       = aws_iam_role.glue_role.arn
  description = "ARN del rol de IAM con privilegios minimos para AWS Glue"
}

output "glue_database_name" {
  value       = aws_glue_catalog_database.finbank_db.name
  description = "Nombre de la base de datos del catalogo de Glue creada"
}