"""Reescreve, em build_memorando.py, os trechos do memorando do Financeiro sobre margens e fotos do DRE
(decisao do usuario em 20/10/2026: olhar financeiro; foto do DRE so para comparar). Nao toca nos relatorios.
"""
m = open("build_memorando.py", encoding="utf-8").read()
base = m.index('p2 = Page("a1b2c3d4e5f607182916"')


def bloco(ini, fim, novo):
    global m
    i = m.index(ini, base)
    j = m.index(fim, i)
    m = m[:i] + novo + m[j:]


bloco('("Curva operacional x financeiro"', '("Conferência com a tela"', '''("Curva operacional x financeiro", [
            "Compara o faturamento operacional (CT-e e NF do painel, pelo mês de emissão do documento) com o faturado, a vencer, recebido e previsto, e mostra o custo dos contratos por mês (pago, previsto e liquidado por desconto).",
            ("Margem:", "o cartão principal é a margem financeira: receita dos documentos menos custo de frete e ocorrência, antes de impostos e repasse, no mês da emissão. Visão financeira, não contábil."),
            ("Fonte:", "Documentos (conciliação Multi x KMM), CustoData e os títulos."),
        ]),
        ''')
bloco('("DRE contábil"', '("Ajustes manuais do DRE"', '''("DRE contábil (só conferência)", [
            "Contabilidade do KMM (contas de resultado) comparada ao DRE gerencial, por mês, conta e origem do lançamento (jul a set). O DRE é uma foto de 20/10/2026, usada só para comparar; nenhum indicador depende dela.",
            ("Situações:", "OK (diferença menor que R$ 1), lançamento manual ausente no Athena (só existe na base do DRE), divergente e fora do período. A tabela do topo mostra o que não bate; hoje são só as NF de serviço de set (R$ 2.703,74 líquido)."),
        ]),
        ''')
bloco('("Ajustes manuais do DRE"', '("DRE em cascata (base KMM)"', '''("Lançamentos manuais (só conferência)", [
            "Detalhe dos lançamentos que a base do DRE tem e a tabela do Athena não tem (origem em branco): conta, histórico e quem lançou. Foto de 20/10/2026 para jul a set, extraída do BI do DRE; usada só para comparar.",
            ("O que são:", "lançamentos manuais do próprio KMM (permite editar), como folha, encargos, seguro, juros, provisões e reclassificações de receita. Ainda não chegam ao Athena; a carga completa foi pedida ao time de dados."),
        ]),
        ''')
bloco('("DRE em cascata (base KMM)"', '    ], alt=255, passo=265)', '''("DRE em cascata (só conferência)", [
            "ROB, ROL, margem de contribuição, resultado operacional, sobra gerencial e sobra contábil calculados com a contabilidade do KMM, ao lado do DRE e dos lançamentos manuais ausentes no Athena.",
            ("Uso:", "provar que a regra de cálculo está certa. A coluna 'diferença sem ajuste manual' zera em todas as linhas, exceto o efeito das NF de serviço de set. Não é a margem do negócio: a margem usada nas decisões é a financeira."),
        ]),
''')
base = m.index('p3 = Page("a1b2c3d4e5f607182917"')
bloco('("Tabelas do modelo"', '("Relações e filtros"', '''("Tabelas do modelo", [
            ("Fatos:", "TituloReceber, TituloPagar, BaixaPagar, CustoData, Documentos, LigacaoContabil e DreContabil. Calendario é a dimensão de datas."),
            ("Medidas:", "Diretoria (caixa, concentração, selo de confiança) e DreLinhas (as 14 linhas do DRE, usadas na conferência)."),
            ("Fotos estáticas, só para comparar:", "DrePlano (plano de contas do DRE), DreAjustesManuais e a referência do DRE dentro de DreContabil. Extraídas do BI do DRE em 19 e 20/10/2026; não atualizam sozinhas e nenhum indicador depende delas."),
        ]),
        ''')
bloco('("Definições usadas"', '("Limitações conhecidas e pendências"', '''("Definições usadas", [
            ("Faturamento operacional:", "receita bruta dos CT-e e NF do painel (status A ou S), cada documento uma vez, pelo mês de emissão."),
            ("Margem financeira (decisão):", "faturamento operacional menos custo de frete e ocorrência das mesmas cargas, antes de impostos e repasse. Visão financeira, não contábil."),
            ("Margem de contribuição (conferência):", "fórmula do DRE aplicada à contabilidade; só para conferir com a controladoria."),
            ("Saídas de caixa:", "todas as baixas de títulos a pagar (folha, tributos, contratos, empréstimos); não é o saldo bancário."),
        ]),
        ''')
bloco('("Limitações conhecidas e pendências"', '    ], alt=255, passo=265)', '''("Limitações conhecidas e pendências", [
            ("Lançamentos manuais do KMM:", "não chegam ao Athena (1 item manual contra mais de 11 mil linhas na base do DRE em jul a set). Afetam o resultado contábil, não a visão financeira; carga completa pedida ao time de dados."),
            ("NF de serviço de set/26:", "3 notas (856, 866 e 868; R$ 2.703,74) foram lançadas duas vezes no KMM e o log do Athena guarda as duas; só a origem pode corrigir."),
            ("ND sem lançamento:", "32 notas de débito (R$ 261 mil em set) sem lançamento contábil pelo número e CNPJ."),
            ("Caixa:", "saldo recente negativo a validar com a tesouraria."),
            ("Períodos:", "maio e junho (conferência contábil incompleta) e outubro (faturamento defasado até a nova versão da conciliação)."),
            ("Margem por cliente:", "é a margem financeira de cada cliente; o DRE não abre por cliente."),
        ]),
''')
open("build_memorando.py", "w", encoding="utf-8", newline="").write(m)
print("memorando do Financeiro ajustado em build_memorando.py")
