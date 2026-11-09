-- Origem da contabilizacao. Lancamento sem agrupamento (ex.: manuais) cai no membro -1 '(sem origem)'.
SELECT
    CAST(-1 AS INT) AS sk_origem,
    CAST(NULL AS STRING) AS cod_origem,
    '(sem origem)' AS origem
UNION ALL
SELECT
    CAST(ROW_NUMBER() OVER (ORDER BY cod_origem) AS INT) AS sk_origem,
    cod_origem,
    descricao AS origem
FROM {env}_silver.kmm_contab_origem
