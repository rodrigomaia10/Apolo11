-- Ponte: agrupamento contabil -> documento (CT-e, NF E/S). Une fato_contab_item (agrupamento_id) ao documento e, dai, a carga.
-- Ligacao deterministica (sem texto do historico). Grao: tipo_documento x documento x agrupamento (lancamento e estorno em linhas separadas).
SELECT tipo_documento, documento_id, agrupamento_id, 0 AS eh_estorno, num_documento, data_emissao, tomador_id,
       solicitacao_carga_id, cancelado, motivo_substituicao_id, motivo_cancelamento_id
FROM {env}_silver.kmm_fiscal_documento_contab
WHERE agrupamento_id IS NOT NULL
UNION ALL
SELECT tipo_documento, documento_id, agrupamento_id_estorno, 1, num_documento, data_emissao, tomador_id,
       solicitacao_carga_id, cancelado, motivo_substituicao_id, motivo_cancelamento_id
FROM {env}_silver.kmm_fiscal_documento_contab
WHERE agrupamento_id_estorno IS NOT NULL
