"""Cria a pagina 'Conferencia contabil' no Financeiro.Report (rodar com o Desktop FECHADO).
Reaproveita as classes/funcoes de pagina de build_financeiro.py (trecho '# ===== relatorio' ate '# ----- pagina 1').
Uso: python build_pagina_conferencia_contabil.py
"""
import json, os

RP = r"C:\project\PowerBIClaudio\14 - Controladoria\Financeiro.Report"
fonte = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_financeiro.py"), encoding="utf-8").read().split("\n")
ini = next(i for i, l in enumerate(fonte) if l.startswith("# ====") and l.rstrip().endswith("relatorio"))
fim = next(i for i, l in enumerate(fonte) if l.startswith("# ----- pagina 1"))
exec("\n".join(fonte[ini:fim]))

PID = "a1b2c3d4e5f607182911"
D, L = "Documentos", "LigacaoContabil"
pg = Page(PID, "Conferência contábil", "Faturamento operacional e custo dos contratos x lançamentos contábeis do KMM (contas 3.1.1.01 e 3.1.2.05)")
pg.slicer("sl_ano", "Ano", 740, 90, "Calendario", "Ano", "g_ano")
pg.slicer("sl_mes", "Mês de emissão", 840, 140, "Calendario", "Ano-Mês", "g_mes")
pg.slicer("sl_grp", "Cliente (grupo)", 990, 590, D, "grupo_tomador", "g_ctb_grp")

pg.cards([
    (D, "Faturamento Operacional (Painel)", NAVY, "Faturamento operacional"),
    (L, "Receita Contábil (CT-e e NF)", TEAL, "Receita contábil"),
    (L, "Diferença Contábil x Operacional", RED, "Diferença"),
    (L, "% Operacional na Contabilidade", NAVY, "% na contabilidade"),
    (D, "Custo Operacional", NAVY, "Custo operacional"),
    (L, "Custo Contábil Total", TEAL, "Custo contábil dos contratos"),
])

MESES = ["2026-%02d" % m for m in range(5, 13)]
fm = [filtro_in("Calendario", "Ano-Mês", MESES, "f_meses")]
cat = pc("Calendario", "Ano-Mês", "Mês")
pg.chart("g_receita", "clusteredColumnChart", 20, 210, 770, 290, cat,
         [pm(D, "Faturamento Operacional (Painel)", "Faturamento operacional"), pm(L, "Receita Contábil (CT-e e NF)", "Receita contábil")],
         "Receita: faturamento operacional x contabilidade", legenda=True, filtros=fm)
pg.chart("g_custo", "clusteredColumnChart", 810, 210, 770, 290, cat,
         [pm(D, "Custo Operacional", "Custo operacional"), pm(L, "Custo Contábil Total", "Custo contábil dos contratos")],
         "Custo: conciliação x contabilidade", legenda=True, filtros=fm)

pg.tabela("t_mes", 20, 515, 940, 335, [
    pc("Calendario", "Ano-Mês", "Mês"),
    pm(D, "Faturamento Operacional (Painel)", "Fat. operacional"),
    pm(L, "Receita Contábil (CT-e e NF)", "Receita contábil"),
    pm(L, "Diferença Contábil x Operacional", "Diferença"),
    pm(L, "% Operacional na Contabilidade", "% na contab."),
    pm(L, "Documentos sem Receita Contábil", "Docs sem lanç."),
    pm(L, "Faturamento Operacional sem Receita Contábil", "Fat. sem lanç."),
    pm(D, "Custo Operacional", "Custo operacional"),
    pm(L, "Custo Contábil Total", "Custo contábil"),
    pm(L, "Custo Contábil menos Custo Operacional", "Custo contábil - oper."),
    pm(L, "Margem Contábil %", "Margem contábil"),
], "Por mês de emissão", ordenar={"field": cref("Calendario", "Ano-Mês"), "direction": "Ascending"}, filtros=fm)

pg.tabela("t_cli", 980, 515, 600, 335, [
    pc(D, "grupo_tomador", "Cliente (grupo)"),
    pm(D, "Faturamento Operacional (Painel)", "Fat. operacional"),
    pm(L, "Receita Contábil (CT-e e NF)", "Receita contábil"),
    pm(L, "Diferença Contábil x Operacional", "Diferença"),
    pm(L, "Documentos sem Receita Contábil", "Docs sem lanç."),
], "Por cliente (maiores diferenças primeiro, no período filtrado)", ordenar=sort_med(L, "Diferença Contábil x Operacional", "Ascending"))

pg.texto("rodape", 20, 856, 1560, 40,
         "Ligação: CT-e/NF pelo número do documento + CNPJ do tomador no mês da emissão; contrato pelo ID do contrato no histórico do lançamento. Receita = conta 3.1.1.01 e custo = conta 3.1.2.05 "
         "(frete + itens), rateado entre as linhas de cada contrato. Lançamentos contábeis existem de 01/05/2026 a 30/09/2026 e contratos desde 18/05: a margem contábil de maio e todo o mês de outubro "
         "não são comparáveis. O filtro de filial não vale nesta página.", "8pt", GRAY)

# ordem das paginas: logo depois de 'Conferencia com a tela'
pp = os.path.join(RP, "definition", "pages", "pages.json")
meta = json.load(open(pp, encoding="utf-8"))
if PID not in meta["pageOrder"]:
    i = meta["pageOrder"].index("a1b2c3d4e5f607182909")
    meta["pageOrder"].insert(i + 1, PID)
json.dump(meta, open(pp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("pagina criada:", PID)
