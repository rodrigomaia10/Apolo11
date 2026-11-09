import json, os, uuid

BASE = r"C:\PowerBIClaudio\14 - Controladoria"
SM = os.path.join(BASE, "Financeiro.SemanticModel")
RP = os.path.join(BASE, "Financeiro.Report")
PAGES = os.path.join(RP, "definition", "pages")
R, Q = "TituloReceber", "TituloPagar"
MON = '"R$"\\ #,##0.00;-"R$"\\ #,##0.00'


def g():
    return str(uuid.uuid4())


# ============================================================ modelo
def col(nome, tipo, fmt=None, hidden=False):
    L = ["\tcolumn %s" % nome, "\t\tdataType: %s" % tipo]
    if fmt: L.append("\t\tformatString: %s" % fmt)
    if hidden: L.append("\t\tisHidden")
    L += ["\t\tlineageTag: %s" % g(), "\t\tsummarizeBy: none", "\t\tsourceColumn: %s" % nome]
    return L


def patch(tabela, colunas, medidas):
    p = os.path.join(SM, "definition", "tables", tabela + ".tmdl")
    t = open(p, "rb").read().decode("utf-8")
    nl = "\r\n" if "\r\n" in t else "\n"
    assert "tipo_docto_descricao" not in t, "ja aplicado"
    add = ""
    for c in colunas:
        add += nl.join(col(*c)) + nl + nl
    for nome, expr, fmt, pasta in medidas:
        add += nl.join(["\tmeasure '%s' = %s" % (nome, expr), "\t\tformatString: %s" % fmt, "\t\tdisplayFolder: %s" % pasta, "\t\tlineageTag: %s" % g()]) + nl + nl
    marker = "\tpartition %s = m" % tabela
    assert t.count(marker) == 1
    open(p, "wb").write(t.replace(marker, add + marker).encode("utf-8"))


patch(R, [("tipo_docto_descricao", "string")], [])
patch(Q, [("tipo_docto_descricao", "string"), ("cod_historico", "int64", "0", True), ("cod_tipo_pagamento", "int64", "0", True)],
      [("A Pagar (visão do sistema)",
        'CALCULATE([A Pagar (títulos)], NOT (TituloPagar[tipo_docto] = "NF" && TituloPagar[cod_historico] = 106 && TituloPagar[cod_tipo_pagamento] = 13))',
        MON, "1. Contas a pagar"),
       ("A Pagar Restrito na Tela",
        'CALCULATE([A Pagar (títulos)], TituloPagar[tipo_docto] = "NF", TituloPagar[cod_historico] = 106, TituloPagar[cod_tipo_pagamento] = 13)',
        MON, "1. Contas a pagar")])
print("modelo ok")

# ============================================================ relatorio
src = open(r"C:\project\Apolo11\build_financeiro.py", encoding="utf-8").read()
i = src.index("# ============================================================ relatorio")
j = src.index("# ----- pagina 1")
exec(src[i:j])

# ---- slicer 'Tipo de documento' nas paginas existentes (redistribui os 4 slicers do cabecalho)
LAYOUT = {"sl_ano": (740, 80), "sl_mes": (830, 130), "sl_fil": (970, 170), "sl_tipo": (1150, 230), "sl_grp": (1390, 190)}
for pid in sorted(os.listdir(PAGES)):
    d = os.path.join(PAGES, pid, "visuals")
    if not os.path.isdir(d) or "sl_ano" not in os.listdir(d):
        continue
    fato = R if json.load(open(os.path.join(d, "sl_fil", "visual.json"), encoding="utf-8"))["visual"]["query"]["queryState"]["Values"]["projections"][0]["field"]["Column"]["Expression"]["SourceRef"]["Entity"] == R else Q
    # novo slicer + rotulo (clona o do filial)
    for nome in ("sl_fil", "lbl_sl_fil"):
        v = json.load(open(os.path.join(d, nome, "visual.json"), encoding="utf-8"))
        novo = nome.replace("fil", "tipo")
        v["name"] = novo
        if nome == "sl_fil":
            pr = v["visual"]["query"]["queryState"]["Values"]["projections"][0]
            pr["field"]["Column"]["Property"] = "tipo_docto_descricao"
            pr["queryRef"] = "%s.tipo_docto_descricao" % fato
            pr["nativeQueryRef"] = "tipo_docto_descricao"
            v["visual"]["syncGroup"]["groupName"] = "g_tipo"
        else:
            v["visual"]["objects"]["general"][0]["properties"]["paragraphs"][0]["textRuns"][0]["value"] = "Tipo de documento"
        os.makedirs(os.path.join(d, novo), exist_ok=True)
        json.dump(v, open(os.path.join(d, novo, "visual.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    for slic, (x, w) in LAYOUT.items():
        for nome in (slic, "lbl_" + slic):
            p = os.path.join(d, nome, "visual.json")
            v = json.load(open(p, encoding="utf-8"))
            v["position"]["x"], v["position"]["width"] = x, w
            json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("slicer de tipo adicionado nas paginas")

# ---- pagina de conferencia por tipo de documento
p7 = Page("a1b2c3d4e5f607182907", "Conferência por tipo de documento", "Receber e pagar por tipo de documento, para conferir com a tela do KMM")
p7.slicer("sl_ano", "Ano", 740, 80, "Calendario", "Ano", "g_ano")
p7.slicer("sl_mes", "Mês de emissão", 830, 130, "Calendario", "Ano-Mês", "g_mes")
p7.cards([(Q, "A Pagar (títulos)", NAVY, "A pagar no BI"), (Q, "A Pagar (visão do sistema)", TEAL, "A pagar (visão do sistema)"),
          (Q, "A Pagar Restrito na Tela", AMBER, "NF restritas na tela (hist. 106 / pagto 13)"), (Q, "A Pagar Bloqueado", RED, "A pagar bloqueado"),
          (R, "Faturado", NAVY, "A receber (faturado)"), (R, "Saldo em Aberto", AMBER, "Saldo a receber")])
p7.tabela("t_pagar", 20, 208, 770, 646,
          [pc(Q, "tipo_docto_descricao", "Tipo (a pagar)"), pm(Q, "Títulos a Pagar"), pm(Q, "A Pagar (títulos)"), pm(Q, "Pago"), pm(Q, "Saldo a Pagar"), pm(Q, "A Pagar Bloqueado")],
          "A pagar por tipo de documento", ordenar=sort_med(Q, "A Pagar (títulos)"))
p7.tabela("t_receber", 810, 208, 770, 646,
          [pc(R, "tipo_docto_descricao", "Tipo (a receber)"), pm(R, "Títulos"), pm(R, "Faturado"), pm(R, "Recebido"), pm(R, "Saldo em Aberto"), pm(R, "Faturado sem Documento")],
          "A receber por tipo de documento", ordenar=sort_med(R, "Faturado"))
p7.texto("rodape", 20, 862, 1560, 34, "Tipo de documento do título no KMM (docto_id). Os nomes vêm da tela do contas a pagar; códigos sem nome (CT, NS, AC, NC no a receber) ficam só com o código. "
         "'Visão do sistema' tira do a pagar as NF com histórico 106 e tipo de pagamento 13, que a tela do usuário não lista.")
pj = os.path.join(PAGES, "pages.json")
d = json.load(open(pj, encoding="utf-8"))
if p7.pid not in d["pageOrder"]:
    d["pageOrder"].append(p7.pid)
json.dump(d, open(pj, "w", encoding="utf-8"), indent=2)
print("pagina de conferencia ok:", d["pageOrder"])
