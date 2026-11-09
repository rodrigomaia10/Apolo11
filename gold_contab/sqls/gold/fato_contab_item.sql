-- Fato: 1 item contabil, 2026+, todas as contas. Base unica do DRE (fato_dre_contabil) e do futuro Balanco.
-- Sem historico em texto (fica na silver). Origem: lancamento.agrupamento_id -> agrupamento.cod_origem -> dim_origem_contabil (sem agrupamento = -1).
SELECT
    i.num_lancamento_it,
    i.num_lancamento,
    l.agrupamento_id,
    CAST(l.data_lancamento AS DATE) AS data_lancamento,
    date_format(l.data_lancamento, 'yyyy-MM') AS mes_lancamento,
    CAST(date_trunc('month', l.data_lancamento) AS DATE) AS data_mes,
    COALESCE(i.cod_reduzido, CAST(-1 AS BIGINT)) AS sk_conta,
    COALESCE(o.sk_origem, -1) AS sk_origem,
    COALESCE(i.cod_centro_custo, CAST(-1 AS BIGINT)) AS sk_centro_custo,
    i.valor_debito,
    i.valor_credito,
    i.valor_credito - i.valor_debito AS valor_saldo,
    CASE WHEN l.permite_editar = 1 THEN 1 ELSE 0 END AS eh_manual
FROM {env}_silver.kmm_contab_lancamento_item i
JOIN {env}_silver.kmm_contab_lancamento l ON l.num_lancamento = i.num_lancamento
LEFT JOIN {env}_silver.kmm_contab_agrupamento g ON g.agrupamento_id = l.agrupamento_id
LEFT JOIN {env}_gold.dim_origem_contabil o ON o.cod_origem = g.cod_origem
