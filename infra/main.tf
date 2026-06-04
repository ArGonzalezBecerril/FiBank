# ☁️ RECURSO 1: BUCKETS S3 (Arquitectura Medallón)
resource "aws_s3_bucket" "medallion_buckets" {
  for_each = toset(["bronze", "silver", "gold"])

  # Esto creará automáticamente: finbank-data-dev-bronze, finbank-data-dev-silver, etc.
  bucket        = "finbank-data-${var.environment}-${each.key}"
  force_destroy = true # Te permite borrar todo con un "destroy" sin que AWS te ponga trabas por tener datos adentro
}

# Configuración de cifrado obligatorio (AES256)
resource "aws_s3_bucket_server_side_encryption_configuration" "sse" {
  for_each = aws_s3_bucket.medallion_buckets
  bucket   = each.value.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# =============================================================
# 🔐 RECURSO 2: AWS SECRETS MANAGER (Credenciales Origen)
# =============================================================
resource "aws_secretsmanager_secret" "db_secret" {
  name                    = "finbank-${var.environment}-db-credentials"
  recovery_window_in_days = 0 # Si lo borras en tus pruebas, se elimina al instante sin bloquearse por días
}

resource "aws_secretsmanager_secret_version" "db_secret_val" {
  secret_id     = aws_secretsmanager_secret.db_secret.id

  # Guardamos los datos en formato JSON para que Python los lea facilito
  secret_string = jsonencode({
    engine   = "postgresql"
    host     = "localhost"
    port     = 5433
    user     = "postgres"
    password = "postgres"
    database = "dataknow"
  })
}

# =============================================================
# 🛡️ RECURSO 3: ROLES IAM CON POLÍTICA DE MÍNIMO PRIVILEGIO
# =============================================================
resource "aws_iam_role" "glue_role" {
  name = "finbank-${var.environment}-glue-role"

  # Le da permiso al servicio de AWS Glue de asumir este rol
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "glue.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "glue_policy" {
  name = "finbank-${var.environment}-glue-policy"
  role = aws_iam_role.glue_role.id

  # Definición estricta de accesos limitados
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
        Resource = [for b in aws_s3_bucket.medallion_buckets : "${b.arn}/*"]
      },
      {
        Effect   = "Allow"
        Action   = [for b in aws_s3_bucket.medallion_buckets : "s3:ListBucket"]
        Resource = [for b in aws_s3_bucket.medallion_buckets : b.arn]
      },
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = [aws_secretsmanager_secret.db_secret.arn]
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = ["arn:aws:logs:*:*:*"]
      }
    ]
  })
}

# =============================================================
# 📊 RECURSO 4: CLOUDWATCH LOG GROUP & SNS TOPIC (Alertas)
# =============================================================
resource "aws_cloudwatch_log_group" "glue_logs" {
  name              = "/aws-glue/jobs/finbank-${var.environment}-logs"
  retention_in_days = 7 # Guarda tus logs una semana para auditar errores sin gastar créditos
}

resource "aws_sns_topic" "alerts" {
  name = "finbank-${var.environment}-alerts-topic"
}

# =============================================================
# 🤖 RECURSO 5: AWS GLUE DATABASE & CRAWLERS (Catálogo)
# =============================================================
resource "aws_glue_catalog_database" "finbank_db" {
  name = "finbank_${var.environment}_catalog"
}

resource "aws_glue_crawler" "bronze_crawler" {
  database_name = aws_glue_catalog_database.finbank_db.name
  name          = "finbank-${var.environment}-bronze-crawler"
  role          = aws_iam_role.glue_role.arn # El rol de permisos del Paso 3

  # Le dice al robot que escanee la raíz de tu bucket bronze
  s3_target {
    path = "s3://${aws_s3_bucket.medallion_buckets["bronze"].bucket}/"
  }
}
