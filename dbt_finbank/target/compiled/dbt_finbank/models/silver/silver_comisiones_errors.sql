

SELECT
    CAST(c.id_comision AS VARCHAR) AS id_comision,
    CAST(c.id_cli AS VARCHAR) AS id_cli,
    CAST(c.cod_prod AS VARCHAR) AS cod_prod,
    CAST(c.fec_cobro AS DATE) AS fec_cobro,
    CAST(c.vr_comision AS DOUBLE) AS vr_comision,
    CAST(c.tip_comision AS VARCHAR) AS tip_comision,
    CAST(c.estado_cobro AS VARCHAR) AS estado_cobro,
    'Integridad Referencial Violada: id_cli no existe en Core de Clientes' AS motivo_rechazo,
    CAST(current_timestamp AS TIMESTAMP) AS audit_silver_timestamp
FROM "AwsDataCatalog"."finbank_dev_catalog"."tb_comisiones_log" c
LEFT JOIN "AwsDataCatalog"."finbank_dev_catalog"."dim_clientes" cl ON c.id_cli = cl.id_cli
WHERE cl.id_cli IS NULL -- Captura lo que se quedó fuera del cruce