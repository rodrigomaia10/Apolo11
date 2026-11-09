-- Fato: conciliacao Multi (TMS) x KMM (ERP), CT-e + NF, uma linha por documento. Gerado de conciliacao_multi_kmm.sql por gerar_conciliacao_gold.py.
-- Traducao Athena->Spark: try_cast->CAST, varchar->STRING, date_diff->datediff, array_agg->array_sort(collect_set), contains->array_contains, split_part->split()[n], GREATEST preserva NULL,
-- ORDER BY com NULLS LAST (Spark ordena NULL primeiro no ASC), view vw_fato_operacional_painel_filial -> CTE painel_view (mesma regra).
-- Colunas e tipos iguais aos da tabela hml_gold.fato_conciliacao_multi_kmm (105 colunas), para o BI ler com select *.
SELECT
    CAST(tipo_analise AS STRING) AS tipo_analise,
    CAST(ano_emissao AS BIGINT) AS ano_emissao,
    CAST(tipo_documento AS STRING) AS tipo_documento,
    CAST(cte AS STRING) AS cte,
    CAST(con_codigo AS INT) AS con_codigo,
    CAST(con_status AS STRING) AS con_status,
    CAST(car_codigo_carga_embarcador AS STRING) AS car_codigo_carga_embarcador,
    CAST(sk_filial AS INT) AS sk_filial,
    CAST(sk_cliente AS INT) AS sk_cliente,
    CAST(sk_cooperado AS BIGINT) AS sk_cooperado,
    CAST(sk_documento AS INT) AS sk_documento,
    CAST(status_multi_descricao AS STRING) AS status_multi_descricao,
    CAST(data_emissao AS DATE) AS data_emissao,
    CAST(cnpj_tomador AS STRING) AS cnpj_tomador,
    CAST(nome_tomador AS STRING) AS nome_tomador,
    CAST(grupo_tomador AS STRING) AS grupo_tomador,
    CAST(tem_grupo_pagador AS STRING) AS tem_grupo_pagador,
    CAST(filial_multi AS STRING) AS filial_multi,
    CAST(filial_duplicada AS STRING) AS filial_duplicada,
    CAST(cooperado AS STRING) AS cooperado,
    CAST(vei_placa AS STRING) AS vei_placa,
    CAST(inicio_da_prestacao AS STRING) AS inicio_da_prestacao,
    CAST(fim_da_prestacao AS STRING) AS fim_da_prestacao,
    CAST(situacao_carga AS STRING) AS situacao_carga,
    CAST(doc_fiscal AS STRING) AS doc_fiscal,
    CAST(emissao_manual AS STRING) AS emissao_manual,
    CAST(qtd_cargas AS BIGINT) AS qtd_cargas,
    CAST(multiplas_cargas AS STRING) AS multiplas_cargas,
    CAST(mod_abreviacao AS STRING) AS mod_abreviacao,
    CAST(tipodocumento AS STRING) AS tipodocumento,
    CAST(ciot AS STRING) AS ciot,
    CAST(vinculo_carga AS STRING) AS vinculo_carga,
    CAST(transbordo AS STRING) AS transbordo,
    CAST(anulacao AS STRING) AS anulacao,
    CAST(kmm_doc_id AS BIGINT) AS kmm_doc_id,
    CAST(filial_kmm AS STRING) AS filial_kmm,
    CAST(filial_contabil AS STRING) AS filial_contabil,
    CAST(unidade_negocio_kmm AS STRING) AS unidade_negocio_kmm,
    CAST(origem_mapeamento AS STRING) AS origem_mapeamento,
    CAST(status_kmm_descricao AS STRING) AS status_kmm_descricao,
    CAST(match_priority_nf AS STRING) AS match_priority_nf,
    CAST(match_gap_dias AS BIGINT) AS match_gap_dias,
    CAST(match_confianca AS STRING) AS match_confianca,
    CAST(valor_documento_kmm AS DOUBLE) AS valor_documento_kmm,
    CAST(valor_icms_kmm AS DOUBLE) AS valor_icms_kmm,
    CAST(valor_iss_kmm AS DOUBLE) AS valor_iss_kmm,
    CAST(num_fatura AS STRING) AS num_fatura,
    CAST(tipo_docto_fatura AS STRING) AS tipo_docto_fatura,
    CAST(qtd_faturas AS BIGINT) AS qtd_faturas,
    CAST(qtd_parcelas AS BIGINT) AS qtd_parcelas,
    CAST(valor_fatura AS DOUBLE) AS valor_fatura,
    CAST(venc_primeiro AS DATE) AS venc_primeiro,
    CAST(venc_ultimo AS DATE) AS venc_ultimo,
    CAST(usuario_fatura AS STRING) AS usuario_fatura,
    CAST(status_fatura AS STRING) AS status_fatura,
    CAST(fatura_cancelada_kmm AS STRING) AS fatura_cancelada_kmm,
    CAST(valor_pago_receber AS DOUBLE) AS valor_pago_receber,
    CAST(valor_juro_receber AS DOUBLE) AS valor_juro_receber,
    CAST(valor_desconto_receber AS DOUBLE) AS valor_desconto_receber,
    CAST(saldo_aberto_receber AS DOUBLE) AS saldo_aberto_receber,
    CAST(status_pagamento_receber AS STRING) AS status_pagamento_receber,
    CAST(dias_emissao_ate_faturamento AS BIGINT) AS dias_emissao_ate_faturamento,
    CAST(data_emissao_fatura AS DATE) AS data_emissao_fatura,
    CAST(contrato AS INT) AS contrato,
    CAST(contrato_cancelado_kmm AS STRING) AS contrato_cancelado_kmm,
    CAST(contrato_avulso AS INT) AS contrato_avulso,
    CAST(valor_contrato_bruto AS DOUBLE) AS valor_contrato_bruto,
    CAST(valor_contrato_liquido AS DOUBLE) AS valor_contrato_liquido,
    CAST(num_titulo_pagar AS STRING) AS num_titulo_pagar,
    CAST(valor_titulo_pagar AS DOUBLE) AS valor_titulo_pagar,
    CAST(usuario_titulo_pagar AS STRING) AS usuario_titulo_pagar,
    CAST(status_fatura_pagar AS STRING) AS status_fatura_pagar,
    CAST(fatura_pagar_cancelada_kmm AS STRING) AS fatura_pagar_cancelada_kmm,
    CAST(valor_pago_pagar AS DOUBLE) AS valor_pago_pagar,
    CAST(valor_juro_pagar AS DOUBLE) AS valor_juro_pagar,
    CAST(valor_desconto_pagar AS DOUBLE) AS valor_desconto_pagar,
    CAST(custo_ocorrencia AS DOUBLE) AS custo_ocorrencia,
    CAST(status_pagamento_pagar AS STRING) AS status_pagamento_pagar,
    CAST(data_ref_pagar AS DATE) AS data_ref_pagar,
    CAST(data_ref_receber AS DATE) AS data_ref_receber,
    CAST(prazo_dias AS BIGINT) AS prazo_dias,
    CAST(prazo_tipo AS STRING) AS prazo_tipo,
    CAST(margem_bruta AS DOUBLE) AS margem_bruta,
    CAST(margem_pct AS DOUBLE) AS margem_pct,
    CAST(status_integracao AS STRING) AS status_integracao,
    CAST(linha_custo_carga AS STRING) AS linha_custo_carga,
    CAST(tipo_cooperado AS STRING) AS tipo_cooperado,
    CAST(operador_pagamento_contrato AS STRING) AS operador_pagamento_contrato,
    CAST(divergencia_negocio AS STRING) AS divergencia_negocio,
    CAST(num_fatura_estimada AS STRING) AS num_fatura_estimada,
    CAST(valor_fatura_estimada AS DOUBLE) AS valor_fatura_estimada,
    CAST(gap_dias_fatura_estimada AS BIGINT) AS gap_dias_fatura_estimada,
    CAST(usuario_doc_kmm AS STRING) AS usuario_doc_kmm,
    CAST(tipo_operacao AS STRING) AS tipo_operacao,
    CAST(doc_anulacao AS STRING) AS doc_anulacao,
    CAST(con_anulacao_ref AS BIGINT) AS con_anulacao_ref,
    CAST(vlr_receita_bruta_multi AS DOUBLE) AS vlr_receita_bruta_multi,
    CAST(no_painel AS STRING) AS no_painel,
    CAST(motivo_fora_painel AS STRING) AS motivo_fora_painel,
    CAST(qtd_linhas_painel AS BIGINT) AS qtd_linhas_painel,
    CAST(vlr_painel_view AS DOUBLE) AS vlr_painel_view,
    CAST(variacao_dias_cargas AS BIGINT) AS variacao_dias_cargas,
    CAST(alerta_variacao_30d AS STRING) AS alerta_variacao_30d,
    CAST(valor_desconto_devolucao_receber AS DOUBLE) AS valor_desconto_devolucao_receber,
    CAST(ids_titulo_receber AS STRING) AS ids_titulo_receber
FROM (
WITH
painel_view AS (
    SELECT sk_cliente, sk_documento, sk_cooperado, sk_filial, sk_tipo_operacao, con_codigo, car_codigo_carga_embarcador, cte, data_emissao,
           vlr_receita_bruta, vlr_receita_liquida, vlr_prest_servico, vlr_a_receber, vlr_total_merc, vlr_adv, vlr_gris, vei_placa,
           inicio_da_prestacao, fim_da_prestacao, ccv_descricao, ccv_codigo, codfil,
           CASE WHEN tipo_operacao_anulacao LIKE '%ANULA%' THEN 'S' ELSE 'N' END AS operacao_anulacao,
           dt_min_entrega, con_status, car_situacao, ped_situacao, custo_bruto, tipo_documento, cooperado, tipo_operacao, custo_descarga,
           custo_estadia_rateio, custo_carga, custo_pedagio_extra, custo_loggi, grupo_pessoa_tratado, tipo_cooperado, filial
    FROM {env}_gold.fato_operacional
    WHERE con_status IN ('A') AND car_situacao NOT IN (18, 13) AND ped_situacao <> 2
      AND NOT (tipo_operacao_anulacao LIKE '%CIOT CANCELADO%')
      AND NOT (tipo_operacao_anulacao LIKE '%TRANSBORDO%' OR tipo_operacao_anulacao LIKE '%REUTILIZACAO%'
               OR (tipo_operacao_anulacao LIKE '%REPASSE%' AND tipo_documento = 'CT-e'))
      AND (oco_anulacao IS NULL OR oco_anulacao = 0) AND mod_abreviacao IS NOT NULL
      AND mod_abreviacao NOT IN ('DV', 'OST') AND tipo_documento IS NOT NULL AND tipo_documento NOT IN ('CV', 'OST', 'NDA', 'DV')
      AND ((has_true = 1 AND flag_anulacao = true AND con_codigo = max_con_anulacao)
           OR (has_true = 0 AND (flag_anulacao = false OR flag_anulacao IS NULL)))
),
mapa_filial_kmm AS (
    SELECT
        cc.cod_centro_custo,
        neg.cod_unidade_negocio,
        neg.unidade_negocio,
        COALESCE(fil_path1.sk_filial, fil_path2.sk_filial)       AS sk_filial,
        COALESCE(fil_path1.nome_display, fil_path2.nome_display) AS filial_nome,
        CASE
            WHEN fil_path1.sk_filial IS NOT NULL THEN 'ORGANOGRAMA'
            WHEN fil_path2.sk_filial IS NOT NULL THEN 'CODIGO_CLIENTE'
            ELSE 'SEM MAPEAMENTO'
        END AS origem_mapeamento
    FROM {env}_bronze.kmm_kss_centro_custo cc
    JOIN {env}_bronze.kmm_kss_organograma org      ON cc.cod_centro_custo = org.cod_centro_custo
    JOIN {env}_bronze.kmm_kss_unidade_negocio neg  ON org.cod_unidade_negocio = neg.cod_unidade_negocio
    LEFT JOIN {env}_bronze.multi_dbo_t_centro_custo_viagem cen1
        ON CAST(neg.cod_unidade_negocio AS STRING) = cen1.ccv_codigo_integracao
       AND neg.cod_unidade_negocio != 1
    LEFT JOIN {env}_gold.dim_filial fil_path1 ON fil_path1.ccv_codigo = cen1.ccv_codigo
    LEFT JOIN {env}_bronze.multi_dbo_t_centro_custo_viagem cen2
        ON cc.codigo_cliente = cen2.ccv_codigo_integracao
       AND neg.cod_unidade_negocio = 1
    LEFT JOIN {env}_gold.dim_filial fil_path2 ON fil_path2.ccv_codigo = cen2.ccv_codigo
),
mapa AS (
    SELECT * FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY cod_centro_custo
                                     ORDER BY sk_filial NULLS LAST) AS rn
        FROM mapa_filial_kmm
    ) WHERE rn = 1
),
kmm_enriquecido AS (
    SELECT
        kc.conhecimento_id, kc.serie, kc.num_conhecimento, kc.cob_cnpj_cpf,
        kc.cod_centro_custo, kc.cancelado,
        kc.user_insert AS usuario_doc_kmm,
        DATE(kc.data_emissao) AS data_emissao_kmm,
        kc.total_conhecimento AS valor_documento_kmm,
        kc.valor_icms         AS valor_icms_kmm,
        kc.valor_iss          AS valor_iss_kmm,
        CONCAT(CAST(kc.serie AS STRING), '-', CAST(CAST(kc.num_conhecimento AS bigint) AS STRING)) AS cte_chave,
        mf.sk_filial AS sk_filial_kmm, mf.filial_nome AS filial_kmm,
        mf.cod_unidade_negocio, mf.unidade_negocio, mf.origem_mapeamento
    FROM {env}_bronze.kmm_fiscal_conhecimento kc
    LEFT JOIN mapa mf ON kc.cod_centro_custo = mf.cod_centro_custo
),
angeloni_ctes AS (
    SELECT DISTINCT con_codigo
    FROM {env}_silver.operacional_por_cte
    WHERE tipo_de_carga LIKE '%ANGELONI%'
       OR tipo_operacao LIKE '%ANGELONI%'
),
filial_qtd_distinta AS (
    SELECT con_codigo, COUNT(DISTINCT sk_filial) AS total_filiais_distintas
    FROM {env}_gold.fato_operacional
    WHERE con_codigo IS NOT NULL
    GROUP BY con_codigo
),
filial_multi_map AS (
    SELECT t.con_codigo, t.sk_filial,
           CASE WHEN ac.con_codigo IS NOT NULL THEN 'NAO'
                WHEN d.total_filiais_distintas > 1 THEN 'SIM'
                ELSE 'NAO'
           END AS filial_duplicada
    FROM (
        SELECT fo.con_codigo, fo.sk_filial,
               ROW_NUMBER() OVER (PARTITION BY fo.con_codigo
                                  ORDER BY (CASE WHEN fo.ped_situacao = 2 THEN 1 ELSE 0 END) NULLS LAST, fo.data_emissao NULLS LAST) AS rn
        FROM {env}_gold.fato_operacional fo
        WHERE fo.con_codigo IS NOT NULL
    ) t
    JOIN filial_qtd_distinta d ON d.con_codigo = t.con_codigo
    LEFT JOIN angeloni_ctes ac ON t.con_codigo = ac.con_codigo
    WHERE t.rn = 1
),
info_carga_flags AS (
    SELECT
        con_codigo,
        MAX(CASE WHEN car_situacao IN (18,13) THEN 0 ELSE 1 END)                       AS tem_ativa,
        MIN(CASE WHEN tipodocumento IN ('DV','OST','CV','NDA','ND') THEN 1 ELSE 0 END) AS todos_nao_fiscal,
        COUNT(DISTINCT CASE
            WHEN tipo_de_carga  NOT LIKE '%ANGELONI%'
             AND tipo_operacao NOT LIKE '%ANGELONI%'
            THEN car_codigo_carga_embarcador
        END)                                                                            AS qtd_cargas,
        CASE WHEN COUNT(DISTINCT CASE
                WHEN tipo_de_carga  NOT LIKE '%ANGELONI%'
                 AND tipo_operacao NOT LIKE '%ANGELONI%'
                THEN car_codigo_carga_embarcador
             END) > 1 THEN 'SIM' ELSE 'NAO'
        END                                                                             AS multiplas_cargas
    FROM {env}_silver.operacional_por_cte
    WHERE con_codigo IS NOT NULL
    GROUP BY con_codigo
),
info_carga_texto AS (
    SELECT con_codigo, mod_abreviacao, tipodocumento
    FROM (
        SELECT con_codigo, mod_abreviacao, tipodocumento,
               ROW_NUMBER() OVER (PARTITION BY con_codigo ORDER BY car_situacao DESC) AS rn
        FROM {env}_silver.operacional_por_cte
        WHERE con_codigo IS NOT NULL
    ) WHERE rn = 1
),
grupo_tomador AS (
    SELECT g.grc_cnpj, gp.grp_descricao AS grupo_tomador
    FROM {env}_bronze.multi_dbo_t_grupo_pessoas_raiz_cnpj g
    JOIN {env}_bronze.multi_dbo_t_grupo_pessoas gp ON gp.grp_codigo = g.grp_codigo
),
nfs_manual_por_carga AS (
    SELECT cu.car_codigo_carga_embarcador,
           bool_or(cp.ped_possui_nfs_manual) AS ped_possui_nfs_manual
    FROM {env}_bronze.multi_dbo_t_carga cu
    JOIN {env}_bronze.multi_dbo_t_carga_pedido cp ON cp.car_codigo = cu.car_codigo
    GROUP BY cu.car_codigo_carga_embarcador
),
ciot_por_car_codigo AS (
    SELECT cco.car_codigo,
           bool_or(ciot.cio_data_cancelamento IS NULL) AS tem_ciot_ativo,
           COUNT(ciot.cio_codigo) AS qtd_ciot
    FROM {env}_bronze.multi_dbo_t_carga_ciot cco
    JOIN {env}_bronze.multi_dbo_t_ciot ciot ON ciot.cio_codigo = cco.cio_codigo
    WHERE ciot.cio_numero IS NOT NULL AND ciot.cio_numero <> ''
    GROUP BY cco.car_codigo
),
ciot_por_documento AS (
    SELECT cct.con_codigo, cpc.tem_ciot_ativo, cpc.qtd_ciot
    FROM {env}_bronze.multi_dbo_t_carga_cte cct
    JOIN ciot_por_car_codigo cpc ON cpc.car_codigo = cct.car_codigo
),
carga_sem_documento AS (
    SELECT cu.car_codigo, cu.car_codigo_carga_embarcador, cu.car_situacao,
           DATE(cu.date_insert) AS data_criacao
    FROM {env}_bronze.multi_dbo_t_carga cu
    LEFT JOIN {env}_bronze.multi_dbo_t_carga_cte cct ON cct.car_codigo = cu.car_codigo
    WHERE cct.car_codigo IS NULL
      AND cu.car_codigo_carga_embarcador IS NOT NULL
      AND year(cu.date_insert) = 2026
),
doc_multi AS (
    SELECT
        con_codigo, cte, con_status, tipo_documento, vlr_frete, vlr_receita_bruta AS vlr_receita_bruta_multi, sk_filial,
        sk_cliente, sk_cooperado, sk_documento, filial AS filial_contabil,
        car_codigo_carga_embarcador,
        DATE(data_hora_emissao)     AS data_emissao,
        split(cte, '-')[0]     AS serie_multi,
        split(cte, '-')[1]     AS num_doc_multi,
        tipo_operacao_anulacao, oco_anulacao, has_true, flag_anulacao, max_con_anulacao,
        cooperado, vei_placa, inicio_da_prestacao, fim_da_prestacao
    FROM (
        SELECT fo.*,
               ROW_NUMBER() OVER (PARTITION BY fo.con_codigo
                                  ORDER BY (CASE WHEN fo.con_status IN ('A') AND fo.car_situacao NOT IN (18, 13) AND fo.ped_situacao <> 2
                                                  AND NOT (fo.tipo_operacao_anulacao LIKE '%CIOT CANCELADO%')
                                                  AND NOT (fo.tipo_operacao_anulacao LIKE '%TRANSBORDO%' OR fo.tipo_operacao_anulacao LIKE '%REUTILIZACAO%'
                                                           OR (fo.tipo_operacao_anulacao LIKE '%REPASSE%' AND fo.tipo_documento = 'CT-e'))
                                                  AND (fo.oco_anulacao IS NULL OR fo.oco_anulacao = 0) AND fo.mod_abreviacao IS NOT NULL
                                                  AND fo.mod_abreviacao NOT IN ('DV', 'OST') AND fo.tipo_documento NOT IN ('CV', 'OST', 'NDA', 'DV')
                                                  AND ((fo.has_true = 1 AND fo.flag_anulacao = true AND fo.con_codigo = fo.max_con_anulacao)
                                                       OR (fo.has_true = 0 AND (fo.flag_anulacao = false OR fo.flag_anulacao IS NULL)))
                                                 THEN 0 ELSE 1 END) NULLS LAST, (CASE WHEN fo.ped_situacao = 2 THEN 1 ELSE 0 END) NULLS LAST, fo.data_hora_emissao DESC, fo.sk_documento DESC, fo.car_codigo_carga_embarcador DESC) AS rn
        FROM {env}_gold.fato_operacional fo
        WHERE fo.con_codigo IS NOT NULL
          AND fo.tipo_documento IS NOT NULL
          AND year(fo.data_hora_emissao) = 2026
    ) t
    WHERE t.rn = 1
),
painel_na_view AS (
    SELECT pvw.con_codigo,
           MAX(pvw.operacao_anulacao) AS operacao_anulacao,
           MAX(pvw.tipo_operacao)     AS tipo_operacao_painel,
           MAX(pvw.tipo_documento)    AS tipo_documento_painel,
           COUNT(*)                   AS qtd_linhas_painel,
           SUM(pvw.vlr_receita_bruta) AS vlr_painel_view,
           CASE WHEN COUNT(*) > 1 THEN datediff(MAX(cd.dt), MIN(cd.dt)) END AS variacao_dias_cargas
    FROM painel_view pvw
    LEFT JOIN (SELECT car_codigo_carga_embarcador AS k, MIN(car_data_criacao) AS dt
               FROM {env}_bronze.multi_dbo_t_carga GROUP BY car_codigo_carga_embarcador) cd
           ON cd.k = pvw.car_codigo_carga_embarcador
    WHERE pvw.con_codigo IS NOT NULL AND year(pvw.data_emissao) = 2026
    GROUP BY pvw.con_codigo
),
painel_rank AS (
    SELECT con_codigo,
           MAX(CASE WHEN con_status <> 'A'                                         THEN 1
                    WHEN car_situacao IN (18, 13)                                  THEN 2
                    WHEN ped_situacao = 2                                          THEN 3
                    WHEN tipo_operacao_anulacao LIKE '%CIOT CANCELADO%'            THEN 4
                    WHEN tipo_operacao_anulacao LIKE '%TRANSBORDO%'
                      OR tipo_operacao_anulacao LIKE '%REUTILIZACAO%'
                      OR (tipo_operacao_anulacao LIKE '%REPASSE%' AND tipo_documento = 'CT-e') THEN 5
                    WHEN NOT (oco_anulacao IS NULL OR oco_anulacao = 0)            THEN 6
                    WHEN mod_abreviacao IS NULL OR mod_abreviacao IN ('DV','OST')
                      OR tipo_documento IN ('CV','OST','NDA','DV')                 THEN 7
                    WHEN tipo_operacao_anulacao IS NULL                            THEN 8
                    ELSE 99 END) AS rk
    FROM {env}_gold.fato_operacional
    WHERE con_codigo IS NOT NULL AND year(data_hora_emissao) = 2026
    GROUP BY con_codigo
),
painel_motivo AS (
    SELECT dm.con_codigo, pv.qtd_linhas_painel, pv.vlr_painel_view, pv.variacao_dias_cargas,
        CASE WHEN pv.con_codigo IS NOT NULL THEN
                  CASE WHEN pv.operacao_anulacao = 'S'                                    THEN 'ANULACAO'
                       WHEN upper(pv.tipo_operacao_painel) LIKE '%REPASSE%'
                         OR upper(pv.tipo_operacao_painel) LIKE '%TRANSBORDO%'
                         OR upper(pv.tipo_operacao_painel) LIKE '%REUTILIZACAO%' THEN 'TRANSBORDO / REUTILIZACAO / REPASSE'
                       WHEN pv.tipo_documento_painel NOT IN ('COMPL FRETE','CT-e','ND','NFS','NFS-e') THEN 'TIPO DE DOCUMENTO FORA DO PAINEL'
                       ELSE NULL END
             ELSE CASE pr.rk WHEN 1 THEN 'STATUS DO DOCUMENTO DIFERENTE DE A'
                             WHEN 2 THEN 'CARGA CANCELADA'
                             WHEN 3 THEN 'PEDIDO CANCELADO'
                             WHEN 4 THEN 'CIOT CANCELADO'
                             WHEN 5 THEN 'TRANSBORDO / REUTILIZACAO / REPASSE'
                             WHEN 6 THEN 'OCORRENCIA DE ANULACAO'
                             WHEN 7 THEN 'TIPO DE DOCUMENTO FORA DO PAINEL'
                             WHEN 8 THEN 'SEM TIPO DE OPERACAO'
                             ELSE 'REGRA DE ANULACAO DA VIEW' END
        END AS motivo_fora_painel
    FROM doc_multi dm
    LEFT JOIN painel_na_view pv ON pv.con_codigo = dm.con_codigo
    LEFT JOIN painel_rank   pr ON pr.con_codigo = dm.con_codigo
),
doc_enriquecido AS (
    SELECT
        dm.con_codigo, dm.cte, dm.con_status, dm.tipo_documento, dm.vlr_frete, dm.vlr_receita_bruta_multi,
        pm.motivo_fora_painel, pm.qtd_linhas_painel, pm.vlr_painel_view, pm.variacao_dias_cargas,
        CASE WHEN pm.motivo_fora_painel IS NULL THEN 'SIM' ELSE 'NAO' END AS no_painel,
        dm.sk_filial AS sk_filial_fo, dm.sk_cliente, dm.sk_cooperado, dm.sk_documento, dm.filial_contabil,
        dm.car_codigo_carga_embarcador,
        dm.data_emissao, dm.serie_multi, dm.num_doc_multi,
        dm.tipo_operacao_anulacao, dm.oco_anulacao, dm.has_true,
        dm.flag_anulacao, dm.max_con_anulacao,
        dm.cooperado, dm.vei_placa, dm.inicio_da_prestacao, dm.fim_da_prestacao,
        ctp.pct_cpf_cnpj            AS cnpj_tomador,
        ctp.pct_nome                AS nome_tomador,
        gt.grupo_tomador,
        CASE WHEN gt.grupo_tomador IS NOT NULL THEN 'SIM' ELSE 'NAO' END AS tem_grupo_pagador,
        fil.nome_display            AS filial_multi,
        fm.sk_filial,
        fm.filial_duplicada,
        cen.ccv_codigo_integracao   AS filial_integracao,
        CASE WHEN fl.tem_ativa = 1        THEN 'ATIVA' ELSE 'CANCELADA' END AS situacao_carga,
        CASE WHEN fl.todos_nao_fiscal = 1 THEN 'NAO'   ELSE 'SIM'       END AS doc_fiscal,
        CASE WHEN COALESCE(cte_m.con_gerado_manualmente, FALSE)
               OR COALESCE(nmc.ped_possui_nfs_manual, FALSE)     THEN 'SIM' ELSE 'NAO'
        END                                                                 AS emissao_manual,
        CASE WHEN cip.qtd_ciot IS NULL OR cip.qtd_ciot = 0 THEN 'NAO APLICAVEL'
             WHEN cip.tem_ciot_ativo                      THEN 'VALIDO'
             ELSE 'CANCELADO'
        END                                                                 AS ciot,
        CASE WHEN dm.car_codigo_carga_embarcador IS NOT NULL      THEN 'COM CARGA'
             WHEN COALESCE(cte_m.con_sem_carga, FALSE)            THEN 'SEM CARGA - SERVICO AVULSO'
             ELSE 'SEM CARGA - GAP'
        END                                                                 AS vinculo_carga,
        fl.qtd_cargas, fl.multiplas_cargas, tx.mod_abreviacao, tx.tipodocumento,
        dc.tpt_codigo AS tipo_cooperado_codigo, dc.tpt_descricao AS tipo_cooperado
    FROM doc_multi dm
    LEFT JOIN painel_motivo pm ON pm.con_codigo = dm.con_codigo
    JOIN {env}_bronze.multi_dbo_t_cte cte_m
        ON cte_m.con_codigo = dm.con_codigo
    JOIN {env}_bronze.multi_dbo_t_cte_participante ctp
        ON ctp.pct_codigo = cte_m.con_tomador_pagador_cte
    LEFT JOIN grupo_tomador gt ON gt.grc_cnpj = SUBSTR(ctp.pct_cpf_cnpj, 1, 8)
    LEFT JOIN filial_multi_map fm ON fm.con_codigo = dm.con_codigo
    LEFT JOIN {env}_gold.dim_filial fil ON fil.sk_filial = fm.sk_filial
    LEFT JOIN {env}_bronze.multi_dbo_t_centro_custo_viagem cen ON cen.ccv_codigo = fil.ccv_codigo
    LEFT JOIN info_carga_flags fl ON fl.con_codigo = dm.con_codigo
    LEFT JOIN info_carga_texto tx ON tx.con_codigo = dm.con_codigo
    LEFT JOIN nfs_manual_por_carga nmc ON nmc.car_codigo_carga_embarcador = dm.car_codigo_carga_embarcador
    LEFT JOIN ciot_por_documento cip ON cip.con_codigo = dm.con_codigo
    LEFT JOIN {env}_gold.dim_cooperado dc ON dc.sk_cooperado = dm.sk_cooperado
),
cte_multi AS (
    SELECT * FROM doc_enriquecido WHERE tipo_documento = 'CT-e'
),
cte_kmm_p1_raw AS (
    SELECT
        cm.con_codigo,
        kcf.conhecimento_id,
        datediff(kcf.data_emissao_kmm, cm.data_emissao) AS match_gap_dias,
        1 AS match_priority,
        ROW_NUMBER() OVER (
            PARTITION BY cm.con_codigo
            ORDER BY ABS(datediff(kcf.data_emissao_kmm, cm.data_emissao)) NULLS LAST) AS rn
    FROM cte_multi cm
    JOIN kmm_enriquecido kcf
        ON cm.cte = kcf.cte_chave
       AND CAST(cm.cnpj_tomador AS bigint) = CAST(kcf.cob_cnpj_cpf AS bigint)
       AND ABS(datediff(kcf.data_emissao_kmm, cm.data_emissao)) <= 3
),
cte_kmm_p1_match AS (
    SELECT * FROM cte_kmm_p1_raw WHERE rn = 1
),
cte_kmm_p2_raw AS (
    SELECT
        cm.con_codigo,
        kcf.conhecimento_id,
        datediff(kcf.data_emissao_kmm, cm.data_emissao) AS match_gap_dias,
        2 AS match_priority,
        ROW_NUMBER() OVER (
            PARTITION BY cm.con_codigo
            ORDER BY ABS(datediff(kcf.data_emissao_kmm, cm.data_emissao)) NULLS LAST) AS rn
    FROM (
        SELECT c.*
        FROM cte_multi c
        LEFT JOIN cte_kmm_p1_match p1 ON p1.con_codigo = c.con_codigo
        WHERE p1.con_codigo IS NULL
    ) cm
    JOIN kmm_enriquecido kcf
        ON CAST(cm.cnpj_tomador AS bigint) = CAST(kcf.cob_cnpj_cpf AS bigint)
       AND ABS(kcf.valor_documento_kmm - cm.vlr_frete) <= 0.01
       AND ABS(datediff(kcf.data_emissao_kmm, cm.data_emissao)) <= 5
       AND (cm.con_status IN ('A','S')) = (kcf.cancelado IS NULL)
       AND kcf.conhecimento_id NOT IN (SELECT conhecimento_id FROM cte_kmm_p1_match)
),
cte_kmm_p2_match AS (
    SELECT con_codigo, conhecimento_id, match_gap_dias, match_priority
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY conhecimento_id
                                  ORDER BY ABS(match_gap_dias) NULLS LAST, con_codigo NULLS LAST) AS rn_kmm
        FROM cte_kmm_p2_raw
        WHERE rn = 1
    ) WHERE rn_kmm = 1
),
cte_kmm_match AS (
    SELECT con_codigo, conhecimento_id, match_gap_dias, match_priority FROM cte_kmm_p1_match
    UNION ALL
    SELECT con_codigo, conhecimento_id, match_gap_dias, match_priority FROM cte_kmm_p2_match
),
nf_multi AS (
    SELECT de.*,
        CASE de.tipo_documento
            WHEN 'NFS'   THEN array('X1')
            WHEN 'NFS-e' THEN array('X1')
            ELSE CAST(array() AS ARRAY<STRING>)
        END AS modelos_kmm,
        CASE WHEN de.tipo_documento IN ('OST','DV','CV','ND','NDA')
             THEN 'NAO FISCAL' ELSE 'FISCAL'
        END AS escopo_kmm
    FROM doc_enriquecido de
    WHERE de.tipo_documento <> 'CT-e'
),
nf_candidatos_raw AS (
    SELECT
        nm.con_codigo, nm.cte, nm.tipo_documento, nm.cnpj_tomador,
        nm.vlr_frete, nm.data_emissao, nm.serie_multi, nm.filial_integracao,
        kn.num_nota_id, kn.serie AS serie_kmm, kn.cod_centro_custo, kn.cod_modelo,
        kn.cancelada,
        kn.user_insert AS usuario_doc_kmm,
        (nm.con_status IN ('A','S')) AS nm_ativo,
        kn.calc_valor_total_nota AS valor_documento_kmm,
        kn.calc_valor_icms       AS valor_icms_kmm,
        kn.serv_iss_valor        AS valor_iss_kmm,
        datediff(DATE(kn.data_emissao), nm.data_emissao) AS match_gap_dias,
        org.cod_unidade_negocio AS unidade_negocio_kmm,
        CASE
            WHEN CAST(kn.serie AS STRING) = nm.serie_multi
             AND CAST(kn.dest_cnpj_cpf AS bigint) = CAST(nm.cnpj_tomador AS bigint)
             AND CAST(org.cod_unidade_negocio AS STRING) = nm.filial_integracao
             AND DATE(kn.data_emissao) = nm.data_emissao
             AND kn.calc_valor_total_nota = nm.vlr_frete   THEN 1
            WHEN CAST(kn.serie AS STRING) = nm.serie_multi
             AND CAST(kn.dest_cnpj_cpf AS bigint) = CAST(nm.cnpj_tomador AS bigint)
             AND DATE(kn.data_emissao) = nm.data_emissao
             AND kn.calc_valor_total_nota = nm.vlr_frete   THEN 2
            WHEN CAST(kn.serie AS STRING) = nm.serie_multi
             AND CAST(kn.dest_cnpj_cpf AS bigint) = CAST(nm.cnpj_tomador AS bigint)
             AND DATE(kn.data_emissao) = nm.data_emissao   THEN 3
            WHEN CAST(kn.serie AS STRING) = nm.serie_multi
             AND CAST(kn.dest_cnpj_cpf AS bigint) = CAST(nm.cnpj_tomador AS bigint)
             AND kn.calc_valor_total_nota = nm.vlr_frete   THEN 4
            WHEN CAST(kn.serie AS STRING) = nm.serie_multi
             AND CAST(kn.dest_cnpj_cpf AS bigint) = CAST(nm.cnpj_tomador AS bigint)
                                                          THEN 5
            WHEN nm.con_status IN ('A','S')
             AND CAST(kn.dest_cnpj_cpf AS bigint) = CAST(nm.cnpj_tomador AS bigint)
             AND kn.calc_valor_total_nota = nm.vlr_frete
             AND DATE(kn.data_emissao) = nm.data_emissao   THEN 6
            WHEN nm.con_status IN ('A','S')
             AND CAST(kn.dest_cnpj_cpf AS bigint) = CAST(nm.cnpj_tomador AS bigint)
             AND kn.calc_valor_total_nota = nm.vlr_frete   THEN 7
            WHEN (nm.con_status IN ('A','S') OR kn.cancelada = 1)
             AND CAST(kn.dest_cnpj_cpf AS bigint) = CAST(nm.cnpj_tomador AS bigint)
             AND ABS(datediff(DATE(kn.data_emissao), nm.data_emissao)) <= 3
             AND ABS(kn.calc_valor_total_nota - nm.vlr_frete) <= 0.05 THEN 8
        END AS match_priority
    FROM nf_multi nm
    JOIN {env}_bronze.kmm_fiscal_nf_es kn
        ON CAST(CAST(kn.num_nota_fiscal AS bigint) AS STRING) = nm.num_doc_multi
       AND array_contains(nm.modelos_kmm, kn.cod_modelo)
    LEFT JOIN {env}_bronze.kmm_kss_organograma org ON kn.cod_centro_custo = org.cod_centro_custo
),
nf_kmm_match AS (
    SELECT * FROM (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY con_codigo
                                  ORDER BY (CASE WHEN (nm_ativo = (cancelada = 0)) THEN 0 ELSE 1 END) NULLS LAST, match_priority NULLS LAST, num_nota_id NULLS LAST) AS rn
        FROM nf_candidatos_raw
        WHERE match_priority IS NOT NULL
    ) WHERE rn = 1
),
receber_fallback_cte_raw AS (
    SELECT
        cm.con_codigo,
        kr.contas_receber_id,
        kr.num_docto,
        kr.valor_docto,
        DATE(kr.data_emissao) AS data_emissao_estimada,
        datediff(DATE(kr.data_emissao), cm.data_emissao) AS gap_dias,
        ROW_NUMBER() OVER (PARTITION BY cm.con_codigo
                           ORDER BY ABS(datediff(DATE(kr.data_emissao), cm.data_emissao)) NULLS LAST) AS rn
    FROM (
        SELECT c.*
        FROM cte_multi c
        LEFT JOIN cte_kmm_match ckm ON ckm.con_codigo = c.con_codigo
        WHERE ckm.con_codigo IS NULL AND c.con_status IN ('A','S')
    ) cm
    JOIN {env}_bronze.kmm_kss_pessoa pc ON CAST(pc.cnpj_cpf AS bigint) = CAST(cm.cnpj_tomador AS bigint)
    JOIN {env}_bronze.kmm_finan_finan_contas_receber kr
        ON kr.cod_pessoa = pc.cod_pessoa
       AND ABS(kr.valor_docto - cm.vlr_frete) <= 0.01
       AND ABS(datediff(DATE(kr.data_emissao), cm.data_emissao)) <= 5
       AND kr.cancelado = 0
       AND kr.data_estorno IS NULL
),
receber_fallback_cte_match AS (
    SELECT con_codigo, contas_receber_id, num_docto, valor_docto, data_emissao_estimada, gap_dias
    FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY contas_receber_id
                                     ORDER BY ABS(gap_dias) NULLS LAST, con_codigo NULLS LAST) AS rn_kr
        FROM receber_fallback_cte_raw
        WHERE rn = 1
    ) WHERE rn_kr = 1
),
receber_fallback_nf_raw AS (
    SELECT
        nm.con_codigo,
        kr.contas_receber_id,
        kr.num_docto,
        kr.valor_docto,
        DATE(kr.data_emissao) AS data_emissao_estimada,
        datediff(DATE(kr.data_emissao), nm.data_emissao) AS gap_dias,
        ROW_NUMBER() OVER (PARTITION BY nm.con_codigo
                           ORDER BY ABS(datediff(DATE(kr.data_emissao), nm.data_emissao)) NULLS LAST) AS rn
    FROM (
        SELECT n.*
        FROM nf_multi n
        LEFT JOIN nf_kmm_match nkm ON nkm.con_codigo = n.con_codigo
        WHERE nkm.con_codigo IS NULL AND n.con_status IN ('A','S') AND n.escopo_kmm = 'FISCAL'
    ) nm
    JOIN {env}_bronze.kmm_kss_pessoa pc ON CAST(pc.cnpj_cpf AS bigint) = CAST(nm.cnpj_tomador AS bigint)
    JOIN {env}_bronze.kmm_finan_finan_contas_receber kr
        ON kr.cod_pessoa = pc.cod_pessoa
       AND ABS(kr.valor_docto - nm.vlr_frete) <= 0.01
       AND ABS(datediff(DATE(kr.data_emissao), nm.data_emissao)) <= 5
       AND kr.cancelado = 0
       AND kr.data_estorno IS NULL
),
receber_fallback_nf_match AS (
    SELECT con_codigo, contas_receber_id, num_docto, valor_docto, data_emissao_estimada, gap_dias
    FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY contas_receber_id
                                     ORDER BY ABS(gap_dias) NULLS LAST, con_codigo NULLS LAST) AS rn_kr
        FROM receber_fallback_nf_raw
        WHERE rn = 1
    ) WHERE rn_kr = 1
),
receber_pago AS (
    SELECT contas_receber_id,
        SUM(valor_amortizacao)          AS valor_pago,
        MAX(DATE(data_amortizacao))     AS data_ultima_amortizacao
    FROM {env}_bronze.kmm_finan_finan_contas_receber_amort
    WHERE (amort_cancelado = 0 OR amort_cancelado IS NULL) AND data_estorno IS NULL
    GROUP BY contas_receber_id
),
receber_juro AS (
    SELECT contas_receber_id, SUM(valor_juro) AS valor_juro
    FROM {env}_bronze.kmm_finan_finan_contas_receber_juro
    WHERE (estorno_juro = 0 OR estorno_juro IS NULL) AND data_estorno IS NULL
    GROUP BY contas_receber_id
),
receber_desconto AS (
    SELECT contas_receber_id, SUM(valor_desconto) AS valor_desconto,
           SUM(CASE WHEN desconto_devolucao = 1 THEN valor_desconto ELSE 0 END) AS valor_desconto_devolucao
    FROM {env}_bronze.kmm_finan_finan_contas_receber_desc
    WHERE data_estorno IS NULL
    GROUP BY contas_receber_id
),
fatura_cte AS (
    SELECT
        kcr.conhecimento_id,
        COUNT(DISTINCT kr.contas_receber_id)               AS qtd_parcelas,
        COUNT(DISTINCT kr.num_docto)                       AS qtd_faturas,
        array_join(array_sort(collect_set(kr.num_docto)), ', ') AS num_fatura,
        array_join(array_sort(collect_set(kr.docto_id)), ', ')  AS tipo_docto_fatura,
        SUM(kr.valor_docto)                                AS valor_fatura,
        MIN(DATE(kr.data_vencto))                          AS venc_primeiro,
        MAX(DATE(kr.data_vencto))                          AS venc_ultimo,
        MIN(DATE(kr.data_emissao))                         AS data_emissao_fatura,
        array_join(array_sort(collect_set(kr.user_insert)), ', ') AS usuario_fatura,
        SUM(COALESCE(rp.valor_pago,0))                     AS valor_pago_receber,
        SUM(COALESCE(rj.valor_juro,0))                     AS valor_juro_receber,
        SUM(COALESCE(rd.valor_desconto,0))                 AS valor_desconto_receber,
        SUM(COALESCE(rd.valor_desconto_devolucao,0))       AS valor_desconto_devolucao_receber,
        array_join(array_sort(collect_set(CAST(CAST(kr.contas_receber_id AS bigint) AS STRING))), ', ') AS ids_titulo_receber,
        MAX(COALESCE(rp.data_ultima_amortizacao, DATE(kr.data_vencto))) AS data_ref_receber,
        MAX(CASE WHEN rp.data_ultima_amortizacao IS NULL THEN 1 ELSE 0 END) AS receber_tem_parcela_estimada
    FROM (
        SELECT DISTINCT conhecimento_id, contas_receber_id
        FROM {env}_bronze.kmm_fiscal_conhecimento_receber
        WHERE data_cancelamento IS NULL
    ) kcr
    JOIN {env}_bronze.kmm_finan_finan_contas_receber kr
        ON kr.contas_receber_id = kcr.contas_receber_id
       AND kr.data_estorno IS NULL
       AND kr.cancelado = 0
    LEFT JOIN receber_pago rp     ON rp.contas_receber_id = kr.contas_receber_id
    LEFT JOIN receber_juro rj     ON rj.contas_receber_id = kr.contas_receber_id
    LEFT JOIN receber_desconto rd ON rd.contas_receber_id = kr.contas_receber_id
    GROUP BY kcr.conhecimento_id
),
fatura_nf AS (
    SELECT
        r.num_nota_id,
        COUNT(DISTINCT kr.contas_receber_id)               AS qtd_parcelas,
        COUNT(DISTINCT kr.num_docto)                       AS qtd_faturas,
        array_join(array_sort(collect_set(kr.num_docto)), ', ') AS num_fatura,
        array_join(array_sort(collect_set(kr.docto_id)), ', ')  AS tipo_docto_fatura,
        SUM(kr.valor_docto)                                AS valor_fatura,
        MIN(DATE(kr.data_vencto))                          AS venc_primeiro,
        MAX(DATE(kr.data_vencto))                          AS venc_ultimo,
        MIN(DATE(kr.data_emissao))                         AS data_emissao_fatura,
        array_join(array_sort(collect_set(kr.user_insert)), ', ') AS usuario_fatura,
        SUM(COALESCE(rp.valor_pago,0))                     AS valor_pago_receber,
        SUM(COALESCE(rj.valor_juro,0))                     AS valor_juro_receber,
        SUM(COALESCE(rd.valor_desconto,0))                 AS valor_desconto_receber,
        SUM(COALESCE(rd.valor_desconto_devolucao,0))       AS valor_desconto_devolucao_receber,
        array_join(array_sort(collect_set(CAST(CAST(kr.contas_receber_id AS bigint) AS STRING))), ', ') AS ids_titulo_receber,
        MAX(COALESCE(rp.data_ultima_amortizacao, DATE(kr.data_vencto))) AS data_ref_receber,
        MAX(CASE WHEN rp.data_ultima_amortizacao IS NULL THEN 1 ELSE 0 END) AS receber_tem_parcela_estimada
    FROM (
        SELECT DISTINCT num_nota_id, contas_receber_id
        FROM {env}_bronze.kmm_fiscal_nf_es_receber
    ) r
    JOIN {env}_bronze.kmm_finan_finan_contas_receber kr
        ON kr.contas_receber_id = r.contas_receber_id
       AND kr.data_estorno IS NULL
       AND kr.cancelado = 0
    LEFT JOIN receber_pago rp     ON rp.contas_receber_id = kr.contas_receber_id
    LEFT JOIN receber_juro rj     ON rj.contas_receber_id = kr.contas_receber_id
    LEFT JOIN receber_desconto rd ON rd.contas_receber_id = kr.contas_receber_id
    GROUP BY r.num_nota_id
),
fatura_cancelada_cte AS (
    SELECT DISTINCT kcr.conhecimento_id
    FROM {env}_bronze.kmm_fiscal_conhecimento_receber kcr
    JOIN {env}_bronze.kmm_finan_finan_contas_receber kr ON kr.contas_receber_id = kcr.contas_receber_id
    WHERE kr.cancelado = 1 OR kr.data_estorno IS NOT NULL
),
fatura_cancelada_nf AS (
    SELECT DISTINCT r.num_nota_id
    FROM {env}_bronze.kmm_fiscal_nf_es_receber r
    JOIN {env}_bronze.kmm_finan_finan_contas_receber kr ON kr.contas_receber_id = r.contas_receber_id
    WHERE kr.cancelado = 1 OR kr.data_estorno IS NOT NULL
),
avulso_multi AS (
    SELECT
        pm.pam_codigo, pm.pam_numero, pm.pam_valor, pm.pam_data_pagamento,
        pm.car_codigo,
        COALESCE(CAST(NULLIF(trim(cli.cli_cnpjcpf), '') AS bigint),
                 CAST(cu.cli_cgccpf_terceiro AS bigint)) AS cnpj_transportador,
        cu.car_codigo_carga_embarcador,
        cu.car_situacao
    FROM {env}_bronze.multi_dbo_t_pagamento_motorista_tms pm
    JOIN {env}_bronze.multi_dbo_t_carga cu ON cu.car_codigo = pm.car_codigo
    LEFT JOIN {env}_bronze.multi_dbo_t_cliente cli ON cli.cli_cgccpf = cu.cli_cgccpf_terceiro
    WHERE pm.pam_situacao IN (2, 10)
      AND year(pm.pam_data_pagamento) = 2026
),
custo_ocorrencia_por_carga AS (
    SELECT car_codigo_carga_embarcador, SUM(pam_valor) AS custo_ocorrencia
    FROM avulso_multi
    GROUP BY car_codigo_carga_embarcador
),
avulso_enriquecido AS (
    SELECT DISTINCT
        av.*,
        pc.cod_pessoa    AS cod_pessoa_kmm,
        pc.razao_social  AS cooperado
    FROM avulso_multi av
    LEFT JOIN {env}_bronze.kmm_kss_pessoa pc ON av.cnpj_transportador = CAST(pc.cnpj_cpf AS bigint)
),
avulso_kmm_raw AS (
    SELECT
        av.pam_codigo, z.lancto_id, z.num_formulario, z.data_cancelamento, z.proprietario_cod_pessoa,
        z.user_insert          AS usuario_doc_kmm,
        z.valor_frete_bruto    AS valor_contrato_bruto,
        z.valor_frete_liquido  AS valor_contrato_liquido,
        ROW_NUMBER() OVER (
            PARTITION BY av.pam_codigo
            ORDER BY (CASE WHEN z.data_cancelamento IS NULL THEN 0 ELSE 1 END) NULLS LAST, z.lancto_id DESC) AS rn
    FROM avulso_enriquecido av
    JOIN {env}_bronze.kmm_contrato_contrato_transp z
        ON z.num_formulario = av.pam_numero
       AND z.serie_formulario = 'P'
       AND z.proprietario_cod_pessoa = av.cod_pessoa_kmm
),
avulso_kmm_match AS (
    SELECT * FROM avulso_kmm_raw WHERE rn = 1
),
titulo_pagar_por_lancto AS (
    SELECT * FROM (
        SELECT dcp.*,
               ROW_NUMBER() OVER (PARTITION BY dcp.lancto_id ORDER BY dcp.adiantamento_saldo DESC) AS rn
        FROM {env}_bronze.kmm_contrato_contrato_transp_pagar dcp
    ) WHERE rn = 1
),
pagar_pago AS (
    SELECT contas_pagar_id,
        SUM(valor_amortizacao)      AS valor_pago,
        MAX(DATE(data_amortizacao)) AS data_ultima_amortizacao
    FROM {env}_bronze.kmm_finan_finan_contas_pagar_amort
    WHERE data_estorno IS NULL
    GROUP BY contas_pagar_id
),
pagar_juro AS (
    SELECT contas_pagar_id, SUM(valor_juro) AS valor_juro
    FROM {env}_bronze.kmm_finan_finan_contas_pagar_juro
    WHERE data_estorno IS NULL
    GROUP BY contas_pagar_id
),
pagar_desconto AS (
    SELECT contas_pagar_id, SUM(valor_desconto) AS valor_desconto
    FROM {env}_bronze.kmm_finan_finan_contas_pagar_desc
    WHERE data_estorno IS NULL
    GROUP BY contas_pagar_id
),
titulo_pagar_estornado AS (
    SELECT DISTINCT z.num_formulario
    FROM {env}_bronze.kmm_contrato_contrato_transp z
    JOIN {env}_bronze.kmm_contrato_contrato_transp_pagar dcp ON dcp.lancto_id = z.lancto_id
    JOIN {env}_bronze.kmm_finan_finan_contas_pagar cp ON cp.contas_pagar_id = dcp.contas_pagar_id
    WHERE cp.data_estorno IS NOT NULL
),
pagar_agregado AS (
    SELECT t.lancto_id,
        MAX(cp.contas_pagar_id)                                     AS contas_pagar_id,
        array_join(array_sort(collect_set(CAST(cp.num_docto AS STRING))), ', ') AS num_docto,
        MAX_BY(cp.user_insert, cp.contas_pagar_id)                  AS user_insert,
        COALESCE(SUM(cp.valor_docto) FILTER (WHERE cp.data_estorno IS NULL), SUM(cp.valor_docto)) AS valor_docto,
        COALESCE(SUM(pp.valor_pago) FILTER (WHERE cp.data_estorno IS NULL), SUM(pp.valor_pago))   AS valor_pago,
        COALESCE(SUM(pj.valor_juro) FILTER (WHERE cp.data_estorno IS NULL), SUM(pj.valor_juro))   AS valor_juro,
        COALESCE(SUM(pd.valor_desconto) FILTER (WHERE cp.data_estorno IS NULL), SUM(pd.valor_desconto)) AS valor_desconto,
        MAX(COALESCE(pp.data_ultima_amortizacao, DATE(cp.data_vencto))) AS data_ref,
        MAX(CASE WHEN pp.data_ultima_amortizacao IS NULL THEN 1 ELSE 0 END) AS tem_estimado,
        CASE WHEN COUNT_IF(cp.data_estorno IS NULL) > 0 THEN NULL ELSE MAX(cp.data_estorno) END AS data_estorno
    FROM (SELECT DISTINCT lancto_id, contas_pagar_id
          FROM {env}_bronze.kmm_contrato_contrato_transp_pagar) t
    JOIN {env}_bronze.kmm_finan_finan_contas_pagar cp ON cp.contas_pagar_id = t.contas_pagar_id
    LEFT JOIN pagar_pago pp     ON pp.contas_pagar_id = cp.contas_pagar_id
    LEFT JOIN pagar_juro pj     ON pj.contas_pagar_id = cp.contas_pagar_id
    LEFT JOIN pagar_desconto pd ON pd.contas_pagar_id = cp.contas_pagar_id
    GROUP BY t.lancto_id
),
cft_pagar_raw AS (
    SELECT
        cu.car_codigo,
        cu.car_codigo_carga_embarcador,
        cft.cft_numero_contrato AS contrato,
        cp.num_docto AS num_titulo_pagar,
        cp.contas_pagar_id,
        cp.valor_docto AS valor_titulo_pagar,
        cp.user_insert AS usuario_titulo_pagar,
        cp.valor_pago     AS valor_pago_pagar,
        cp.valor_juro     AS valor_juro_pagar,
        cp.valor_desconto AS valor_desconto_pagar,
        cp.data_ref AS data_ref_pagar,
        cp.tem_estimado AS pagar_tem_estimado,
        z.valor_frete_bruto    AS valor_contrato_bruto,
        z.valor_frete_liquido  AS valor_contrato_liquido,
        z.lancto_id  AS pagar_lancto_id,
        z.data_cancelamento AS contrato_data_cancelamento_kmm,
        z.serie_formulario AS operador_contrato,
        (tpe.num_formulario IS NOT NULL) AS teve_titulo_pagar_estornado,
        cp.data_estorno AS titulo_pagar_data_estorno,
        ROW_NUMBER() OVER (
            PARTITION BY cu.car_codigo_carga_embarcador
            ORDER BY (CASE WHEN cp.contas_pagar_id IS NULL THEN 1 ELSE 0 END) NULLS LAST, (CASE WHEN z.lancto_id IS NULL THEN 1 ELSE 0 END) NULLS LAST, (CASE WHEN z.data_cancelamento IS NOT NULL THEN 1 ELSE 0 END) NULLS LAST, (CASE WHEN cp.data_estorno IS NOT NULL THEN 1 ELSE 0 END) NULLS LAST, cp.contas_pagar_id DESC) AS rn
    FROM {env}_bronze.multi_dbo_t_carga cu
    JOIN {env}_bronze.multi_dbo_t_contrato_frete_terceiro cft
        ON cft.car_codigo = cu.car_codigo
       AND cft.cft_contrato_frete <> 3
    LEFT JOIN {env}_bronze.kmm_contrato_contrato_transp z
        ON z.num_formulario = cft.cft_numero_contrato
       AND z.serie_formulario IN ('U','REPOMFRETE','EFRETE','RI','RIC','EXTRATTA',
                                   'UC','REPOMFRETEC','EFRETEC','RIC','EXTRATTAC',
                                   'UCC','REPOMFRETECC','EFRETECC','UCCC','UCCCC','EXTRATTACC')
    LEFT JOIN pagar_agregado cp ON cp.lancto_id = z.lancto_id
    LEFT JOIN titulo_pagar_estornado tpe ON tpe.num_formulario = z.num_formulario
),
cft_pagar AS (
    SELECT * FROM cft_pagar_raw WHERE rn = 1
),
cft_pagar_por_car_codigo AS (
    SELECT * FROM (
        SELECT cfr.*,
               ROW_NUMBER() OVER (
                     PARTITION BY cfr.car_codigo
                     ORDER BY (CASE WHEN cfr.contas_pagar_id IS NULL THEN 1 ELSE 0 END) NULLS LAST, (CASE WHEN cfr.pagar_lancto_id IS NULL THEN 1 ELSE 0 END) NULLS LAST, cfr.contas_pagar_id DESC) AS rn2
        FROM cft_pagar_raw cfr
    ) WHERE rn2 = 1
),
custo_ocorrencia_por_car_codigo AS (
    SELECT car_codigo, SUM(pam_valor) AS custo_ocorrencia
    FROM avulso_multi
    GROUP BY car_codigo
),
conciliacao AS (
SELECT
    'CT-e'                                                     AS tipo_analise,
    year(cm.data_emissao)                                      AS ano_emissao,
    cm.tipo_documento,
    cm.cte, cm.con_codigo, cm.con_status,
    cm.car_codigo_carga_embarcador,
    cm.sk_filial, cm.sk_cliente, cm.sk_cooperado, cm.sk_documento,
    CASE cm.con_status
        WHEN 'A' THEN 'Autorizado'  WHEN 'S' THEN 'Substituido'
        WHEN 'C' THEN 'Cancelado'   WHEN 'I' THEN 'Inutilizado'
        WHEN 'R' THEN 'Rejeitado'   WHEN 'Z' THEN 'Denegado'
        ELSE cm.con_status
    END                                                        AS status_multi_descricao,
    cm.data_emissao,
    cm.cnpj_tomador, cm.nome_tomador, cm.grupo_tomador, cm.tem_grupo_pagador, cm.filial_multi, cm.filial_duplicada,
    cm.cooperado, cm.vei_placa, cm.inicio_da_prestacao, cm.fim_da_prestacao,
    cm.situacao_carga, cm.doc_fiscal, cm.emissao_manual, cm.qtd_cargas, cm.multiplas_cargas,
    cm.mod_abreviacao, cm.tipodocumento,
    cm.ciot,
    cm.vinculo_carga,
    CASE WHEN cm.tipo_operacao_anulacao LIKE '%TRANSBORDO%'     THEN 'SIM'       ELSE 'NAO'    END AS transbordo,
    CASE WHEN cm.oco_anulacao IS NOT NULL
          OR ((cm.has_true = 0) AND (cm.flag_anulacao = FALSE) AND (cm.con_codigo = cm.max_con_anulacao))
          OR ((cm.has_true = 1) AND (cm.flag_anulacao = TRUE OR cm.flag_anulacao IS NOT NULL))
         THEN 'SIM' ELSE 'NAO' END                             AS anulacao,
    kcf.conhecimento_id                                        AS kmm_doc_id,
    kcf.filial_kmm,
    cm.filial_contabil,
    CAST(kcf.unidade_negocio AS STRING)                       AS unidade_negocio_kmm,
    kcf.origem_mapeamento,
    CASE WHEN kcf.conhecimento_id IS NULL THEN NULL
         WHEN kcf.cancelado IS NULL THEN 'Ativo' ELSE 'Cancelado'
    END                                                        AS status_kmm_descricao,
    CAST(NULL AS STRING)                                      AS match_priority_nf,
    ckm.match_gap_dias,
    CASE WHEN ckm.match_gap_dias IS NULL THEN NULL
         WHEN ckm.match_priority = 2     THEN 'DIVERGENTE'
         WHEN ckm.match_gap_dias = 0     THEN 'EXATO'
         ELSE 'PROXIMO'
    END                                                         AS match_confianca,
    kcf.valor_documento_kmm, kcf.valor_icms_kmm, kcf.valor_iss_kmm,
    fc.num_fatura, fc.tipo_docto_fatura, fc.qtd_faturas, fc.qtd_parcelas,
    fc.valor_fatura, fc.venc_primeiro, fc.venc_ultimo, fc.usuario_fatura,
    CASE WHEN fc.num_fatura IS NOT NULL THEN 'FATURADO'
         WHEN kcf.conhecimento_id IS NOT NULL THEN 'SEM FATURA'
         ELSE NULL
    END                                                        AS status_fatura,
    CASE WHEN kcf.conhecimento_id IS NULL     THEN NULL
         WHEN fcc.conhecimento_id IS NULL     THEN 'NUNCA CANCELADA'
         WHEN fc.num_fatura IS NOT NULL       THEN 'CANCELADA E REEMITIDA'
         ELSE 'CANCELADA SEM REEMISSAO'
    END                                                        AS fatura_cancelada_kmm,
    fc.valor_pago_receber, fc.valor_juro_receber, fc.valor_desconto_receber,
    CASE WHEN fc.num_fatura IS NULL THEN NULL
         ELSE CASE WHEN (fc.valor_fatura + COALESCE(fc.valor_juro_receber,0) - COALESCE(fc.valor_desconto_receber,0) - COALESCE(fc.valor_pago_receber,0)) IS NULL OR (0) IS NULL THEN NULL ELSE greatest(fc.valor_fatura + COALESCE(fc.valor_juro_receber,0) - COALESCE(fc.valor_desconto_receber,0) - COALESCE(fc.valor_pago_receber,0), 0) END
    END                                                        AS saldo_aberto_receber,
    CASE WHEN fc.num_fatura IS NULL THEN NULL
         WHEN COALESCE(fc.valor_pago_receber,0) <= 0.005
          AND fc.valor_fatura + COALESCE(fc.valor_juro_receber,0) - COALESCE(fc.valor_desconto_receber,0) <= 0.01 THEN 'LIQUIDADO POR DESCONTO'
         WHEN COALESCE(fc.valor_pago_receber,0) <= 0.005 THEN 'EM ABERTO'
         WHEN fc.valor_pago_receber >= (fc.valor_fatura + COALESCE(fc.valor_juro_receber,0) - COALESCE(fc.valor_desconto_receber,0)) - 0.01 THEN 'QUITADO'
         ELSE 'PAGAMENTO PARCIAL'
    END                                                        AS status_pagamento_receber,
    fc.valor_desconto_devolucao_receber                       AS valor_desconto_devolucao_receber,
    fc.ids_titulo_receber                                      AS ids_titulo_receber,
    datediff(fc.data_emissao_fatura, cm.data_emissao)  AS dias_emissao_ate_faturamento,
    fc.data_emissao_fatura,
    CASE WHEN (cm.situacao_carga = 'ATIVA' AND cm.con_status IN ('A','S')) THEN cfp.contrato ELSE NULL END AS contrato,
    CASE WHEN NOT ((cm.situacao_carga = 'ATIVA' AND cm.con_status IN ('A','S')) AND cm.con_status IN ('A','S')) OR cfp.contrato IS NULL THEN NULL
         WHEN cfp.contrato_data_cancelamento_kmm IS NOT NULL          THEN 'SIM'
         ELSE 'NAO'
    END                                                        AS contrato_cancelado_kmm,
    CAST(NULL AS integer)                                     AS contrato_avulso,
    CASE WHEN (cm.situacao_carga = 'ATIVA' AND cm.con_status IN ('A','S')) THEN cfp.valor_contrato_bruto   ELSE NULL END AS valor_contrato_bruto,
    CASE WHEN (cm.situacao_carga = 'ATIVA' AND cm.con_status IN ('A','S')) THEN cfp.valor_contrato_liquido ELSE NULL END AS valor_contrato_liquido,
    CASE WHEN (cm.situacao_carga = 'ATIVA' AND cm.con_status IN ('A','S')) THEN cfp.num_titulo_pagar ELSE NULL END AS num_titulo_pagar,
    CASE WHEN (cm.situacao_carga = 'ATIVA' AND cm.con_status IN ('A','S')) THEN cfp.valor_titulo_pagar ELSE NULL END AS valor_titulo_pagar,
    CASE WHEN (cm.situacao_carga = 'ATIVA' AND cm.con_status IN ('A','S')) THEN cfp.usuario_titulo_pagar ELSE NULL END AS usuario_titulo_pagar,
    CASE WHEN NOT ((cm.situacao_carga = 'ATIVA' AND cm.con_status IN ('A','S')) AND cm.con_status IN ('A','S'))                      THEN 'NAO APLICAVEL - DOCUMENTO CANCELADO'
         WHEN cfp.titulo_pagar_data_estorno IS NOT NULL        THEN 'ESTORNADO'
         WHEN cfp.num_titulo_pagar IS NOT NULL                 THEN 'FATURADO'
         WHEN cfp.car_codigo_carga_embarcador IS NOT NULL      THEN 'SEM FATURA PAGAR'
         ELSE NULL
    END                                                        AS status_fatura_pagar,
    CASE WHEN NOT ((cm.situacao_carga = 'ATIVA' AND cm.con_status IN ('A','S')) AND cm.con_status IN ('A','S')) OR cfp.contrato IS NULL THEN NULL
         WHEN NOT cfp.teve_titulo_pagar_estornado                   THEN 'NUNCA CANCELADA'
         WHEN cfp.num_titulo_pagar IS NOT NULL
              AND cfp.titulo_pagar_data_estorno IS NULL             THEN 'CANCELADA E REEMITIDA'
         ELSE 'CANCELADA SEM REEMISSAO'
    END                                                        AS fatura_pagar_cancelada_kmm,
    CASE WHEN (cm.situacao_carga = 'ATIVA' AND cm.con_status IN ('A','S')) THEN cfp.valor_pago_pagar     ELSE NULL END AS valor_pago_pagar,
    CASE WHEN (cm.situacao_carga = 'ATIVA' AND cm.con_status IN ('A','S')) THEN cfp.valor_juro_pagar     ELSE NULL END AS valor_juro_pagar,
    CASE WHEN (cm.situacao_carga = 'ATIVA' AND cm.con_status IN ('A','S')) THEN cfp.valor_desconto_pagar ELSE NULL END AS valor_desconto_pagar,
    coc.custo_ocorrencia,
    CASE WHEN NOT ((cm.situacao_carga = 'ATIVA' AND cm.con_status IN ('A','S')) AND cm.con_status IN ('A','S')) OR cfp.num_titulo_pagar IS NULL THEN NULL
         WHEN cfp.titulo_pagar_data_estorno IS NOT NULL THEN 'ESTORNADO'
         WHEN COALESCE(cfp.valor_pago_pagar,0) <= 0.005 THEN 'EM ABERTO'
         WHEN cfp.valor_pago_pagar >= (cfp.valor_titulo_pagar + COALESCE(cfp.valor_juro_pagar,0) - COALESCE(cfp.valor_desconto_pagar,0)) - 0.01 THEN 'QUITADO'
         ELSE 'PAGAMENTO PARCIAL'
    END                                                        AS status_pagamento_pagar,
    CASE WHEN (cm.situacao_carga = 'ATIVA' AND cm.con_status IN ('A','S')) THEN cfp.data_ref_pagar ELSE NULL END AS data_ref_pagar,
    fc.data_ref_receber,
    CASE WHEN (cm.situacao_carga = 'ATIVA' AND cm.con_status IN ('A','S')) AND cfp.data_ref_pagar IS NOT NULL AND fc.data_ref_receber IS NOT NULL
         THEN datediff(fc.data_ref_receber, cfp.data_ref_pagar)
         ELSE NULL
    END                                                        AS prazo_dias,
    CASE WHEN NOT ((cm.situacao_carga = 'ATIVA' AND cm.con_status IN ('A','S')) AND cm.con_status IN ('A','S')) OR cfp.data_ref_pagar IS NULL OR fc.data_ref_receber IS NULL THEN NULL
         WHEN COALESCE(cfp.pagar_tem_estimado,1) = 0 AND COALESCE(fc.receber_tem_parcela_estimada,1) = 0 THEN 'REAL'
         ELSE 'ESTIMADO'
    END                                                        AS prazo_tipo,
    CASE WHEN fc.valor_fatura IS NULL THEN NULL
         ELSE fc.valor_fatura - COALESCE(cfp.valor_titulo_pagar,0) - COALESCE(coc.custo_ocorrencia,0)
    END                                                        AS margem_bruta,
    CASE WHEN fc.valor_fatura IS NULL OR fc.valor_fatura = 0 THEN NULL
         ELSE (fc.valor_fatura - COALESCE(cfp.valor_titulo_pagar,0) - COALESCE(coc.custo_ocorrencia,0)) / fc.valor_fatura
    END                                                        AS margem_pct,
    CASE
        WHEN kcf.conhecimento_id IS NULL AND cm.con_status IN ('A','S')     THEN 'NAO INTEGRADO'
        WHEN kcf.conhecimento_id IS NULL AND cm.con_status = 'I'            THEN 'NAO APLICAVEL - CTE INUTILIZADO'
        WHEN kcf.conhecimento_id IS NULL AND cm.con_status NOT IN ('A','S') THEN 'CANCELADO SEM KMM'
        WHEN cm.con_status NOT IN ('A','S') AND kcf.cancelado IS NULL       THEN 'DIVERGENCIA - CANCELADO MULTI / VALIDO KMM'
        WHEN cm.con_status IN ('A','S') AND kcf.cancelado IS NOT NULL       THEN 'DIVERGENCIA - VALIDO MULTI / CANCELADO KMM'
        ELSE 'INTEGRADO'
    END                                                        AS status_integracao,
    cm.tipo_cooperado,
    CASE WHEN (cm.situacao_carga = 'ATIVA' AND cm.con_status IN ('A','S')) THEN cfp.operador_contrato ELSE NULL END AS operador_pagamento_contrato,
    CASE WHEN (cm.situacao_carga = 'ATIVA' AND cm.con_status IN ('A','S'))
          AND cm.tipo_cooperado_codigo IN (1,2)
          AND cfp.operador_contrato LIKE 'REPOM%'
         THEN 'COOPERADO TIPO ' || CAST(cm.tipo_cooperado_codigo AS STRING) || ' PAGO VIA REPOM'
    END                                                        AS divergencia_negocio,
    rfc.num_docto                                              AS num_fatura_estimada,
    rfc.valor_docto                                            AS valor_fatura_estimada,
    rfc.gap_dias                                               AS gap_dias_fatura_estimada,
    kcf.usuario_doc_kmm                                        AS usuario_doc_kmm,
    cm.tipo_operacao_anulacao                                  AS tipo_operacao,
    CASE WHEN upper(cm.tipo_operacao_anulacao) LIKE '%ANULACAO%' THEN 'SIM' ELSE 'NAO' END AS doc_anulacao,
    CAST(cm.max_con_anulacao AS bigint)                        AS con_anulacao_ref,
    CAST(cm.vlr_receita_bruta_multi AS double)                 AS vlr_receita_bruta_multi,
    cm.no_painel                                               AS no_painel,
    cm.motivo_fora_painel                                      AS motivo_fora_painel,
    CAST(cm.qtd_linhas_painel AS bigint)                       AS qtd_linhas_painel,
    CAST(cm.vlr_painel_view AS double)                         AS vlr_painel_view,
    CAST(cm.variacao_dias_cargas AS bigint)                  AS variacao_dias_cargas,
    CASE WHEN cm.variacao_dias_cargas > 30 THEN 'SIM' ELSE 'NAO' END AS alerta_variacao_30d
FROM cte_multi cm
LEFT JOIN cte_kmm_match ckm ON ckm.con_codigo = cm.con_codigo
LEFT JOIN kmm_enriquecido kcf ON kcf.conhecimento_id = ckm.conhecimento_id
LEFT JOIN fatura_cte fc ON fc.conhecimento_id = kcf.conhecimento_id
LEFT JOIN fatura_cancelada_cte fcc ON fcc.conhecimento_id = kcf.conhecimento_id
LEFT JOIN cft_pagar cfp ON cfp.car_codigo_carga_embarcador = cm.car_codigo_carga_embarcador
LEFT JOIN custo_ocorrencia_por_carga coc ON coc.car_codigo_carga_embarcador = cm.car_codigo_carga_embarcador
LEFT JOIN receber_fallback_cte_match rfc ON rfc.con_codigo = cm.con_codigo
UNION ALL
SELECT
    'NF'                                                       AS tipo_analise,
    year(nm.data_emissao)                                      AS ano_emissao,
    nm.tipo_documento,
    nm.cte, nm.con_codigo, nm.con_status,
    nm.car_codigo_carga_embarcador,
    nm.sk_filial, nm.sk_cliente, nm.sk_cooperado, nm.sk_documento,
    CASE nm.con_status
        WHEN 'A' THEN 'Autorizado'  WHEN 'S' THEN 'Substituido'
        WHEN 'C' THEN 'Cancelado'   WHEN 'I' THEN 'Inutilizado'
        WHEN 'R' THEN 'Rejeitado'   WHEN 'Z' THEN 'Denegado'
        ELSE nm.con_status
    END                                                        AS status_multi_descricao,
    nm.data_emissao,
    nm.cnpj_tomador, nm.nome_tomador, nm.grupo_tomador, nm.tem_grupo_pagador, nm.filial_multi, nm.filial_duplicada,
    nm.cooperado, nm.vei_placa, nm.inicio_da_prestacao, nm.fim_da_prestacao,
    nm.situacao_carga, nm.doc_fiscal, nm.emissao_manual, nm.qtd_cargas, nm.multiplas_cargas,
    nm.mod_abreviacao, nm.tipodocumento,
    nm.ciot,
    nm.vinculo_carga,
    CASE WHEN nm.tipo_operacao_anulacao LIKE '%TRANSBORDO%'     THEN 'SIM'       ELSE 'NAO'    END AS transbordo,
    CASE WHEN nm.oco_anulacao IS NOT NULL
          OR ((nm.has_true = 0) AND (nm.flag_anulacao = FALSE) AND (nm.con_codigo = nm.max_con_anulacao))
          OR ((nm.has_true = 1) AND (nm.flag_anulacao = TRUE OR nm.flag_anulacao IS NOT NULL))
         THEN 'SIM' ELSE 'NAO' END                             AS anulacao,
    nkm.num_nota_id                                            AS kmm_doc_id,
    mf.filial_nome                                             AS filial_kmm,
    nm.filial_contabil,
    CAST(nkm.unidade_negocio_kmm AS STRING)                   AS unidade_negocio_kmm,
    CAST(NULL AS STRING)                                      AS origem_mapeamento,
    CASE WHEN nkm.num_nota_id IS NULL THEN NULL
         WHEN nkm.cancelada = 0 THEN 'Ativo' ELSE 'Cancelado'
    END                                                        AS status_kmm_descricao,
    CAST(nkm.match_priority AS STRING)                        AS match_priority_nf,
    nkm.match_gap_dias,
    CASE WHEN nkm.match_priority IS NULL THEN NULL
         WHEN nkm.match_priority <= 2    THEN 'EXATO'
         WHEN nkm.match_priority <= 5    THEN 'ALTA'
         ELSE 'BAIXA'
    END                                                         AS match_confianca,
    nkm.valor_documento_kmm, nkm.valor_icms_kmm, nkm.valor_iss_kmm,
    fn.num_fatura, fn.tipo_docto_fatura, fn.qtd_faturas, fn.qtd_parcelas,
    fn.valor_fatura, fn.venc_primeiro, fn.venc_ultimo, fn.usuario_fatura,
    CASE WHEN fn.num_fatura IS NOT NULL THEN 'FATURADO'
         WHEN nkm.num_nota_id IS NOT NULL THEN 'SEM FATURA'
         ELSE NULL
    END                                                        AS status_fatura,
    CASE WHEN nkm.num_nota_id IS NULL      THEN NULL
         WHEN fcn.num_nota_id IS NULL      THEN 'NUNCA CANCELADA'
         WHEN fn.num_fatura IS NOT NULL    THEN 'CANCELADA E REEMITIDA'
         ELSE 'CANCELADA SEM REEMISSAO'
    END                                                        AS fatura_cancelada_kmm,
    fn.valor_pago_receber, fn.valor_juro_receber, fn.valor_desconto_receber,
    CASE WHEN fn.num_fatura IS NULL THEN NULL
         ELSE CASE WHEN (fn.valor_fatura + COALESCE(fn.valor_juro_receber,0) - COALESCE(fn.valor_desconto_receber,0) - COALESCE(fn.valor_pago_receber,0)) IS NULL OR (0) IS NULL THEN NULL ELSE greatest(fn.valor_fatura + COALESCE(fn.valor_juro_receber,0) - COALESCE(fn.valor_desconto_receber,0) - COALESCE(fn.valor_pago_receber,0), 0) END
    END                                                        AS saldo_aberto_receber,
    CASE WHEN fn.num_fatura IS NULL THEN NULL
         WHEN COALESCE(fn.valor_pago_receber,0) <= 0.005
          AND fn.valor_fatura + COALESCE(fn.valor_juro_receber,0) - COALESCE(fn.valor_desconto_receber,0) <= 0.01 THEN 'LIQUIDADO POR DESCONTO'
         WHEN COALESCE(fn.valor_pago_receber,0) <= 0.005 THEN 'EM ABERTO'
         WHEN fn.valor_pago_receber >= (fn.valor_fatura + COALESCE(fn.valor_juro_receber,0) - COALESCE(fn.valor_desconto_receber,0)) - 0.01 THEN 'QUITADO'
         ELSE 'PAGAMENTO PARCIAL'
    END                                                        AS status_pagamento_receber,
    fn.valor_desconto_devolucao_receber                       AS valor_desconto_devolucao_receber,
    fn.ids_titulo_receber                                      AS ids_titulo_receber,
    datediff(fn.data_emissao_fatura, nm.data_emissao)  AS dias_emissao_ate_faturamento,
    fn.data_emissao_fatura,
    CASE WHEN (nm.situacao_carga = 'ATIVA' AND nm.con_status IN ('A','S')) THEN cfp.contrato ELSE NULL END AS contrato,
    CASE WHEN NOT ((nm.situacao_carga = 'ATIVA' AND nm.con_status IN ('A','S')) AND nm.con_status IN ('A','S')) OR cfp.contrato IS NULL THEN NULL
         WHEN cfp.contrato_data_cancelamento_kmm IS NOT NULL          THEN 'SIM'
         ELSE 'NAO'
    END                                                        AS contrato_cancelado_kmm,
    CAST(NULL AS integer)                                     AS contrato_avulso,
    CASE WHEN (nm.situacao_carga = 'ATIVA' AND nm.con_status IN ('A','S')) THEN cfp.valor_contrato_bruto   ELSE NULL END AS valor_contrato_bruto,
    CASE WHEN (nm.situacao_carga = 'ATIVA' AND nm.con_status IN ('A','S')) THEN cfp.valor_contrato_liquido ELSE NULL END AS valor_contrato_liquido,
    CASE WHEN (nm.situacao_carga = 'ATIVA' AND nm.con_status IN ('A','S')) THEN cfp.num_titulo_pagar ELSE NULL END AS num_titulo_pagar,
    CASE WHEN (nm.situacao_carga = 'ATIVA' AND nm.con_status IN ('A','S')) THEN cfp.valor_titulo_pagar ELSE NULL END AS valor_titulo_pagar,
    CASE WHEN (nm.situacao_carga = 'ATIVA' AND nm.con_status IN ('A','S')) THEN cfp.usuario_titulo_pagar ELSE NULL END AS usuario_titulo_pagar,
    CASE WHEN NOT ((nm.situacao_carga = 'ATIVA' AND nm.con_status IN ('A','S')) AND nm.con_status IN ('A','S'))                      THEN 'NAO APLICAVEL - DOCUMENTO CANCELADO'
         WHEN cfp.titulo_pagar_data_estorno IS NOT NULL        THEN 'ESTORNADO'
         WHEN cfp.num_titulo_pagar IS NOT NULL                 THEN 'FATURADO'
         WHEN cfp.car_codigo_carga_embarcador IS NOT NULL      THEN 'SEM FATURA PAGAR'
         ELSE NULL
    END                                                        AS status_fatura_pagar,
    CASE WHEN NOT ((nm.situacao_carga = 'ATIVA' AND nm.con_status IN ('A','S')) AND nm.con_status IN ('A','S')) OR cfp.contrato IS NULL THEN NULL
         WHEN NOT cfp.teve_titulo_pagar_estornado                   THEN 'NUNCA CANCELADA'
         WHEN cfp.num_titulo_pagar IS NOT NULL
              AND cfp.titulo_pagar_data_estorno IS NULL             THEN 'CANCELADA E REEMITIDA'
         ELSE 'CANCELADA SEM REEMISSAO'
    END                                                        AS fatura_pagar_cancelada_kmm,
    CASE WHEN (nm.situacao_carga = 'ATIVA' AND nm.con_status IN ('A','S')) THEN cfp.valor_pago_pagar     ELSE NULL END AS valor_pago_pagar,
    CASE WHEN (nm.situacao_carga = 'ATIVA' AND nm.con_status IN ('A','S')) THEN cfp.valor_juro_pagar     ELSE NULL END AS valor_juro_pagar,
    CASE WHEN (nm.situacao_carga = 'ATIVA' AND nm.con_status IN ('A','S')) THEN cfp.valor_desconto_pagar ELSE NULL END AS valor_desconto_pagar,
    coc.custo_ocorrencia,
    CASE WHEN NOT ((nm.situacao_carga = 'ATIVA' AND nm.con_status IN ('A','S')) AND nm.con_status IN ('A','S')) OR cfp.num_titulo_pagar IS NULL THEN NULL
         WHEN cfp.titulo_pagar_data_estorno IS NOT NULL THEN 'ESTORNADO'
         WHEN COALESCE(cfp.valor_pago_pagar,0) <= 0.005 THEN 'EM ABERTO'
         WHEN cfp.valor_pago_pagar >= (cfp.valor_titulo_pagar + COALESCE(cfp.valor_juro_pagar,0) - COALESCE(cfp.valor_desconto_pagar,0)) - 0.01 THEN 'QUITADO'
         ELSE 'PAGAMENTO PARCIAL'
    END                                                        AS status_pagamento_pagar,
    CASE WHEN (nm.situacao_carga = 'ATIVA' AND nm.con_status IN ('A','S')) THEN cfp.data_ref_pagar ELSE NULL END AS data_ref_pagar,
    fn.data_ref_receber,
    CASE WHEN (nm.situacao_carga = 'ATIVA' AND nm.con_status IN ('A','S')) AND cfp.data_ref_pagar IS NOT NULL AND fn.data_ref_receber IS NOT NULL
         THEN datediff(fn.data_ref_receber, cfp.data_ref_pagar)
         ELSE NULL
    END                                                        AS prazo_dias,
    CASE WHEN NOT ((nm.situacao_carga = 'ATIVA' AND nm.con_status IN ('A','S')) AND nm.con_status IN ('A','S')) OR cfp.data_ref_pagar IS NULL OR fn.data_ref_receber IS NULL THEN NULL
         WHEN COALESCE(cfp.pagar_tem_estimado,1) = 0 AND COALESCE(fn.receber_tem_parcela_estimada,1) = 0 THEN 'REAL'
         ELSE 'ESTIMADO'
    END                                                        AS prazo_tipo,
    CASE WHEN fn.valor_fatura IS NULL THEN NULL
         ELSE fn.valor_fatura - COALESCE(cfp.valor_titulo_pagar,0) - COALESCE(coc.custo_ocorrencia,0)
    END                                                        AS margem_bruta,
    CASE WHEN fn.valor_fatura IS NULL OR fn.valor_fatura = 0 THEN NULL
         ELSE (fn.valor_fatura - COALESCE(cfp.valor_titulo_pagar,0) - COALESCE(coc.custo_ocorrencia,0)) / fn.valor_fatura
    END                                                        AS margem_pct,
    CASE
        WHEN nm.escopo_kmm = 'NAO FISCAL'                               THEN 'NAO APLICAVEL - DOC NAO FISCAL'
        WHEN nkm.num_nota_id IS NULL AND nm.con_status IN ('A','S')     THEN 'NAO INTEGRADO'
        WHEN nkm.num_nota_id IS NULL AND nm.con_status NOT IN ('A','S') THEN 'CANCELADO SEM KMM'
        WHEN nm.con_status NOT IN ('A','S') AND nkm.cancelada = 0        THEN 'DIVERGENCIA - CANCELADO MULTI / VALIDO KMM'
        WHEN nm.con_status IN ('A','S')     AND nkm.cancelada = 1        THEN 'DIVERGENCIA - VALIDO MULTI / CANCELADO KMM'
        ELSE 'INTEGRADO'
    END                                                        AS status_integracao,
    nm.tipo_cooperado,
    CASE WHEN (nm.situacao_carga = 'ATIVA' AND nm.con_status IN ('A','S')) THEN cfp.operador_contrato ELSE NULL END AS operador_pagamento_contrato,
    CASE WHEN (nm.situacao_carga = 'ATIVA' AND nm.con_status IN ('A','S'))
          AND nm.tipo_cooperado_codigo IN (1,2)
          AND cfp.operador_contrato LIKE 'REPOM%'
         THEN 'COOPERADO TIPO ' || CAST(nm.tipo_cooperado_codigo AS STRING) || ' PAGO VIA REPOM'
    END                                                        AS divergencia_negocio,
    rfn.num_docto                                              AS num_fatura_estimada,
    rfn.valor_docto                                            AS valor_fatura_estimada,
    rfn.gap_dias                                               AS gap_dias_fatura_estimada,
    nkm.usuario_doc_kmm                                        AS usuario_doc_kmm,
    nm.tipo_operacao_anulacao                                  AS tipo_operacao,
    CASE WHEN upper(nm.tipo_operacao_anulacao) LIKE '%ANULACAO%' THEN 'SIM' ELSE 'NAO' END AS doc_anulacao,
    CAST(nm.max_con_anulacao AS bigint)                        AS con_anulacao_ref,
    CAST(nm.vlr_receita_bruta_multi AS double)                 AS vlr_receita_bruta_multi,
    nm.no_painel                                               AS no_painel,
    nm.motivo_fora_painel                                      AS motivo_fora_painel,
    CAST(nm.qtd_linhas_painel AS bigint)                       AS qtd_linhas_painel,
    CAST(nm.vlr_painel_view AS double)                         AS vlr_painel_view,
    CAST(nm.variacao_dias_cargas AS bigint)                  AS variacao_dias_cargas,
    CASE WHEN nm.variacao_dias_cargas > 30 THEN 'SIM' ELSE 'NAO' END AS alerta_variacao_30d
FROM nf_multi nm
LEFT JOIN nf_kmm_match nkm ON nkm.con_codigo = nm.con_codigo
LEFT JOIN mapa mf          ON mf.cod_centro_custo = nkm.cod_centro_custo
LEFT JOIN fatura_nf fn     ON fn.num_nota_id = nkm.num_nota_id
LEFT JOIN fatura_cancelada_nf fcn ON fcn.num_nota_id = nkm.num_nota_id
LEFT JOIN cft_pagar cfp    ON cfp.car_codigo_carga_embarcador = nm.car_codigo_carga_embarcador
LEFT JOIN custo_ocorrencia_por_carga coc ON coc.car_codigo_carga_embarcador = nm.car_codigo_carga_embarcador
LEFT JOIN receber_fallback_nf_match rfn ON rfn.con_codigo = nm.con_codigo
UNION ALL
SELECT
    'OCORRENCIA'                                               AS tipo_analise,
    year(av.pam_data_pagamento)                                 AS ano_emissao,
    'CTRANSP'                                                   AS tipo_documento,
    CAST(NULL AS STRING)                                       AS cte,
    CAST(NULL AS integer)                                       AS con_codigo,
    CAST(NULL AS STRING)                                       AS con_status,
    av.car_codigo_carga_embarcador,
    CAST(-1 AS integer)                                          AS sk_filial,
    CAST(-1 AS integer)                                          AS sk_cliente,
    CAST(-1 AS bigint)                                           AS sk_cooperado,
    CAST(-1 AS integer)                                          AS sk_documento,
    'Pagamento Motorista'                                       AS status_multi_descricao,
    DATE(av.pam_data_pagamento)                                 AS data_emissao,
    CAST(av.cnpj_transportador AS STRING)                      AS cnpj_tomador,
    CAST(NULL AS STRING)                                       AS nome_tomador,
    CAST(NULL AS STRING)                                       AS grupo_tomador,
    CAST(NULL AS STRING)                                       AS tem_grupo_pagador,
    CAST(NULL AS STRING)                                       AS filial_multi,
    CAST(NULL AS STRING)                                       AS filial_duplicada,
    av.cooperado,
    CAST(NULL AS STRING)                                       AS vei_placa,
    CAST(NULL AS STRING)                                       AS inicio_da_prestacao,
    CAST(NULL AS STRING)                                       AS fim_da_prestacao,
    CASE WHEN av.car_situacao IN (18,13) THEN 'CANCELADA' ELSE 'ATIVA' END AS situacao_carga,
    'NAO'                                                        AS doc_fiscal,
    CAST(NULL AS STRING)                                       AS emissao_manual,
    CAST(NULL AS bigint)                                         AS qtd_cargas,
    CAST(NULL AS STRING)                                       AS multiplas_cargas,
    'PAGAMENTO'                                                  AS mod_abreviacao,
    'CTRANSP'                                                    AS tipodocumento,
    CAST(NULL AS STRING)                                       AS ciot,
    CAST(NULL AS STRING)                                       AS vinculo_carga,
    CAST(NULL AS STRING)                                       AS transbordo,
    CAST(NULL AS STRING)                                       AS anulacao,
    km.lancto_id                                                AS kmm_doc_id,
    CAST(NULL AS STRING)                                       AS filial_kmm,
    CAST(NULL AS STRING)                                       AS filial_contabil,
    CAST(NULL AS STRING)                                       AS unidade_negocio_kmm,
    CAST(NULL AS STRING)                                       AS origem_mapeamento,
    CASE WHEN km.lancto_id IS NULL THEN NULL
         WHEN km.data_cancelamento IS NULL THEN 'Ativo' ELSE 'Cancelado'
    END                                                          AS status_kmm_descricao,
    CAST(NULL AS STRING)                                       AS match_priority_nf,
    CAST(NULL AS bigint)                                         AS match_gap_dias,
    CAST(NULL AS STRING)                                       AS match_confianca,
    CAST(NULL AS double)                                         AS valor_documento_kmm,
    CAST(NULL AS double)                                         AS valor_icms_kmm,
    CAST(NULL AS double)                                         AS valor_iss_kmm,
    CAST(NULL AS STRING)                                       AS num_fatura,
    CAST(NULL AS STRING)                                       AS tipo_docto_fatura,
    CAST(NULL AS bigint)                                         AS qtd_faturas,
    CAST(NULL AS bigint)                                         AS qtd_parcelas,
    CAST(av.pam_valor AS double)                                AS valor_fatura,
    CAST(NULL AS date)                                           AS venc_primeiro,
    CAST(NULL AS date)                                           AS venc_ultimo,
    CAST(NULL AS STRING)                                       AS usuario_fatura,
    CAST(NULL AS STRING)                                       AS status_fatura,
    CAST(NULL AS STRING)                                       AS fatura_cancelada_kmm,
    CAST(NULL AS double)                                         AS valor_pago_receber,
    CAST(NULL AS double)                                         AS valor_juro_receber,
    CAST(NULL AS double)                                         AS valor_desconto_receber,
    CAST(NULL AS double)                                         AS saldo_aberto_receber,
    CAST(NULL AS STRING)                                       AS status_pagamento_receber,
    CAST(NULL AS double)                                         AS valor_desconto_devolucao_receber,
    CAST(NULL AS STRING)                                        AS ids_titulo_receber,
    CAST(NULL AS bigint)                                         AS dias_emissao_ate_faturamento,
    CAST(NULL AS date)                                           AS data_emissao_fatura,
    CAST(NULL AS integer)                                       AS contrato,
    CAST(NULL AS STRING)                                       AS contrato_cancelado_kmm,
    av.pam_numero                                               AS contrato_avulso,
    km.valor_contrato_bruto,
    km.valor_contrato_liquido,
    cp.num_docto                                                AS num_titulo_pagar,
    cp.valor_docto                                               AS valor_titulo_pagar,
    cp.user_insert                                               AS usuario_titulo_pagar,
    CASE WHEN cp.data_estorno IS NOT NULL THEN 'ESTORNADO'
         WHEN cp.num_docto IS NOT NULL THEN 'FATURADO'
         WHEN km.lancto_id IS NOT NULL THEN 'SEM FATURA PAGAR'
         ELSE NULL
    END                                                          AS status_fatura_pagar,
    CAST(NULL AS STRING)                                       AS fatura_pagar_cancelada_kmm,
    pp.valor_pago                                                AS valor_pago_pagar,
    pj.valor_juro                                                AS valor_juro_pagar,
    pd.valor_desconto                                            AS valor_desconto_pagar,
    CAST(NULL AS double)                                         AS custo_ocorrencia,
    CASE WHEN cp.num_docto IS NULL THEN NULL
         WHEN cp.data_estorno IS NOT NULL THEN 'ESTORNADO'
         WHEN COALESCE(pp.valor_pago,0) <= 0.005 THEN 'EM ABERTO'
         WHEN pp.valor_pago >= (cp.valor_docto + COALESCE(pj.valor_juro,0) - COALESCE(pd.valor_desconto,0)) - 0.01 THEN 'QUITADO'
         ELSE 'PAGAMENTO PARCIAL'
    END                                                          AS status_pagamento_pagar,
    CAST(NULL AS date)                                           AS data_ref_pagar,
    CAST(NULL AS date)                                           AS data_ref_receber,
    CAST(NULL AS bigint)                                         AS prazo_dias,
    CAST(NULL AS STRING)                                       AS prazo_tipo,
    CAST(NULL AS double)                                         AS margem_bruta,
    CAST(NULL AS double)                                         AS margem_pct,
    CASE
        WHEN av.cod_pessoa_kmm IS NULL         THEN 'NAO INTEGRADO - PESSOA SEM CADASTRO KMM'
        WHEN km.lancto_id IS NULL              THEN 'NAO INTEGRADO'
        WHEN km.data_cancelamento IS NOT NULL  THEN 'DIVERGENCIA - CANCELADO NO KMM'
        ELSE 'INTEGRADO'
    END                                                          AS status_integracao,
    CAST(NULL AS STRING)                                       AS tipo_cooperado,
    CAST(NULL AS STRING)                                       AS operador_pagamento_contrato,
    CAST(NULL AS STRING)                                       AS divergencia_negocio,
    CAST(NULL AS STRING)                                       AS num_fatura_estimada,
    CAST(NULL AS double)                                         AS valor_fatura_estimada,
    CAST(NULL AS bigint)                                         AS gap_dias_fatura_estimada,
    km.usuario_doc_kmm                                           AS usuario_doc_kmm,
    CAST(NULL AS STRING)                                        AS tipo_operacao,
    CAST(NULL AS STRING)                                        AS doc_anulacao,
    CAST(NULL AS bigint)                                         AS con_anulacao_ref,
    CAST(NULL AS double)                                         AS vlr_receita_bruta_multi,
    CAST(NULL AS STRING)                                        AS no_painel,
    CAST(NULL AS STRING)                                        AS motivo_fora_painel,
    CAST(NULL AS bigint)                                         AS qtd_linhas_painel,
    CAST(NULL AS double)                                         AS vlr_painel_view,
    CAST(NULL AS bigint)                                         AS variacao_dias_cargas,
    CAST(NULL AS STRING)                                        AS alerta_variacao_30d
FROM avulso_enriquecido av
LEFT JOIN avulso_kmm_match km            ON km.pam_codigo = av.pam_codigo
LEFT JOIN titulo_pagar_por_lancto pg     ON pg.lancto_id = km.lancto_id
LEFT JOIN {env}_bronze.kmm_finan_finan_contas_pagar cp ON cp.contas_pagar_id = pg.contas_pagar_id
LEFT JOIN pagar_pago pp     ON pp.contas_pagar_id = cp.contas_pagar_id
LEFT JOIN pagar_juro pj     ON pj.contas_pagar_id = cp.contas_pagar_id
LEFT JOIN pagar_desconto pd ON pd.contas_pagar_id = cp.contas_pagar_id
UNION ALL
SELECT
    'SEM DOCUMENTO'                                             AS tipo_analise,
    year(cs.data_criacao)                                       AS ano_emissao,
    'SEM DOCUMENTO'                                             AS tipo_documento,
    CAST(NULL AS STRING)                                       AS cte,
    CAST(NULL AS integer)                                       AS con_codigo,
    CAST(NULL AS STRING)                                       AS con_status,
    cs.car_codigo_carga_embarcador,
    CAST(-1 AS integer)                                          AS sk_filial,
    CAST(-1 AS integer)                                          AS sk_cliente,
    CAST(-1 AS bigint)                                           AS sk_cooperado,
    CAST(-1 AS integer)                                          AS sk_documento,
    'Carga sem documento'                                       AS status_multi_descricao,
    cs.data_criacao                                             AS data_emissao,
    CAST(NULL AS STRING)                                       AS cnpj_tomador,
    CAST(NULL AS STRING)                                       AS nome_tomador,
    CAST(NULL AS STRING)                                       AS grupo_tomador,
    CAST(NULL AS STRING)                                       AS tem_grupo_pagador,
    CAST(NULL AS STRING)                                       AS filial_multi,
    CAST(NULL AS STRING)                                       AS filial_duplicada,
    CAST(NULL AS STRING)                                       AS cooperado,
    CAST(NULL AS STRING)                                       AS vei_placa,
    CAST(NULL AS STRING)                                       AS inicio_da_prestacao,
    CAST(NULL AS STRING)                                       AS fim_da_prestacao,
    CASE WHEN cs.car_situacao IN (18,13) THEN 'CANCELADA' ELSE 'ATIVA' END AS situacao_carga,
    'NAO'                                                        AS doc_fiscal,
    CAST(NULL AS STRING)                                       AS emissao_manual,
    CAST(NULL AS bigint)                                         AS qtd_cargas,
    CAST(NULL AS STRING)                                       AS multiplas_cargas,
    CAST(NULL AS STRING)                                       AS mod_abreviacao,
    'SEM DOCUMENTO'                                             AS tipodocumento,
    CASE WHEN cpc.qtd_ciot IS NULL OR cpc.qtd_ciot = 0 THEN 'NAO APLICAVEL'
         WHEN cpc.tem_ciot_ativo                       THEN 'VALIDO'
         ELSE 'CANCELADO'
    END                                                          AS ciot,
    CAST(NULL AS STRING)                                       AS vinculo_carga,
    CAST(NULL AS STRING)                                       AS transbordo,
    CAST(NULL AS STRING)                                       AS anulacao,
    CAST(NULL AS bigint)                                         AS kmm_doc_id,
    CAST(NULL AS STRING)                                       AS filial_kmm,
    CAST(NULL AS STRING)                                       AS filial_contabil,
    CAST(NULL AS STRING)                                       AS unidade_negocio_kmm,
    CAST(NULL AS STRING)                                       AS origem_mapeamento,
    CAST(NULL AS STRING)                                       AS status_kmm_descricao,
    CAST(NULL AS STRING)                                       AS match_priority_nf,
    CAST(NULL AS bigint)                                         AS match_gap_dias,
    CAST(NULL AS STRING)                                       AS match_confianca,
    CAST(NULL AS double)                                         AS valor_documento_kmm,
    CAST(NULL AS double)                                         AS valor_icms_kmm,
    CAST(NULL AS double)                                         AS valor_iss_kmm,
    CAST(NULL AS STRING)                                       AS num_fatura,
    CAST(NULL AS STRING)                                       AS tipo_docto_fatura,
    CAST(NULL AS bigint)                                         AS qtd_faturas,
    CAST(NULL AS bigint)                                         AS qtd_parcelas,
    CAST(NULL AS double)                                         AS valor_fatura,
    CAST(NULL AS date)                                           AS venc_primeiro,
    CAST(NULL AS date)                                           AS venc_ultimo,
    CAST(NULL AS STRING)                                       AS usuario_fatura,
    CAST(NULL AS STRING)                                       AS status_fatura,
    CAST(NULL AS STRING)                                       AS fatura_cancelada_kmm,
    CAST(NULL AS double)                                         AS valor_pago_receber,
    CAST(NULL AS double)                                         AS valor_juro_receber,
    CAST(NULL AS double)                                         AS valor_desconto_receber,
    CAST(NULL AS double)                                         AS saldo_aberto_receber,
    CAST(NULL AS STRING)                                       AS status_pagamento_receber,
    CAST(NULL AS double)                                         AS valor_desconto_devolucao_receber,
    CAST(NULL AS STRING)                                        AS ids_titulo_receber,
    CAST(NULL AS bigint)                                         AS dias_emissao_ate_faturamento,
    CAST(NULL AS date)                                           AS data_emissao_fatura,
    cfp.contrato,
    CASE WHEN cfp.contrato IS NULL THEN NULL
         WHEN cfp.contrato_data_cancelamento_kmm IS NOT NULL THEN 'SIM'
         ELSE 'NAO'
    END                                                          AS contrato_cancelado_kmm,
    CAST(NULL AS integer)                                       AS contrato_avulso,
    cfp.valor_contrato_bruto,
    cfp.valor_contrato_liquido,
    cfp.num_titulo_pagar,
    cfp.valor_titulo_pagar,
    cfp.usuario_titulo_pagar,
    CASE WHEN cfp.titulo_pagar_data_estorno IS NOT NULL THEN 'ESTORNADO'
         WHEN cfp.num_titulo_pagar IS NOT NULL THEN 'FATURADO'
         WHEN cfp.car_codigo_carga_embarcador IS NOT NULL THEN 'SEM FATURA PAGAR'
         ELSE NULL
    END                                                          AS status_fatura_pagar,
    CASE WHEN cfp.contrato IS NULL                  THEN NULL
         WHEN NOT cfp.teve_titulo_pagar_estornado   THEN 'NUNCA CANCELADA'
         WHEN cfp.num_titulo_pagar IS NOT NULL
              AND cfp.titulo_pagar_data_estorno IS NULL THEN 'CANCELADA E REEMITIDA'
         ELSE 'CANCELADA SEM REEMISSAO'
    END                                                          AS fatura_pagar_cancelada_kmm,
    cfp.valor_pago_pagar,
    cfp.valor_juro_pagar,
    cfp.valor_desconto_pagar,
    coc.custo_ocorrencia,
    CASE WHEN cfp.num_titulo_pagar IS NULL THEN NULL
         WHEN cfp.titulo_pagar_data_estorno IS NOT NULL THEN 'ESTORNADO'
         WHEN COALESCE(cfp.valor_pago_pagar,0) <= 0.005 THEN 'EM ABERTO'
         WHEN cfp.valor_pago_pagar >= (cfp.valor_titulo_pagar + COALESCE(cfp.valor_juro_pagar,0) - COALESCE(cfp.valor_desconto_pagar,0)) - 0.01 THEN 'QUITADO'
         ELSE 'PAGAMENTO PARCIAL'
    END                                                          AS status_pagamento_pagar,
    cfp.data_ref_pagar,
    CAST(NULL AS date)                                           AS data_ref_receber,
    CAST(NULL AS bigint)                                         AS prazo_dias,
    CAST(NULL AS STRING)                                       AS prazo_tipo,
    CAST(NULL AS double)                                         AS margem_bruta,
    CAST(NULL AS double)                                         AS margem_pct,
    'NAO APLICAVEL - SEM DOCUMENTO'                             AS status_integracao,
    CAST(NULL AS STRING)                                       AS tipo_cooperado,
    cfp.operador_contrato,
    CAST(NULL AS STRING)                                       AS divergencia_negocio,
    CAST(NULL AS STRING)                                       AS num_fatura_estimada,
    CAST(NULL AS double)                                         AS valor_fatura_estimada,
    CAST(NULL AS bigint)                                         AS gap_dias_fatura_estimada,
    CAST(NULL AS STRING)                                        AS usuario_doc_kmm,
    CAST(NULL AS STRING)                                        AS tipo_operacao,
    CAST(NULL AS STRING)                                        AS doc_anulacao,
    CAST(NULL AS bigint)                                         AS con_anulacao_ref,
    CAST(NULL AS double)                                         AS vlr_receita_bruta_multi,
    CAST(NULL AS STRING)                                        AS no_painel,
    CAST(NULL AS STRING)                                        AS motivo_fora_painel,
    CAST(NULL AS bigint)                                         AS qtd_linhas_painel,
    CAST(NULL AS double)                                         AS vlr_painel_view,
    CAST(NULL AS bigint)                                         AS variacao_dias_cargas,
    CAST(NULL AS STRING)                                        AS alerta_variacao_30d
FROM carga_sem_documento cs
LEFT JOIN ciot_por_car_codigo cpc ON cpc.car_codigo = cs.car_codigo
LEFT JOIN cft_pagar_por_car_codigo cfp ON cfp.car_codigo = cs.car_codigo
LEFT JOIN custo_ocorrencia_por_car_codigo coc ON coc.car_codigo = cs.car_codigo
),
carga_tem_doc_ativo AS (
    SELECT car_codigo_carga_embarcador,
           MAX(CASE WHEN con_status IN ('A','S') THEN 1 ELSE 0 END) AS tem_ativo
    FROM conciliacao
    WHERE tipo_analise <> 'OCORRENCIA'
    GROUP BY car_codigo_carga_embarcador
),
conciliacao_final AS (
    SELECT c.*,
        CASE WHEN c.tipo_analise <> 'OCORRENCIA'
               AND (
                     c.con_status IN ('A','S')
                     OR (COALESCE(ca.tem_ativo,0) = 0 AND c.situacao_carga = 'ATIVA')
                   )
               AND ROW_NUMBER() OVER (
                     PARTITION BY c.car_codigo_carga_embarcador,
                                  (c.tipo_analise <> 'OCORRENCIA' AND (
                                        c.con_status IN ('A','S')
                                     OR (COALESCE(ca.tem_ativo,0) = 0 AND c.situacao_carga = 'ATIVA')
                                  ))
                     ORDER BY (CASE WHEN c.tipo_analise = 'CT-e' THEN 0 ELSE 1 END) NULLS LAST, COALESCE(c.valor_fatura, 0) DESC, c.con_codigo NULLS LAST) = 1
             THEN 'SIM' ELSE 'NAO'
        END AS linha_custo_carga
    FROM conciliacao c
    LEFT JOIN carga_tem_doc_ativo ca ON ca.car_codigo_carga_embarcador = c.car_codigo_carga_embarcador
)
SELECT *
FROM conciliacao_final
) t
