-- Silver: origem da contabilizacao, uma linha por cod_origem (versao mais recente; carga completa vem duplicada).
SELECT
    cod_origem,
    COALESCE(NULLIF(descricao, ''), '(sem origem)') AS descricao,
    CAST(tipo AS BIGINT) AS tipo
FROM (
    SELECT
        cod_origem,
        max_by(descricao, date_update) AS descricao,
        max_by(tipo, date_update) AS tipo
    FROM {env}_bronze.kmm_contab_contabilizacao_origem
    GROUP BY cod_origem
)
