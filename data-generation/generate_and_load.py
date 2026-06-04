import os
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from faker import Faker
from sqlalchemy import create_engine
import logging
import calendar
import yaml

# Configuración de logs limpia y profesional
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logging.info("Iniciando lectura de configuración YAML y preparación del entorno...")

# 1. CARGA DINÁMICA DEL ARCHIVO CONFIG.YAML
ruta_script = os.path.dirname(os.path.abspath(__file__))
ruta_yaml = os.path.join(ruta_script, "config.yaml")

try:
    with open(ruta_yaml, "r", encoding="utf-8") as archivo:
        config = yaml.safe_load(archivo)
    logging.info("Configuración YAML cargada exitosamente.")
except Exception as e:
    logging.error(f"Error crítico al cargar el archivo YAML: {e}")
    raise

# 2. ASIGNACIÓN DE PARÁMETROS GENERALES
FAKER_SEED = config["generation_params"]["seed"]
START_DATE = datetime.strptime(config["generation_params"]["start_date"], "%Y-%m-%d")
END_DATE = datetime.strptime(config["generation_params"]["end_date"], "%Y-%m-%d")
NULL_RATE = config["generation_params"]["null_rate"]
ANOMALY_OBLIGACIONES = config["generation_params"]["anomaly_rate_obligaciones"]
ANOMALY_MOVIMIENTOS = config["generation_params"]["anomaly_rate_movimientos"]

# VOLÚMENES DINÁMICOS DESDE EL YAML
VOL_SUCURSALES = config["target_volumes"]["tb_sucursales_red"]
VOL_PRODUCTOS = config["target_volumes"]["tb_productos_cat"]
VOL_CLIENTES = config["target_volumes"]["tb_clientes_core"]
VOL_OBLIGACIONES = config["target_volumes"]["tb_obligaciones"]
VOL_MOVIMIENTOS = config["target_volumes"]["tb_mov_financieros"]
VOL_COMISIONES = config["target_volumes"]["tb_comisiones_log"]

# 3. CONFIGURACIÓN DE SEMILLAS PARA REPRODUCIBILIDAD ABSOLUTA
random.seed(FAKER_SEED)
np.random.seed(FAKER_SEED)
fake = Faker(['es_MX', 'es_CO'])
Faker.seed(FAKER_SEED)

def random_date(start, end):
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

# =============================================================
# ---- TABLA 1: TB_SUCURSALES_RED ----
# =============================================================
logging.info(f" Generando {VOL_SUCURSALES} registros para TB_SUCURSALES_RED...")
ciudades = [
    ("Bogotá", "Cundinamarca", 4.7110, -74.0721),
    ("Ciudad de México", "CDMX", 19.4326, -99.1332),
    ("Lima", "Lima", -12.0464, -77.0428),
    ("Santiago", "Metropolitana", -33.4489, -70.6693),
    ("Buenos Aires", "CABA", -34.6037, -58.3816)
]

sucursales_data = []
for i in range(1, VOL_SUCURSALES + 1):
    ciu = random.choice(ciudades)
    sucursales_data.append({
        "cod_suc": f"SUC_{i:03d}",
        "nom_suc": f"Sucursal {ciu[0]} Nro {i}",
        "tip_punto": random.choice(["Fisico", "Digital", "Corresponsal"]),
        "ciudad": ciu[0],
        "depto": ciu[1],
        "latitud": ciu[2] + random.uniform(-0.05, 0.05),
        "longitud": ciu[3] + random.uniform(-0.05, 0.05),
        "activo": random.choices([1, 0], weights=[0.95, 0.05])[0]
    })
df_sucursales = pd.DataFrame(sucursales_data)

# =============================================================
# ---- TABLA 2: TB_PRODUCTOS_CAT ----
# =============================================================
logging.info(f" Generando {VOL_PRODUCTOS} registros para TB_PRODUCTOS_CAT...")
tipos_producto = [
    ("Credito Consumo", "credito", 0.28, 36, 50000),
    ("Tarjeta Digital", "credito", 0.34, 12, 0),
    ("Cuenta de Ahorros", "ahorro", 0.10, 0, 0),
    ("Transferencia ACH", "transaccional", 0.0, 0, 0),
    ("Pago PSE", "transaccional", 0.0, 0, 0)
]

productos_data = []
for i in range(1, VOL_PRODUCTOS + 1):
    tp = random.choice(tipos_producto)
    productos_data.append({
        "cod_prod": f"PROD_{i:02d}",
        "desc_prod": f"{tp[0]} Premium v{i}",
        "tip_prod": tp[1],
        "tasa_ea": tp[2] if tp[1] in ["credito", "ahorro"] else 0.0,
        "plazo_max_meses": tp[3],
        "cuota_min": tp[4],
        "comision_admin": random.choice([0.0, 5000.0, 12000.0]),
        "estado_prod": "Activo"
    })
df_productos = pd.DataFrame(productos_data)

# =============================================================
# ---- TABLA 3: TB_CLIENTES_CORE ----
# =============================================================
logging.info(f" Generando {VOL_CLIENTES} registros para TB_CLIENTES_CORE...")
clientes_data = []
for i in range(1, VOL_CLIENTES + 1):
    fec_nac = fake.date_of_birth(minimum_age=18, maximum_age=75)
    fec_alta = random_date(START_DATE, END_DATE)

    # Inclusión intencional parametrizada de Nulos en score_buro
    score_buro = int(np.random.normal(650, 100))
    score_buro = max(300, min(850, score_buro))
    if random.random() < NULL_RATE:
        score_buro = None

    ciu = random.choice(ciudades)
    clientes_data.append({
        "id_cli": f"CLI_{i:06d}",
        "nomb_cli": fake.first_name(),
        "apell_cli": fake.last_name(),
        "tip_doc": random.choice(["CC", "CE", "DNI"]),
        "num_doc": str(random.randint(10000000, 999999999)),
        "fec_nac": fec_nac,
        "fec_alta": fec_alta,
        "cod_segmento": random.choices(["BAS", "STD", "PRM", "ELT"], weights=[0.50, 0.35, 0.12, 0.03])[0],
        "score_buro": score_buro,
        "ciudad_res": ciu[0],
        "depto_res": ciu[1],
        "estado_cli": random.choices(["Activo", "Inactivo", "Bloqueado"], weights=[0.92, 0.06, 0.02])[0],
        "canal_adquis": random.choice(["App", "Web", "Referido", "Campaña"])
    })
df_clientes = pd.DataFrame(clientes_data)

# =============================================================
# ---- TABLA 4: TB_OBLIGACIONES ----
# =============================================================
logging.info(f" Generando {VOL_OBLIGACIONES} registros para TB_OBLIGACIONES...")
prods_credito = df_productos[df_productos['tip_prod'] == 'credito']['cod_prod'].tolist()
obligaciones_data = []
for i in range(1, VOL_OBLIGACIONES + 1):
    fec_desemb = random_date(START_DATE, END_DATE)
    venc_meses = random.choice([6, 12, 24, 36])
    fec_venc = fec_desemb + timedelta(days=venc_meses * 30)

    # Anomalía Intencional 1: Fechas fuera de rango controlada por el YAML
    if random.random() < ANOMALY_OBLIGACIONES:
        fec_venc = fec_desemb - timedelta(days=random.randint(1, 30))

    vr_aprobado = round(random.uniform(500000, 50000000), 2)
    sdo_capital = round(vr_aprobado * random.uniform(0, 1), 2)
    dias_mora = random.choices([0, random.randint(1, 30), random.randint(31, 90), random.randint(91, 180)],
                               weights=[0.80, 0.12, 0.05, 0.03])[0]

    obligaciones_data.append({
        "id_oblig": f"OBL_{i:06d}",
        "id_cli": random.choice(df_clientes['id_cli']),
        "cod_prod": random.choice(prods_credito),
        "vr_aprobado": vr_aprobado,
        "vr_desembolsado": vr_aprobado,
        "sdo_capital": sdo_capital,
        "vr_cuota": round(vr_aprobado / venc_meses, 2),
        "fec_desembolso": fec_desemb,
        "fec_venc": fec_venc,
        "dias_mora_act": dias_mora,
        "num_cuotas_pend": random.randint(1, venc_meses),
        "calif_riesgo": "A" if dias_mora == 0 else ("B" if dias_mora <= 30 else ("C" if dias_mora <= 60 else "D"))
    })
df_obligaciones = pd.DataFrame(obligaciones_data)

# =============================================================
# ---- TABLA 5: TB_MOV_FINANCIEROS ----
# =============================================================
logging.info(f" Generando estructura base de transacciones (Concentración en Quincenas)...")
movimientos_data = []
canales = ["APP", "WEB", "CORRESPONSAL"]
dates_pool = []
current_ptr = START_DATE

while current_ptr <= END_DATE:
    ultimo_dia_mes = calendar.monthrange(current_ptr.year, current_ptr.month)[1]
    if current_ptr.day in [15, ultimo_dia_mes]:
        for _ in range(3):
            dates_pool.append(current_ptr)
    dates_pool.append(current_ptr)
    current_ptr += timedelta(days=1)

# Se define el volumen base para el bucle iterativo (10% del volumen objetivo total)
volumen_base_mov = int(VOL_MOVIMIENTOS / 10)
for i in range(1, volumen_base_mov + 1):
    fec_m = random.choice(dates_pool)
    hra_m = random.choices(
        [f"{random.randint(12, 13)}:{random.randint(10, 59)}:00",
         f"{random.randint(18, 19)}:{random.randint(10, 59)}:00",
         f"{random.randint(8, 11)}:{random.randint(10, 59)}:00"],
        weights=[0.45, 0.35, 0.20]
    )[0]

    movimientos_data.append({
        "id_mov": f"MOV_{i:07d}",
        "id_cli": random.choice(df_clientes['id_cli']),
        "cod_prod": random.choice(df_productos['cod_prod']),
        "num_cuenta": f"CTA-{random.randint(100000, 999999)}",
        "fec_mov": fec_m.date(),
        "hra_mov": hra_m,
        "vr_mov": round(np.random.exponential(150000), 2),
        "tip_mov": random.choice(["DEBITO", "CREDITO"]),
        "cod_canal": random.choice(canales),
        "cod_ciudad": random.choice(df_sucursales['ciudad']),
        "cod_estado_mov": random.choices(["APROBADA", "RECHAZADA"], weights=[0.97, 0.03])[0],
        "id_dispositivo": f"DEV_{random.randint(1000, 9999)}"
    })
df_movimientos = pd.DataFrame(movimientos_data)

if len(df_movimientos) > 0 and isinstance(df_movimientos['hra_mov'].iloc[0], list):
    df_movimientos['hra_mov'] = df_movimientos['hra_mov'].str[0]

logging.info(f"⚡ Multiplicando registros de transacciones para cumplir volumen de {VOL_MOVIMIENTOS}...")
factor_multiplicador = int(VOL_MOVIMIENTOS / volumen_base_mov)
df_movimientos = pd.concat([df_movimientos] * factor_multiplicador, ignore_index=True)
df_movimientos['id_mov'] = [f"MOV_{x:07d}" for x in range(1, len(df_movimientos) + 1)]

logging.info("🛠️ Inyectando duplicados exactos controlados desde tasa de anomalía del YAML...")
duplicados = df_movimientos.sample(frac=ANOMALY_MOVIMIENTOS, random_state=FAKER_SEED)
df_movimientos = pd.concat([df_movimientos, duplicados], ignore_index=True)

df_movimientos['fec_mov'] = df_movimientos['fec_mov'].astype(str)
df_movimientos['hra_mov'] = df_movimientos['hra_mov'].astype(str)

# =============================================================
# ---- TABLA 6: TB_COMISIONES_LOG ----
# =============================================================
logging.info(f" Generando {VOL_COMISIONES} registros para TB_COMISIONES_LOG...")
comisiones_data = []
for i in range(1, VOL_COMISIONES + 1):
    comisiones_data.append({
        "id_comision": f"COM_{i:06d}",
        "id_cli": random.choice(df_clientes['id_cli']),
        "cod_prod": random.choice(df_productos['cod_prod']),
        "fec_cobro": random_date(START_DATE, END_DATE).date(),
        "vr_comision": random.choice([0.0, 2500.0, 4800.0, 11500.0]),
        "tip_comision": random.choice(["MANTE_CUENTA", "RETIRO_CAJERO", "TRANSFERENCIA"]),
        "estado_cobro": random.choices(["COBRADO", "REVERTIDO", "PENDIENTE"], weights=[0.96, 0.01, 0.03])[0]
    })
df_comisiones = pd.DataFrame(comisiones_data)

logging.info(" Inyectando clientes huérfanos para probar tablas de rechazo...")
df_comisiones.iloc[200:400, df_comisiones.columns.get_loc("id_cli")] = "CLI_HUERFANO_999"

# =============================================================
#  EXPORTACIÓN EFECTIVA MULTIFORMATO HETEROGÉNEA
# =============================================================
logging.info(" Guardando archivos locales estructurados en la carpeta data_origen/...")
os.makedirs("data_origen", exist_ok=True)

# 1. Dimensiones en formato CSV
df_sucursales.to_csv("data_origen/TB_SUCURSALES_RED.csv", index=False)
df_productos.to_csv("data_origen/TB_PRODUCTOS_CAT.csv", index=False)
df_clientes.to_csv("data_origen/TB_CLIENTES_CORE.csv", index=False)
logging.info(" Archivos CSV de Dimensiones creados con éxito.")

# 2. Conversión forzada a strings para evitar fallas de objetos en Parquet
df_obligaciones['fec_desembolso'] = df_obligaciones['fec_desembolso'].astype(str)
df_obligaciones['fec_venc'] = df_obligaciones['fec_venc'].astype(str)
df_movimientos['fec_mov'] = df_movimientos['fec_mov'].astype(str)
df_movimientos['hra_mov'] = df_movimientos['hra_mov'].astype(str)
df_comisiones['fec_cobro'] = df_comisiones['fec_cobro'].astype(str)

# 3. Escritura limpia y directa a Parquet sin duplicidades
df_obligaciones.to_parquet("data_origen/TB_OBLIGACIONES.parquet", index=False)
df_movimientos.to_parquet("data_origen/TB_MOV_FINANCIEROS.parquet", index=False)
df_comisiones.to_parquet("data_origen/TB_COMISIONES_LOG.parquet", index=False)
logging.info(" Archivos Parquet de Hechos creados con éxito.")

# =============================================================
# 🔌 CARGA EN POSTGRESQL DESDE LAS CONFIGURACIONES DEL YAML (LIMPIO)
# =============================================================
logging.info("🔌 Conectando a la base de datos relacional parametrizada...")
db = config["database_source"]

# 🛠️ ¡Aquí quedó corregido! Toma db['user'] y db['password'] de tu archivo config.yaml de forma dinámica.
DB_URL = f"{db['engine']}://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db['database']}"

try:
    engine = create_engine(DB_URL)

    logging.info(" Cargando tb_sucursales_red...")
    df_sucursales.to_sql("tb_sucursales_red", engine, if_exists="replace", index=False)

    logging.info(" Cargando tb_productos_cat...")
    df_productos.to_sql("tb_productos_cat", engine, if_exists="replace", index=False)

    logging.info(" Cargando tb_clientes_core...")
    df_clientes.to_sql("tb_clientes_core", engine, if_exists="replace", index=False)

    logging.info(" Cargando tb_obligaciones...")
    df_obligaciones.to_sql("tb_obligaciones", engine, if_exists="replace", index=False)

    logging.info(" Cargando tb_mov_financieros (Chunking optimizado)...")
    df_movimientos.to_sql("tb_mov_financieros", engine, if_exists="replace", index=False, chunksize=50000)

    logging.info(" Cargando tb_comisiones_log...")
    df_comisiones.to_sql("tb_comisiones_log", engine, if_exists="replace", index=False, chunksize=40000)

    logging.info(" ¡Fase 1 completada con éxito de forma 100% parametrizada!")

    # AUDITORÍA AUTOMÁTICA FINAL
    print("\n" + "=" * 60)
    print(" CONTROL DE CALIDAD - RESULTADO DE SELECT COUNT(*)")
    print("=" * 60)
    tablas_check = [
        "tb_sucursales_red", "tb_productos_cat", "tb_clientes_core",
        "tb_obligaciones", "tb_mov_financieros", "tb_comisiones_log"
    ]
    with engine.connect() as connection:
        for tabla in tablas_check:
            res = connection.execute(f"SELECT COUNT(*) FROM {tabla};").fetchone()
            print(f"Tabla: {tabla.ljust(22)} | Conteo de Filas: {res[0]:,}")
    print("=" * 60 + "\n")

except Exception as e:
    logging.error(f" Error al conectar o insertar en Postgres. ¿Ya ejecutaste tu contenedor?\nDetalle: {e}")
