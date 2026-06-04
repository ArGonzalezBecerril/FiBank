import os
import json
import io
import time
import logging
from datetime import datetime
import uuid
import pandas as pd
import sqlalchemy
import boto3
import DaoS3 as dao

# Configuración profesional de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logging.info(" Iniciando Pipeline Incremental Corporativo - Capa Bronze...")

SISTEMA_FUENTE = "postgresql_docker"
ID_LOTE = str(uuid.uuid4())
FECHA_PROCESO = datetime.now()
PARTICION_PATH = f"year={FECHA_PROCESO.strftime('%Y')}/month={FECHA_PROCESO.strftime('%m')}/day={FECHA_PROCESO.strftime('%d')}"
STATE_FILE = "watermark_state.json"

# =============================================================
#  PASO 1: AUTENTICACIÓN Y CONEXIÓN A BASE DE DATOS
# =============================================================

dao_conexion = dao.DaoS3()
engine = dao_conexion.obten()

# =============================================================
#  PASO 2: GESTIÓN DE MARCAS DE AGUA (ESTADO INCREMENTAL)
# =============================================================
# Cargar el estado anterior si existe para saber qué procesamos la última vez
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        watermarks = json.load(f)
    logging.info(f"Estado previo detectado. Marcas de agua actuales: {watermarks}")
else:
    # Si es la primera corrida, la marca de agua inicia en el año 1900 (Trae todo)
    watermarks = {
        "tb_sucursales_red": "1900-01-01",
        "tb_productos_cat": "1900-01-01",
        "tb_clientes_core": "1900-01-01",
        "tb_obligaciones": "1900-01-01",
        "tb_mov_financieros": "1900-01-01",
        "tb_comisiones_log": "1900-01-01"
    }
    logging.info("🆕 No se detectó estado previo. Iniciando carga inicial completa.")

# Configuración de las columnas de control de tiempo para cada tabla
pipeline_config = {
    "tb_sucursales_red": {"control_col": None, "s3_folder": "sucursales", "file_name": "TB_SUCURSALES_RED"},
    "tb_productos_cat": {"control_col": None, "s3_folder": "productos", "file_name": "TB_PRODUCTOS_CAT"},
    "tb_clientes_core": {"control_col": "fec_alta", "s3_folder": "clientes", "file_name": "TB_CLIENTES_CORE"},
    "tb_obligaciones": {"control_col": "fec_desembolso", "s3_folder": "obligaciones", "file_name": "TB_OBLIGACIONES"},
    "tb_mov_financieros": {"control_col": "fec_mov", "s3_folder": "movimientos", "file_name": "TB_MOV_FINANCIEROS"},
    "tb_comisiones_log": {"control_col": "fec_cobro", "s3_folder": "comisiones", "file_name": "TB_COMISIONES_LOG"}
}

BUCKET_BRONZE = "finbank-data-dev-bronze"
s3_client = boto3.client("s3", region_name=dao_conexion.AWS_REGION)

print("\n" + "=" * 75)
print(" REPORTE MÈTRICO DE INGESTA INCREMENTAL (CAPA BRONZE)")
print("=" * 75)

# =============================================================
#  PASO 3: BUCLE DE PROCESAMIENTO INCREMENTAL
# =============================================================
for tabla, info in pipeline_config.items():
    inicio_tabla = time.time()
    last_watermark = watermarks[tabla]

    # Construcción del Query SQL con filtro incremental dinámico
    if info["control_col"]:
        query = f"SELECT * FROM {tabla} WHERE {info['control_col']} > '{last_watermark}';"
    else:
        # Tablas catálogo o dimensiones pequeñas se procesan completas (Catálogos de sucursales/productos)
        query = f"SELECT * FROM {tabla};"

    df = pd.read_sql_query(query, engine)
    num_registros = len(df)

    # Si no hay registros nuevos o modificados, nos saltamos la subida a S3 para optimizar costos
    if num_registros == 0:
        print(f"Tabla: {tabla.ljust(20)} | 💤 Sin cambios o registros nuevos desde {last_watermark}.")
        continue

    # Inyección obligatoria de metadatos de auditoría
    df["audit_timestamp"] = datetime.utcnow().isoformat()
    df["audit_src_system"] = SISTEMA_FUENTE
    df["audit_batch_id"] = ID_LOTE

    # Limpieza de tipos de columnas para el formato Parquet
    df.columns = df.columns.astype(str)
    for col in df.columns:
        if df[col].dtype == 'object' or 'fec' in col or 'hra' in col:
            df[col] = df[col].astype(str)

    # Actualizar la marca de agua interna con el valor más reciente del lote procesado
    if info["control_col"]:
        max_date = df[info["control_col"]].max()
        watermarks[tabla] = str(max_date)

    # Ruta de destino con particionamiento año/mes/día
    s3_key = f"{info['s3_folder']}/{PARTICION_PATH}/{info['file_name']}.parquet"

    # Conversión a Parquet en memoria con PyArrow
    buffer_parquet = io.BytesIO()
    df.to_parquet(buffer_parquet, index=False, engine="pyarrow")
    body_data = buffer_parquet.getvalue()
    tamano_bytes = len(body_data)

    # Subida limpia a AWS S3
    s3_client.put_object(Bucket=BUCKET_BRONZE, Key=s3_key, Body=body_data)
    duracion_tabla = time.time() - inicio_tabla

    print(f"Tabla Procesada: {tabla.ljust(20)}")
    print(f"  └─  Registros Nuevos:   {num_registros:,}")
    print(f"  └─  Tamaño del Archivo: {tamano_bytes / 1024:.2f} KB")
    print(f"  └─ ️ Duración:           {duracion_tabla:.4f} seg")
    print(f"  └─  Nueva Marca de Agua: {watermarks[tabla]}\n")

# Guardar las marcas de agua actualizadas localmente para la siguiente ejecución
with open(STATE_FILE, "w") as f:
    json.dump(watermarks, f, indent=4)

print("=" * 75)
logging.info(" ¡PIPELINE INCREMENTAL INTEGRADO AL 100% DE LA ESPECIFICACIÓN!")
