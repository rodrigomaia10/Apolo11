-- Silver: documentos fiscais que geram lancamento contabil (CT-e e NF E/S), uma linha por documento (estado atual),
-- com o agrupamento do lancamento e o do estorno. Marcas de cancelado/substituido ficam como vieram da origem.
-- Fonte em prd_bronze (kmm_fiscal_* ja atualizado diariamente); trocar para {env}_bronze quando houver carga nos dois ambientes.
SELECT
    'CTE' AS tipo_documento,
    CAST(conhecimento_id AS BIGINT) AS documento_id,
    CAST(max_by(num_conhecimento, date_update) AS STRING) AS num_documento,
    CAST(max_by(data_emissao, date_update) AS DATE) AS data_emissao,
    CAST(max_by(tomador_servico_id, date_update) AS BIGINT) AS tomador_id,
    CAST(max_by(solicitacao_carga_id, date_update) AS BIGINT) AS solicitacao_carga_id,
    CAST(max_by(cancelado, date_update) AS STRING) AS cancelado,
    CAST(max_by(motivo_substituicao_id, date_update) AS BIGINT) AS motivo_substituicao_id,
    CAST(max_by(motivo_cancelamento_id, date_update) AS BIGINT) AS motivo_cancelamento_id,
    CAST(max_by(contab_agrupamento_id, date_update) AS BIGINT) AS agrupamento_id,
    CAST(max_by(contab_agrupamento_estorno_id, date_update) AS BIGINT) AS agrupamento_id_estorno
FROM prd_bronze.kmm_fiscal_conhecimento
GROUP BY conhecimento_id
UNION ALL
SELECT
    'NF_ES' AS tipo_documento,
    CAST(num_nota_id AS BIGINT) AS documento_id,
    CAST(max_by(num_nota_fiscal, date_update) AS STRING) AS num_documento,
    CAST(max_by(data_emissao, date_update) AS DATE) AS data_emissao,
    CAST(NULL AS BIGINT) AS tomador_id,
    CAST(NULL AS BIGINT) AS solicitacao_carga_id,
    CAST(NULL AS STRING) AS cancelado,
    CAST(NULL AS BIGINT) AS motivo_substituicao_id,
    CAST(NULL AS BIGINT) AS motivo_cancelamento_id,
    CAST(max_by(contab_agrupamento_id, date_update) AS BIGINT) AS agrupamento_id,
    CAST(max_by(contab_agrupamento_id_estorno, date_update) AS BIGINT) AS agrupamento_id_estorno
FROM prd_bronze.kmm_fiscal_nf_es
GROUP BY num_nota_id
