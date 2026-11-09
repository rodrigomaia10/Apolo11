-- Silver: pessoa (KSS), uma linha por cod_pessoa (estado atual: a carga completa do bronze pode vir repetida).
SELECT
    CAST(cod_pessoa AS BIGINT) AS cod_pessoa,
    first(cnpj_cpf) AS cnpj_cpf,
    first(razao_social) AS razao_social,
    first(cliente) AS cliente
FROM {env}_bronze.kmm_kss_pessoa
WHERE cod_pessoa IS NOT NULL
GROUP BY CAST(cod_pessoa AS BIGINT)
