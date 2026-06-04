{{ config(materialized='table', s3_data_naming='table_unique') }}

SELECT DISTINCT
    CAST(id_cli AS VARCHAR) AS id_cli,
    -- Criptografía SHA-256 para enmascarar información personal (PII)
    to_hex(sha256(to_utf8(CAST(nomb_cli AS VARCHAR)))) AS nomb_cli_hash,
    to_hex(sha256(to_utf8(CAST(apell_cli AS VARCHAR)))) AS apell_cli_hash,
    CAST(tip_doc AS VARCHAR) AS tip_doc,
    to_hex(sha256(to_utf8(CAST(num_doc AS VARCHAR)))) AS num_doc_hash,
    CAST(fec_nac AS DATE) AS fec_nac,
    CAST(fec_alta AS TIMESTAMP) AS fec_alta,
    CAST(cod_segmento AS VARCHAR) AS cod_segmento,
    -- Estrategia de Nulos: Imputación con valor por defecto (-1) como indicador binario
    COALESCE(CAST(score_buro AS INTEGER), -1) AS score_buro,
    CAST(ciudad_res AS VARCHAR) AS ciudad_res,
    CAST(depto_res AS VARCHAR) AS depto_res,
    CAST(estado_cli AS VARCHAR) AS estado_cli,
    CAST(canal_adquis AS VARCHAR) AS canal_adquis,
    CAST(current_timestamp AS TIMESTAMP) AS audit_silver_timestamp
FROM {{ source('bronze_layer', 'clientes') }}
WHERE id_cli IS NOT NULL