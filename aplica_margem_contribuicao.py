"""Decisao do usuario (20/10/2026): a margem principal da curva e da Diretoria e a MARGEM DE CONTRIBUICAO calculada dos lancamentos
(formula do DRE sobre a tabela, sem usar a foto do DRE); a margem financeira (receita - custo de frete e ocorrencia) fica so por cliente/referencia.
Atualiza build_diretoria.py, build_memorando.py e a curva do Financeiro (JSON). Rodar com Financeiro e Diretoria FECHADOS.
"""
import json, os, shutil

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = r"C:\project\PowerBIClaudio\14 - Controladoria"


def le(n):
    return open(os.path.join(AQUI, n), encoding="utf-8").read()


def grava(n, t):
    open(os.path.join(AQUI, n), "w", encoding="utf-8", newline="").write(t)


# ---------------- build_diretoria.py
t = le("build_diretoria.py")
a = '(DOC, "Margem de Frete % (bruta)", TEAL, "Margem financeira (receita − custo de frete)")'
assert t.count(a) == 1
t = t.replace(a, '(DL, "Margem de Contribuição % (KMM, método DRE)", TEAL, "Margem de contribuição (lançamentos)")')
i = t.index('p1.chart("g_mar"')
j = t.index("filtros=fm)", i) + len("filtros=fm)")
t = t[:i] + ('p1.chart("g_mar", "lineChart", 810, 210, 770, 300, cat, [pm(DL, "Margem de Contribuição % (KMM, método DRE)", "Margem de contribuição")],\n'
             '         "Margem de contribuição por mês (fórmula do DRE sobre os lançamentos)", cor=TEAL, filtros=fm)') + t[j:]
i = t.index('p1.texto("leitura"')
j = t.index('container=p1.box("Leitura"))', i) + len('container=p1.box("Leitura"))')
t = t[:i] + ('p1.texto("leitura", 1040, 655, 540, 190,\n'
             '         "Como ler: a margem de contribuição segue a regra do DRE (receita líquida menos custos dos serviços, repasse, fretes anulados e abatimentos), calculada com os lançamentos do KMM. "\n'
             '         "Ela fica perto da margem do DRE, mas pode ficar até cerca de 2 pontos abaixo ou acima porque os lançamentos manuais do KMM (folha, encargos, provisões) ainda não chegam ao Athena. "\n'
             '         "A margem por cliente na tabela é a margem financeira: receita menos custo de frete e ocorrência, antes de impostos e repasse; serve para comparar clientes, não para somar. "\n'
             '         "Maio, junho e outubro ficam de fora porque a conferência com a contabilidade só está completa de julho a setembro.",\n'
             '         "10pt", GRAY, container=p1.box("Leitura"))') + t[j:]
grava("build_diretoria.py", t)

# ---------------- build_memorando.py
m = le("build_memorando.py")


def bloco(ini, fim, novo, base=0):
    global m
    i = m.index(ini, base)
    j = m.index(fim, i)
    m = m[:i] + novo + m[j:]


bloco('("Página 1: Visão da diretoria"', '("Página 2: Caixa e prazos"', '''("Página 1: Visão da diretoria", [
            ("Cartões:", "faturamento operacional, margem de contribuição (regra do DRE, calculada dos lançamentos), peso dos 5 maiores clientes, peso do maior cliente e fretes anulados em % da receita."),
            ("Gráficos:", "faturamento x custo de frete por mês e margem de contribuição por mês."),
            ("Tabela de clientes:", "faturamento, participação e margem financeira de cada cliente (receita menos custo de frete e ocorrência). Serve para comparar clientes entre si."),
        ]),
        ''')
bloco('("Visão financeira, não contábil"', '("De onde vêm os números"', '''("As duas margens (não confundir)", [
            ("Margem de contribuição (principal):", "receita líquida menos custos dos serviços, repasse, fretes anulados e abatimentos, pela fórmula do DRE, calculada com os lançamentos do KMM. Fica em torno de 9% a 10% em jul a set, perto da margem do DRE."),
            ("Margem financeira (por cliente):", "receita menos custo de frete e ocorrência, antes de impostos e repasse. Fica em 26% a 28%; é mais alta porque não desconta impostos nem os demais custos. Usada só para comparar clientes."),
        ]),
        ''')
bloco('("De onde vêm os números", [\n            "Títulos', '("O que ainda está em validação"', '''("De onde vêm os números", [
            "Títulos, baixas, conciliação de documentos e cargas e lançamentos contábeis do KMM, lidos do Athena (camada gold). A margem do DRE só entra como conferência na Controladoria.",
            ("Selo de confiança:", "mostra quanto da receita está conciliado com a contabilidade."),
            "O relatório usa o mesmo modelo de dados do Financeiro, então os números são os mesmos nos dois.",
        ]),
        ''')
bloco('("O que ainda está em validação"', '    ], alt=255, passo=265)', '''("O que ainda está em validação", [
            ("Caixa:", "o saldo recente negativo precisa ser confirmado com a tesouraria e o extrato bancário."),
            ("Lançamentos manuais do KMM:", "ainda não chegam ao Athena (folha, encargos, provisões). Por isso a margem de contribuição pode diferir da do DRE em até cerca de 2 pontos; a carga completa foi pedida ao time de dados."),
            ("Fora do período:", "maio e junho (conferência contábil incompleta) e outubro (faturamento ainda na versão anterior da conciliação)."),
        ]),
''')
b2 = m.index('p2 = Page("a1b2c3d4e5f607182916"')
bloco('("Curva operacional x financeiro"', '("Conferência com a tela"', '''("Curva operacional x financeiro", [
            "Compara o faturamento operacional (CT-e e NF do painel, pelo mês de emissão do documento) com o faturado, a vencer, recebido e previsto, e mostra o custo dos contratos por mês (pago, previsto e liquidado por desconto).",
            ("Margem:", "o cartão principal é a margem de contribuição pela regra do DRE, calculada dos lançamentos do KMM (jul a set); fica perto da do DRE (pode diferir em até cerca de 2 pontos por causa dos lançamentos manuais ainda ausentes no Athena). A margem financeira (receita menos custo de frete e ocorrência, antes de impostos e repasse) fica na tabela, como referência."),
            ("Fonte:", "Documentos (conciliação Multi x KMM), CustoData, títulos e DreContabil/DreLinhas (lançamentos)."),
        ]),
        ''', b2)
bloco('("DRE em cascata (só conferência)"', '    ], alt=255, passo=265)', '''("DRE em cascata (só conferência)", [
            "ROB, ROL, margem de contribuição, resultado operacional, sobra gerencial e sobra contábil calculados com a contabilidade do KMM, ao lado do DRE e dos lançamentos manuais ausentes no Athena.",
            ("Uso:", "provar que a regra de cálculo está certa. A coluna 'diferença sem ajuste manual' zera em todas as linhas, exceto o efeito das NF de serviço de set. A margem de contribuição da curva usa essa mesma regra, só com a tabela de lançamentos; a foto do DRE serve apenas para comparar."),
        ]),
''', b2)
b3 = m.index('p3 = Page("a1b2c3d4e5f607182917"')
bloco('("Definições usadas"', '("Limitações conhecidas e pendências"', '''("Definições usadas", [
            ("Faturamento operacional:", "receita bruta dos CT-e e NF do painel (status A ou S), cada documento uma vez, pelo mês de emissão."),
            ("Margem de contribuição (principal):", "fórmula do DRE (contas marcadas na margem bruta sobre as marcadas XD) aplicada aos lançamentos do KMM; é a margem da curva e da Diretoria."),
            ("Margem financeira (por cliente):", "faturamento operacional menos custo de frete e ocorrência das mesmas cargas, antes de impostos e repasse; compara clientes."),
            ("Saídas de caixa:", "todas as baixas de títulos a pagar (folha, tributos, contratos, empréstimos); não é o saldo bancário."),
        ]),
        ''', b3)
bloco('("Limitações conhecidas e pendências"', '    ], alt=255, passo=265)', '''("Limitações conhecidas e pendências", [
            ("Lançamentos manuais do KMM:", "não chegam ao Athena (1 item manual contra mais de 11 mil linhas na base do DRE em jul a set). Afetam o resultado contábil e deslocam a margem de contribuição em cerca de -0,2 a +1,7 ponto; carga completa pedida ao time de dados."),
            ("NF de serviço de set/26:", "3 notas (856, 866 e 868; R$ 2.703,74) foram lançadas duas vezes no KMM e o log do Athena guarda as duas; só a origem pode corrigir."),
            ("ND sem lançamento:", "32 notas de débito (R$ 261 mil em set) sem lançamento contábil pelo número e CNPJ."),
            ("Caixa:", "saldo recente negativo a validar com a tesouraria."),
            ("Períodos:", "maio e junho (conferência contábil incompleta) e outubro (faturamento defasado até a nova versão da conciliação)."),
            ("Margem por cliente:", "é a margem financeira de cada cliente; o DRE não abre por cliente."),
        ]),
''', b3)
grava("build_memorando.py", m)

# ---------------- curva do Financeiro (JSON)
rep = os.path.join(BASE, "Financeiro.Report")
bk = rep + "_backup_20261020_i"
if not os.path.exists(bk):
    shutil.copytree(rep, bk)
vis = os.path.join(rep, "definition", "pages", "a1b2c3d4e5f607182908", "visuals")


def ref(tab, med, dn):
    return {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": tab}}, "Property": med}},
            "queryRef": "%s.%s" % (tab, med), "nativeQueryRef": med, "displayName": dn}


def lit(v):
    return {"expr": {"Literal": {"Value": v}}}


MC = "Margem de Contribuição % (KMM, método DRE)"
p = os.path.join(vis, "a5", "visual.json")
d = json.load(open(p, encoding="utf-8"))
d["visual"]["query"]["queryState"]["Values"]["projections"] = [ref("DreLinhas", MC, "Margem de contribuição % (lançamentos, jul a set)")]
filtro = {"name": "f_meses", "field": {"Column": {"Expression": {"SourceRef": {"Entity": "Calendario"}}, "Property": "Ano-Mês"}}, "type": "Categorical",
          "filter": {"Version": 2, "From": [{"Name": "d", "Entity": "Calendario", "Type": 0}],
                     "Where": [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": "Ano-Mês"}}],
                                                      "Values": [[{"Literal": {"Value": "'%s'" % x}}] for x in ("2026-07", "2026-08", "2026-09")]}}}]},
          "howCreated": "User"}
d["filterConfig"] = {"filters": [filtro]}
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

p = os.path.join(vis, "t_curva", "visual.json")
d = json.load(open(p, encoding="utf-8"))
pr = d["visual"]["query"]["queryState"]["Values"]["projections"]
idx = next(k for k, x in enumerate(pr) if "Measure" in x["field"] and x["field"]["Measure"]["Property"] == "Margem de Frete % (bruta)")
pr[idx]["displayName"] = "Margem financeira (receita − custo de frete)"
if not any("Measure" in x["field"] and x["field"]["Measure"]["Property"] == MC for x in pr):
    pr.insert(idx, ref("DreLinhas", MC, "Margem de contribuição % (lançamentos)"))
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

p = os.path.join(vis, "rodape", "visual.json")
d = json.load(open(p, encoding="utf-8"))
r = d["visual"]["objects"]["general"][0]["properties"]["paragraphs"][0]["textRuns"][0]
i = r["value"].find(" MARGEM FINANCEIRA =")
if i >= 0:
    r["value"] = r["value"][:i]
r["value"] += (" MARGEM DE CONTRIBUIÇÃO % = fórmula do DRE aplicada aos lançamentos do KMM (jul a set); fica perto da margem do DRE e pode diferir em até cerca de 2 pontos "
               "porque os lançamentos manuais do KMM ainda não chegam ao Athena. MARGEM FINANCEIRA = receita menos custo de frete e ocorrência, antes de impostos e repasse; compara clientes.")
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("ajustes aplicados nos scripts e na curva do Financeiro")
