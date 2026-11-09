-- Silver: centro de custo (KSS), uma linha por codigo; nome original e nome sem o prefixo numerico.
SELECT
    CAST(cod_centro_custo AS BIGINT) AS cod_centro_custo,
    first(centro_custo) AS centro_custo_original,
    regexp_replace(first(centro_custo), '^[0-9]+ - ', '') AS centro_custo
FROM {env}_bronze.kmm_kss_centro_custo
WHERE cod_centro_custo IS NOT NULL
GROUP BY CAST(cod_centro_custo AS BIGINT)
