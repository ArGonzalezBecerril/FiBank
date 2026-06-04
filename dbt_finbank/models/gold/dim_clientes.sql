{{ config(
    materialized='table',
    s3_data_naming='table_unique'
) }}

SELECT
    id_cli,
    num_doc_hash,
    -- Jalamos los hashes reales que generaste en la capa plata
    nomb_cli_hash,
    apell_cli_hash,
    tip_doc,
    fec_nac,
    score_buro,
    ciudad_res,
    depto_res,
    estado_cli,
    canal_adquis,
    CAST(current_timestamp AS TIMESTAMP) AS fecha_carga_oro
FROM {{ ref('silver_clientes') }}
