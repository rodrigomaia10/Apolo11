-- =====================================================================
-- hml_gold.vw_fato_ligacao_contabil -> liga cada linha do faturamento operacional (fato_conciliacao_multi_kmm)
--   aos lancamentos CONTABEIS do KMM: receita do CT-e/NF e custo do contrato de transporte.
-- Definida em 19/10/2026 (validada em set/26 contra o BI "INFORMACOES GERENCIAIS" / DRE).
--
-- Fonte contabil: prd_bronze.kmm_listas_contab_lancamentos_incremental (log com ~37 versoes de cada item).
--   Deduplicada por contabilizacao_id (id estavel do item; recontabilizacao gera novo num_lancamento com o mesmo
--   contabilizacao_id, como ocorre com Nota Fiscal de E/S). A tabela sem _incremental tem so 1 item por lancamento: nao usar.
-- Chaves:
--   CT-e : numero do cte (depois do "-") + CNPJ do tomador  = num_documento + cnpj_cpf_participante, origem "Conhecimento de Transporte"
--   NF/ND: numero (depois do "-") + CNPJ do tomador         = num_documento + cnpj_cpf_participante, origem "Nota Fiscal de E/S"
--   Nos dois casos o MES do lancamento tem que ser o mes da emissao (o mesmo numero se repete entre series/meses).
--   Contrato: contrato = ID entre colchetes no historico ("CT COOPERADO PJ 295304 [228241]"), origem "Contrato de Transporte"
-- Valores: receita = creditos - debitos da conta 3.1.1.01*; custo = debitos - creditos da conta 3.1.2.05*.
-- O mesmo contrato/chave aparece em varias linhas da conciliacao: o total vem em *_documento/*_contrato e o valor
--   RATEADO (total / qtd de linhas com a mesma chave) em *_rateada, que pode ser somado sem duplicar.
-- Lancamentos contabeis disponiveis a partir de 01/05/2026.
-- =====================================================================
CREATE OR REPLACE VIEW hml_gold.vw_fato_ligacao_contabil AS
WITH contab AS (
    SELECT contabilizacao_id,
           arbitrary(origem_descricao) AS origem,
           arbitrary(classificacao)    AS classificacao,
           arbitrary(CAST(num_documento AS varchar)) AS num_documento,
           arbitrary(regexp_replace(CAST(cnpj_cpf_participante AS varchar), '[^0-9]', '')) AS cnpj,
           arbitrary(regexp_extract(historico, '\[(\d+)\]', 1)) AS contrato_hist,
           arbitrary(valor_credito) AS cr,
           arbitrary(valor_debito)  AS db,
           arbitrary(date_format(data_lancamento, '%Y-%m')) AS mes_lanc
    FROM prd_bronze.kmm_listas_contab_lancamentos_incremental
    WHERE origem_descricao IN ('Conhecimento de Transporte', 'Nota Fiscal de E/S', 'Contrato de Transporte', 'Contrato de Transporte - Item')
      AND (classificacao LIKE '3.1.1.01%' OR classificacao LIKE '3.1.2.05%'
           OR classificacao IN ('3.1.1.02.00001', '3.1.1.02.00002', '3.1.1.02.00003', '3.1.1.02.00006', '3.1.1.02.00008', '3.1.1.02.00011', '3.1.1.02.00013', '3.1.1.02.00015'))
    GROUP BY contabilizacao_id
),
rec AS (
    SELECT CASE WHEN origem = 'Conhecimento de Transporte' THEN 'CT-e' ELSE 'NF' END AS tipo_analise,
           num_documento AS num, cnpj, mes_lanc,
           SUM(CASE WHEN classificacao LIKE '3.1.1.01%' THEN cr - db END) AS receita_contabil,
           SUM(CASE WHEN classificacao LIKE '3.1.1.01%' THEN 1 ELSE 0 END) AS itens_receita,
           -- deducoes da receita (ICMS, credito presumido, ISS, PIS/COFINS) lancadas no proprio documento; valor negativo, como no DRE
           SUM(CASE WHEN classificacao LIKE '3.1.1.02%' THEN cr - db ELSE 0 END) AS deducoes_contabeis
    FROM contab
    WHERE (classificacao LIKE '3.1.1.01%' OR classificacao LIKE '3.1.1.02%') AND origem IN ('Conhecimento de Transporte', 'Nota Fiscal de E/S')
    GROUP BY 1, 2, 3, 4
),
cst AS (
    SELECT contrato_hist AS contrato,
           SUM(CASE WHEN origem = 'Contrato de Transporte'        THEN db - cr ELSE 0 END) AS custo_contrato,
           SUM(CASE WHEN origem = 'Contrato de Transporte - Item' THEN db - cr ELSE 0 END) AS custo_contrato_item,
           COUNT(*) AS itens_custo
    FROM contab
    WHERE classificacao LIKE '3.1.2.05%' AND origem IN ('Contrato de Transporte', 'Contrato de Transporte - Item')
    GROUP BY 1
),
c AS (
    SELECT tipo_analise, con_codigo, con_status, data_emissao, ano_emissao,
           CAST(cte AS varchar) AS cte, CAST(tipodocumento AS varchar) AS tipodocumento, CAST(kmm_doc_id AS varchar) AS kmm_doc_id,
           car_codigo_carga_embarcador,
           cnpj_tomador, nome_tomador, grupo_tomador, tem_grupo_pagador, filial_contabil,
           CAST(num_fatura AS varchar) AS num_fatura, CAST(ids_titulo_receber AS varchar) AS ids_titulo_receber,
           CAST(contrato AS varchar) AS contrato, CAST(num_titulo_pagar AS varchar) AS num_titulo_pagar,
           valor_documento_kmm, valor_contrato_liquido, valor_contrato_bruto,
           no_painel, vlr_painel_view,
           date_format(data_emissao, '%Y-%m') AS mes_emissao,
           split_part(CAST(cte AS varchar), '-', 2) AS num_doc,
           regexp_replace(CAST(cnpj_tomador AS varchar), '[^0-9]', '') AS cnpj_tom
    FROM hml_gold.fato_conciliacao_multi_kmm
),
j AS (
    SELECT c.*, rec.receita_contabil, rec.itens_receita, rec.deducoes_contabeis,
           cst.custo_contrato, cst.custo_contrato_item, cst.itens_custo,
           COUNT(*) OVER (PARTITION BY c.tipo_analise, c.num_doc, c.cnpj_tom, c.mes_emissao) AS qtd_linhas_chave_doc,
           COUNT(*) OVER (PARTITION BY c.contrato) AS qtd_linhas_contrato
    FROM c
    LEFT JOIN rec ON rec.tipo_analise = c.tipo_analise AND rec.num = c.num_doc AND rec.cnpj = c.cnpj_tom AND rec.mes_lanc = c.mes_emissao
    LEFT JOIN cst ON cst.contrato = c.contrato
)
SELECT tipo_analise, con_codigo, con_status, data_emissao, ano_emissao, cte, tipodocumento, kmm_doc_id, car_codigo_carga_embarcador,
       cnpj_tomador, nome_tomador, grupo_tomador, tem_grupo_pagador, filial_contabil,
       num_fatura, ids_titulo_receber, contrato, num_titulo_pagar,
       valor_documento_kmm, valor_contrato_liquido, valor_contrato_bruto, no_painel, vlr_painel_view,
       -- receita contabil do CT-e/NF
       CASE WHEN receita_contabil IS NULL THEN 'NAO' ELSE 'SIM' END AS receita_na_contabilidade,
       receita_contabil AS receita_contabil_documento,
       receita_contabil / qtd_linhas_chave_doc AS receita_contabil_rateada,
       receita_contabil / qtd_linhas_chave_doc - COALESCE(vlr_painel_view, 0) AS dif_receita_contabil_x_painel,
       CASE WHEN qtd_linhas_chave_doc > 1 THEN 'SIM' ELSE 'NAO' END AS chave_documento_repetida,
       -- custo contabil do contrato
       CASE WHEN custo_contrato IS NULL THEN 'NAO' ELSE 'SIM' END AS custo_na_contabilidade,
       custo_contrato AS custo_contabil_contrato,
       custo_contrato / qtd_linhas_contrato AS custo_contabil_contrato_rateado,
       custo_contrato_item AS custo_contabil_contrato_item,
       custo_contrato_item / qtd_linhas_contrato AS custo_contabil_contrato_item_rateado,
       qtd_linhas_contrato,
       -- deducoes da receita do documento (negativas) e valor rateado entre as linhas com a mesma chave
       deducoes_contabeis AS deducoes_contabeis_documento,
       deducoes_contabeis / qtd_linhas_chave_doc AS deducoes_contabeis_rateadas
FROM j
