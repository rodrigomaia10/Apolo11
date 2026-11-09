import sys
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import current_timestamp, expr, col
from pyspark.sql import functions as F
from pyspark.storagelevel import StorageLevel

print("=== PIPELINE ATHENA -> SQL SERVER ===", flush=True)

args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

spark.conf.set("spark.sql.legacy.timeParserPolicy", "LEGACY")
spark.conf.set("spark.sql.legacy.parquet.datetimeRebaseModeInRead", "LEGACY")
spark.conf.set("spark.sql.legacy.parquet.int96RebaseModeInRead", "LEGACY")
spark.conf.set("spark.sql.ansi.enabled", "false")

job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# =====================================================
# FLAGS DE EXECUÇÃO
# =====================================================

# RECRIAR_TABELAS:
#   False -> TRUNCATE + INSERT. Preserva índices, constraints e permissões,
#            MAS o Spark nunca altera o schema: coluna nova não é criada.
#   True  -> DROP + CREATE. O schema novo passa a valer, PORÉM índices,
#            constraints e permissões da tabela são perdidos.
#
# Use True em UMA execução, depois de rodar os ALTER TABLE ou de aceitar o DROP,
# e volte para False. Ver checar_colunas_destino() abaixo.
RECRIAR_TABELAS = False

# INCLUIR_ABASTECIMENTO_BENEFICIO (regra de negócio - decidir antes de ativar):
#   No union, 'abastecimento', 'beneficio' e 'item de contrato' gravam liberado = ''
#   (apenas 'adiantamento' e 'saldo' geram 'sim'/'não'). Com o filtro original
#   liberado = 'não', SÓ sobram linhas de tipo_consulta = 'saldo' -- o que torna
#   o ramo abastecimento/beneficio do cálculo de pagamento código morto.
#   True  -> trata liberado = '' como "não liberado" e revive esse ramo.
#   False -> mantém o comportamento atual (só 'saldo').
INCLUIR_ABASTECIMENTO_BENEFICIO = False

# =====================================================
# DESTINOS JDBC
# =====================================================
DESTINOS = {
    "sqlserver": {
        "driver": "com.microsoft.sqlserver.jdbc.SQLServerDriver",
        "url": "jdbc:sqlserver://172.31.14.242:1433;databaseName=portalCooperado;encrypt=false;trustServerCertificate=true",
        "user": "cootravale-admin",
        "password": "jkPbvdCcP3_hBLPXVZcZ",
        "batchsize": "5000",
    },
    "postgres": {
        "driver": "org.postgresql.Driver",
        "url": "jdbc:postgresql://172.31.28.247:5432/portalccs?sslmode=disable",
        "user": "portalccs",
        "password": "p_T3Q2Rj5eUQo^b35",
        "batchsize": "10000",
    },
}


def checar_colunas_destino(df, destino, tabela):
    """Compara as colunas do DataFrame com as da tabela de destino.

    Com truncate=true o Spark reusa o schema existente e nunca faz ALTER TABLE:
    coluna nova simplesmente não tem para onde ir. Isso torna o problema visível
    no log em vez de silencioso.
    """
    cfg = DESTINOS[destino]
    try:
        dest = spark.read \
            .format("jdbc") \
            .option("driver", cfg["driver"]) \
            .option("url", cfg["url"]) \
            .option("dbtable", tabela) \
            .option("user", cfg["user"]) \
            .option("password", cfg["password"]) \
            .load()
    except Exception as e:
        print(f"⚠️  não foi possível ler o schema de {destino}.{tabela}: {e}")
        return

    dest_cols = {c.lower() for c in dest.columns}
    faltando = [c for c in df.columns if c.lower() not in dest_cols]
    if faltando:
        print(f"🚨 {destino}.{tabela} NÃO possui as colunas: {faltando}")
        print("   -> rode o ALTER TABLE correspondente, ou execute uma vez com RECRIAR_TABELAS = True")
    else:
        print(f"✅ schema de {destino}.{tabela} compatível")


def gravar_jdbc(df, destino, tabela):
    """Grava em overwrite. Sem truncate o Spark dropa e recria (schema novo vale)."""
    cfg = DESTINOS[destino]
    checar_colunas_destino(df, destino, tabela)

    writer = df.write \
        .format("jdbc") \
        .option("driver", cfg["driver"]) \
        .option("url", cfg["url"]) \
        .option("dbtable", tabela) \
        .option("user", cfg["user"]) \
        .option("password", cfg["password"]) \
        .option("batchsize", cfg["batchsize"]) \
        .mode("overwrite")

    if not RECRIAR_TABELAS:
        writer = writer.option("truncate", "true")

    writer.save()
    print(f"💾 gravado em {destino}.{tabela}")


# =====================================================
# ETAPA 1: Carregar dados do via_facil (TUDO MINÚSCULO)
# =====================================================
print("📖 Carregando via_facil...")
df_via_facil = spark.sql("""
    select distinct
        cp.contas_pagar_id,
        cp.num_docto,
        cp.parc_docto
    from prd_bronze.kmm_finan_finan_contas_pagar cp
    inner join prd_bronze.kmm_finan_finan_contas_pagar_amort ca
        on ca.contas_pagar_id = cp.contas_pagar_id
    inner join prd_bronze.kmm_finan_ccorrente cs
        on cs.cod_conta = ca.cc_sacado
    where cs.descricao_conta like '%via facil%'
""").persist(StorageLevel.MEMORY_AND_DISK)

print(f"✅ via_facil: {df_via_facil.count()} registros")

# =====================================================
# ETAPA 2: Consulta 1 - Beneficio (TUDO MINÚSCULO)
# =====================================================
print("📖 Carregando dados - Beneficio...")
df_beneficio = spark.sql("""
    select distinct
        'beneficio' as tipo_consulta,
        replace(replace(replace(p.identificador, '.', ''), '-', ''),'/', '') as cnpj_cpf,
        null as tipo_item,
        p.razao_social as transportador,
        null as contas_pagar_id,
        null as docto_id,
        cast(la.lancto_id as string) as num_docto,
        null as num_formulario,
        cp.parc_docto,
        'lançamento manual' as tipo_docto,
        v.placa,
        t.nome as taxa,
        la.taxa_id,
        null as item,
        la.complemento as obs,
        null as valor,
        fc.fechamento_id as acerto,
        fc.data_fechamento as data_acerto,
        max(cpp.data_amortizacao) over (partition by fc.fechamento_id) as data_liberacao,
        max(cpp2.data_amortizacao) over (partition by fc.fechamento_id) as data_pagamento,
        cast(cpa.data_vencto as string) as data_vencimento,
        case when la.cred_deb = 1 then la.valor else 0 end as credito,
        case when la.cred_deb = -1 then la.cred_deb * la.valor else 0 end as debito,
        cp.data_emissao,
        null as produto,
        0 as quantidade,
        case when la.data_cancelamento is not null then 'estornado' else 'gerado' end as situacao,
        '' as liberado,
        max(cpa.data_vencto) over (partition by fc.contas_pagar_id) as data_vencto_acerto,
        case when cp.parc_docto =1 then 'bloqueado'
             when cp.parc_docto = 2 then 'realizado'
             else 'sem status'
        end status,
        p.cod_pessoa
    from prd_bronze.kmm_oper_agr_lancamento la
    left join prd_bronze.kmm_finan_finan_contas_receber cp
        on cp.contas_receber_id = la.contas_receber_id
    left join prd_bronze.kmm_veiculo_veiculo v
        on v.veiculo_id = la.veiculo_id
    left join prd_bronze.kmm_agreg_taxa t
        on t.taxa_id = la.taxa_id
    left join prd_bronze.kmm_oper_agr_fechto_agregado fc
        on la.fechamento_id = fc.fechamento_id
    left join prd_bronze.kmm_kss_pessoa p
        on p.cod_pessoa = la.cod_pessoa
    left join prd_bronze.kmm_finan_finan_contas_receber_amort cpp
        on cpp.contas_receber_id = fc.fechamento_id
    left join prd_bronze.kmm_finan_finan_contas_receber_amort cpp2
        on cpp2.contas_receber_id = fc.fechamento_id
    left join prd_bronze.kmm_finan_finan_contas_pagar cpa
        on cpa.contas_pagar_id = fc.contas_pagar_id
    where fc.data_cancelamento is null
""")

# =====================================================
# ETAPA 3: Consulta 2 - Adiantamento (TUDO MINÚSCULO)
# =====================================================
print("📖 Carregando dados - Adiantamento...")
df_adiantamento = spark.sql("""
    select
        'adiantamento' as tipo_consulta,
        p.cnpj_cpf,
        '' as tipo_item,
        p.razao_social as transportador,
        cp.contas_pagar_id,
        cp.docto_id,
        cp.num_docto,
        ctp.num_formulario,
        cp.parc_docto,
        'cf - adiantamento' as tipo_docto,
        ctp.placa_controle as placa,
        null as taxa,
        null as taxa_id,
        null as item,
        cp.comentario as obs,
        cp.valor_docto as valor,
        f.fechamento_id as acerto,
        f.data_fechamento as data_acerto,
        l.data_liberacao,
        null as data_pagamento,
        cp.data_vencto,
        null as credito,
        null as debito,
        cp.data_emissao,
        null as produto,
        0 as quantidade,
        case when la.data_cancelamento is not null then 'estornado' else 'gerado' end as situacao,
        case when l.data_liberacao is not null then 'sim' else 'não' end as liberado,
        cpa.data_vencto as data_vencto_acerto,
        case when cp.parc_docto =1 then 'bloqueado'
             when cp.parc_docto = 2 then 'realizado'
             else 'sem status'
        end as status,
        p.cod_pessoa
    from prd_bronze.kmm_finan_finan_contas_pagar cp
    left join prd_bronze.kmm_oper_agr_lancamento la on cp.contas_pagar_id = la.lancto_id
    left join prd_bronze.kmm_contrato_contrato_transp_pagar dcp on dcp.contas_pagar_id = cp.contas_pagar_id
    left join prd_bronze.kmm_contrato_contrato_transp ctp on dcp.lancto_id = ctp.lancto_id
    inner join prd_bronze.kmm_kss_pessoa p on p.cod_pessoa = ctp.proprietario_cod_pessoa
    left join prd_bronze.kmm_finan_finan_contas_pagar_liberacao l on l.contas_pagar_id = cp.contas_pagar_id
    left join prd_bronze.kmm_agreg_agr_contrato_pagar cpg on cp.contas_pagar_id = cpg.contas_pagar_id
    left join prd_bronze.kmm_oper_agr_fechto_agregado f on cpg.fechamento_id = f.fechamento_id
    left join prd_bronze.kmm_finan_finan_contas_pagar cpa on cpa.contas_pagar_id = la.contas_pagar_id
    where cp.parc_docto = '1'
      and f.data_cancelamento is null
""")

# =====================================================
# ETAPA 4: Consulta 3 - Saldo (parc_docto = 2 com fechamento_id null)
# =====================================================
print("📖 Carregando dados - Saldo 1...")
df_saldo1 = spark.sql("""
    select
        'saldo' as tipo_consulta,
        p.cnpj_cpf,
        '' as tipo_item,
        p.razao_social as transportador,
        cp.contas_pagar_id,
        cp.docto_id,
        cp.num_docto,
        ctp.num_formulario,
        cp.parc_docto,
        'cf - saldo' as tipo_docto,
        ctp.placa_controle as placa,
        null as taxa,
        null as taxa_id,
        null as item,
        cp.comentario as obs,
        cp.valor_docto as valor,
        null as acerto,
        null as data_acerto,
        l.data_liberacao,
        null as data_pagamento,
        cp.data_vencto,
        null as credito,
        null as debito,
        cp.data_emissao,
        null as produto,
        0 as quantidade,
        case when cp.data_estorno is not null then 'estornado' else 'gerado' end as situacao,
        case when l.data_liberacao is not null then 'sim' else 'não' end as liberado,
        null as data_vencto_acerto,
        case when cp.parc_docto =1 then 'bloqueado'
             when cp.parc_docto = 2 then 'realizado'
             else 'sem status'
        end as status,
        p.cod_pessoa
    from prd_bronze.kmm_finan_finan_contas_pagar cp
    left join prd_bronze.kmm_contrato_contrato_transp_pagar dcp on dcp.contas_pagar_id = cp.contas_pagar_id
    left join prd_bronze.kmm_contrato_contrato_transp ctp on dcp.lancto_id = ctp.lancto_id
    inner join prd_bronze.kmm_kss_pessoa p on p.cod_pessoa = ctp.proprietario_cod_pessoa
    left join prd_bronze.kmm_finan_finan_contas_pagar_liberacao l on l.contas_pagar_id = cp.contas_pagar_id
    left join prd_bronze.kmm_agreg_agr_contrato_pagar cpg on cp.contas_pagar_id = cpg.contas_pagar_id
    left join prd_bronze.kmm_oper_agr_fechto_agregado f on cpg.fechamento_id = f.fechamento_id
    where cp.parc_docto = '2'
      and f.fechamento_id is null
      and f.data_cancelamento is null
""")

# =====================================================
# ETAPA 5: Consulta 4 - Saldo (parc_docto = 2 com fechamento_id not null)
# =====================================================
print("📖 Carregando dados - Saldo 2...")
df_saldo2 = spark.sql("""
    select
        'saldo' as tipo_consulta,
        p.cnpj_cpf,
        '' as tipo_item,
        p.razao_social as transportador,
        cp.contas_pagar_id,
        cp.docto_id,
        cp.num_docto,
        ctp.num_formulario,
        cp.parc_docto,
        'cf - saldo' as tipo_docto,
        ctp.placa_controle as placa,
        null as taxa,
        null as taxa_id,
        null as item,
        cp.comentario as obs,
        cpg.valor as valor,
        f.fechamento_id as acerto,
        f.data_fechamento as data_acerto,
        l.data_liberacao,
        null as data_pagamento,
        cp.data_vencto,
        cpg.valor as credito,
        null as debito,
        cp.data_emissao,
        null as produto,
        0 as quantidade,
        case when cp.data_estorno is not null then 'estornado' else 'gerado' end as situacao,
        case when l.data_liberacao is not null then 'sim' else 'não' end as liberado,
        cpa.data_vencto as data_vencto_acerto,
        case when cp.parc_docto =1 then 'bloqueado'
             when cp.parc_docto = 2 then 'realizado'
             else 'sem status'
        end as status,
        p.cod_pessoa
    from prd_bronze.kmm_finan_finan_contas_pagar cp
    left join prd_bronze.kmm_contrato_contrato_transp_pagar dcp on dcp.contas_pagar_id = cp.contas_pagar_id
    left join prd_bronze.kmm_contrato_contrato_transp ctp on dcp.lancto_id = ctp.lancto_id
    inner join prd_bronze.kmm_kss_pessoa p on p.cod_pessoa = ctp.proprietario_cod_pessoa
    left join prd_bronze.kmm_finan_finan_contas_pagar_liberacao l on l.contas_pagar_id = cp.contas_pagar_id
    left join prd_bronze.kmm_agreg_agr_contrato_pagar cpg on cp.contas_pagar_id = cpg.contas_pagar_id
    left join prd_bronze.kmm_oper_agr_fechto_agregado f on cpg.fechamento_id = f.fechamento_id
    left join prd_bronze.kmm_finan_finan_contas_pagar cpa on cpa.contas_pagar_id = f.contas_pagar_id
    where cp.parc_docto = '2'
      and f.fechamento_id is not null
      and f.data_cancelamento is null
""")

# =====================================================
# ETAPA 6: Consulta 5 - Item de Contrato (TUDO MINÚSCULO)
# =====================================================
print("📖 Carregando dados - Item de Contrato...")
df_item_contrato = spark.sql("""
    select
        'item de contrato' as tipo_consulta,
        p.cnpj_cpf,
        case when cti.desconto = 0 then 'acréscimo' else 'desconto' end as tipo_item,
        p.razao_social as transportador,
        null as contas_pagar_id,
        null as docto_id,
        cast(null as string) as num_docto,
        ctp.num_formulario,
        null as parc_docto,
        'item de contrato' as tipo_docto,
        ctp.placa_controle as placa,
        null as taxa,
        null as taxa_id,
        ctis.descricao as item,
        ctp.observacao as obs,
        cti.valor as valor,
        null as acerto,
        null as data_acerto,
        null as data_liberacao,
        null as data_pagamento,
        null as data_vencto,
        null as credito,
        null as debito,
        null as data_emissao,
        null as produto,
        0 as quantidade,
        null as situacao,
        '' as liberado,
        null as data_vencto_acerto,
        cast(null as string) as status,
        p.cod_pessoa
    from prd_bronze.kmm_contrato_contrato_transp ctp
    left join prd_bronze.kmm_contrato_contrato_transp_item cti on cti.lancto_id = ctp.lancto_id
    left join prd_bronze.kmm_contrato_contrato_transp_item_setup ctis on ctis.item_id = cti.item_id
    inner join prd_bronze.kmm_kss_pessoa p on p.cod_pessoa = ctp.proprietario_cod_pessoa
""")

# =====================================================
# ETAPA 7: Consulta 6 - Abastecimento (TUDO MINÚSCULO)
# =====================================================
print("📖 Carregando dados - Abastecimento...")
df_abastecimento = spark.sql("""
    select
        'abastecimento' as tipo_consulta,
        p.cnpj_cpf,
        null as tipo_item,
        p.razao_social as transportador,
        null as contas_pagar_id,
        null as docto_id,
        cast(a.controle_id as string) as num_docto,
        null as num_formulario,
        null as parc_docto,
        'abastecimento' as tipo_docto,
        v.placa,
        null as taxa,
        null as taxa_id,
        null as item,
        pr.descricao as obs,
        ab.valor_abastecimento as valor,
        ab.fechamento_id as acerto,
        fc.data_fechamento as data_acerto,
        null as data_liberacao,
        null as data_pagamento,
        null as data_vencto,
        null as credito,
        ab.valor_abastecimento * -1 as debito,
        a.data_hora as data_emissao,
        pr.descricao as produto,
        a.quantidade,
        'gerado' as situacao,
        '' as liberado,
        cpa.data_vencto as data_vencto_acerto,
        cast(null as string) as status,
        p.cod_pessoa
    from prd_bronze.kmm_abastecimento_abastecimento a
    left join prd_bronze.kmm_veiculo_veiculo v on v.placa = a.placa
    left join prd_bronze.kmm_oper_agr_abastecimento ab on ab.controle_id = a.controle_id
    left join prd_bronze.kmm_oper_agr_fechto_agregado fc on fc.fechamento_id = ab.fechamento_id
    left join prd_bronze.kmm_kss_pessoa p on p.cod_pessoa = fc.cod_pessoa
    left join prd_bronze.kmm_fiscal_produto pr on pr.produto_id = a.produto_id
    left join prd_bronze.kmm_finan_finan_contas_pagar cpa on cpa.contas_pagar_id = fc.contas_pagar_id
    where fc.data_cancelamento is null
""")

# =====================================================
# ETAPA 8: Union de todos os DataFrames
# =====================================================
print("🔄 Realizando union dos dados...")

dfs = [df_beneficio, df_adiantamento, df_saldo1, df_saldo2, df_item_contrato, df_abastecimento]

# unionAll é POSICIONAL: a ordem das colunas de cada consulta acima precisa
# bater exatamente com a de df_beneficio (31 colunas). Ao editar qualquer
# consulta, confira a posição, não só o nome.
df_union = dfs[0]
for df_part in dfs[1:]:
    df_union = df_union.unionAll(df_part)

# =====================================================
# ETAPA 9: Aplicar filtros
# =====================================================
print("🔍 Aplicando filtros...")

# Anti-join: remover registros que existem no via_facil
df_final = df_union.join(
    df_via_facil,
    on=["num_docto", "parc_docto", "contas_pagar_id"],
    how="left_anti"
)

# =====================================================
# ETAPA 10: Adicionar data_processamento
# =====================================================
print("📅 Adicionando data_processamento...")

df_final = df_final.withColumn(
    "data_processamento",
    current_timestamp() - expr("interval 3 hours")
)

# =====================================================
# ETAPA 11: Remover duplicatas
# =====================================================
print("🗑️ Removendo duplicatas...")

df_final = df_final.distinct()

# df_final alimenta 6 ações (counts + 4 writes + as duas queries finais).
# Sem persistir, todo o pipeline (6 consultas no bronze + union + distinct)
# é recalculado a cada ação. Persistir também congela o current_timestamp()
# acima, garantindo o mesmo data_processamento nas quatro tabelas.
df_final = df_final.persist(StorageLevel.MEMORY_AND_DISK)

registros_finais = df_final.count()
print(f"✅ Total final (após via_facil e distinct): {registros_finais:,} registros")

# =====================================================
# ETAPA 12: Mostrar schema e amostra
# =====================================================
print("📊 Schema final:")
df_final.printSchema()

print("📊 Amostra (5 primeiros):")
df_final.show(5)

# =====================================================
# ETAPA 13: Gravar saldo_realizado_v2
# =====================================================
print(f"💾 Gravando {registros_finais:,} registros...")

try:
    gravar_jdbc(df_final, "sqlserver", "saldo_realizado_v2")
    gravar_jdbc(df_final, "postgres", "dbo.saldo_realizado_v2")

    verify_df = spark.read \
        .format("jdbc") \
        .option("driver", DESTINOS["sqlserver"]["driver"]) \
        .option("url", DESTINOS["sqlserver"]["url"]) \
        .option("dbtable", "saldo_realizado_v2") \
        .option("user", DESTINOS["sqlserver"]["user"]) \
        .option("password", DESTINOS["sqlserver"]["password"]) \
        .load()

    print(f"✅ Verificação: {verify_df.count():,} registros no SQL Server")

except Exception as e:
    print(f"❌ Erro na gravação: {e}")
    raise

# =====================================================
# ETAPA 14: Carregar tabelas auxiliares
# =====================================================
print("📖 Carregando lista_cooperados do Postgres...")
df_lista_cooperados = spark.read \
    .format("jdbc") \
    .option("driver", DESTINOS["postgres"]["driver"]) \
    .option("url", DESTINOS["postgres"]["url"]) \
    .option("dbtable", "dbo.lista_cooperados") \
    .option("user", DESTINOS["postgres"]["user"]) \
    .option("password", DESTINOS["postgres"]["password"]) \
    .load() \
    .persist(StorageLevel.MEMORY_AND_DISK)

df_lista_cooperados.createOrReplaceTempView("lista_cooperados")

print("📖 Carregando consumer_lista_operacional_v2 do SQL Server...")
df_temp_operacional = spark.read \
    .format("jdbc") \
    .option("driver", DESTINOS["sqlserver"]["driver"]) \
    .option("url", DESTINOS["sqlserver"]["url"]) \
    .option("dbtable", "consumer_lista_operacional_v2") \
    .option("user", DESTINOS["sqlserver"]["user"]) \
    .option("password", DESTINOS["sqlserver"]["password"]) \
    .load()
df_temp_operacional.createOrReplaceTempView("consumer_lista_operacional_v2")

# =====================================================
# ETAPA 15: df_final (já em memória) como saldo_realizado_v2
# =====================================================
df_final.createOrReplaceTempView("saldo_realizado_v2")

# =====================================================
# ETAPA 16: saldo_realizado_final
# =====================================================
print("📝 Gerando saldo_realizado_final...")

df_saldo_final = spark.sql("""
    WITH DCOData AS (
        SELECT
            cft_numero_contrato as CONTRATO,
            codfil as CODFIL,
            serie_cte as SERCON,
            con_num as CODCON,
            origem_x_destino AS `ORIGEM X DESTINO`
        FROM consumer_lista_operacional_v2
        -- Se quiser filtrar por ERP_ID, descomente:
        -- WHERE ERP_ID = 'MULTI'
    ),
    final AS (
        SELECT
            CONTRATO,
            CONCAT_WS(' / ', COLLECT_LIST(CONCAT(CODFIL, '-', SERCON, '-', CODCON))) AS CTE,
            `ORIGEM X DESTINO`
        FROM DCOData
        GROUP BY CONTRATO, `ORIGEM X DESTINO`
    ),
    CalculoDataVencimento AS (
        SELECT DISTINCT
            sr.TRANSPORTADOR,
            l.COD_PESSOA,
            sr.NUM_FORMULARIO,
            f.CONTRATO,
            sr.NUM_DOCTO AS DOCUMENTO,
            sr.CREDITO,
            sr.DEBITO,
            sr.DATA_ACERTO,
            sr.DATA_LIBERACAO,
            cast(sr.data_vencimento as string) as data_vencimento,
            COALESCE(sr.DATA_EMISSAO, sr.DATA_ACERTO) AS DATA_EMISSAO,
            sr.PLACA,
            sr.TAXA,
            sr.TIPO_CONSULTA,
            sr.OBS,
            sr.DATA_PROCESSAMENTO,
            sr.QUANTIDADE,
            f.CTE,
            f.`ORIGEM X DESTINO`,
            CAST(
                CASE
                    WHEN sr.DATA_VENCTO_ACERTO IS NULL OR sr.DATA_VENCTO_ACERTO = ''
                    THEN DATE_ADD(sr.DATA_ACERTO, 45)
                    ELSE sr.DATA_VENCTO_ACERTO
                END AS STRING
            ) AS DATA_VENCIMENTO_CALCULADO
        FROM saldo_realizado_v2 sr
        INNER JOIN lista_cooperados l
            ON sr.TRANSPORTADOR = l.RAZAO_SOCIAL
        LEFT JOIN final f
            ON CAST(sr.NUM_FORMULARIO AS STRING) = CAST(f.CONTRATO AS STRING)
    --    where status = 'realizado'
    ),
    SaldoCTE AS (
        SELECT
            cv.TRANSPORTADOR,
            SUM(cv.DEBITO) AS TotalDebito,
            SUM(cv.CREDITO) AS TotalCredito,
            (SUM(cv.DEBITO) + SUM(cv.CREDITO)) AS TOTAL_SALDO
        FROM CalculoDataVencimento cv
        GROUP BY cv.TRANSPORTADOR
    ),
    CTE_Dados AS (
        SELECT
            cv.TRANSPORTADOR,
            cv.COD_PESSOA,
            cv.NUM_FORMULARIO,
            cv.DOCUMENTO,
            cv.CREDITO,
            cv.DEBITO,
            cv.DATA_ACERTO,
            cv.DATA_LIBERACAO,
            cv.data_vencimento,
            cv.DATA_EMISSAO,
            cv.PLACA,
            cv.TAXA,
            cv.OBS,
            cv.TIPO_CONSULTA,
            cv.CONTRATO,
            cv.DATA_VENCIMENTO_CALCULADO,
            cv.DATA_PROCESSAMENTO,
            cv.QUANTIDADE,
            cv.CTE,
            cv.`ORIGEM X DESTINO`
        FROM CalculoDataVencimento cv
    )
    SELECT
        CD.TRANSPORTADOR,
        CD.COD_PESSOA,
        CD.NUM_FORMULARIO,
        CD.DOCUMENTO,
        CD.CREDITO,
        CD.DEBITO,
        CD.DATA_ACERTO,
        CD.DATA_LIBERACAO,
        data_vencimento,
        CD.DATA_EMISSAO,
        CD.PLACA,
        CD.TAXA,
        CD.OBS,
        CD.TIPO_CONSULTA,
        CD.CONTRATO,
        CD.DATA_VENCIMENTO_CALCULADO,
        CD.DATA_PROCESSAMENTO,
        CD.CTE,
        CD.`ORIGEM X DESTINO`,
        SC.TotalDebito,
        SC.TotalCredito,
        SC.TOTAL_SALDO,
        CD.QUANTIDADE
    FROM CTE_Dados CD
    INNER JOIN SaldoCTE SC ON CD.TRANSPORTADOR = SC.TRANSPORTADOR
""").persist(StorageLevel.MEMORY_AND_DISK)

print("💾 Gravando saldo_realizado_final...")
gravar_jdbc(df_saldo_final, "sqlserver", "saldo_realizado_final_V2")
gravar_jdbc(df_saldo_final, "postgres", "dbo.saldo_realizado_final_V2")
print(f"✅ saldo_realizado_final gerada com {df_saldo_final.count():,} registros")

# =====================================================
# ETAPA 17: saldo_previsto_final
# =====================================================
print("📝 Gerando saldo_previsto_final...")

# Regra de negócio: quais linhas contam como "não liberado".
# Ver INCLUIR_ABASTECIMENTO_BENEFICIO no topo do arquivo.
filtro_liberado = (
    "COALESCE(NULLIF(TRIM(liberado), ''), 'não') = 'não'"
    if INCLUIR_ABASTECIMENTO_BENEFICIO
    else "liberado = 'não'"
)

# ATENÇÃO ao prefixo rf: a string PRECISA ser raw.
# Sem o r, o Python entrega \d ao Spark, e o parser de literais do Spark
# descarta a barra em escapes desconhecidos (\d -> d), virando o regex
# ^d{4}-d{2}-d{2}, que nunca casa com data nenhuma.
# Com raw, o Spark recebe \\d e o regex final é o \d pretendido.
# Sendo f-string, todo { literal do SQL precisa ser dobrado ({{ }}).
df_saldo_previsto = spark.sql(rf"""
WITH
dados_filtrados AS (
    SELECT
        num_formulario,
        transportador,
        tipo_consulta,
        taxa,
        obs,
        credito,
        debito,
        valor,
        data_acerto,
        data_liberacao,
        -- vencimento normalizado: prioriza a liberação; se não houver,
        -- usa o vencimento apenas quando for uma data reconhecível.
        COALESCE(
            CAST(data_liberacao AS STRING),
            CASE
                WHEN data_vencimento RLIKE '^\\d{{4}}-\\d{{2}}-\\d{{2}}'
                THEN data_vencimento
                ELSE NULL
            END
        ) AS data_vencimento_norm,
        -- 'data_vencimento' aqui é a coluna de ORIGEM, não o alias acima
        -- (Spark não resolve alias no mesmo SELECT). É intencional.
        COALESCE(NULLIF(TRIM(CAST(data_liberacao AS STRING)), ''), data_vencimento) AS data_liberacao_clean,
        data_emissao,
        placa,
        data_processamento,
        data_pagamento,
        COALESCE(CAST((credito + debito) AS DECIMAL(18,2)), valor) AS total_saldo
    FROM saldo_realizado_v2
    WHERE LOWER(TRIM(tipo_consulta)) IN ('abastecimento', 'beneficio', 'saldo')
      AND situacao = 'gerado'
      AND {filtro_liberado}
      AND acerto IS NULL
),
dados_join AS (
    SELECT
        df.*,
        l.cod_pessoa
    FROM dados_filtrados df
    INNER JOIN lista_cooperados l
        ON df.transportador = l.razao_social
),
data_pagamento_calc AS (
    SELECT
        *,
        -- Uma única coluna decide qual data alimenta o cálculo,
        -- em vez de duplicar o CASE de corte em cada ramo.
        CASE
            WHEN LOWER(TRIM(tipo_consulta)) IN ('abastecimento', 'beneficio')
            THEN TO_DATE(data_vencimento_norm)
            ELSE TO_DATE(data_liberacao_clean)
        END AS data_base_pagamento,
        CAST(num_formulario AS STRING) AS num_str,
        data_processamento AS data_processamento_ajustada
    FROM dados_join
),
pagamento_calculado AS (
    SELECT
        *,
        -- Corte da quinzena (dia 5, 15, 25 ou dia 5 do mês seguinte) + 45 dias.
        -- TRUNC(d,'MM') é o dia 1 do mês: +4 -> dia 5, +14 -> 15, +24 -> 25.
        DATE_ADD(
            CASE
                WHEN DAYOFMONTH(data_base_pagamento) BETWEEN 1 AND 5
                    THEN DATE_ADD(TRUNC(data_base_pagamento, 'MM'), 4)
                WHEN DAYOFMONTH(data_base_pagamento) BETWEEN 6 AND 15
                    THEN DATE_ADD(TRUNC(data_base_pagamento, 'MM'), 14)
                WHEN DAYOFMONTH(data_base_pagamento) BETWEEN 16 AND 25
                    THEN DATE_ADD(TRUNC(data_base_pagamento, 'MM'), 24)
                ELSE DATE_ADD(TRUNC(ADD_MONTHS(data_base_pagamento, 1), 'MM'), 4)
            END,
            45
        ) AS data_pagamento_calculado
    FROM data_pagamento_calc
)
SELECT
    num_formulario,
    transportador,
    cod_pessoa,
    tipo_consulta,
    taxa,
    obs,
    credito,
    debito,
    valor,
    data_acerto,
    data_liberacao_clean AS data_liberacao,
    data_vencimento_norm AS data_vencimento,
    data_emissao,
    placa,
    data_processamento_ajustada AS data_processamento,
    data_pagamento_calculado,
    CASE
        WHEN SUBSTRING(num_str, 1, 2) = SUBSTRING(num_str, 3, 2)
        THEN CONCAT(
                SUBSTRING(num_str, 1, 2),
                '-C',
                SUBSTRING(num_str, 3, 2),
                '-',
                SUBSTRING(num_str, 5, LENGTH(num_str) - 4)
            )
        ELSE CONCAT(
                SUBSTRING(num_str, 1, 1),
                '-C',
                SUBSTRING(num_str, 2, 2),
                '-',
                SUBSTRING(num_str, 4, LENGTH(num_str) - 3)
            )
    END AS contrato,
    total_saldo
FROM pagamento_calculado
""").persist(StorageLevel.MEMORY_AND_DISK)

# Diagnóstico: quantas linhas ficaram sem data_pagamento_calculado, por tipo.
print("🔎 Preenchimento de data_pagamento_calculado por tipo_consulta:")
df_saldo_previsto.groupBy("tipo_consulta").agg(
    F.count("*").alias("linhas"),
    F.count("data_pagamento_calculado").alias("com_data"),
    F.count("data_vencimento").alias("com_vencimento"),
).show(truncate=False)

gravar_jdbc(df_saldo_previsto, "sqlserver", "saldo_previsto_final_v2")
gravar_jdbc(df_saldo_previsto, "postgres", "dbo.saldo_previsto_final_v2")

print(f"✅ saldo_previsto_final gerada com {df_saldo_previsto.count():,} registros")

job.commit()
print("🏁 Job finalizado!")
