-- PROPOSTA (nao aplicada): rateio do CT-e repetido + alerta de variacao de datas das cargas.
-- Base: prd_gold.vw_fato_operacional_painel_filial (definicao atual, filtros inalterados).
--
-- 1) RATEIO: o mesmo documento (con_codigo) aparece em mais de uma linha, uma por carga/cooperado/filial,
--    e cada linha traz a receita do documento inteiro.
--      CT-e : o valor do KMM e o de UMA linha  -> rateia (valor / n de linhas) e a soma volta ao valor do documento.
--      NFS  : cada linha ja e a parte da carga -> a soma das linhas bate com a nota no KMM -> NAO rateia.
--    Validado em 2026: 71 CT-e (KMM = 1 linha) e 6 NFS (KMM = soma das linhas).
-- 2) ALERTA: quando o documento tem mais de uma linha, compara a data de criacao das cargas ligadas a ele
--    (multi_dbo_t_carga.car_data_criacao). Variacao > 30 dias -> alerta_variacao_30d = 'SIM'.
--
-- Colunas novas ficam no FIM da view (as existentes mantem nome e ordem):
--   qtd_linhas_documento, dt_carga_min, dt_carga_max, variacao_dias_cargas, alerta_variacao_30d,
--   vlr_receita_bruta_original (valor antes do rateio)
CREATE OR REPLACE VIEW prd_gold.vw_fato_operacional_painel_filial AS
WITH base AS (
SELECT
  sk_cliente
, sk_documento
, sk_cooperado
, sk_filial
, sk_tipo_operacao
, con_codigo
, car_codigo_carga_embarcador
, cte
, data_emissao
, vlr_receita_bruta
, vlr_receita_liquida
, vlr_prest_servico
, vlr_a_receber
, vlr_total_merc
, vlr_adv
, vlr_gris
, vei_placa
, inicio_da_prestacao
, fim_da_prestacao
, ccv_descricao
, ccv_codigo
, codfil
, (CASE WHEN ((tipo_operacao_anulacao LIKE '%ANULA%') OR (tipo_operacao_anulacao LIKE U&'%ANULA\00C7\00C3O%')) THEN 'S' ELSE 'N' END) operacao_anulacao
, dt_min_entrega
, con_status
, car_situacao
, ped_situacao
, custo_bruto
, tipo_documento
, cooperado
, tipo_operacao
, custo_descarga
, custo_estadia_rateio
, custo_carga
, custo_pedagio_extra
, custo_loggi
, grupo_pessoa_tratado
, tipo_cooperado
, filial
FROM
  prd_gold.fato_operacional
WHERE ((con_status IN ('A')) AND (NOT (car_situacao IN (18, 13))) AND (ped_situacao <> 2) AND (NOT (tipo_operacao_anulacao LIKE '%CIOT CANCELADO%')) AND (NOT ((tipo_operacao_anulacao LIKE '%TRANSBORDO%') OR (tipo_operacao_anulacao LIKE '%REUTILIZACAO%') OR ((tipo_operacao_anulacao LIKE '%REPASSE%') AND (tipo_documento = 'CT-e')))) AND ((oco_anulacao IS NULL) OR (oco_anulacao = 0)) AND (mod_abreviacao IS NOT NULL) AND (NOT (mod_abreviacao IN ('DV', 'OST'))) AND (tipo_documento IS NOT NULL) AND (NOT (tipo_documento IN ('CV', 'OST', 'NDA', 'DV'))) AND (((has_true = 1) AND (flag_anulacao = true) AND (con_codigo = max_con_anulacao)) OR ((has_true = 0) AND ((flag_anulacao = false) OR (flag_anulacao IS NULL)))))
),
carga_data AS (
  SELECT car_codigo_carga_embarcador AS k, MIN(car_data_criacao) AS dt
  FROM prd_bronze.multi_dbo_t_carga
  GROUP BY car_codigo_carga_embarcador
),
x AS (
  SELECT b.*,
         COUNT(*) OVER (PARTITION BY b.con_codigo) AS qtd_linhas_documento,
         cd.dt AS dt_criacao_carga
  FROM base b
  LEFT JOIN carga_data cd ON cd.k = b.car_codigo_carga_embarcador
),
y AS (
  SELECT x.*,
         MIN(dt_criacao_carga) OVER (PARTITION BY con_codigo) AS dt_carga_min,
         MAX(dt_criacao_carga) OVER (PARTITION BY con_codigo) AS dt_carga_max
  FROM x
)
SELECT
sk_cliente
, sk_documento
, sk_cooperado
, sk_filial
, sk_tipo_operacao
, con_codigo
, car_codigo_carga_embarcador
, cte
, data_emissao
, CASE WHEN tipo_documento = 'CT-e' THEN vlr_receita_bruta / qtd_linhas_documento ELSE vlr_receita_bruta END AS vlr_receita_bruta
, CASE WHEN tipo_documento = 'CT-e' THEN vlr_receita_liquida / qtd_linhas_documento ELSE vlr_receita_liquida END AS vlr_receita_liquida
, vlr_prest_servico
, vlr_a_receber
, vlr_total_merc
, vlr_adv
, vlr_gris
, vei_placa
, inicio_da_prestacao
, fim_da_prestacao
, ccv_descricao
, ccv_codigo
, codfil
, operacao_anulacao
, dt_min_entrega
, con_status
, car_situacao
, ped_situacao
, custo_bruto
, tipo_documento
, cooperado
, tipo_operacao
, custo_descarga
, custo_estadia_rateio
, custo_carga
, custo_pedagio_extra
, custo_loggi
, grupo_pessoa_tratado
, tipo_cooperado
, filial
, qtd_linhas_documento
, dt_carga_min
, dt_carga_max
, CASE WHEN qtd_linhas_documento > 1 THEN date_diff('day', dt_carga_min, dt_carga_max) END AS variacao_dias_cargas
, CASE WHEN qtd_linhas_documento > 1 AND date_diff('day', dt_carga_min, dt_carga_max) > 30 THEN 'SIM' ELSE 'NAO' END AS alerta_variacao_30d
, vlr_receita_bruta AS vlr_receita_bruta_original
FROM y
