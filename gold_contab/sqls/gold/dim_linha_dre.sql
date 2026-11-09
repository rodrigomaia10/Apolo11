-- As 14 linhas da cascata do DRE (ROB ... Sobra Contabil). Antes: tabela fixa dentro de DreLinhas no BI.
SELECT * FROM VALUES
    (1, 'RECEITA TOTAL (ROB)', 1, '='),
    (2, 'INGRESSOS E RECEITAS DE FRETE', 0, '+'),
    (3, 'REPASSE LÍQUIDO', 0, '+'),
    (4, 'DEDUÇÕES DA RECEITA', 0, '-'),
    (5, 'RECEITAS OPERACIONAIS LÍQUIDAS (ROL)', 1, '='),
    (6, 'CUSTOS DOS SERVIÇOS PRESTADOS', 0, '-'),
    (7, 'MARGEM DE CONTRIBUIÇÃO BRUTA', 1, '='),
    (8, 'DESPESAS OPERACIONAIS', 0, '-'),
    (9, 'INDEDUTÍVEIS E TRIBUTÁRIAS', 0, '-'),
    (10, 'RESULTADO OPERACIONAL', 1, '='),
    (11, 'RECEITAS E DESPESAS FINANCEIRAS', 0, '-'),
    (12, 'SOBRA GERENCIAL', 1, '='),
    (13, 'OUTRAS RECEITAS/DESPESAS', 0, '-'),
    (14, 'SOBRA CONTÁBIL', 1, '=')
AS t (codigo, linha, subtotal, sinal)
