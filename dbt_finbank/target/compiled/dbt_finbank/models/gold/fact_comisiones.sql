

SELECT
    id_comision,
    id_cli,
    cod_prod,
    fec_cobro,
    vr_comision AS monto_comision,
    tip_comision,
    estado_cobro
FROM "AwsDataCatalog"."finbank_dev_catalog"."silver_comisiones_clean"