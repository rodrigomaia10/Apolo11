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
