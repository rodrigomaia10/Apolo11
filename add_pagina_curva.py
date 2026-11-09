import json, os

BASE = r"C:\PowerBIClaudio\14 - Controladoria"
RP = os.path.join(BASE, "Financeiro.Report")
PAGES = os.path.join(RP, "definition", "pages")
R, Q, D = "TituloReceber", "TituloPagar", "Documentos"

src = open(r"C:\project\Apolo11\build_financeiro.py", encoding="utf-8").read()
i = src.index("# ============================================================ relatorio")
j = src.index("# ----- pagina 1")
exec(src[i:j])


def linha(pg, name, x, y, wd, h, series, titulo):
    q = {"queryState": {"Category": {"projections": [pc("Calendario", "Ano-Mês", active=True)]},
                        "Y": {"projections": [pm(t, m, dn) for t, m, dn in series]}}}
    obj = {"labels": [{"properties": {"show": lit("false")}}], "legend": [{"properties": {"show": lit("true"), "position": lit("'Bottom'")}}],
           "valueAxis": [{"properties": {"show": lit("true"), "fontSize": lit("9D")}}], "categoryAxis": [{"properties": {"fontSize": lit("9D")}}]}
    pg.put(name, x, y, wd, h, {"visualType": "lineChart", "query": q, "objects": obj}, pg.box(titulo))


p8 = Page("a1b2c3d4e5f607182908", "Curva operacional x financeiro", "Faturamento operacional, receita, faturado e custo, mês a mês: documentos (Multi/KMM) contra títulos (contas a receber e a pagar)")
p8.slicer("sl_ano", "Ano", 740, 80, "Calendario", "Ano", "g_ano")
p8.slicer("sl_mes", "Mês de emissão", 830, 130, "Calendario", "Ano-Mês", "g_mes")
p8.slicer("sl_fil", "Filial (documentos)", 970, 220, D, "filial_multi", "g_cur_fil")
p8.slicer("sl_grp", "Cliente (grupo) dos documentos", 1200, 380, D, "grupo_tomador", "g_cur_grp")
p8.cards([(D, "Faturamento Operacional (Painel)", NAVY, "Faturamento operacional"), (D, "Receita dos Documentos (KMM)", TEAL, "Receita dos documentos (KMM)"),
          (R, "Faturado", AMBER, "Faturado (títulos a receber)"), (D, "Custo Operacional", RED, "Custo operacional (frete + ocorrência)"),
          (Q, "A Pagar (títulos)", GRAY, "A pagar total (títulos)"), (D, "Margem Operacional % (bruta)", TEAL, "Margem operacional bruta")])
linha(p8, "g_receita", 20, 208, 770, 300,
      [(D, "Faturamento Operacional (Painel)", "Faturamento operacional"), (D, "Receita dos Documentos (KMM)", "Receita dos documentos (KMM)"),
       (R, "Faturado", "Faturado (títulos)"), (R, "Recebido", "Recebido")],
      "Receita: operacional x faturado x recebido")
linha(p8, "g_custo", 810, 208, 770, 300,
      [(D, "Custo Operacional", "Custo operacional"), (Q, "A Pagar (títulos)", "A pagar total"), (Q, "Pago", "Pago")],
      "Custo: operacional x a pagar x pago")
p8.tabela("t_curva", 20, 524, 1560, 330,
          [pc("Calendario", "Ano-Mês", "Mês"), pm(D, "Faturamento Operacional (Painel)", "Fat. operacional"), pm(D, "Receita dos Documentos (KMM)", "Receita docs (KMM)"),
           pm(R, "Faturado", "Faturado"), pm(D, "Faturado menos Operacional", "Faturado − operacional"), pm(R, "Recebido", "Recebido"),
           pm(D, "Custo Operacional", "Custo operacional"), pm(Q, "A Pagar (títulos)", "A pagar total"), pm(D, "A Pagar menos Custo Operacional", "A pagar − custo oper."),
           pm(Q, "Pago", "Pago"), pm(D, "Margem Operacional % (bruta)", "Margem oper. bruta")],
          "Mês a mês", ordenar={"field": cref("Calendario", "Ano-Mês"), "direction": "Ascending"})
p8.texto("rodape", 20, 862, 1560, 34,
         "Operacional = documentos (CT-e e NF do Multi) pelo mês de EMISSÃO do documento. Faturado e a pagar = títulos do KMM pelo mês de EMISSÃO do título. "
         "Os meses não casam exatamente: a fatura sai depois do documento, e o a pagar inclui despesas que não são frete (folha, tributos, Repom, financiamento). "
         "Filtros de filial e cliente valem só para os documentos.")
pj = os.path.join(PAGES, "pages.json")
d = json.load(open(pj, encoding="utf-8"))
if p8.pid not in d["pageOrder"]:
    d["pageOrder"].insert(1, p8.pid)
json.dump(d, open(pj, "w", encoding="utf-8"), indent=2)
print("pagina curva ok:", d["pageOrder"])
