-- =====================================================================
-- hml_gold.vw_fato_dre_contabil -> contas de RESULTADO (classificacao >= '3') por mes, conta, origem e centro de custo.
-- Versao 2 (21/10/2026): fonte = tabelas carregadas do Postgres KMM (banco datalake) no hml_bronze, que INCLUEM os lancamentos manuais
--   (PERMITE_EDITAR = 1) que a versao 1 (prd_bronze.kmm_listas_contab_lancamentos_incremental) nao trazia.
--   Validado jul-set/26: margem de contribuicao (regra do DRE) = 9,51% / 10,16% / 10,21%, igual ao DRE.
-- Backup da versao 1: vw_fato_dre_contabil.sql.bak_20261021 e vw_fato_dre_contabil.glue_backup_20261021.json.
-- Cuidados de dados:
--   * kmm_contab_plano_contas e kmm_contab_contabilizacao_origem vieram DUPLICADAS na carga (cada linha 2x) -> deduplicadas por chave.
--   * kmm_contab_contab_lancamento (cabecalho) tem numeros repetidos (mesmo date_update) -> um por num_lancamento.
--   * Origem: cabecalho.agrupamento_id -> kmm_contab_contabilizacao_agrupamento.cod_origem -> kmm_contab_contabilizacao_origem.descricao (op_origem dos itens vem VAZIO).
--   * kmm_contab_contab_lancamento_it e a tabela final deduplicada por num_lancamento_it (nao usar a _incremental).
--   * Fonte em hml_bronze enquanto nao houver carga em prd_bronze (trocar o database quando existir).
-- Colunas identicas a versao 1: mes_lancamento, data_mes, classificacao, num_conta, conta_descricao, nivel_1, nivel_2, origem, centro_custo, valor, itens.
-- =====================================================================
CREATE OR REPLACE VIEW hml_gold.vw_fato_dre_contabil AS
WITH h AS (
    SELECT num_lancamento, max_by(data_lancamento, date_update) AS dt, max_by(agrupamento_id, date_update) AS agr
    FROM hml_bronze.kmm_contab_contab_lancamento
    GROUP BY num_lancamento
),
g AS (
    SELECT agrupamento_id, arbitrary(cod_origem) AS cod_origem
    FROM hml_bronze.kmm_contab_contabilizacao_agrupamento
    GROUP BY agrupamento_id
),
p AS (
    SELECT cod_reduzido, arbitrary(classificacao) AS cl, arbitrary(descricao) AS ds
    FROM hml_bronze.kmm_contab_plano_contas
    GROUP BY cod_reduzido
),
o AS (
    SELECT cod_origem, arbitrary(descricao) AS ds
    FROM hml_bronze.kmm_contab_contabilizacao_origem
    GROUP BY cod_origem
),
cc AS (
    SELECT CAST(cod_centro_custo AS bigint) AS cod, arbitrary(centro_custo) AS nome
    FROM prd_bronze.kmm_kss_centro_custo
    GROUP BY CAST(cod_centro_custo AS bigint)
)
SELECT date_format(h.dt, '%Y-%m')                                 AS mes_lancamento,
       CAST(date_trunc('month', h.dt) AS date)                    AS data_mes,
       p.cl                                                       AS classificacao,
       CAST(regexp_replace(p.cl, '\.', '') AS bigint)             AS num_conta,
       p.ds                                                       AS conta_descricao,
       substr(p.cl, 1, 3)                                         AS nivel_1,
       substr(p.cl, 1, 8)                                         AS nivel_2,
       coalesce(nullif(o.ds, ''), '(sem origem)')                 AS origem,
       regexp_replace(cc.nome, '^[0-9]+ - ', '')                  AS centro_custo,
       SUM(i.valor_credito - i.valor_debito)                      AS valor,
       COUNT(*)                                                   AS itens
FROM hml_bronze.kmm_contab_contab_lancamento_it i
JOIN h  ON h.num_lancamento = i.num_lancamento
JOIN p  ON p.cod_reduzido   = i.cod_reduzido
LEFT JOIN g  ON g.agrupamento_id = h.agr
LEFT JOIN o  ON o.cod_origem = g.cod_origem
LEFT JOIN cc ON cc.cod       = i.cod_centro_custo
WHERE p.cl >= '3'
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9
