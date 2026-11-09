-- Silver: vinculo centro de custo x pessoa do organograma (KSS), uma linha por par distinto.
SELECT DISTINCT
    CAST(cod_centro_custo AS BIGINT) AS cod_centro_custo,
    CAST(cod_pessoa AS BIGINT) AS cod_pessoa
FROM {env}_bronze.kmm_kss_organograma
WHERE cod_centro_custo IS NOT NULL AND cod_pessoa IS NOT NULL
