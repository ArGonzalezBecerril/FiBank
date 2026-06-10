import subprocess
import os
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                    )


class EtlFinBank:
    def __init__(self, proyecto_path: str):
        self.proyecto_path = proyecto_path

    def extraccion(self):
        logging.info(" Iniciando Fase 1: Extracción y Carga a Bronce...")

        env_actual = os.environ.copy()

        # 2. Le inyectamos las rutas de tus credenciales a esa copia
        env_actual['AWS_SHARED_CREDENTIALS_FILE'] = '/home/arturo/.aws/credentials'
        env_actual['AWS_PROFILE'] = 'default'
        env_actual['HOME'] = '/home/arturo'

        # 1. Ejecuta tu script que genera la data y la mete a Postgres en Docker
        script_generar = os.path.join(self.proyecto_path, "data-generation", "generate_and_load.py")

        # 2. Ejecuta el puente que saca los datos de Postgres y los sube a AWS S3 (Bronce)
        script_extraer = os.path.join(self.proyecto_path, "data-extraction", "extract_to_bronze.py")
        # Reemplaza la línea 30 de tu EtlFiBank.py por esta versión:
        subprocess.run(
            ["/bin/bash", "-c",
             f"source /home/arturo/airflow_proyectos/airflow_env/bin/activate && python3 {script_extraer}"],
            check=True,
            env=env_actual
        )

        logging.info(" Fase 1 completada con éxito.")

    def transformacion(self):
        logging.info(" Iniciando Fase 2: Transformación (dbt Silver)...")
        path_dbt = os.path.join(self.proyecto_path, "dbt_finbank")

        # dbt clean para asegurar consistencia y dbt run dirigido a Silver
        subprocess.run(["dbt", "clean"], cwd=path_dbt, check=True)
        subprocess.run(["dbt", "run", "--select", "models/silver"], cwd=path_dbt, check=True)
        logging.info(" Fase 2 completada con éxito.")

    def carga(self):
        """Ejecuta la carga final con dbt hacia la capa Oro (Modelado analítico)"""
        logging.info(" Iniciando Fase 3: Carga Final (dbt Gold)...")
        path_dbt = os.path.join(self.proyecto_path, "dbt_finbank")

        # dbt run dirigido exclusivamente a Gold
        subprocess.run(["dbt", "run", "--select", "models/gold"], cwd=path_dbt, check=True)
        logging.info(" Fase 3 (Capa Oro) completada con éxito.")

