"""Gera os SQLs contabeis no padrao do repo datalake-glue, em duas camadas (staging, NAO altera o repo):
  SILVER (limpeza: dedup, tipos, estado atual, 1 linha por entidade)  -> gold_contab\\sqls\\silver\\silver_<tabela>.sql
  GOLD   (modelo: dims com sk_ e membro -1, fatos)                    -> gold_contab\\sqls\\gold\\<tabela>.sql
  + trechos dos JSONs: gold_contab\\silver_sources_contab.json e gold_contab\\gold_sources_contab.json
Fluxo: bronze (hml_bronze.kmm_*) -> silver ({env}_silver.kmm_*) -> gold ({env}_gold.dim_/fato_*).
Uso:  python gerar_sql_gold_contab.py
Cuidado: o job faz sql.format(env=env) -> nada de chaves { } literais; strings Spark sem aspas duplicadas ('').
"""
import json, os, shutil

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, "gold_contab")
SQL_GOLD = os.path.join(SAIDA, "sqls", "gold")
SQL_SILVER = os.path.join(SAIDA, "sqls", "silver")
shutil.rmtree(SAIDA, ignore_errors=True)  # staging: sempre regerado do zero
MANUAL = os.path.join(AQUI, "gold_contab_manual")  # SQLs gold escritos a mao (ponte, ajustes, ligacao...): copiados para sqls/gold ao final, nunca apagados
os.makedirs(SQL_GOLD)
os.makedirs(SQL_SILVER)


def grava(pasta, nome, texto):
    assert "{" not in texto.replace("{env}", "") and "}" not in texto.replace("{env}", ""), nome
    with open(os.path.join(pasta, nome + ".sql"), "w", encoding="utf-8") as f:
        f.write(texto.strip() + "\n")
    print("gerado", os.path.basename(pasta), nome + ".sql")


def silver(tabela, texto):
    grava(SQL_SILVER, "silver_" + tabela, texto)


def gold(tabela, texto):
    grava(SQL_GOLD, tabela, texto)


def lit(v):
    s = str(v if v is not None else "")
    assert "'" not in s, s
    return "'" + s.replace("\\", "\\\\") + "'"


# =========================================================================== SILVER (limpeza)
silver("kmm_contab_plano_contas", """
-- Silver: plano de contas KMM, uma linha por cod_reduzido (a versao mais recente; a carga completa do bronze vem duplicada).
SELECT
    CAST(cod_reduzido AS BIGINT) AS cod_reduzido,
    classificacao,
    CAST(regexp_replace(classificacao, '[.]', '') AS BIGINT) AS num_conta,
    descricao,
    CAST(nivel AS BIGINT) AS nivel,
    natureza_conta,
    tipo_conta,
    CAST(permite_lanc_manual AS BIGINT) AS permite_lanc_manual
FROM (
    SELECT
        cod_reduzido,
        max_by(classificacao, date_update) AS classificacao,
        max_by(descricao, date_update) AS descricao,
        max_by(nivel, date_update) AS nivel,
        max_by(natureza_conta, date_update) AS natureza_conta,
        max_by(tipo_conta, date_update) AS tipo_conta,
        max_by(permite_lanc_manual, date_update) AS permite_lanc_manual
    FROM {env}_bronze.kmm_contab_plano_contas
    GROUP BY cod_reduzido
)
""")

silver("kmm_contab_origem", """
-- Silver: origem da contabilizacao, uma linha por cod_origem (versao mais recente; carga completa vem duplicada).
SELECT
    cod_origem,
    COALESCE(NULLIF(descricao, ''), '(sem origem)') AS descricao,
    CAST(tipo AS BIGINT) AS tipo
FROM (
    SELECT
        cod_origem,
        max_by(descricao, date_update) AS descricao,
        max_by(tipo, date_update) AS tipo
    FROM {env}_bronze.kmm_contab_contabilizacao_origem
    GROUP BY cod_origem
)
""")

silver("kmm_contab_agrupamento", """
-- Silver: agrupamento contabil (liga o lancamento a origem e ao documento), uma linha por agrupamento_id (versao mais recente).
SELECT
    CAST(agrupamento_id AS BIGINT) AS agrupamento_id,
    max_by(cod_origem, date_update) AS cod_origem,
    CAST(max_by(agrupamento_id_estorno, date_update) AS BIGINT) AS agrupamento_id_estorno,
    CAST(max_by(num_lancamento_contab, date_update) AS BIGINT) AS num_lancamento_contab
FROM {env}_bronze.kmm_contab_contabilizacao_agrupamento
GROUP BY agrupamento_id
""")

silver("kmm_contab_lancamento", """
-- Silver: cabecalho do lancamento contabil, uma linha por num_lancamento (o bronze repete numeros; fica a versao mais recente).
-- permite_editar = 1 identifica lancamento MANUAL. Bronze = Postgres KMM (carga de 2026 em diante).
SELECT
    CAST(num_lancamento AS BIGINT) AS num_lancamento,
    max_by(data_lancamento, date_update) AS data_lancamento,
    CAST(max_by(agrupamento_id, date_update) AS BIGINT) AS agrupamento_id,
    CAST(max_by(permite_editar, date_update) AS BIGINT) AS permite_editar,
    max(date_update) AS date_update
FROM {env}_bronze.kmm_contab_contab_lancamento
GROUP BY num_lancamento
""")

silver("kmm_contab_lancamento_item", """
-- Silver: item do lancamento contabil, uma linha por num_lancamento_it, tipos ajustados, historico mantido (a gold da DRE nao leva o texto).
-- user_insert, num_documento e cod_participante servem aos ajustes manuais e a ligacao contabil (fato_dre_ajuste_manual, fato_ligacao_contabil).
-- O bronze final ja vem deduplicado por num_lancamento_it pelo job jdbc_to_bronze (nao usar a _incremental).
SELECT
    CAST(num_lancamento_it AS BIGINT) AS num_lancamento_it,
    CAST(num_lancamento AS BIGINT) AS num_lancamento,
    CAST(cod_reduzido AS BIGINT) AS cod_reduzido,
    CAST(cod_centro_custo AS BIGINT) AS cod_centro_custo,
    CAST(valor_debito AS DOUBLE) AS valor_debito,
    CAST(valor_credito AS DOUBLE) AS valor_credito,
    CAST(contabilizacao_id AS BIGINT) AS contabilizacao_id,
    historico,
    user_insert,
    CAST(num_documento AS STRING) AS num_documento,
    CAST(cod_participante AS BIGINT) AS cod_participante
FROM {env}_bronze.kmm_contab_contab_lancamento_it
""")

silver("kmm_centro_custo", """
-- Silver: centro de custo (KSS), uma linha por codigo; nome original e nome sem o prefixo numerico.
SELECT
    CAST(cod_centro_custo AS BIGINT) AS cod_centro_custo,
    first(centro_custo) AS centro_custo_original,
    regexp_replace(first(centro_custo), '^[0-9]+ - ', '') AS centro_custo
FROM {env}_bronze.kmm_kss_centro_custo
WHERE cod_centro_custo IS NOT NULL
GROUP BY CAST(cod_centro_custo AS BIGINT)
""")

silver("kmm_pessoa", """
-- Silver: pessoa (KSS), uma linha por cod_pessoa (estado atual: a carga completa do bronze pode vir repetida).
SELECT
    CAST(cod_pessoa AS BIGINT) AS cod_pessoa,
    first(cnpj_cpf) AS cnpj_cpf,
    first(razao_social) AS razao_social,
    first(cliente) AS cliente
FROM {env}_bronze.kmm_kss_pessoa
WHERE cod_pessoa IS NOT NULL
GROUP BY CAST(cod_pessoa AS BIGINT)
""")

silver("kmm_organograma", """
-- Silver: vinculo centro de custo x pessoa do organograma (KSS), uma linha por par distinto.
SELECT DISTINCT
    CAST(cod_centro_custo AS BIGINT) AS cod_centro_custo,
    CAST(cod_pessoa AS BIGINT) AS cod_pessoa
FROM {env}_bronze.kmm_kss_organograma
WHERE cod_centro_custo IS NOT NULL AND cod_pessoa IS NOT NULL
""")

silver("kmm_fiscal_documento_contab", """
-- Silver: documentos fiscais que geram lancamento contabil (CT-e e NF E/S), uma linha por documento (estado atual),
-- com o agrupamento do lancamento e o do estorno. Marcas de cancelado/substituido ficam como vieram da origem.
-- Fonte em prd_bronze (kmm_fiscal_* ja atualizado diariamente); trocar para {env}_bronze quando houver carga nos dois ambientes.
SELECT
    'CTE' AS tipo_documento,
    CAST(conhecimento_id AS BIGINT) AS documento_id,
    CAST(max_by(num_conhecimento, date_update) AS STRING) AS num_documento,
    CAST(max_by(data_emissao, date_update) AS DATE) AS data_emissao,
    CAST(max_by(tomador_servico_id, date_update) AS BIGINT) AS tomador_id,
    CAST(max_by(solicitacao_carga_id, date_update) AS BIGINT) AS solicitacao_carga_id,
    CAST(max_by(cancelado, date_update) AS STRING) AS cancelado,
    CAST(max_by(motivo_substituicao_id, date_update) AS BIGINT) AS motivo_substituicao_id,
    CAST(max_by(motivo_cancelamento_id, date_update) AS BIGINT) AS motivo_cancelamento_id,
    CAST(max_by(contab_agrupamento_id, date_update) AS BIGINT) AS agrupamento_id,
    CAST(max_by(contab_agrupamento_estorno_id, date_update) AS BIGINT) AS agrupamento_id_estorno
FROM prd_bronze.kmm_fiscal_conhecimento
GROUP BY conhecimento_id
UNION ALL
SELECT
    'NF_ES' AS tipo_documento,
    CAST(num_nota_id AS BIGINT) AS documento_id,
    CAST(max_by(num_nota_fiscal, date_update) AS STRING) AS num_documento,
    CAST(max_by(data_emissao, date_update) AS DATE) AS data_emissao,
    CAST(NULL AS BIGINT) AS tomador_id,
    CAST(NULL AS BIGINT) AS solicitacao_carga_id,
    CAST(NULL AS STRING) AS cancelado,
    CAST(NULL AS BIGINT) AS motivo_substituicao_id,
    CAST(NULL AS BIGINT) AS motivo_cancelamento_id,
    CAST(max_by(contab_agrupamento_id, date_update) AS BIGINT) AS agrupamento_id,
    CAST(max_by(contab_agrupamento_id_estorno, date_update) AS BIGINT) AS agrupamento_id_estorno
FROM prd_bronze.kmm_fiscal_nf_es
GROUP BY num_nota_id
""")

# =========================================================================== GOLD (modelo, le da silver)
gold("dim_conta", """
-- Conta contabil (plano de contas KMM). Serve ao DRE (grupo RESULTADO) e ao Balanco (ATIVO / PASSIVO E PL). sk_conta = cod_reduzido.
SELECT
    CAST(-1 AS BIGINT) AS sk_conta,
    CAST(NULL AS STRING) AS classificacao,
    CAST(-1 AS BIGINT) AS num_conta,
    'NAO IDENTIFICADA' AS conta_descricao,
    CAST(NULL AS BIGINT) AS nivel,
    CAST(NULL AS STRING) AS nivel_1,
    CAST(NULL AS STRING) AS nivel_2,
    CAST(NULL AS STRING) AS natureza_conta,
    CAST(NULL AS STRING) AS tipo_conta,
    CAST(NULL AS BIGINT) AS permite_lanc_manual,
    'NAO IDENTIFICADA' AS grupo_conta
UNION ALL
SELECT
    cod_reduzido AS sk_conta,
    classificacao,
    num_conta,
    descricao AS conta_descricao,
    nivel,
    substr(classificacao, 1, 3) AS nivel_1,
    substr(classificacao, 1, 8) AS nivel_2,
    natureza_conta,
    tipo_conta,
    permite_lanc_manual,
    CASE substr(classificacao, 1, 1)
        WHEN '1' THEN 'ATIVO'
        WHEN '2' THEN 'PASSIVO E PL'
        ELSE 'RESULTADO'
    END AS grupo_conta
FROM {env}_silver.kmm_contab_plano_contas
""")

gold("dim_origem_contabil", """
-- Origem da contabilizacao. Lancamento sem agrupamento (ex.: manuais) cai no membro -1 '(sem origem)'.
SELECT
    CAST(-1 AS INT) AS sk_origem,
    CAST(NULL AS STRING) AS cod_origem,
    '(sem origem)' AS origem
UNION ALL
SELECT
    CAST(ROW_NUMBER() OVER (ORDER BY cod_origem) AS INT) AS sk_origem,
    cod_origem,
    descricao AS origem
FROM {env}_silver.kmm_contab_origem
""")

gold("dim_centro_custo", """
-- Centro de custo da contabilidade. sk_centro_custo = cod_centro_custo.
SELECT
    CAST(-1 AS BIGINT) AS sk_centro_custo,
    'NAO IDENTIFICADO' AS centro_custo
UNION ALL
SELECT
    cod_centro_custo AS sk_centro_custo,
    centro_custo
FROM {env}_silver.kmm_centro_custo
""")

plano = json.load(open(os.path.join(AQUI, "dre_plano_20261020.json"), encoding="utf-8"))
vals = ",\n".join(
    "        (%d, %s, %s, %s, %s, %d, %s, %s, %s)" % (
        p["num_conta"], lit(p["descricao"]), lit(p["nivel_2"]), lit(p["nivel_1"]), lit(p.get("deduzir")),
        p["ordem"], lit(p.get("mb")), lit(p.get("mo")), lit(p.get("mr")))
    for p in plano)
gold("dim_centro_custo_pessoa", """
-- Centro de custo x pessoa do organograma KSS: 1 linha por par (um centro de custo pode ter varias pessoas).
-- Substitui a consulta ODBC kss.centro_custo x organograma x pessoa da d_Filial do BI gerencial. sk_centro_custo = cod_centro_custo.
SELECT
    CAST(-1 AS BIGINT) AS sk_centro_custo,
    CAST(-1 AS BIGINT) AS cod_pessoa,
    'NAO IDENTIFICADO' AS centro_custo,
    'NAO IDENTIFICADO' AS cnpj_cpf,
    'NAO IDENTIFICADO' AS cliente
UNION ALL
SELECT
    cc.cod_centro_custo AS sk_centro_custo,
    p.cod_pessoa,
    cc.centro_custo,
    p.cnpj_cpf,
    p.cliente
FROM {env}_silver.kmm_centro_custo cc
JOIN {env}_silver.kmm_organograma o ON o.cod_centro_custo = cc.cod_centro_custo
JOIN {env}_silver.kmm_pessoa p ON p.cod_pessoa = o.cod_pessoa
""")

gold("dim_conta_dre", """
-- Mapeamento conta -> linha do DRE gerencial (%d contas; antes a foto DrePlano dentro do BI). Dono do conteudo: controladoria.
-- Origem: dre_plano_20261020.json (regerar com gerar_sql_gold_contab.py quando o plano mudar).
-- margem_*: 'X' entra no numerador da margem, 'XD' tambem marca o denominador. sk_conta liga a dim_conta (-1 = conta fora do plano).
SELECT
    COALESCE(c.sk_conta, CAST(-1 AS BIGINT)) AS sk_conta,
    d.num_conta,
    d.descricao_dre,
    d.nivel_2,
    d.nivel_1,
    d.deduzir,
    d.ordem,
    d.margem_bruta,
    d.margem_operacional,
    d.margem_repasse
FROM (
    SELECT * FROM VALUES
%s
    AS t (num_conta, descricao_dre, nivel_2, nivel_1, deduzir, ordem, margem_bruta, margem_operacional, margem_repasse)
) d
LEFT JOIN {env}_gold.dim_conta c ON c.num_conta = d.num_conta
""" % (len(plano), vals))

cascata = [
    (1, "RECEITA TOTAL (ROB)", 1, "="), (2, "INGRESSOS E RECEITAS DE FRETE", 0, "+"), (3, "REPASSE LÍQUIDO", 0, "+"),
    (4, "DEDUÇÕES DA RECEITA", 0, "-"), (5, "RECEITAS OPERACIONAIS LÍQUIDAS (ROL)", 1, "="),
    (6, "CUSTOS DOS SERVIÇOS PRESTADOS", 0, "-"), (7, "MARGEM DE CONTRIBUIÇÃO BRUTA", 1, "="),
    (8, "DESPESAS OPERACIONAIS", 0, "-"), (9, "INDEDUTÍVEIS E TRIBUTÁRIAS", 0, "-"),
    (10, "RESULTADO OPERACIONAL", 1, "="), (11, "RECEITAS E DESPESAS FINANCEIRAS", 0, "-"),
    (12, "SOBRA GERENCIAL", 1, "="), (13, "OUTRAS RECEITAS/DESPESAS", 0, "-"), (14, "SOBRA CONTÁBIL", 1, "="),
]
v = ",\n".join("    (%d, %s, %d, %s)" % (c, lit(l), s, lit(g)) for c, l, s, g in cascata)
gold("dim_linha_dre", """
-- As 14 linhas da cascata do DRE (ROB ... Sobra Contabil). Antes: tabela fixa dentro de DreLinhas no BI.
SELECT * FROM VALUES
%s
AS t (codigo, linha, subtotal, sinal)
""" % v)

gold("fato_contab_item", """
-- Fato: 1 item contabil, 2026+, todas as contas. Base unica do DRE (fato_dre_contabil) e do futuro Balanco.
-- Sem historico em texto (fica na silver). Origem: lancamento.agrupamento_id -> agrupamento.cod_origem -> dim_origem_contabil (sem agrupamento = -1).
SELECT
    i.num_lancamento_it,
    i.num_lancamento,
    l.agrupamento_id,
    CAST(l.data_lancamento AS DATE) AS data_lancamento,
    date_format(l.data_lancamento, 'yyyy-MM') AS mes_lancamento,
    CAST(date_trunc('month', l.data_lancamento) AS DATE) AS data_mes,
    COALESCE(i.cod_reduzido, CAST(-1 AS BIGINT)) AS sk_conta,
    COALESCE(o.sk_origem, -1) AS sk_origem,
    COALESCE(i.cod_centro_custo, CAST(-1 AS BIGINT)) AS sk_centro_custo,
    i.valor_debito,
    i.valor_credito,
    i.valor_credito - i.valor_debito AS valor_saldo,
    CASE WHEN l.permite_editar = 1 THEN 1 ELSE 0 END AS eh_manual
FROM {env}_silver.kmm_contab_lancamento_item i
JOIN {env}_silver.kmm_contab_lancamento l ON l.num_lancamento = i.num_lancamento
LEFT JOIN {env}_silver.kmm_contab_agrupamento g ON g.agrupamento_id = l.agrupamento_id
LEFT JOIN {env}_gold.dim_origem_contabil o ON o.cod_origem = g.cod_origem
""")

gold("fato_contab_documento", """
-- Ponte: agrupamento contabil -> documento (CT-e, NF E/S). Une fato_contab_item (agrupamento_id) ao documento e, dai, a carga.
-- Ligacao deterministica (sem texto do historico). Grao: tipo_documento x documento x agrupamento (lancamento e estorno em linhas separadas).
SELECT tipo_documento, documento_id, agrupamento_id, 0 AS eh_estorno, num_documento, data_emissao, tomador_id,
       solicitacao_carga_id, cancelado, motivo_substituicao_id, motivo_cancelamento_id
FROM {env}_silver.kmm_fiscal_documento_contab
WHERE agrupamento_id IS NOT NULL
UNION ALL
SELECT tipo_documento, documento_id, agrupamento_id_estorno, 1, num_documento, data_emissao, tomador_id,
       solicitacao_carga_id, cancelado, motivo_substituicao_id, motivo_cancelamento_id
FROM {env}_silver.kmm_fiscal_documento_contab
WHERE agrupamento_id_estorno IS NOT NULL
""")

gold("fato_dre_contabil", """
-- Fato: contas de RESULTADO (classificacao >= '3') por mes x conta x origem x centro de custo. Substitui hml_gold.vw_fato_dre_contabil (v2).
-- Valor = SUM(credito - debito). Descricoes e niveis vem das dimensoes. Aceite: diferenca zero contra a v2 (jan-set/26).
SELECT
    f.mes_lancamento,
    f.data_mes,
    f.sk_conta,
    f.sk_origem,
    f.sk_centro_custo,
    SUM(f.valor_saldo) AS valor,
    COUNT(*) AS itens
FROM {env}_gold.fato_contab_item f
JOIN {env}_gold.dim_conta c ON c.sk_conta = f.sk_conta
WHERE c.classificacao >= '3'
GROUP BY f.mes_lancamento, f.data_mes, f.sk_conta, f.sk_origem, f.sk_centro_custo
""")

gold("fato_dre_documento", """
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
""")


# =========================================================================== JSONs (ordem importa)
tab_silver = ["kmm_contab_plano_contas", "kmm_contab_origem", "kmm_contab_agrupamento", "kmm_contab_lancamento",
              "kmm_contab_lancamento_item", "kmm_centro_custo", "kmm_pessoa", "kmm_organograma", "kmm_fiscal_documento_contab"]
json.dump([{"bucket_silver": "cootravale-layer-silver-us", "table": t, "database": "silver",
            "sql_bucket": "cootravale-glue", "sql_path": "sqls/silver/{env}/silver_%s.sql" % t} for t in tab_silver],
          open(os.path.join(SAIDA, "silver_sources_contab.json"), "w", encoding="utf-8"), indent=2)
tab_gold = ["dim_conta", "dim_origem_contabil", "dim_centro_custo", "dim_centro_custo_pessoa", "dim_conta_dre", "dim_linha_dre",
            "fato_contab_item", "fato_contab_documento", "fato_dre_contabil", "fato_dre_documento",
            "ponte_lancamento_documento_carga", "fato_dre_ajuste_manual", "fato_conciliacao_multi_kmm", "fato_ligacao_contabil"]  # SQL da ponte mantido a mao em gold_contab/sqls/gold (nao gerado aqui)
json.dump([{"inc": 0, "bucket_gold": "cootravale-layer-gold", "table": t, "database": "gold",
            "sql_bucket": "cootravale-glue", "sql_path": "sqls/gold/{env}/%s.sql" % t} for t in tab_gold],
          open(os.path.join(SAIDA, "gold_sources_contab.json"), "w", encoding="utf-8"), indent=2)
if os.path.isdir(MANUAL):
    for f in sorted(os.listdir(MANUAL)):
        if f.endswith(".sql"):
            shutil.copy(os.path.join(MANUAL, f), os.path.join(SQL_GOLD, f))
            print("copiado (manual) gold", f)
print("gerados silver_sources_contab.json (anexar a sources/silver_sources.json) e gold_sources_contab.json (a sources/gold_sources.json)")
