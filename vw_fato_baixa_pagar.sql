-- =====================================================================
-- hml_gold.vw_fato_baixa_pagar  -> uma linha por BAIXA (amortizacao) de titulo a pagar
--   Fonte: prd_bronze.kmm_finan_finan_contas_pagar_amort (baixas do KMM)
--   Atributos do titulo (emissao, tipo, cliente do custo, fornecedor, filial) vem de hml_gold.vw_fato_titulo_pagar,
--   que ja le as tabelas prd_bronze e a conciliacao.
-- Para responder: "quanto paguei em cada mes, e de que mes de emissao do titulo era esse pagamento?"
--   situacao_baixa = REALIZADA (data <= hoje) ou PROGRAMADA (baixa lancada com data futura, ainda nao paga).
-- Estornadas ficam de fora (data_estorno IS NULL), como no resto das views de titulos.
-- =====================================================================
CREATE OR REPLACE VIEW hml_gold.vw_fato_baixa_pagar AS
SELECT
    CAST(a.contas_pagar_id AS bigint)                          AS contas_pagar_id,
    DATE(a.data_amortizacao)                                   AS data_baixa,
    date_format(a.data_amortizacao, '%Y-%m')                   AS mes_baixa,
    CAST(a.valor_amortizacao AS double)                        AS valor_baixa,
    CASE WHEN DATE(a.data_amortizacao) <= current_date THEN 'REALIZADA' ELSE 'PROGRAMADA' END AS situacao_baixa,
    v.data_emissao                                             AS data_emissao_titulo,
    date_format(v.data_emissao, '%Y-%m')                       AS mes_emissao_titulo,
    v.data_vencto,
    v.data_previsao,
    v.num_docto, v.parc_docto,
    v.tipo_docto, v.tipo_docto_descricao,
    v.cliente_custo,
    v.fornecedor, v.filial,
    v.valor_titulo
FROM prd_bronze.kmm_finan_finan_contas_pagar_amort a
JOIN hml_gold.vw_fato_titulo_pagar v ON v.contas_pagar_id = CAST(a.contas_pagar_id AS bigint)
WHERE a.data_estorno IS NULL
