-- Silver: plano de contas KMM, uma linha por cod_reduzido (a versao mais recente; a carga completa do bronze vem duplicada).
SELECT
    CAST(cod_reduzido AS BIGINT) AS cod_reduzido,
    classificacao,
    CAST(regexp_replace(classificacao, '[.]', '') AS BIGINT) AS num_conta,
    descricao,
    CAST(nivel AS BIGINT) AS nivel,
    natureza_conta,
    tipo_conta,
    CAST(permite_lanc_manual AS BIGINT) AS permite_lanc_manual
FROM (
    SELECT
        cod_reduzido,
        max_by(classificacao, date_update) AS classificacao,
        max_by(descricao, date_update) AS descricao,
        max_by(nivel, date_update) AS nivel,
        max_by(natureza_conta, date_update) AS natureza_conta,
        max_by(tipo_conta, date_update) AS tipo_conta,
        max_by(permite_lanc_manual, date_update) AS permite_lanc_manual
    FROM {env}_bronze.kmm_contab_plano_contas
    GROUP BY cod_reduzido
)
