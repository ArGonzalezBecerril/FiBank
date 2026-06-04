{{ config(materialized='table', s3_data_naming='table_unique') }}

SELECT
    CAST(c.id_comision AS VARCHAR) AS id_comision,
    CAST(c.id_cli AS VARCHAR) AS id_cli,
    CAST(c.cod_prod AS VARCHAR) AS cod_prod,
    CAST(c.fec_cobro AS DATE) AS fec_cobro,
    CAST(c.vr_comision AS DOUBLE) AS vr_comision,
    CAST(c.tip_comision AS VARCHAR) AS tip_comision,
    CAST(c.estado_cobro AS VARCHAR) AS estado_cobro,
    CAST(current_timestamp AS TIMESTAMP) AS audit_silver_timestamp
FROM {{ source('bronze_layer', 'comisiones') }} c
LEFT JOIN {{ ref('dim_clientes') }} cl ON c.id_cli = cl.id_cli
