-- Silver: agrupamento contabil (liga o lancamento a origem e ao documento), uma linha por agrupamento_id (versao mais recente).
SELECT
    CAST(agrupamento_id AS BIGINT) AS agrupamento_id,
    max_by(cod_origem, date_update) AS cod_origem,
    CAST(max_by(agrupamento_id_estorno, date_update) AS BIGINT) AS agrupamento_id_estorno,
    CAST(max_by(num_lancamento_contab, date_update) AS BIGINT) AS num_lancamento_contab
FROM {env}_bronze.kmm_contab_contabilizacao_agrupamento
GROUP BY agrupamento_id
