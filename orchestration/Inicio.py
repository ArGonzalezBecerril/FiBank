import sys
import logging
import os

sys.path.append(os.path.dirname(__file__))
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                    )

sys.path.append("/home/arturo/airflow/dags/ProcesoFibank")

from etl.EtlFiBank import EtlFinBank
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import pendulum
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                    )

RUTA_PROYECTO = "/home/arturo/Proyectos/Fibank"

###################################
# AIFLOW                         ##
# PROCESO DE FIBANK              ##
###################################


def notificar_fallo_contexto(context):
    dag_id = context.get('task_instance').dag_id
    task_id = context.get('task_instance').task_id
    execution_date = context.get('execution_date')
    exception = context.get('exception')

    logging.info("  ALERTA DE ERROR EN EL PIPELINE ")
    logging.info(f" DAG: {dag_id}")
    logging.info(f" Tarea Fallida: {task_id}")
    logging.info(f" Fecha/Hora: {execution_date}")
    logging.info(f" Mensaje de Error: {exception}")
    logging.info("------------------------------------------\n")


etl_processor = EtlFinBank(proyecto_path=RUTA_PROYECTO)

default_args = {
    'owner': 'ArGonzalez',
    'depends_on_past': False,
    'retries': 3,                                    # Reintentos
    'retry_delay': timedelta(minutes=2),             # Delay
    'retry_exponential_backoff': True,               # Backoff exponencial activo
    'max_retry_delay': timedelta(minutes=15),        # Límite máximo de espera
    'execution_timeout': timedelta(minutes=45),      # Tiempo máximo coherente por tarea
    'on_failure_callback': notificar_fallo_contexto, # Disparador de alerta estructurada
}

with DAG(
        'pipeline_fibank_demo',
        default_args=default_args,
        description='Pipeline End-to-End FiBank  - Reto Técnico ',
        # Programación automática diaria a las 02:00 AM hora local
        start_date=datetime(2026, 1, 1, tzinfo=pendulum.timezone("America/Mexico_City")),
        schedule_interval='0 2 * * *',
        catchup=False,
        tags=['fibank', 'challenge_25', 'programado'],
) as dag:
    # 1️⃣ Tarea de Extracción (Llama al método de la clase)
    task_extraccion = PythonOperator(
        task_id='fase_extraccion_a_bronze',
        python_callable=etl_processor.extraccion,
    )

    # 2️⃣ Tarea de Transformación (Llama al método de la clase)
    task_transformacion = PythonOperator(
        task_id='fase_transformacion_silver',
        python_callable=etl_processor.transformacion,
    )

    # 3️⃣ Tarea de Carga (Llama al método de la clase)
    task_carga = PythonOperator(
        task_id='fase_carga_gold',
        python_callable=etl_processor.carga,
    )

    # Flujo de ejecución secuencial utilizando Programación Orientada a Objetos
    task_extraccion >> task_transformacion >> task_carga
