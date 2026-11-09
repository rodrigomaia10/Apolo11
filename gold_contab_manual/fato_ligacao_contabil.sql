-- Fato: ligacao entre os documentos da conciliacao Multi x KMM e a contabilidade (receita 3.1.1.01, deducoes 3.1.1.02, custo de contrato 3.1.2.05).
-- Grao: igual ao de fato_conciliacao_multi_kmm (uma linha por documento/carga da conciliacao), com as colunas da contabilidade.
-- Mesma regra da antiga vw_fato_ligacao_contabil, mas lendo os itens contabeis do KMM (fato_contab_item, origem e conta do DRE) em vez do log
-- kmm_listas_contab_lancamentos_incremental, que so tem dados desde maio/26.
--   CT-e e NF: numero do documento + CNPJ do tomador + mes de emissao (receita e deducoes). Contrato: ID entre colchetes no historico do lancamento.
-- Atencao: o custo do contrato e rateado pelas linhas da conciliacao com o mesmo contrato (qtd_linhas_contrato); a receita e a deducao, pelas linhas
-- com a mesma chave documento (qtd_linhas_chave_doc). Somar o valor "documento" repete o valor por linha: use os campos *_rateada.
WITH contab AS (
    SELECT
        f.num_lancamento_it AS contabilizacao_id,
        o.origem AS origem,
        c.classificacao AS classificacao,
        i.num_documento AS num_documento,
        regexp_replace(CAST(pe.cnpj_cpf AS STRING), '[^0-9]', '') AS cnpj,
        regexp_extract(i.historico, '\\[(\\d+)\\]', 1) AS contrato_hist,
        f.valor_credito AS cr,
        f.valor_debito AS db,
        f.mes_lancamento AS mes_lanc
    FROM {env}_gold.fato_contab_item f
    JOIN {env}_gold.dim_conta c ON c.sk_conta = f.sk_conta
    JOIN {env}_gold.dim_origem_contabil o ON o.sk_origem = f.sk_origem
    JOIN {env}_silver.kmm_contab_lancamento_item i ON i.num_lancamento_it = f.num_lancamento_it
    LEFT JOIN {env}_silver.kmm_pessoa pe ON pe.cod_pessoa = i.cod_participante
    WHERE o.origem IN ('Conhecimento de Transporte', 'Nota Fiscal de E/S', 'Contrato de Transporte', 'Contrato de Transporte - Item')
      AND (c.classificacao LIKE '3.1.1.01%' OR c.classificacao LIKE '3.1.2.05%'
           OR c.classificacao IN ('3.1.1.02.00001', '3.1.1.02.00002', '3.1.1.02.00003', '3.1.1.02.00006', '3.1.1.02.00008',
                                  '3.1.1.02.00011', '3.1.1.02.00013', '3.1.1.02.00015'))
),
rec AS (
    SELECT
        CASE WHEN origem = 'Conhecimento de Transporte' THEN 'CT-e' ELSE 'NF' END AS tipo_analise,
        num_documento AS num, cnpj, mes_lanc,
        SUM(CASE WHEN classificacao LIKE '3.1.1.01%' THEN (cr - db) END) AS receita_contabil,
        SUM(CASE WHEN classificacao LIKE '3.1.1.01%' THEN 1 ELSE 0 END) AS itens_receita,
        SUM(CASE WHEN classificacao LIKE '3.1.1.02%' THEN (cr - db) ELSE 0 END) AS deducoes_contabeis
    FROM contab
    WHERE (classificacao LIKE '3.1.1.01%' OR classificacao LIKE '3.1.1.02%')
      AND origem IN ('Conhecimento de Transporte', 'Nota Fiscal de E/S')
    GROUP BY 1, 2, 3, 4
),
cst AS (
    SELECT
        contrato_hist AS contrato,
        SUM(CASE WHEN origem = 'Contrato de Transporte' THEN (db - cr) ELSE 0 END) AS custo_contrato,
        SUM(CASE WHEN origem = 'Contrato de Transporte - Item' THEN (db - cr) ELSE 0 END) AS custo_contrato_item,
        COUNT(*) AS itens_custo
    FROM contab
    WHERE classificacao LIKE '3.1.2.05%' AND origem IN ('Contrato de Transporte', 'Contrato de Transporte - Item')
    GROUP BY 1
),
c AS (
    SELECT
        tipo_analise, con_codigo, con_status, data_emissao, ano_emissao,
        CAST(cte AS STRING) AS cte, CAST(tipodocumento AS STRING) AS tipodocumento, CAST(kmm_doc_id AS STRING) AS kmm_doc_id,
        car_codigo_carga_embarcador, cnpj_tomador, nome_tomador, grupo_tomador, tem_grupo_pagador, filial_contabil,
        CAST(num_fatura AS STRING) AS num_fatura, CAST(ids_titulo_receber AS STRING) AS ids_titulo_receber,
        CAST(contrato AS STRING) AS contrato, CAST(num_titulo_pagar AS STRING) AS num_titulo_pagar,
        valor_documento_kmm, valor_contrato_liquido, valor_contrato_bruto, no_painel, vlr_painel_view,
        date_format(data_emissao, 'yyyy-MM') AS mes_emissao,
        split(CAST(cte AS STRING), '-')[1] AS num_doc,
        regexp_replace(CAST(cnpj_tomador AS STRING), '[^0-9]', '') AS cnpj_tom
    FROM {env}_gold.fato_conciliacao_multi_kmm
),
j AS (
    SELECT
        c.*, rec.receita_contabil, rec.itens_receita, rec.deducoes_contabeis,
        cst.custo_contrato, cst.custo_contrato_item, cst.itens_custo,
        COUNT(*) OVER (PARTITION BY c.tipo_analise, c.num_doc, c.cnpj_tom, c.mes_emissao) AS qtd_linhas_chave_doc,
        COUNT(*) OVER (PARTITION BY c.contrato) AS qtd_linhas_contrato
    FROM c
    LEFT JOIN rec ON rec.tipo_analise = c.tipo_analise AND rec.num = c.num_doc AND rec.cnpj = c.cnpj_tom AND rec.mes_lanc = c.mes_emissao
    LEFT JOIN cst ON cst.contrato = c.contrato
)
SELECT
    tipo_analise, con_codigo, con_status, data_emissao, ano_emissao, cte, tipodocumento, kmm_doc_id, car_codigo_carga_embarcador,
    cnpj_tomador, nome_tomador, grupo_tomador, tem_grupo_pagador, filial_contabil, num_fatura, ids_titulo_receber, contrato, num_titulo_pagar,
    valor_documento_kmm, valor_contrato_liquido, valor_contrato_bruto, no_painel, vlr_painel_view,
    CASE WHEN receita_contabil IS NULL THEN 'NAO' ELSE 'SIM' END AS receita_na_contabilidade,
    receita_contabil AS receita_contabil_documento,
    receita_contabil / qtd_linhas_chave_doc AS receita_contabil_rateada,
    (receita_contabil / qtd_linhas_chave_doc) - COALESCE(vlr_painel_view, 0) AS dif_receita_contabil_x_painel,
    CASE WHEN qtd_linhas_chave_doc > 1 THEN 'SIM' ELSE 'NAO' END AS chave_documento_repetida,
    CASE WHEN custo_contrato IS NULL THEN 'NAO' ELSE 'SIM' END AS custo_na_contabilidade,
    custo_contrato AS custo_contabil_contrato,
    custo_contrato / qtd_linhas_contrato AS custo_contabil_contrato_rateado,
    custo_contrato_item AS custo_contabil_contrato_item,
    custo_contrato_item / qtd_linhas_contrato AS custo_contabil_contrato_item_rateado,
    qtd_linhas_contrato,
    deducoes_contabeis AS deducoes_contabeis_documento,
    deducoes_contabeis / qtd_linhas_chave_doc AS deducoes_contabeis_rateadas
FROM j
