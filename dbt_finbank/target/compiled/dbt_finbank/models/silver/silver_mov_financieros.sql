

SELECT DISTINCT
    CAST(id_mov AS VARCHAR) AS id_mov,
    CAST(id_cli AS VARCHAR) AS id_cli,
    CAST(cod_prod AS VARCHAR) AS cod_prod,
    CAST(num_cuenta AS VARCHAR) AS num_cuenta,
    CAST(fec_mov AS DATE) AS fec_mov,
    CAST(hra_mov AS VARCHAR) AS hra_mov,
    CAST(vr_mov AS DOUBLE) AS vr_mov,
    CAST(tip_mov AS VARCHAR) AS tip_mov,
    CAST(cod_canal AS VARCHAR) AS cod_canal,
    CAST(cod_ciudad AS VARCHAR) AS cod_ciudad,
    CAST(cod_estado_mov AS VARCHAR) AS cod_estado_mov,
    CAST(id_dispositivo AS VARCHAR) AS id_dispositivo,
    CAST(current_timestamp AS TIMESTAMP) AS audit_silver_timestamp
FROM "AwsDataCatalog"."finbank_dev_catalog"."tb_mov_financieros"
WHERE id_mov IS NOT NULL