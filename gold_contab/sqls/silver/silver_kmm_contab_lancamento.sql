-- Silver: cabecalho do lancamento contabil, uma linha por num_lancamento (o bronze repete numeros; fica a versao mais recente).
-- permite_editar = 1 identifica lancamento MANUAL. Bronze = Postgres KMM (carga de 2026 em diante).
SELECT
    CAST(num_lancamento AS BIGINT) AS num_lancamento,
    max_by(data_lancamento, date_update) AS data_lancamento,
    CAST(max_by(agrupamento_id, date_update) AS BIGINT) AS agrupamento_id,
    CAST(max_by(permite_editar, date_update) AS BIGINT) AS permite_editar,
    max(date_update) AS date_update
FROM {env}_bronze.kmm_contab_contab_lancamento
GROUP BY num_lancamento
