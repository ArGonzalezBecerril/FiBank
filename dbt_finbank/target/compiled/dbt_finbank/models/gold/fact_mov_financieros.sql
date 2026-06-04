

WITH base_silver AS (
    SELECT
        id_mov,
        id_cli,
        cod_prod,
        num_cuenta,
        fec_mov,
        hra_mov,
        vr_mov,
        tip_mov,
        cod_canal,
        cod_ciudad,
        cod_estado_mov,
        id_dispositivo,
        -- Calculamos promedio y desviación estándar de los movimientos del cliente
       AVG(vr_mov) OVER(
            PARTITION BY id_cli
            ORDER BY CAST(fec_mov AS DATE)
            RANGE BETWEEN INTERVAL '30' DAY PRECEDING AND INTERVAL '1' DAY PRECEDING
        ) AS avg_monto_30d,
        STDDEV(vr_mov) OVER(
            PARTITION BY id_cli
            ORDER BY CAST(fec_mov AS DATE)
            RANGE BETWEEN INTERVAL '30' DAY PRECEDING AND INTERVAL '1' DAY PRECEDING
        ) AS stddev_monto_30d
    FROM "AwsDataCatalog"."finbank_dev_catalog"."silver_mov_financieros"
)

SELECT
    id_mov,
    id_cli,
    cod_prod,
    num_cuenta,
    fec_mov,
    hra_mov,
    vr_mov AS monto_movimiento,
    tip_mov,
    cod_canal,
    cod_ciudad,
    cod_estado_mov,
    id_dispositivo,
    -- Regla de Negocio Estricta: Si supera 3 desviaciones estándar del promedio, es sospechoso
    CASE
        WHEN vr_mov > (avg_monto_30d + (3 * COALESCE(stddev_monto_30d, 0))) THEN 1
        ELSE 0
    END AS ind_sospechoso,
    CAST(current_timestamp AS TIMESTAMP) AS fecha_carga_oro
FROM base_silver