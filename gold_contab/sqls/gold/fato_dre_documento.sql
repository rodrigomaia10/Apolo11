-- Fato: DRE no grao do DOCUMENTO contabil (agrupamento_id), com as cargas OPERACIONAIS do documento como LISTA (sem rateio).
-- Contas de RESULTADO (classificacao >= '3') por agrupamento x mes x conta x origem x centro de custo; a soma de valor fecha com fato_dre_contabil.
-- Tudo em prd, sem a conciliacao Multi x KMM:
--   CT-e     : kmm_fiscal_conhecimento (serie-numero) = fato_operacional.cte, so linhas do painel (mesmos filtros da vw_fato_operacional_painel_filial).
--   Contrato : agrupamento do contrato/itens (kmm_contrato_contrato_transp[_item]) -> num_formulario -> multi_dbo_t_contrato_frete_terceiro
--              (cft_numero_contrato) -> multi_dbo_t_carga, so cargas que estao no painel.
--   NF E/S   : sem ligacao de carga (status NF SEM LIGACAO DE CARGA). Sem documento: lancamentos manuais e outros.
-- Carga operacional = carga que esta no painel. Um documento/contrato pode ter varias: lista ordenada, separada por virgula.
WITH painel AS (
    SELECT cte, car_codigo_carga_embarcador AS car
    FROM {env}_gold.fato_operacional
    WHERE con_status IN ('A') AND car_situacao NOT IN (18, 13) AND ped_situacao <> 2
      AND NOT (tipo_operacao_anulacao LIKE '%CIOT CANCELADO%')
      AND NOT (tipo_operacao_anulacao LIKE '%TRANSBORDO%' OR tipo_operacao_anulacao LIKE '%REUTILIZACAO%'
               OR (tipo_operacao_anulacao LIKE '%REPASSE%' AND tipo_documento = 'CT-e'))
      AND (oco_anulacao IS NULL OR oco_anulacao = 0) AND mod_abreviacao IS NOT NULL
      AND mod_abreviacao NOT IN ('DV', 'OST') AND tipo_documento IS NOT NULL
      AND tipo_documento NOT IN ('CV', 'OST', 'NDA', 'DV')
      AND ((has_true = 1 AND flag_anulacao = true AND con_codigo = max_con_anulacao)
           OR (has_true = 0 AND (flag_anulacao = false OR flag_anulacao IS NULL)))
    GROUP BY cte, car_codigo_carga_embarcador
),
cargas_painel AS (SELECT DISTINCT car FROM painel),
carga_cte AS (
    SELECT cte AS chave, array_join(sort_array(collect_set(car)), ',') AS cargas, size(collect_set(car)) AS qtd
    FROM painel GROUP BY cte
),
conhecimento AS (
    SELECT CAST(conhecimento_id AS BIGINT) AS id,
           concat(CAST(serie AS STRING), '-', CAST(CAST(num_conhecimento AS BIGINT) AS STRING)) AS chave
    FROM {env}_bronze.kmm_fiscal_conhecimento
),
contrato AS (
    SELECT lancto_id, CAST(num_formulario AS BIGINT) AS nf, contab_agrupamento_id AS a1, contab_agrupamento_id_estorno AS a2
    FROM {env}_bronze.kmm_contrato_contrato_transp
    WHERE serie_formulario IN ('U','REPOMFRETE','EFRETE','RI','RIC','EXTRATTA','UC','REPOMFRETEC','EFRETEC','UCC',
                               'REPOMFRETECC','EFRETECC','UCCC','UCCCC','EXTRATTACC')
),
contrato_item AS (
    SELECT lancto_id, contab_agrupamento_id AS a1, contab_agrupamento_id_estorno AS a2
    FROM {env}_bronze.kmm_contrato_contrato_transp_item
),
contrato_agrup AS (
    SELECT agrupamento_id, MAX(nf) AS nf
    FROM (
        SELECT a1 AS agrupamento_id, nf FROM contrato WHERE a1 IS NOT NULL
        UNION ALL SELECT a2, nf FROM contrato WHERE a2 IS NOT NULL
        UNION ALL SELECT i.a1, c.nf FROM contrato_item i JOIN contrato c ON c.lancto_id = i.lancto_id WHERE i.a1 IS NOT NULL
        UNION ALL SELECT i.a2, c.nf FROM contrato_item i JOIN contrato c ON c.lancto_id = i.lancto_id WHERE i.a2 IS NOT NULL
    ) GROUP BY agrupamento_id
),
carga_contrato AS (
    SELECT CAST(CAST(cft.cft_numero_contrato AS BIGINT) AS STRING) AS chave,
           array_join(sort_array(collect_set(cu.car_codigo_carga_embarcador)), ',') AS cargas,
           size(collect_set(cu.car_codigo_carga_embarcador)) AS qtd
    FROM {env}_bronze.multi_dbo_t_contrato_frete_terceiro cft
    JOIN {env}_bronze.multi_dbo_t_carga cu ON cu.car_codigo = cft.car_codigo
    JOIN cargas_painel cp ON cp.car = cu.car_codigo_carga_embarcador
    WHERE cft.cft_contrato_frete <> 3
    GROUP BY CAST(CAST(cft.cft_numero_contrato AS BIGINT) AS STRING)
),
fiscal AS (
    SELECT agrupamento_id, MAX(tipo_documento) AS tipo, MAX(documento_id) AS id
    FROM {env}_gold.fato_contab_documento GROUP BY agrupamento_id
),
doc AS (
    SELECT f.agrupamento_id, f.tipo,
           CASE WHEN f.tipo = 'CTE' THEN k.chave ELSE CAST(f.id AS STRING) END AS chave
    FROM fiscal f LEFT JOIN conhecimento k ON f.tipo = 'CTE' AND k.id = f.id
    UNION ALL
    SELECT c.agrupamento_id, 'CONTRATO', CAST(c.nf AS STRING)
    FROM contrato_agrup c LEFT ANTI JOIN fiscal f ON f.agrupamento_id = c.agrupamento_id
),
carga_doc AS (
    SELECT 'CTE' AS tipo, chave, cargas, qtd FROM carga_cte
    UNION ALL
    SELECT 'CONTRATO', chave, cargas, qtd FROM carga_contrato
)
SELECT
    f.mes_lancamento,
    f.data_mes,
    f.agrupamento_id,
    f.sk_conta,
    f.sk_origem,
    f.sk_centro_custo,
    COALESCE(d.tipo, 'SEM DOCUMENTO') AS tipo_documento,
    d.chave AS documento_chave,
    CASE WHEN cd.qtd > 0 THEN cd.cargas END AS cargas_operacionais,
    COALESCE(cd.qtd, 0) AS qtd_cargas_operacionais,
    CASE
        WHEN d.tipo IS NULL THEN 'SEM DOCUMENTO'
        WHEN d.tipo = 'NF_ES' THEN 'NF SEM LIGACAO DE CARGA'
        WHEN cd.qtd > 0 THEN 'OPERACIONAL'
        ELSE 'SEM CARGA OPERACIONAL'
    END AS status_carga,
    SUM(f.valor_saldo) AS valor,
    COUNT(*) AS itens
FROM {env}_gold.fato_contab_item f
JOIN {env}_gold.dim_conta c ON c.sk_conta = f.sk_conta
LEFT JOIN doc d ON d.agrupamento_id = f.agrupamento_id
LEFT JOIN carga_doc cd ON cd.tipo = d.tipo AND cd.chave = d.chave
WHERE c.classificacao >= '3'
GROUP BY f.mes_lancamento, f.data_mes, f.agrupamento_id, f.sk_conta, f.sk_origem, f.sk_centro_custo,
         COALESCE(d.tipo, 'SEM DOCUMENTO'), d.chave,
         CASE WHEN cd.qtd > 0 THEN cd.cargas END, COALESCE(cd.qtd, 0),
         CASE WHEN d.tipo IS NULL THEN 'SEM DOCUMENTO' WHEN d.tipo = 'NF_ES' THEN 'NF SEM LIGACAO DE CARGA'
              WHEN cd.qtd > 0 THEN 'OPERACIONAL' ELSE 'SEM CARGA OPERACIONAL' END
