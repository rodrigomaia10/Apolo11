-- Fato: itens contabeis sem origem (lancamentos manuais e de rotinas) nas contas do DRE, com historico e usuario.
-- Grao: mes x conta x historico x usuario. Serve a pagina "Ajustes manuais do DRE" do BI Financeiro (substitui o Odbc.Query com join no bronze).
-- Regra: origem '(sem origem)' (sk_origem -1) e conta presente em dim_conta_dre; valor = credito - debito (valor_saldo).
SELECT
    f.mes_lancamento AS mes,
    f.data_mes,
    c.num_conta,
    c.classificacao,
    c.conta_descricao,
    i.historico,
    i.user_insert AS usuario,
    SUM(f.valor_saldo) AS valor,
    COUNT(*) AS linhas
FROM {env}_gold.fato_contab_item f
JOIN {env}_gold.dim_conta c ON c.sk_conta = f.sk_conta
JOIN {env}_gold.dim_conta_dre d ON d.sk_conta = f.sk_conta
JOIN {env}_gold.dim_origem_contabil o ON o.sk_origem = f.sk_origem AND o.origem = '(sem origem)'
JOIN {env}_silver.kmm_contab_lancamento_item i ON i.num_lancamento_it = f.num_lancamento_it
GROUP BY f.mes_lancamento, f.data_mes, c.num_conta, c.classificacao, c.conta_descricao, i.historico, i.user_insert
