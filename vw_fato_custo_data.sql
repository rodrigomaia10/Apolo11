-- =====================================================================
-- hml_gold.vw_fato_custo_data -> custo dos contratos de frete (titulos a pagar ligados a cliente) por DATA DO CUSTO
-- Regra (13/10/2026, definida pelo usuario):
--   * baixa com data MENOR que hoje            -> PAGO      , data = data da baixa
--   * baixa com data de hoje em diante         -> PREVISTO  , data = a propria data da baixa programada
--   * titulo (ou parte dele) sem baixa         -> PREVISTO  , data = data de previsao do titulo
--   * liquidado por desconto / ajuste (sem $)  -> LIQUIDADO POR DESCONTO, data = vencimento do titulo
-- Fontes: prd_bronze.kmm_finan_finan_contas_pagar_amort (baixas) + hml_gold.vw_fato_titulo_pagar (titulo e cliente do custo).
-- A soma das linhas de um titulo = valor do titulo (quando ha juro maior que desconto, as baixas podem passar do titulo).
-- =====================================================================
CREATE OR REPLACE VIEW hml_gold.vw_fato_custo_data AS
WITH t AS (
    SELECT contas_pagar_id, cliente_custo, tipo_docto, tipo_docto_descricao, fornecedor, filial,
           data_emissao, data_vencto, data_previsao, valor_titulo, valor_juro, valor_desconto
    FROM hml_gold.vw_fato_titulo_pagar
    WHERE cliente_custo IS NOT NULL
),
b AS (
    SELECT CAST(contas_pagar_id AS bigint) AS contas_pagar_id, DATE(data_amortizacao) AS data_baixa, valor_amortizacao AS valor
    FROM prd_bronze.kmm_finan_finan_contas_pagar_amort
    WHERE data_estorno IS NULL
),
p AS (
    SELECT contas_pagar_id,
           SUM(CASE WHEN data_baixa <  current_date THEN valor ELSE 0 END) AS pago,
           SUM(CASE WHEN data_baixa >= current_date THEN valor ELSE 0 END) AS programado
    FROM b GROUP BY contas_pagar_id
),
base AS (
    SELECT t.*, COALESCE(p.pago, 0) AS pago, COALESCE(p.programado, 0) AS programado,
           GREATEST(t.valor_titulo + t.valor_juro - t.valor_desconto - COALESCE(p.pago, 0) - COALESCE(p.programado, 0), 0) AS aberto_sem_baixa
    FROM t LEFT JOIN p ON p.contas_pagar_id = t.contas_pagar_id
),
f AS (
    -- 1 e 2: cada baixa na sua data
    SELECT t.contas_pagar_id, CASE WHEN b.data_baixa < current_date THEN 'PAGO' ELSE 'PREVISTO' END AS situacao,
           CASE WHEN b.data_baixa < current_date THEN 'baixa realizada' ELSE 'baixa programada' END AS origem,
           b.data_baixa AS data_custo, CAST(b.valor AS double) AS valor, t.contas_pagar_id AS k
    FROM t JOIN b ON b.contas_pagar_id = t.contas_pagar_id
    UNION ALL
    -- 3: saldo sem baixa, na data de previsao
    SELECT contas_pagar_id, 'PREVISTO', 'saldo sem baixa', data_previsao, CAST(aberto_sem_baixa AS double), contas_pagar_id
    FROM base WHERE aberto_sem_baixa > 0.005
    UNION ALL
    -- 4: liquidado por desconto/ajuste (valor do titulo que nao virou baixa nem saldo), no vencimento
    SELECT contas_pagar_id, 'LIQUIDADO POR DESCONTO', 'desconto/ajuste', data_vencto,
           CAST(GREATEST(valor_titulo - (pago + programado + aberto_sem_baixa), 0) AS double), contas_pagar_id
    FROM base WHERE GREATEST(valor_titulo - (pago + programado + aberto_sem_baixa), 0) > 0.005
)
SELECT f.contas_pagar_id, f.situacao, f.origem, f.data_custo, date_format(f.data_custo, '%Y-%m') AS mes_custo, f.valor,
       CASE WHEN f.situacao = 'PREVISTO' AND f.data_custo < current_date THEN 'SIM' ELSE 'NAO' END AS previsto_atrasado,
       t.cliente_custo, t.tipo_docto, t.tipo_docto_descricao, t.fornecedor, t.filial,
       t.data_emissao AS data_emissao_titulo, date_format(t.data_emissao, '%Y-%m') AS mes_emissao_titulo,
       t.data_vencto, t.data_previsao, t.valor_titulo
FROM f JOIN t ON t.contas_pagar_id = f.contas_pagar_id
