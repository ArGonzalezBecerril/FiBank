import os
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from faker import Faker
from sqlalchemy import create_engine
import logging
import calendar

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

FAKER_SEED = 42
random.seed(FAKER_SEED)
np.random.seed(FAKER_SEED)
fake = Faker(['es_MX', 'es_CO'])
Faker.seed(FAKER_SEED)

START_DATE = datetime(2025, 6, 1)
END_DATE = datetime(2026, 6, 1) # 12 meses de histórico uniforme

logging.info("🚀 Iniciando generación de datos sintéticos realistas para FinBank S.A...")

def random_date(start, end):
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

# ---- TABLA 1: TB_SUCURSALES_RED (200 registros) ----
logging.info("🔹 Generando TB_SUCURSALES_RED...")
ciudades = [
    ("Bogotá", "Cundinamarca", 4.7110, -74.0721),
    ("Ciudad de México", "CDMX", 19.4326, -99.1332),
    ("Lima", "Lima", -12.0464, -77.0428),
    ("Santiago", "Metropolitana", -33.4489, -70.6693),
    ("Buenos Aires", "CABA", -34.6037, -58.3816)
]

sucursales_data = []
for i in range(1, 201):
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

# ---- TABLA 2: TB_PRODUCTOS_CAT (50 registros) ----
logging.info("🔹 Generando TB_PRODUCTOS_CAT...")
tipos_producto = [
    ("Credito Consumo", "credito", 0.28, 36, 50000),
    ("Tarjeta Digital", "credito", 0.34, 12, 0),
    ("Cuenta de Ahorros", "ahorro", 0.10, 0, 0),
    ("Transferencia ACH", "transaccional", 0.0, 0, 0),
    ("Pago PSE", "transaccional", 0.0, 0, 0)
]
productos_data = []
for i in range(1, 51):
    tp = random.choice(tipos_producto)
    productos_data.append({
        "cod_prod": f"PROD_{i:02d}",
        "desc_prod": f"{tp[0]} Premium v{i}",
        "tip_prod": tp[1],
        "tasa_ea": tp[2] if tp[1] == "credito" or tp[1] == "ahorro" else 0.0,
        "plazo_max_meses": tp[3],
        "cuota_min": tp[4],
        "comision_admin": random.choice([0.0, 5000.0, 12000.0]),
        "estado_prod": "Activo"
    })
df_productos = pd.DataFrame(productos_data)

# ---- TABLA 3: TB_CLIENTES_CORE (10,000 registros) ----
logging.info("🔹 Generando TB_CLIENTES_CORE...")
clientes_data = []
for i in range(1, 10001):
    fec_nac = fake.date_of_birth(minimum_age=18, maximum_age=75)
    fec_alta = random_date(START_DATE, END_DATE)
    
    # Inclusión intencional de 5% de Nulos Controlados en score_buro (Requisito Prueba)
    score_buro = int(np.random.normal(650, 100))
    score_buro = max(300, min(850, score_buro))
    if random.random() < 0.05:
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

# ---- TABLA 4: TB_OBLIGACIONES (30,000 registros) ----
logging.info("🔹 Generando TB_OBLIGACIONES...")
prods_credito = df_productos[df_productos['tip_prod'] == 'credito']['cod_prod'].tolist()
obligaciones_data = []
for i in range(1, 30001):
    fec_desemb = random_date(START_DATE, END_DATE)
    venc_meses = random.choice([6, 12, 24, 36])
    fec_venc = fec_desemb + timedelta(days=venc_meses * 30)
    
    # Anomalía Intencional 1: 1% de registros con fecha de vencimiento anterior al desembolso
    if random.random() < 0.01:
        fec_venc = fec_desemb - timedelta(days=random.randint(1, 30))
        
    vr_aprobado = round(random.uniform(500000, 50000000), 2)
    sdo_capital = round(vr_aprobado * random.uniform(0, 1), 2)
    dias_mora = random.choices([0, random.randint(1, 30), random.randint(31, 90), random.randint(91, 180)], weights=[0.80, 0.12, 0.05, 0.03])[0]
    
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

# ---- TABLA 5: TB_MOV_FINANCIEROS (500,000 registros) ----
logging.info("🔹 Generando TB_MOV_FINANCIEROS (Concentración en Quincenas)...")
movimientos_data = []
canales = ["APP", "WEB", "CORRESPONSAL"]

dates_pool = []
current_ptr = START_DATE
while current_ptr <= END_DATE:
    ultimo_dia_mes = calendar.monthrange(current_ptr.year, current_ptr.month)[1]
    if current_ptr.day in [15, ultimo_dia_mes]:
        # Mayor probabilidad de transacciones en días de pago
        for _ in range(3): 
            dates_pool.append(current_ptr)
    dates_pool.append(current_ptr)
    current_ptr += timedelta(days=1)

for i in range(1, 50001): # Bloque inicial base
    fec_m = random.choice(dates_pool)
    # Patrón realista horario: picos al almuerzo (12-14) y tarde (18-20)
    hra_m = random.choices(
        [f"{random.randint(12,13)}:{random.randint(10,59)}:00", f"{random.randint(18,19)}:{random.randint(10,59)}:00", f"{random.randint(8,11)}:{random.randint(10,59)}:00"],
        weights=[0.45, 0.35, 0.20]
    )[0]
    
    movimientos_data.append({
        "id_mov": f"MOV_{i:07d}",
        "id_cli": random.choice(df_clientes['id_cli']),
        "cod_prod": random.choice(df_productos['cod_prod']),
        "num_cuenta": f"CTA-{random.randint(100000, 999999)}",
        "fec_mov": fec_m.date(),
        "hra_mov": hra_m,
        "vr_mov": round(np.random.exponential(150000), 2), # La mayoría montos bajos, pocos muy altos
        "tip_mov": random.choice(["DEBITO", "CREDITO"]),
        "cod_canal": random.choice(canales),
        "cod_ciudad": random.choice(df_sucursales['ciudad']),
        "cod_estado_mov": random.choices(["APROBADA", "RECHAZADA"], weights=[0.97, 0.03])[0],
        "id_dispositivo": f"DEV_{random.randint(1000, 9999)}"
    })

df_movimientos = pd.DataFrame(movimientos_data)

# Replicar hasta llegar a los 500k registros manteniendo integridad
logging.info("✨ Multiplicando registros de transacciones para cumplir volumen de 500k...")
df_movimientos = pd.concat([df_movimientos] * 10, ignore_index=True)
df_movimientos['id_mov'] = [f"MOV_{x:07d}" for x in range(1, len(df_movimientos) + 1)]

# Anomalía Intencional 2: 0.5% de registros duplicados exactos (Requisito Prueba)
logging.info("⚠️ Inyectando duplicados exactos controlados...")
duplicados = df_movimientos.sample(frac=0.005, random_state=42)
df_movimientos = pd.concat([df_movimientos, duplicados], ignore_index=True)

# ---- TABLA 6: TB_COMISIONES_LOG (80,000 registros) ----
logging.info("🔹 Generando TB_COMISIONES_LOG...")
comisiones_data = []
for i in range(1, 80001):
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

# ---- ENVIAR A POSTGRESQL (DOCKER) ----
logging.info("🔌 Conectando a la base de datos relacional local en Docker...")
DB_URL = "postgresql://postgres:postgres@localhost:5433/dataknow"

try:
    engine = create_engine(DB_URL)
    
    logging.info("📥 Cargando TB_SUCURSALES_RED...")
    df_sucursales.to_sql("tb_sucursales_red", engine, if_exists="replace", index=False)
    
    logging.info("📥 Cargando TB_PRODUCTOS_CAT...")
    df_productos.to_sql("tb_productos_cat", engine, if_exists="replace", index=False)
    
    logging.info("📥 Cargando TB_CLIENTES_CORE...")
    df_clientes.to_sql("tb_clientes_core", engine, if_exists="replace", index=False)
    
    logging.info("📥 Cargando TB_OBLIGACIONES...")
    df_obligaciones.to_sql("tb_obligaciones", engine, if_exists="replace", index=False)
    
    logging.info("📥 Cargando TB_MOV_FINANCIEROS (Chunking optimizado)...")
    df_movimientos.to_sql("tb_mov_financieros", engine, if_exists="replace", index=False, chunksize=50000)
    
    logging.info("📥 Cargando TB_COMISIONES_LOG...")
    df_comisiones.to_sql("tb_comisiones_log", engine, if_exists="replace", index=False, chunksize=40000)
    
    logging.info("🏆 ¡Fase 1 Completada con éxito en tu entorno local!")
    
except Exception as e:
    logging.info(f"❌ Error al conectar o insertar en Postgres. ¿Ya ejecutaste `docker-compose up -d`?\nDetalle: {e}")

