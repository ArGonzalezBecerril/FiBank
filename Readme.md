# FinBank Data Pipeline - Arquitectura Medallón con dbt & AWS Athena

Este proyecto implementa una solución de ingeniería de datos de extremo a extremo (End-to-End) para el procesamiento, limpieza y análisis de la información financiera de **FinBank** (Escenario A). La arquitectura sigue el patrón **Medallón (Bronze, Silver y Gold)**, garantizando la calidad del dato, seguridad de la información (PII) e integridad referencial utilizando herramientas modernas y declarativas.

---

## 🛠️ Stack Tecnológico
*   **Infraestructura como Código (IaC):** Terraform (Creación automatizada de Buckets S3 y roles).
*   **Orquestación y Procesamiento Local:** Python 3 (Script de simulación de datos sintéticos inyectados a PostgreSQL local).
*   **Motor de Consultas y Almacenamiento Cloud:** AWS S3, AWS Glue (Data Catalog) y AWS Athena (Motor Trino).
*   **Transformación de Datos:** dbt (Data Build Tool) v1.8.7 con el adaptador `dbt-athena-community`.

---

## 📐 Arquitectura de Datos (Patrón Medallón)

El pipeline centraliza el procesamiento en el catálogo de AWS Glue `finbank_dev_catalog` optimizando el almacenamiento en archivos **Parquet particionados** en S3:

### 1. Capa Bronze (Raw Data)
Ingección directa de los sistemas origen mediante archivos binarios Parquet. Las tablas se registran de forma externa en el Data Catalog apuntando a las rutas correspondientes:
*   `tb_clientes_core`
*   `tb_mov_financieros`
*   `tb_comisiones_log`

### 2. Capa Silver (Clean & Conformed)
En esta capa se aplican reglas estrictas de limpieza, tipado de datos compatible con Hive y seguridad de la información:
*   **Seguridad y Enmascaramiento PII:** Criptografía irreversible mediante funciones hashing **SHA-256** (`to_hex(sha256(to_utf8(...)))`) sobre los campos sensibles de identidad del cliente (`nomb_cli`, `apell_cli`, `num_doc`), cumpliendo con normativas globales de protección de datos.
*   **Aislamiento y Gestión de Errores:** Implementación de un filtro estricto de integridad referencial. Las comisiones válidas se mueven a `silver_comisiones_clean`, mientras que los registros huérfanos se aíslan automáticamente en la tabla de excepciones `silver_comisiones_errors` para su posterior auditoría.

### 3. Capa Gold (Business & Dimensional)
Modelado dimensional en estrella (`dim_` y `fact_`) optimizado para herramientas de BI (como PowerBI):
*   **Motor de Detección de Fraude (Anomalías):** Cálculo estadístico avanzado implementado de forma nativa en AWS Athena mediante funciones analíticas de ventana. El flag `ind_sospechoso` se calcula evaluando si el monto actual supera en **más de 3 desviaciones estándar** el promedio de los **últimos 30 días** del mismo cliente.
*   *Optimización Senior:* Se migró el cálculo de un enfoque tradicional basado en registros (`ROWS`) a un enfoque basado en rangos de tiempo temporales reales (`RANGE BETWEEN INTERVAL '30' DAY PRECEDING...`), resolviendo con exactitud matemática el requerimiento de negocio.

---

## 🧪 Pruebas de Calidad del Dato (dbt Data Tests)

Para asegurar la robustez de la data antes de ser expuesta a negocio, se implementaron **7 pruebas automatizadas** en la capa Silver que validan la calidad en cada ejecución:
*   `unique`: Garantiza la unicidad de las llaves primarias en clientes, comisiones y movimientos financieros.
*   `not_null`: Asegura la ausencia de valores nulos en columnas críticas de negocio.
*   `relationships`: Certifica la integridad referencial de los movimientos financieros con la tabla maestra de clientes.

---

## 🚀 Instrucciones de Ejecución

### Prerrequisitos
Tener configuradas tus credenciales de AWS localmente (`~/.aws/credentials`) y el archivo `~/.dbt/profiles.yml` apuntando al `s3_staging_dir` de Athena.

### Ejecución del Pipeline Completo
Para limpiar el caché, compilar y ejecutar los 7 modelos de forma secuencial con un paralelismo de 4 hilos (threads):
```bash
dbt clean
dbt run
```

### Ejecución de Pruebas de Calidad
Para correr la suite de pruebas automatizadas:
```bash
dbt test --select models/silver
```

---

## 📈 Rendimiento y Resultados
El pipeline procesa de manera eficiente **medio millón de registros (500,000 transacciones)** en la tabla de hechos financieros y **10,000 registros de clientes** en un tiempo récord de **2 minutos y 46 segundos**, demostrando la alta escalabilidad del diseño de consultas en AWS Athena.
