-- =====================================================================
-- FINANCEIRO -- views no hml_gold, UMA LINHA POR TITULO (contas a receber e contas a pagar do KMM)
-- Fonte: prd_bronze.kmm_* (nunca hml_bronze). Regra do projeto: view so em hml_gold.
--   hml_gold.vw_fato_titulo_receber   -> titulo a receber (fatura/parcela), com amortizacao/juro/desconto
--   hml_gold.vw_fato_titulo_pagar     -> titulo a pagar (fornecedor/transportador)
-- Grao: contas_receber_id / contas_pagar_id (o mesmo num_docto pode ter varios titulos = parcelas).
-- Regras (validadas contra a base crua em 2026-10-09):
--   * receber: cancelado = 0 e data_estorno IS NULL; pagar: data_estorno IS NULL (nao tem campo cancelado)
--   * pago = SUM(amortizacao nao cancelada/estornada); juro e desconto sem estorno; sem duplicidade nas tabelas
--   * saldo_aberto = GREATEST(valor + juro - desconto - pago, 0)
--   * status: QUITADO (pago cobre valor+juro-desconto) | LIQUIDADO POR DESCONTO (sem pagamento, saldo zero)
--             | PAGAMENTO PARCIAL | EM ABERTO
--   * aging so para saldo > 0, em dias de atraso sobre o vencimento, calculado em current_date
--   * a partir de 2025-01-01 (permite ver titulo de 2026 de documento de 2025)
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1) CONTAS A RECEBER
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW hml_gold.vw_fato_titulo_receber AS
WITH
mapa_filial_kmm AS (
    SELECT cc.cod_centro_custo, neg.cod_unidade_negocio, neg.unidade_negocio,
           COALESCE(fil_path1.sk_filial, fil_path2.sk_filial)       AS sk_filial,
           COALESCE(fil_path1.nome_display, fil_path2.nome_display) AS filial_nome
    FROM prd_bronze.kmm_kss_centro_custo cc
    JOIN prd_bronze.kmm_kss_organograma org      ON cc.cod_centro_custo = org.cod_centro_custo
    JOIN prd_bronze.kmm_kss_unidade_negocio neg  ON org.cod_unidade_negocio = neg.cod_unidade_negocio
    LEFT JOIN prd_bronze.multi_dbo_t_centro_custo_viagem cen1
        ON try_cast(neg.cod_unidade_negocio AS varchar) = cen1.ccv_codigo_integracao AND neg.cod_unidade_negocio != 1
    LEFT JOIN prd_gold.dim_filial fil_path1 ON fil_path1.ccv_codigo = cen1.ccv_codigo
    LEFT JOIN prd_bronze.multi_dbo_t_centro_custo_viagem cen2
        ON cc.codigo_cliente = cen2.ccv_codigo_integracao AND neg.cod_unidade_negocio = 1
    LEFT JOIN prd_gold.dim_filial fil_path2 ON fil_path2.ccv_codigo = cen2.ccv_codigo
),
mapa AS (
    SELECT * FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY cod_centro_custo ORDER BY sk_filial NULLS LAST) AS rn
                   FROM mapa_filial_kmm) WHERE rn = 1
),
grupo_cliente AS (
    SELECT g.grc_cnpj, MAX(gp.grp_descricao) AS grupo
    FROM prd_bronze.multi_dbo_t_grupo_pessoas_raiz_cnpj g
    JOIN prd_bronze.multi_dbo_t_grupo_pessoas gp ON gp.grp_codigo = g.grp_codigo
    GROUP BY g.grc_cnpj
),
pago AS (
    SELECT contas_receber_id, SUM(valor_amortizacao) AS valor_pago, MAX(DATE(data_amortizacao)) AS data_ultima_amortizacao
    FROM prd_bronze.kmm_finan_finan_contas_receber_amort
    WHERE (amort_cancelado = 0 OR amort_cancelado IS NULL) AND data_estorno IS NULL
    GROUP BY contas_receber_id
),
juro AS (
    SELECT contas_receber_id, SUM(valor_juro) AS valor_juro
    FROM prd_bronze.kmm_finan_finan_contas_receber_juro
    WHERE (estorno_juro = 0 OR estorno_juro IS NULL) AND data_estorno IS NULL
    GROUP BY contas_receber_id
),
desconto AS (
    SELECT contas_receber_id, SUM(valor_desconto) AS valor_desconto,
           SUM(CASE WHEN desconto_devolucao = 1 THEN valor_desconto ELSE 0 END) AS valor_desconto_devolucao
    FROM prd_bronze.kmm_finan_finan_contas_receber_desc
    WHERE data_estorno IS NULL
    GROUP BY contas_receber_id
),
-- documentos ligados ao titulo (o centro de custo do titulo quase nunca vem preenchido, entao a filial
-- vem do documento, mesma regra da conciliacao: cod_centro_custo do conhecimento/nota)
-- filial do Multi por documento KMM, vinda da tabela de conciliacao (o mapeamento por centro de custo do KMM
-- so resolve filial para uma minoria dos centros). Documentos de 2026, titulos de docs antigos caem no fallback.
conc_doc AS (
    SELECT kmm_doc_id, tipo_analise, MAX(sk_filial) AS sk_filial, MAX(filial_multi) AS filial_multi
    FROM hml_gold.fato_conciliacao_multi_kmm
    WHERE kmm_doc_id IS NOT NULL AND tipo_analise IN ('CT-e', 'NF') AND filial_multi IS NOT NULL
    GROUP BY kmm_doc_id, tipo_analise
),
docs AS (
    SELECT contas_receber_id, COUNT(DISTINCT doc_id) AS qtd_documentos, MIN(cod_centro_custo) AS cc_doc,
           MIN(sk_filial_conc) AS sk_filial_conc, MIN(filial_conc) AS filial_conc
    FROM (
        SELECT r.contas_receber_id, CONCAT('C', CAST(CAST(r.conhecimento_id AS bigint) AS varchar)) AS doc_id, kc.cod_centro_custo,
               cf.sk_filial AS sk_filial_conc, cf.filial_multi AS filial_conc
        FROM prd_bronze.kmm_fiscal_conhecimento_receber r
        JOIN prd_bronze.kmm_fiscal_conhecimento kc ON kc.conhecimento_id = r.conhecimento_id
        LEFT JOIN conc_doc cf ON cf.kmm_doc_id = CAST(r.conhecimento_id AS bigint) AND cf.tipo_analise = 'CT-e'
        WHERE r.data_cancelamento IS NULL
        UNION ALL
        SELECT r.contas_receber_id, CONCAT('N', CAST(CAST(r.num_nota_id AS bigint) AS varchar)), kn.cod_centro_custo,
               cf.sk_filial, cf.filial_multi
        FROM prd_bronze.kmm_fiscal_nf_es_receber r
        JOIN prd_bronze.kmm_fiscal_nf_es kn ON kn.num_nota_id = r.num_nota_id
        LEFT JOIN conc_doc cf ON cf.kmm_doc_id = CAST(r.num_nota_id AS bigint) AND cf.tipo_analise = 'NF'
        WHERE r.data_cancelamento IS NULL
    ) GROUP BY contas_receber_id
),
base AS (
    SELECT
        CAST(kr.contas_receber_id AS bigint)  AS contas_receber_id,
        kr.num_docto, kr.parc_docto, kr.docto_id AS tipo_docto,
        DATE(kr.data_emissao) AS data_emissao, DATE(kr.data_vencto) AS data_vencto, DATE(kr.data_previsao) AS data_previsao,
        CAST(kr.cod_pessoa AS bigint) AS cod_pessoa, p.cnpj_cpf, p.razao_social AS cliente,
        gc.grupo AS grupo_cliente, COALESCE(gc.grupo, p.razao_social) AS cliente_grupo,
        CAST(COALESCE(dc.cc_doc, kr.cod_centro_custo) AS bigint) AS cod_centro_custo,
        COALESCE(dc.sk_filial_conc, mf.sk_filial) AS sk_filial, COALESCE(dc.filial_conc, mf.filial_nome) AS filial, mf.unidade_negocio,
        kr.user_insert AS usuario_titulo,
        CAST(kr.valor_docto AS double)                          AS valor_titulo,
        CAST(COALESCE(pg.valor_pago, 0) AS double)              AS valor_pago,
        CAST(COALESCE(j.valor_juro, 0) AS double)               AS valor_juro,
        CAST(COALESCE(d.valor_desconto, 0) AS double)           AS valor_desconto,
        CAST(COALESCE(d.valor_desconto_devolucao, 0) AS double) AS valor_desconto_devolucao,
        pg.data_ultima_amortizacao,
        COALESCE(dc.qtd_documentos, 0)                          AS qtd_documentos
    FROM prd_bronze.kmm_finan_finan_contas_receber kr
    LEFT JOIN prd_bronze.kmm_kss_pessoa p ON p.cod_pessoa = kr.cod_pessoa
    LEFT JOIN grupo_cliente gc ON gc.grc_cnpj = SUBSTR(LPAD(regexp_replace(p.cnpj_cpf, '[^0-9]', ''), 14, '0'), 1, 8)
                              AND LENGTH(regexp_replace(p.cnpj_cpf, '[^0-9]', '')) >= 14
    LEFT JOIN docs dc ON dc.contas_receber_id = kr.contas_receber_id
    LEFT JOIN mapa mf ON mf.cod_centro_custo = COALESCE(dc.cc_doc, kr.cod_centro_custo)
    LEFT JOIN pago pg ON pg.contas_receber_id = kr.contas_receber_id
    LEFT JOIN juro j ON j.contas_receber_id = kr.contas_receber_id
    LEFT JOIN desconto d ON d.contas_receber_id = kr.contas_receber_id
    WHERE kr.cancelado = 0 AND kr.data_estorno IS NULL AND kr.data_emissao >= TIMESTAMP '2025-01-01 00:00:00'
)
SELECT b.*,
    CASE b.tipo_docto WHEN 'CF' THEN 'CF - Contrato de transporte' WHEN 'CR' THEN 'CR - Contrato Repom' WHEN 'NF' THEN 'NF - Despesas (NFT)'
         WHEN 'TR' THEN 'TR - Tributo' WHEN 'AT' THEN 'AT - Acerto do transportador' WHEN 'DA' THEN 'DA - Despesas bancarias'
         WHEN 'FI' THEN 'FI - Financiamento' WHEN 'TT' THEN 'TT - Taxa do transportador' WHEN 'JA' THEN 'JA - Juros antecipacao clientes'
         WHEN 'AV' THEN 'AV - Adto colaborador' WHEN 'FL' THEN 'FL - Folha de pagamento' WHEN 'FR' THEN 'FR - Fatura Repom'
         WHEN 'AF' THEN 'AF - Adto fornecedor' WHEN 'CP' THEN 'CP - Cotas capital' ELSE b.tipo_docto END AS tipo_docto_descricao,
    GREATEST(b.valor_titulo + b.valor_juro - b.valor_desconto - b.valor_pago, 0) AS saldo_aberto,
    CASE WHEN b.valor_pago <= 0.005 AND b.valor_titulo + b.valor_juro - b.valor_desconto <= 0.01 THEN 'LIQUIDADO POR DESCONTO'
         WHEN b.valor_pago <= 0.005 THEN 'EM ABERTO'
         WHEN b.valor_pago >= b.valor_titulo + b.valor_juro - b.valor_desconto - 0.01 THEN 'QUITADO'
         ELSE 'PAGAMENTO PARCIAL' END                                           AS status_pagamento,
    date_diff('day', b.data_emissao, b.data_vencto)                             AS prazo_dias,
    CASE WHEN b.valor_pago > 0.005 AND b.valor_pago >= b.valor_titulo + b.valor_juro - b.valor_desconto - 0.01
         THEN date_diff('day', b.data_emissao, b.data_ultima_amortizacao) END   AS dias_ate_recebimento,
    CASE WHEN b.valor_titulo + b.valor_juro - b.valor_desconto - b.valor_pago > 0.01 AND b.data_vencto < current_date THEN 'SIM' ELSE 'NAO' END AS vencido,
    CASE WHEN b.valor_titulo + b.valor_juro - b.valor_desconto - b.valor_pago > 0.01 AND b.data_vencto < current_date
         THEN date_diff('day', b.data_vencto, current_date) END                 AS dias_atraso,
    CASE WHEN b.valor_titulo + b.valor_juro - b.valor_desconto - b.valor_pago <= 0.01 THEN 'SEM SALDO'
         WHEN b.data_vencto >= current_date THEN 'A VENCER'
         WHEN date_diff('day', b.data_vencto, current_date) <= 30 THEN 'VENCIDO 1-30'
         WHEN date_diff('day', b.data_vencto, current_date) <= 60 THEN 'VENCIDO 31-60'
         WHEN date_diff('day', b.data_vencto, current_date) <= 90 THEN 'VENCIDO 61-90'
         ELSE 'VENCIDO > 90' END                                                AS faixa_aging,
    CASE WHEN b.qtd_documentos > 0 THEN 'SIM' ELSE 'NAO' END                    AS tem_documento
FROM base b;

-- ---------------------------------------------------------------------
-- 2) CONTAS A PAGAR
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW hml_gold.vw_fato_titulo_pagar AS
WITH
mapa_filial_kmm AS (
    SELECT cc.cod_centro_custo, neg.cod_unidade_negocio, neg.unidade_negocio,
           COALESCE(fil_path1.sk_filial, fil_path2.sk_filial)       AS sk_filial,
           COALESCE(fil_path1.nome_display, fil_path2.nome_display) AS filial_nome
    FROM prd_bronze.kmm_kss_centro_custo cc
    JOIN prd_bronze.kmm_kss_organograma org      ON cc.cod_centro_custo = org.cod_centro_custo
    JOIN prd_bronze.kmm_kss_unidade_negocio neg  ON org.cod_unidade_negocio = neg.cod_unidade_negocio
    LEFT JOIN prd_bronze.multi_dbo_t_centro_custo_viagem cen1
        ON try_cast(neg.cod_unidade_negocio AS varchar) = cen1.ccv_codigo_integracao AND neg.cod_unidade_negocio != 1
    LEFT JOIN prd_gold.dim_filial fil_path1 ON fil_path1.ccv_codigo = cen1.ccv_codigo
    LEFT JOIN prd_bronze.multi_dbo_t_centro_custo_viagem cen2
        ON cc.codigo_cliente = cen2.ccv_codigo_integracao AND neg.cod_unidade_negocio = 1
    LEFT JOIN prd_gold.dim_filial fil_path2 ON fil_path2.ccv_codigo = cen2.ccv_codigo
),
mapa AS (
    SELECT * FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY cod_centro_custo ORDER BY sk_filial NULLS LAST) AS rn
                   FROM mapa_filial_kmm) WHERE rn = 1
),
pago AS (
    SELECT contas_pagar_id, SUM(valor_amortizacao) AS valor_pago, MAX(DATE(data_amortizacao)) AS data_ultima_amortizacao,
           -- baixa com data FUTURA e pagamento programado, nao realizado: so conta como pago a baixa com data <= hoje
           SUM(CASE WHEN DATE(data_amortizacao) <= current_date THEN valor_amortizacao ELSE 0 END) AS valor_pago_realizado,
           SUM(CASE WHEN DATE(data_amortizacao) >  current_date THEN valor_amortizacao ELSE 0 END) AS valor_pago_programado,
           MAX(CASE WHEN DATE(data_amortizacao) <= current_date THEN DATE(data_amortizacao) END)  AS data_ultima_baixa_realizada
    FROM prd_bronze.kmm_finan_finan_contas_pagar_amort
    WHERE data_estorno IS NULL
    GROUP BY contas_pagar_id
),
juro AS (
    SELECT contas_pagar_id, SUM(valor_juro) AS valor_juro
    FROM prd_bronze.kmm_finan_finan_contas_pagar_juro
    WHERE data_estorno IS NULL
    GROUP BY contas_pagar_id
),
desconto AS (
    SELECT contas_pagar_id, SUM(valor_desconto) AS valor_desconto,
           SUM(CASE WHEN desconto_devolucao = 1 THEN valor_desconto ELSE 0 END) AS valor_desconto_devolucao
    FROM prd_bronze.kmm_finan_finan_contas_pagar_desc
    WHERE data_estorno IS NULL
    GROUP BY contas_pagar_id
),
-- contrato de transporte do titulo (o centro de custo do titulo vem vazio na maioria, entao a filial vem do contrato)
conc_contrato AS (
    SELECT contrato, MAX(sk_filial) AS sk_filial, MAX(filial_multi) AS filial_multi
    FROM hml_gold.fato_conciliacao_multi_kmm
    WHERE contrato IS NOT NULL AND filial_multi IS NOT NULL
    GROUP BY contrato
),
-- liberacao de pagamento: o titulo que exige liberacao (exige_liberacao_pagamento = 1) fica BLOQUEADO enquanto nao houver
-- valor liberado (kmm_finan_finan_contas_pagar_liberacao). A tela do KMM do usuario esconde parte desses titulos.
liberacao AS (
    SELECT contas_pagar_id, SUM(valor_liberacao) AS valor_liberado
    FROM prd_bronze.kmm_finan_finan_contas_pagar_liberacao
    GROUP BY contas_pagar_id
),
contrato AS (
    SELECT tp.contas_pagar_id, MIN(ct.cod_centro_custo) AS cc_contrato,
           MIN(cc.sk_filial) AS sk_filial_conc, MIN(cc.filial_multi) AS filial_conc
    FROM prd_bronze.kmm_contrato_contrato_transp_pagar tp
    LEFT JOIN prd_bronze.kmm_contrato_contrato_transp ct ON ct.lancto_id = tp.lancto_id
    LEFT JOIN conc_contrato cc ON cc.contrato = TRY_CAST(ct.num_formulario AS bigint)
    GROUP BY tp.contas_pagar_id
),
-- cliente do CUSTO: o titulo de contrato de frete e da carga; o cliente da carga e o tomador do documento que
-- carrega o custo na conciliacao (linha_custo_carga = 'SIM'). Titulo que nao e de contrato (folha, tributo,
-- financiamento) fica sem cliente. Mesmo criterio de cliente do Custo Operacional (grupo, ou nome se nao ha grupo).
conc_cliente AS (
    SELECT contrato, MAX(COALESCE(grupo_tomador, nome_tomador)) AS cliente_custo
    FROM hml_gold.fato_conciliacao_multi_kmm
    WHERE contrato IS NOT NULL AND linha_custo_carga = 'SIM'
    GROUP BY contrato
),
cliente_titulo AS (
    SELECT tp.contas_pagar_id, MAX(cc.cliente_custo) AS cliente_custo
    FROM prd_bronze.kmm_contrato_contrato_transp_pagar tp
    JOIN prd_bronze.kmm_contrato_contrato_transp ct ON ct.lancto_id = tp.lancto_id
    JOIN conc_cliente cc ON cc.contrato = TRY_CAST(ct.num_formulario AS bigint)
    GROUP BY tp.contas_pagar_id
),
base AS (
    SELECT
        CAST(cp.contas_pagar_id AS bigint) AS contas_pagar_id,
        cp.num_docto, cp.parc_docto, cp.docto_id AS tipo_docto,
        DATE(cp.data_emissao) AS data_emissao, DATE(cp.data_vencto) AS data_vencto, DATE(cp.data_previsao) AS data_previsao,
        CAST(cp.cod_pessoa AS bigint) AS cod_pessoa, p.cnpj_cpf, p.razao_social AS fornecedor,
        CAST(cp.cod_pessoa_pagamento AS bigint) AS cod_pessoa_pagamento,
        CAST(COALESCE(ct.cc_contrato, cp.cod_centro_custo) AS bigint) AS cod_centro_custo,
        COALESCE(ct.sk_filial_conc, mf.sk_filial) AS sk_filial, COALESCE(ct.filial_conc, mf.filial_nome) AS filial, mf.unidade_negocio,
        cp.user_insert AS usuario_titulo,
        CAST(cp.cod_historico AS bigint) AS cod_historico, CAST(cp.tipo_pagto_id AS bigint) AS cod_tipo_pagamento,
        CASE WHEN cp.aprovacao IS NOT NULL THEN 'SIM' ELSE 'NAO' END AS aprovado,
        CASE WHEN ct.contas_pagar_id IS NOT NULL THEN 'SIM' ELSE 'NAO' END AS tem_contrato_transporte,
        CASE WHEN cp.exige_liberacao_pagamento = 1 THEN 'SIM' ELSE 'NAO' END AS exige_liberacao,
        CAST(COALESCE(lb.valor_liberado, 0) AS double) AS valor_liberado,
        CAST(cp.valor_docto AS double)                          AS valor_titulo,
        CAST(COALESCE(pg.valor_pago, 0) AS double)              AS valor_pago,
        CAST(COALESCE(j.valor_juro, 0) AS double)               AS valor_juro,
        CAST(COALESCE(d.valor_desconto, 0) AS double)           AS valor_desconto,
        CAST(COALESCE(d.valor_desconto_devolucao, 0) AS double) AS valor_desconto_devolucao,
        pg.data_ultima_amortizacao
    FROM prd_bronze.kmm_finan_finan_contas_pagar cp
    LEFT JOIN prd_bronze.kmm_kss_pessoa p ON p.cod_pessoa = cp.cod_pessoa
    LEFT JOIN contrato ct ON ct.contas_pagar_id = cp.contas_pagar_id
    LEFT JOIN liberacao lb ON lb.contas_pagar_id = cp.contas_pagar_id
    LEFT JOIN mapa mf ON mf.cod_centro_custo = COALESCE(ct.cc_contrato, cp.cod_centro_custo)
    LEFT JOIN pago pg ON pg.contas_pagar_id = cp.contas_pagar_id
    LEFT JOIN juro j ON j.contas_pagar_id = cp.contas_pagar_id
    LEFT JOIN desconto d ON d.contas_pagar_id = cp.contas_pagar_id
    WHERE cp.data_estorno IS NULL AND cp.data_emissao >= TIMESTAMP '2025-01-01 00:00:00'
)
SELECT b.*,
    CASE b.tipo_docto WHEN 'CF' THEN 'CF - Contrato de transporte' WHEN 'CR' THEN 'CR - Contrato Repom' WHEN 'NF' THEN 'NF - Despesas (NFT)'
         WHEN 'TR' THEN 'TR - Tributo' WHEN 'AT' THEN 'AT - Acerto do transportador' WHEN 'DA' THEN 'DA - Despesas bancarias'
         WHEN 'FI' THEN 'FI - Financiamento' WHEN 'TT' THEN 'TT - Taxa do transportador' WHEN 'JA' THEN 'JA - Juros antecipacao clientes'
         WHEN 'AV' THEN 'AV - Adto colaborador' WHEN 'FL' THEN 'FL - Folha de pagamento' WHEN 'FR' THEN 'FR - Fatura Repom'
         WHEN 'AF' THEN 'AF - Adto fornecedor' WHEN 'CP' THEN 'CP - Cotas capital' ELSE b.tipo_docto END AS tipo_docto_descricao,
    GREATEST(b.valor_titulo + b.valor_juro - b.valor_desconto - b.valor_pago, 0) AS saldo_aberto,
    CASE WHEN b.valor_pago <= 0.005 AND b.valor_titulo + b.valor_juro - b.valor_desconto <= 0.01 THEN 'LIQUIDADO POR DESCONTO'
         WHEN b.valor_pago <= 0.005 THEN 'EM ABERTO'
         WHEN b.valor_pago >= b.valor_titulo + b.valor_juro - b.valor_desconto - 0.01 THEN 'QUITADO'
         ELSE 'PAGAMENTO PARCIAL' END                                           AS status_pagamento,
    date_diff('day', b.data_emissao, b.data_vencto)                             AS prazo_dias,
    CASE WHEN b.valor_pago > 0.005 AND b.valor_pago >= b.valor_titulo + b.valor_juro - b.valor_desconto - 0.01
         THEN date_diff('day', b.data_emissao, b.data_ultima_amortizacao) END   AS dias_ate_pagamento,
    CASE WHEN b.valor_titulo + b.valor_juro - b.valor_desconto - b.valor_pago > 0.01 AND b.data_vencto < current_date THEN 'SIM' ELSE 'NAO' END AS vencido,
    CASE WHEN b.valor_titulo + b.valor_juro - b.valor_desconto - b.valor_pago > 0.01 AND b.data_vencto < current_date
         THEN date_diff('day', b.data_vencto, current_date) END                 AS dias_atraso,
    CASE WHEN b.valor_titulo + b.valor_juro - b.valor_desconto - b.valor_pago <= 0.01 THEN 'SEM SALDO'
         WHEN b.data_vencto >= current_date THEN 'A VENCER'
         WHEN date_diff('day', b.data_vencto, current_date) <= 30 THEN 'VENCIDO 1-30'
         WHEN date_diff('day', b.data_vencto, current_date) <= 60 THEN 'VENCIDO 31-60'
         WHEN date_diff('day', b.data_vencto, current_date) <= 90 THEN 'VENCIDO 61-90'
         ELSE 'VENCIDO > 90' END                                                AS faixa_aging,
    -- BLOQUEADO so quando ainda ha saldo a pagar: titulo ja pago/liquidado sem registro de liberacao nao esta travando nada
    CASE WHEN b.exige_liberacao = 'NAO' THEN 'NAO EXIGE'
         WHEN b.valor_liberado >= b.valor_titulo - 0.01 THEN 'LIBERADO'
         WHEN b.valor_liberado > 0.005 THEN 'LIBERADO PARCIAL'
         WHEN b.valor_titulo + b.valor_juro - b.valor_desconto - b.valor_pago > 0.01 THEN 'BLOQUEADO'
         ELSE 'PAGO SEM LIBERACAO REGISTRADA' END                               AS status_liberacao,
    ctl.cliente_custo,
    -- visao "como de hoje": pago = so baixa com data <= hoje; o que esta programado (baixa futura) continua em aberto ate a data chegar
    CAST(COALESCE(pg2.valor_pago_realizado, 0) AS double)   AS valor_pago_realizado,
    CAST(COALESCE(pg2.valor_pago_programado, 0) AS double)  AS valor_pago_programado,
    pg2.data_ultima_baixa_realizada,
    GREATEST(b.valor_titulo + b.valor_juro - b.valor_desconto - COALESCE(pg2.valor_pago_realizado, 0), 0) AS saldo_aberto_hoje
FROM base b
LEFT JOIN cliente_titulo ctl ON ctl.contas_pagar_id = b.contas_pagar_id
LEFT JOIN pago pg2 ON pg2.contas_pagar_id = b.contas_pagar_id;
