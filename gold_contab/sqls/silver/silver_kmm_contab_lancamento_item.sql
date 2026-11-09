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
