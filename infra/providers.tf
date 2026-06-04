terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket         = "finbank-data-dev-bronze" # <--- Tu bucket real en AWS
    key            = "terraform/state/terraform.tfstate" # Ruta interna donde guardará el archivo
    region         = "us-east-1"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
}
