-- Centro de custo da contabilidade. sk_centro_custo = cod_centro_custo.
SELECT
    CAST(-1 AS BIGINT) AS sk_centro_custo,
    'NAO IDENTIFICADO' AS centro_custo
UNION ALL
SELECT
    cod_centro_custo AS sk_centro_custo,
    centro_custo
FROM {env}_silver.kmm_centro_custo
