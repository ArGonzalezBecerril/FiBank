import logging
import os
import json
import io
import logging
import pandas as pd
import sqlalchemy
import boto3
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class DaoS3:
    def __init__(self):
        logging.info("🔐 Conectando a AWS Secrets Manager para descargar credenciales...")
        self.AWS_REGION = "us-east-1"
        self.SECRET_NAME = "finbank-dev-db-credentials"

    def obten(self):
        return self.conexion()

    def conexion(self):
        try:
            # Boto3 toma tus credenciales de AWS del archivo local configurado en tu Linux
            secrets_client = boto3.client("secretsmanager", region_name=self.AWS_REGION)
            response = secrets_client.get_secret_value(SecretId=self.SECRET_NAME)
            credentials = json.loads(response["SecretString"])

            DB_ENGINE = credentials["engine"]
            DB_USER = credentials["user"]
            DB_PASS = credentials["password"]
            DB_HOST = credentials["host"]
            DB_PORT = credentials["port"]
            DB_NAME = credentials["database"]
            logging.info("🔑 Credenciales descargadas con éxito.")
            DB_URL = f"{DB_ENGINE}://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
            return DB_URL
        except Exception as e:
            logging.error(f"❌ Error crítico al consultar Secrets Manager: {e}")
            return None
