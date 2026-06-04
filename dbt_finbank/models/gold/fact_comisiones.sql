{{ config(
    materialized='table',
    s3_data_naming='table_unique'
) }}

SELECT
    id_comision,
    id_cli,
    cod_prod,
    fec_cobro,
    vr_comision AS monto_comision,
    tip_comision,
    estado_cobro
FROM {{ ref('silver_comisiones_clean') }}
