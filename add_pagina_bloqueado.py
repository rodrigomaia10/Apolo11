import json, os, uuid

BASE = r"C:\PowerBIClaudio\14 - Controladoria"
SM = os.path.join(BASE, "Financeiro.SemanticModel")
RP = os.path.join(BASE, "Financeiro.Report")
PAGES = os.path.join(RP, "definition", "pages")
R, Q = "TituloReceber", "TituloPagar"

# ---------------- modelo: medida nova (as 3 de bloqueado e as colunas ja foram salvas pelo Desktop)
tp = os.path.join(SM, "definition", "tables", "TituloPagar.tmdl")
t = open(tp, "rb").read().decode("utf-8")
assert "status_liberacao" in t and "A Pagar Bloqueado" in t, "salve o Financeiro antes (colunas/medidas de bloqueado)"
assert "% Bloqueado" not in t
nl = "\r\n" if "\r\n" in t else "\n"
m = nl.join(["\tmeasure '% Bloqueado' = DIVIDE([A Pagar Bloqueado], [A Pagar (títulos)])", "\t\tformatString: 0.0%",
             "\t\tdisplayFolder: 1. Contas a pagar", "\t\tlineageTag: %s" % uuid.uuid4()]) + nl + nl
marker = "\tpartition TituloPagar = m"
assert t.count(marker) == 1
open(tp, "wb").write(t.replace(marker, m + marker).encode("utf-8"))
print("medida % Bloqueado ok")

src = open(r"C:\project\Apolo11\build_financeiro.py", encoding="utf-8").read()
i = src.index("# ============================================================ relatorio")
j = src.index("# ----- pagina 1")
exec(src[i:j])

p6 = Page("a1b2c3d4e5f607182906", "A pagar bloqueado", "Títulos a pagar que exigem liberação de pagamento e ainda não têm valor liberado no KMM")
slicers(p6, Q, "fornecedor", "Fornecedor", "g_blq")
p6.cards([(Q, "Títulos Bloqueados", RED, "Títulos bloqueados"), (Q, "A Pagar Bloqueado", RED, "Valor bloqueado"), (Q, "Saldo Bloqueado", AMBER, "Saldo bloqueado"),
          (Q, "% Bloqueado", AMBER, "% do valor a pagar"), (Q, "A Pagar (títulos)", NAVY, "A pagar total (referência)"), (Q, "Títulos a Pagar", GRAY, "Títulos (total)")])
p6.chart("c_mes", "clusteredColumnChart", 20, 208, 760, 300, pc("Calendario", "Ano-Mês", active=True), [pm(Q, "A Pagar Bloqueado")],
         "Valor bloqueado, por mês de emissão do título", cor=RED)
p6.chart("c_lib", "donutChart", 800, 208, 360, 300, pc(Q, "status_liberacao", active=True), [pm(Q, "A Pagar (títulos)")], "A pagar por situação da liberação", legenda=True)
p6.chart("c_fil", "barChart", 1180, 208, 400, 300, pc(Q, "filial", active=True), [pm(Q, "A Pagar Bloqueado")], "Bloqueado por filial", cor=RED, ordenar=sort_med(Q, "A Pagar Bloqueado"))
p6.tabela("t_blq", 20, 524, 1560, 330,
          [pc(Q, "tipo_docto", "Tipo"), pc(Q, "num_docto", "Documento"), pc(Q, "parc_docto", "Parcela"), pc(Q, "data_emissao", "Emissão"), pc(Q, "data_vencto", "Vencimento"),
           pc(Q, "fornecedor", "Fornecedor"), pc(Q, "filial", "Filial"), pc(Q, "usuario_titulo", "Usuário"), pc(Q, "status_pagamento", "Situação do pagamento"),
           pm(Q, "A Pagar (títulos)"), pm(Q, "Saldo a Pagar")], "Títulos bloqueados (ordenado pelo valor)", ordenar=sort_med(Q, "A Pagar (títulos)"),
          filtros=[filtro_in(Q, "status_liberacao", ["BLOQUEADO"], "f_bq1")])
p6.texto("rodape", 20, 862, 1560, 34, "Bloqueado = o título exige liberação de pagamento (exige_liberacao_pagamento) e não tem valor liberado em contas_pagar_liberacao. O bloqueado continua somado no 'a pagar' total: "
         "aqui ele só é destacado. Parte dos bloqueados aparece e parte some em telas do KMM; o BI mostra todos.")
pj = os.path.join(PAGES, "pages.json")
d = json.load(open(pj, encoding="utf-8"))
if p6.pid not in d["pageOrder"]:
    # logo depois de "Contas a pagar" (3a pagina)
    k = d["pageOrder"].index("a1b2c3d4e5f607182903") + 1
    d["pageOrder"].insert(k, p6.pid)
json.dump(d, open(pj, "w", encoding="utf-8"), indent=2)
print("pagina A pagar bloqueado ok:", d["pageOrder"])
