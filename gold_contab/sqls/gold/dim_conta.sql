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
