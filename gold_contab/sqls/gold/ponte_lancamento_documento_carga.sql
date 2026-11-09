-- Ponte: lancamento contabil -> documento (CT-e, contrato, NF E/S) -> carga operacional (+ grupo pagador). Grao: num_lancamento x documento x carga.
-- Serve o BI (INFORMACOES GERENCIAIS) e a aplicacao de DRE: o valor vem dos itens (kmm_contab_lancamento_item) por num_lancamento; a ponte so diz a que documento/carga o lancamento pertence.
-- Atencao: juntar item x ponte repete o valor por carga. Use qtd_cargas_documento / peso_rateio (1 / qtd) se precisar somar sem duplicar.
-- Carga operacional = linha da vw_fato_operacional_painel_filial. A view NAO e lida (job Spark nao le view do Athena): a regra dela esta copiada em 'painel'.
-- Se a regra da view mudar, atualizar aqui tambem.
--   CT-e     : kmm_fiscal_conhecimento (serie-numero + data de emissao) x fato_operacional.cte. Chave unica nos dois lados -> CHAVE_UNICA.
--              Chave ambigua (mais de um CT-e no KMM ou mais de um documento na Multi com mesma serie-numero e data) -> desempate por valor:
--              vlr_prest_servico (Multi) = total_conhecimento (KMM), tolerancia 0,02 -> VALOR. Sem valor igual: sem carga (SEM_MATCH).
--   Contrato : agrupamento do contrato/itens (kmm_contrato_contrato_transp[_item]) -> num_formulario -> multi_dbo_t_contrato_frete_terceiro
--              (cft_numero_contrato) -> multi_dbo_t_carga, so cargas do painel -> NUMERO_CONTRATO. documento_id = numero do contrato (num_formulario).
--   NF E/S   : sem ligacao de carga. Sem documento: lancamentos manuais e outros (tipo_documento nulo).
WITH painel AS (
    SELECT con_codigo, cte, CAST(data_emissao AS DATE) AS d, car_codigo_carga_embarcador AS car,
           MAX(grupo_pessoa_tratado) AS grp, MAX(vlr_prest_servico) AS v
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
    GROUP BY con_codigo, cte, CAST(data_emissao AS DATE), car_codigo_carga_embarcador
),
doc_multi AS (
    SELECT cte, d, con_codigo, MAX(v) AS v, COUNT(*) OVER (PARTITION BY cte, d) AS nm
    FROM painel GROUP BY cte, d, con_codigo
),
conhecimento AS (
    SELECT id, chave, d, t, COUNT(*) OVER (PARTITION BY chave, d) AS nk
    FROM (
        SELECT CAST(conhecimento_id AS BIGINT) AS id,
               concat(CAST(serie AS STRING), '-', CAST(CAST(num_conhecimento AS BIGINT) AS STRING)) AS chave,
               CAST(data_emissao AS DATE) AS d, total_conhecimento AS t
        FROM {env}_bronze.kmm_fiscal_conhecimento
    )
),
cte_liga AS (
    SELECT k.id AS documento_id, m.con_codigo, m.cte, m.d,
           CASE WHEN k.nk = 1 AND m.nm = 1 THEN 'CHAVE_UNICA' ELSE 'VALOR' END AS metodo
    FROM conhecimento k
    JOIN doc_multi m ON m.cte = k.chave AND m.d = k.d
    WHERE (k.nk = 1 AND m.nm = 1) OR ABS(m.v - k.t) < 0.02
),
carga_cte AS (
    SELECT 'CTE' AS tipo, l.documento_id, l.con_codigo, p.car, p.grp, l.metodo
    FROM cte_liga l
    JOIN painel p ON p.con_codigo = l.con_codigo AND p.cte = l.cte AND p.d = l.d
),
cargas_painel AS (SELECT car, MAX(grp) AS grp FROM painel GROUP BY car),
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
    SELECT 'CONTRATO' AS tipo, CAST(cft.cft_numero_contrato AS BIGINT) AS documento_id,
           CAST(NULL AS BIGINT) AS con_codigo, cu.car_codigo_carga_embarcador AS car, cp.grp,
           'NUMERO_CONTRATO' AS metodo
    FROM {env}_bronze.multi_dbo_t_contrato_frete_terceiro cft
    JOIN {env}_bronze.multi_dbo_t_carga cu ON cu.car_codigo = cft.car_codigo
    JOIN cargas_painel cp ON cp.car = cu.car_codigo_carga_embarcador
    WHERE cft.cft_contrato_frete <> 3
    GROUP BY CAST(cft.cft_numero_contrato AS BIGINT), cu.car_codigo_carga_embarcador, cp.grp
),
carga_doc AS (
    SELECT tipo, documento_id, con_codigo, car, grp, metodo FROM carga_cte
    UNION ALL
    SELECT tipo, documento_id, con_codigo, car, grp, metodo FROM carga_contrato
),
qtd_doc AS (
    SELECT tipo, documento_id, COUNT(DISTINCT car) AS qtd FROM carga_doc GROUP BY tipo, documento_id
),
fiscal AS (
    SELECT agrupamento_id, MAX(tipo_documento) AS tipo, MAX(documento_id) AS documento_id, MAX(data_emissao) AS data_emissao
    FROM {env}_gold.fato_contab_documento GROUP BY agrupamento_id
),
doc_agrup AS (
    SELECT agrupamento_id, tipo, documento_id, data_emissao FROM fiscal
    UNION ALL
    SELECT c.agrupamento_id, 'CONTRATO', c.nf, CAST(NULL AS DATE)
    FROM contrato_agrup c
    WHERE NOT EXISTS (SELECT 1 FROM fiscal f WHERE f.agrupamento_id = c.agrupamento_id)
)
SELECT
    l.num_lancamento,
    l.agrupamento_id,
    l.data_lancamento,
    da.tipo AS tipo_documento,
    da.documento_id,
    CASE WHEN da.tipo = 'CTE' THEN k.chave ELSE CAST(da.documento_id AS STRING) END AS documento_chave,
    COALESCE(k.d, da.data_emissao) AS data_emissao,
    cd.con_codigo,
    cd.car AS carga,
    cd.grp AS grupo_pessoa_tratado,
    CASE WHEN da.tipo IN ('CTE', 'CONTRATO') THEN COALESCE(cd.metodo, 'SEM_MATCH') END AS metodo_ligacao,
    COALESCE(q.qtd, 0) AS qtd_cargas_documento,
    CASE WHEN q.qtd > 0 THEN 1.0 / q.qtd END AS peso_rateio,
    CASE WHEN da.tipo IS NULL THEN 'SEM DOCUMENTO'
         WHEN da.tipo = 'NF_ES' THEN 'NF SEM LIGACAO DE CARGA'
         WHEN q.qtd > 0 THEN 'OPERACIONAL'
         ELSE 'SEM CARGA OPERACIONAL' END AS status_carga
FROM {env}_silver.kmm_contab_lancamento l
LEFT JOIN doc_agrup da ON da.agrupamento_id = l.agrupamento_id
LEFT JOIN conhecimento k ON da.tipo = 'CTE' AND k.id = da.documento_id
LEFT JOIN carga_doc cd ON cd.tipo = da.tipo AND cd.documento_id = da.documento_id
LEFT JOIN qtd_doc q ON q.tipo = da.tipo AND q.documento_id = da.documento_id
