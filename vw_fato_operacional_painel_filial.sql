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
