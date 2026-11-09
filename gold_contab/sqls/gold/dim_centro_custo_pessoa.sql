-- Centro de custo x pessoa do organograma KSS: 1 linha por par (um centro de custo pode ter varias pessoas).
-- Substitui a consulta ODBC kss.centro_custo x organograma x pessoa da d_Filial do BI gerencial. sk_centro_custo = cod_centro_custo.
SELECT
    CAST(-1 AS BIGINT) AS sk_centro_custo,
    CAST(-1 AS BIGINT) AS cod_pessoa,
    'NAO IDENTIFICADO' AS centro_custo,
    'NAO IDENTIFICADO' AS cnpj_cpf,
    'NAO IDENTIFICADO' AS cliente
UNION ALL
SELECT
    cc.cod_centro_custo AS sk_centro_custo,
    p.cod_pessoa,
    cc.centro_custo,
    p.cnpj_cpf,
    p.cliente
FROM {env}_silver.kmm_centro_custo cc
JOIN {env}_silver.kmm_organograma o ON o.cod_centro_custo = cc.cod_centro_custo
JOIN {env}_silver.kmm_pessoa p ON p.cod_pessoa = o.cod_pessoa
