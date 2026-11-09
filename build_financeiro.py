import json, os, shutil, uuid

BASE = r"C:\PowerBIClaudio\14 - Controladoria"
SRC_SM = os.path.join(BASE, "AnaliseDocumentos.SemanticModel")
SRC_RP = os.path.join(BASE, "AnaliseDocumentos.Report")
NAME = "Financeiro"
SM = os.path.join(BASE, NAME + ".SemanticModel")
RP = os.path.join(BASE, NAME + ".Report")
assert not os.path.exists(SM) and not os.path.exists(RP), "ja existe"
NL = "\n"


def g():
    return str(uuid.uuid4())


def w(path, text, bom=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "wb").write(text.encode("utf-8"))


# ============================================================ projeto
w(os.path.join(BASE, NAME + ".pbip"), json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
    "version": "1.0", "artifacts": [{"report": {"path": NAME + ".Report"}}], "settings": {"enableAutoRecovery": True}}, indent=2))
w(os.path.join(SM, "definition.pbism"), open(os.path.join(SRC_SM, "definition.pbism"), "rb").read().decode("utf-8"))
w(os.path.join(SM, ".platform"), json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
    "metadata": {"type": "SemanticModel", "displayName": NAME}, "config": {"version": "2.0", "logicalId": g()}}, indent=2))
w(os.path.join(RP, ".platform"), json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
    "metadata": {"type": "Report", "displayName": NAME}, "config": {"version": "2.0", "logicalId": g()}}, indent=2))
w(os.path.join(RP, "definition.pbir"), json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
    "version": "4.0", "datasetReference": {"byPath": {"path": "../" + NAME + ".SemanticModel"}}}, indent=2))
shutil.copytree(os.path.join(SRC_RP, "StaticResources"), os.path.join(RP, "StaticResources"))
os.makedirs(os.path.join(RP, "definition"), exist_ok=True)
shutil.copy(os.path.join(SRC_RP, "definition", "version.json"), os.path.join(RP, "definition", "version.json"))
rep = json.load(open(os.path.join(SRC_RP, "definition", "report.json"), encoding="utf-8"))
rep.pop("filterConfig", None)
json.dump(rep, open(os.path.join(RP, "definition", "report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ============================================================ modelo
w(os.path.join(SM, "definition", "database.tmdl"), "database" + NL + "\tcompatibilityLevel: 1606" + NL)
shutil.copytree(os.path.join(SRC_SM, "definition", "cultures"), os.path.join(SM, "definition", "cultures"))
w(os.path.join(SM, "definition", "model.tmdl"), NL.join([
    "model Model", "\tculture: pt-BR", "\tdefaultPowerBIDataSourceVersion: powerBI_V3", "\tsourceQueryCulture: pt-BR",
    "\tvalueFilterBehavior: independent", "\tdataAccessOptions", "\t\tlegacyRedirects", "\t\treturnErrorValuesAsNull", "",
    "annotation __PBI_TimeIntelligenceEnabled = 1", "", 'annotation PBI_QueryOrder = ["TituloReceber","TituloPagar"]', "",
    "ref table TituloReceber", "ref table TituloPagar", "ref table Calendario", "", "ref cultureInfo pt-BR", ""]))

MON = '"R$"\\ #,##0.00;-"R$"\\ #,##0.00'
MIL = '[>=1000000]"R$ "#,0.00,," Mi";[>=1000]"R$ "#,0.0," mil";"R$ "#,0.00'


def col(name, typ, fmt=None, hidden=False, sort=None):
    L = ["\tcolumn %s" % (name if name.isidentifier() else "'%s'" % name), "\t\tdataType: %s" % typ]
    if fmt:
        L.append("\t\tformatString: %s" % fmt)
    if hidden:
        L.append("\t\tisHidden")
    L += ["\t\tlineageTag: %s" % g(), "\t\tsummarizeBy: none", "\t\tsourceColumn: %s" % name]
    if sort:
        L.append("\t\tsortByColumn: %s" % sort)
    return NL.join(L) + NL + NL


def meas(name, expr, fmt, folder, desc=None):
    d = ("\t/// %s" % desc + NL) if desc else ""
    return d + NL.join(["\tmeasure '%s' = %s" % (name, expr), "\t\tformatString: %s" % fmt, "\t\tdisplayFolder: %s" % folder,
                        "\t\tlineageTag: %s" % g()]) + NL + NL


def tabela(nome, view, colunas, medidas, datas):
    tipos = ", ".join('{"%s", type date}' % c for c in datas)
    m = NL.join(["\tpartition %s = m" % nome, "\t\tmode: import", "\t\tsource =", "\t\t\t\tlet",
                 '\t\t\t\t    Fonte = Odbc.Query("dsn=Athena_Cootravale_Producao", "select * from hml_gold.%s"),' % view,
                 "\t\t\t\t    Tipos = Table.TransformColumnTypes(Fonte, {%s})" % tipos, "\t\t\t\tin", "\t\t\t\t    Tipos", "",
                 "\tannotation PBI_ResultType = Table", ""])
    w(os.path.join(SM, "definition", "tables", nome + ".tmdl"),
      "table %s%s\tlineageTag: %s%s%s" % (nome, NL, g(), NL + NL, "".join(colunas) + "".join(medidas) + m))


# --------- receber
R = "TituloReceber"
colsR = [col("contas_receber_id", "int64", "0", True), col("num_docto", "string"), col("parc_docto", "string"), col("tipo_docto", "string"),
         col("data_emissao", "dateTime", "dd/mm/yyyy"), col("data_vencto", "dateTime", "dd/mm/yyyy"), col("data_previsao", "dateTime", "dd/mm/yyyy", True),
         col("data_ultima_amortizacao", "dateTime", "dd/mm/yyyy"), col("cod_pessoa", "int64", "0", True), col("cnpj_cpf", "string"),
         col("cliente", "string"), col("grupo_cliente", "string"), col("cliente_grupo", "string"), col("filial", "string"), col("unidade_negocio", "string"),
         col("usuario_titulo", "string"), col("valor_titulo", "double", "#,0.00"), col("valor_pago", "double", "#,0.00"), col("valor_juro", "double", "#,0.00"),
         col("valor_desconto", "double", "#,0.00"), col("valor_desconto_devolucao", "double", "#,0.00"), col("saldo_aberto", "double", "#,0.00"),
         col("status_pagamento", "string"), col("prazo_dias", "int64", "0"), col("dias_ate_recebimento", "int64", "0"), col("vencido", "string"),
         col("dias_atraso", "int64", "0"), col("faixa_aging", "string"), col("qtd_documentos", "int64", "0"), col("tem_documento", "string")]
F = "1. Receita e faturamento"
medR = [
    meas("Faturado", "SUM(TituloReceber[valor_titulo])", MIL, F, "Valor dos títulos a receber emitidos (uma linha por título)."),
    meas("Recebido", "SUM(TituloReceber[valor_pago])", MIL, F),
    meas("Juros", "SUM(TituloReceber[valor_juro])", MON, F),
    meas("Descontos", "SUM(TituloReceber[valor_desconto])", MON, F),
    meas("Devoluções", "SUM(TituloReceber[valor_desconto_devolucao])", MON, F, "Parte do desconto marcada como devolução no KMM."),
    meas("Títulos", "COUNTROWS(TituloReceber)", "#,0", F),
    meas("Taxa de Recebimento", "DIVIDE([Recebido], [Faturado])", "0.0%", F),
    meas("Faturado Liquidado por Desconto", 'CALCULATE([Faturado], TituloReceber[status_pagamento] = "LIQUIDADO POR DESCONTO")', MON, F,
         "Títulos sem pagamento e com saldo zero porque o desconto cobre 100%."),
    meas("Faturado sem Documento", 'CALCULATE([Faturado], TituloReceber[tem_documento] = "NAO")', MON, F, "Títulos sem conhecimento/nota ligados na conciliação."),
    meas("% sem Documento", "DIVIDE([Faturado sem Documento], [Faturado])", "0.0%", F),
]
A = "2. Saldo e aging"
medR += [
    meas("Saldo em Aberto", "SUM(TituloReceber[saldo_aberto])", MIL, A, "valor + juros - desconto - recebido, nunca negativo."),
    meas("Saldo Vencido", 'CALCULATE([Saldo em Aberto], TituloReceber[vencido] = "SIM")', MIL, A),
    meas("Saldo a Vencer", 'CALCULATE([Saldo em Aberto], TituloReceber[faixa_aging] = "A VENCER")', MIL, A),
    meas("Vencido > 90 dias", 'CALCULATE([Saldo em Aberto], TituloReceber[faixa_aging] = "VENCIDO > 90")', MIL, A),
    meas("% Vencido", "DIVIDE([Saldo Vencido], [Saldo em Aberto])", "0.0%", A),
    meas("Títulos Vencidos", 'CALCULATE([Títulos], TituloReceber[vencido] = "SIM")', "#,0", A),
    meas("Atraso Médio (dias)", 'DIVIDE(SUMX(FILTER(TituloReceber, TituloReceber[vencido] = "SIM"), TituloReceber[saldo_aberto] * TituloReceber[dias_atraso]), [Saldo Vencido])', "0.0", A,
         "Média dos dias de atraso ponderada pelo saldo vencido."),
]
P = "3. Prazos"
medR += [
    meas("Prazo Médio de Recebimento (dias)",
         "VAR t = FILTER(TituloReceber, NOT ISBLANK(TituloReceber[dias_ate_recebimento])) RETURN DIVIDE(SUMX(t, TituloReceber[valor_titulo] * TituloReceber[dias_ate_recebimento]), SUMX(t, TituloReceber[valor_titulo]))",
         "0.0", P, "Dias entre emissão e a última amortização, só dos títulos quitados, ponderado pelo valor."),
    meas("Prazo Médio Concedido (dias)", "DIVIDE(SUMX(TituloReceber, TituloReceber[valor_titulo] * TituloReceber[prazo_dias]), [Faturado])", "0.0", P, "Dias entre emissão e vencimento, ponderado pelo valor."),
]
tabela(R, "vw_fato_titulo_receber", colsR, medR, ["data_emissao", "data_vencto", "data_previsao", "data_ultima_amortizacao"])

# --------- pagar
Q = "TituloPagar"
colsP = [col("contas_pagar_id", "int64", "0", True), col("num_docto", "string"), col("parc_docto", "string"), col("tipo_docto", "string"),
         col("data_emissao", "dateTime", "dd/mm/yyyy"), col("data_vencto", "dateTime", "dd/mm/yyyy"), col("data_previsao", "dateTime", "dd/mm/yyyy", True),
         col("data_ultima_amortizacao", "dateTime", "dd/mm/yyyy"), col("cod_pessoa", "int64", "0", True), col("cnpj_cpf", "string"),
         col("fornecedor", "string"), col("filial", "string"), col("unidade_negocio", "string"), col("usuario_titulo", "string"),
         col("aprovado", "string"), col("tem_contrato_transporte", "string"), col("valor_titulo", "double", "#,0.00"), col("valor_pago", "double", "#,0.00"),
         col("valor_juro", "double", "#,0.00"), col("valor_desconto", "double", "#,0.00"), col("valor_desconto_devolucao", "double", "#,0.00"),
         col("saldo_aberto", "double", "#,0.00"), col("status_pagamento", "string"), col("prazo_dias", "int64", "0"), col("dias_ate_pagamento", "int64", "0"),
         col("vencido", "string"), col("dias_atraso", "int64", "0"), col("faixa_aging", "string")]
F = "1. Contas a pagar"
medP = [
    meas("A Pagar (títulos)", "SUM(TituloPagar[valor_titulo])", MIL, F, "Valor dos títulos a pagar emitidos (uma linha por título)."),
    meas("Pago", "SUM(TituloPagar[valor_pago])", MIL, F),
    meas("Juros (pagar)", "SUM(TituloPagar[valor_juro])", MON, F),
    meas("Descontos (pagar)", "SUM(TituloPagar[valor_desconto])", MON, F),
    meas("Títulos a Pagar", "COUNTROWS(TituloPagar)", "#,0", F),
    meas("Baixado por Desconto (pagar)", 'CALCULATE([A Pagar (títulos)], TituloPagar[status_pagamento] = "LIQUIDADO POR DESCONTO")', MON, F,
         "Títulos sem amortização e saldo zero por desconto (em contrato de frete costuma ser compensação)."),
    meas("Pagar Sem Aprovação", 'CALCULATE([A Pagar (títulos)], TituloPagar[aprovado] = "NAO")', MON, F),
]
A = "2. Saldo e aging"
medP += [
    meas("Saldo a Pagar", "SUM(TituloPagar[saldo_aberto])", MIL, A),
    meas("Saldo Vencido a Pagar", 'CALCULATE([Saldo a Pagar], TituloPagar[vencido] = "SIM")', MIL, A),
    meas("Saldo a Pagar a Vencer", 'CALCULATE([Saldo a Pagar], TituloPagar[faixa_aging] = "A VENCER")', MIL, A),
    meas("% Vencido a Pagar", "DIVIDE([Saldo Vencido a Pagar], [Saldo a Pagar])", "0.0%", A),
    meas("Atraso Médio a Pagar (dias)", 'DIVIDE(SUMX(FILTER(TituloPagar, TituloPagar[vencido] = "SIM"), TituloPagar[saldo_aberto] * TituloPagar[dias_atraso]), [Saldo Vencido a Pagar])', "0.0", A),
    meas("Prazo Médio de Pagamento (dias)",
         "VAR t = FILTER(TituloPagar, NOT ISBLANK(TituloPagar[dias_ate_pagamento])) RETURN DIVIDE(SUMX(t, TituloPagar[valor_titulo] * TituloPagar[dias_ate_pagamento]), SUMX(t, TituloPagar[valor_titulo]))",
         "0.0", "3. Prazos", "Dias entre emissão e a última amortização, só dos títulos quitados, ponderado pelo valor."),
]
tabela(Q, "vw_fato_titulo_pagar", colsP, medP, ["data_emissao", "data_vencto", "data_previsao", "data_ultima_amortizacao"])

# --------- calendario
cal = NL.join(["table Calendario", "\tlineageTag: %s" % g(), "",
               "\tcolumn Data", "\t\tdataType: dateTime", "\t\tformatString: dd/mm/yyyy", "\t\tlineageTag: %s" % g(), "\t\tsummarizeBy: none", "\t\tsourceColumn: [Data]", "",
               "\tcolumn Ano", "\t\tdataType: int64", "\t\tformatString: 0", "\t\tlineageTag: %s" % g(), "\t\tsummarizeBy: none", "\t\tsourceColumn: [Ano]", "",
               "\tcolumn 'Ano-Mês'", "\t\tdataType: string", "\t\tlineageTag: %s" % g(), "\t\tsummarizeBy: none", "\t\tsourceColumn: [Ano-Mês]", "",
               "\tpartition Calendario = calculated", "\t\tmode: import",
               '\t\tsource = SELECTCOLUMNS(CALENDAR(DATE(2025, 1, 1), DATE(2026, 12, 31)), "Data", [Date], "Ano", YEAR([Date]), "Ano-Mês", FORMAT([Date], "yyyy-mm"))', ""])
w(os.path.join(SM, "definition", "tables", "Calendario.tmdl"), cal)
rel = NL.join([
    "relationship %s" % g(), "\tfromColumn: TituloReceber.data_emissao", "\ttoColumn: Calendario.Data", "",
    "relationship %s" % g(), "\tisActive: false", "\tfromColumn: TituloReceber.data_vencto", "\ttoColumn: Calendario.Data", "",
    "relationship %s" % g(), "\tfromColumn: TituloPagar.data_emissao", "\ttoColumn: Calendario.Data", "",
    "relationship %s" % g(), "\tisActive: false", "\tfromColumn: TituloPagar.data_vencto", "\ttoColumn: Calendario.Data", ""])
w(os.path.join(SM, "definition", "relationships.tmdl"), rel)
print("modelo ok")

# ============================================================ relatorio
NAVY, TEAL, RED, AMBER, GRAY, LINE = "#0B2545", "#13A89E", "#D64545", "#E08A00", "#5B6B7F", "#E1E6EE"
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.12.0/schema.json"
PAGES = os.path.join(RP, "definition", "pages")


def lit(v): return {"expr": {"Literal": {"Value": v}}}
def colr(c): return {"solid": {"color": lit("'%s'" % c)}}
def mref(t, n): return {"Measure": {"Expression": {"SourceRef": {"Entity": t}}, "Property": n}}
def cref(t, n): return {"Column": {"Expression": {"SourceRef": {"Entity": t}}, "Property": n}}
def pm(t, n, dn=None):
    d = {"field": mref(t, n), "queryRef": "%s.%s" % (t, n), "nativeQueryRef": n}
    if dn: d["displayName"] = dn
    return d
def pc(t, n, dn=None, active=False):
    d = {"field": cref(t, n), "queryRef": "%s.%s" % (t, n), "nativeQueryRef": n}
    if dn: d["displayName"] = dn
    if active: d["active"] = True
    return d


class Page:
    def __init__(self, pid, titulo, sub):
        self.pid, self.dir, self.z = pid, os.path.join(PAGES, pid), 100
        self.titulo = titulo
        os.makedirs(os.path.join(self.dir, "visuals"), exist_ok=True)
        json.dump({"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
                   "name": pid, "displayName": titulo, "displayOption": "FitToPage", "height": 900, "width": 1600,
                   "objects": {"background": [{"properties": {"color": colr("#F4F6F9"), "transparency": lit("0D")}}]}},
                  open(os.path.join(self.dir, "page.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        bg = {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": [{"textRuns": [{"value": " ", "textStyle": {"fontFamily": "Segoe UI", "fontSize": "8pt", "color": NAVY}}]}]}}]}}
        self.put("hdr_bg", 0, 0, 1600, 74, bg, {"background": [{"properties": {"show": lit("true"), "color": colr(NAVY), "transparency": lit("0D")}}]})
        self.texto("hdr_titulo", 24, 6, 700, 46, titulo, "22pt", "#FFFFFF", True, "Segoe UI Semibold")
        self.texto("hdr_sub", 24, 46, 700, 28, sub, "11pt", "#B8C7DC")

    def put(self, name, x, y, wd, h, visual, container=None, filters=None):
        self.z += 100
        d = {"$schema": SCHEMA, "name": name, "position": {"x": x, "y": y, "z": self.z, "height": h, "width": wd, "tabOrder": self.z}, "visual": visual}
        if container: d["visual"]["visualContainerObjects"] = container
        d["visual"]["drillFilterOtherVisuals"] = True
        if filters: d["filterConfig"] = {"filters": filters}
        os.makedirs(os.path.join(self.dir, "visuals", name), exist_ok=True)
        json.dump(d, open(os.path.join(self.dir, "visuals", name, "visual.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    def texto(self, name, x, y, wd, h, t, size="9pt", color=GRAY, bold=False, family="Segoe UI", container=None):
        run = {"value": t, "textStyle": {"fontFamily": family, "fontSize": size, "color": color}}
        if bold: run["textStyle"]["fontWeight"] = "bold"
        self.put(name, x, y, wd, h, {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": [{"textRuns": [run], "horizontalTextAlignment": "Left"}]}}]}}, container)

    def box(self, title=None):
        c = {"background": [{"properties": {"show": lit("true"), "color": colr("#FFFFFF"), "transparency": lit("0D")}}],
             "border": [{"properties": {"show": lit("true"), "color": colr(LINE), "radius": lit("10D")}}]}
        if title:
            c["title"] = [{"properties": {"show": lit("true"), "text": lit("'%s'" % title), "fontColor": colr(NAVY), "fontSize": lit("13D"), "bold": lit("true")}}]
            c["subTitle"] = [{"properties": {"show": lit("false")}}]
        return c

    def slicer(self, name, label, x, wd, tabela, campo, grupo):
        self.texto("lbl_" + name, x, 4, wd, 22, label, "9pt", "#B8C7DC")
        v = {"visualType": "slicer", "query": {"queryState": {"Values": {"projections": [pc(tabela, campo, active=True)]}}},
             "objects": {"data": [{"properties": {"mode": lit("'Dropdown'")}}], "header": [{"properties": {"show": lit("false")}}],
                         "items": [{"properties": {"fontColor": colr(NAVY), "background": colr("#FFFFFF")}}],
                         "selection": [{"properties": {"selectAllCheckboxEnabled": lit("true")}}]}}
        c = self.box()
        c["syncGroup"] = {"groupName": grupo, "fieldChanges": True, "filterChanges": True}
        self.put(name, x, 26, wd, 38, v, {k: c[k] for k in ("background", "border")})
        # syncGroup fica no visual
        p = os.path.join(self.dir, "visuals", name, "visual.json")
        d = json.load(open(p, encoding="utf-8")); d["visual"]["syncGroup"] = c["syncGroup"]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    def card(self, name, tabela, medida, x, wd, cor, dn=None, y=92, h=100):
        v = {"visualType": "card", "query": {"queryState": {"Values": {"projections": [pm(tabela, medida, dn)]}}},
             "objects": {"labels": [{"properties": {"fontSize": lit("24D"), "color": colr(cor), "fontFamily": lit("'Segoe UI Semibold'")}}],
                         "categoryLabels": [{"properties": {"show": lit("true"), "fontSize": lit("11D"), "color": colr(GRAY)}}]}}
        self.put(name, x, y, wd, h, v, self.box())

    def cards(self, lista):
        n = len(lista)
        wd = round((1560 - 20 * (n - 1)) / n, 1)
        for i, (t, m, c, dn) in enumerate(lista):
            self.card("a%d" % i, t, m, round(20 + i * (wd + 20), 1), wd, c, dn)

    def chart(self, name, tipo, x, y, wd, h, cat, valores, titulo, cor=NAVY, legenda=False, ordenar=None, filtros=None):
        q = {"queryState": {"Category": {"projections": [cat]}, "Y": {"projections": valores}}}
        if ordenar: q["sortDefinition"] = {"sort": [ordenar], "isDefaultSort": False}
        obj = {"labels": [{"properties": {"show": lit("true"), "fontSize": lit("9D")}}], "legend": [{"properties": {"show": lit("true" if legenda else "false")}}]}
        if tipo in ("barChart", "clusteredColumnChart"):
            obj["valueAxis"] = [{"properties": {"show": lit("false")}}]
        if not legenda and tipo != "donutChart":
            obj["dataPoint"] = [{"properties": {"fill": colr(cor)}}]
        self.put(name, x, y, wd, h, {"visualType": tipo, "query": q, "objects": obj}, self.box(titulo), filtros)

    def tabela(self, name, x, y, wd, h, colunas, titulo, ordenar=None, filtros=None):
        hdr = {"columnHeaders": [{"properties": {"fontColor": colr("#FFFFFF"), "backColor": colr(NAVY), "fontSize": lit("11D"), "bold": lit("true")}}],
               "values": [{"properties": {"fontSize": lit("11D")}}], "grid": [{"properties": {"gridVertical": lit("false"), "rowPadding": lit("3D")}}]}
        q = {"queryState": {"Values": {"projections": colunas}}}
        if ordenar: q["sortDefinition"] = {"sort": [ordenar], "isDefaultSort": False}
        self.put(name, x, y, wd, h, {"visualType": "tableEx", "query": q, "objects": hdr}, self.box(titulo), filtros)


def filtro_not_in(tabela, campo, valores, nome):
    return {"name": nome, "field": cref(tabela, campo), "type": "Categorical",
            "filter": {"Version": 2, "From": [{"Name": "d", "Entity": tabela, "Type": 0}],
                       "Where": [{"Condition": {"Not": {"Expression": {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": campo}}],
                                                                              "Values": [[{"Literal": {"Value": "'%s'" % v}}] for v in valores]}}}}}]},
            "howCreated": "User"}


def filtro_in(tabela, campo, valores, nome):
    return {"name": nome, "field": cref(tabela, campo), "type": "Categorical",
            "filter": {"Version": 2, "From": [{"Name": "d", "Entity": tabela, "Type": 0}],
                       "Where": [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": campo}}],
                                                       "Values": [[{"Literal": {"Value": "'%s'" % v}}] for v in valores]}}}]},
            "howCreated": "User"}


def slicers(pg, tfato, grupo_col, grupo_label, g):
    pg.slicer("sl_ano", "Ano", 740, 90, "Calendario", "Ano", "g_ano")
    pg.slicer("sl_mes", "Mês de emissão", 840, 140, "Calendario", "Ano-Mês", "g_mes")
    pg.slicer("sl_fil", "Filial", 990, 190, tfato, "filial", g + "_fil")
    pg.slicer("sl_grp", grupo_label, 1190, 390, tfato, grupo_col, g + "_grp")


def sort_med(t, m, d="Descending"): return {"field": mref(t, m), "direction": d}


# ----- pagina 1: visao do mes (receber)
p1 = Page("a1b2c3d4e5f607182901", "Visão do mês (a receber)", "Faturado, recebido e saldo dos títulos a receber do KMM, uma linha por título")
slicers(p1, R, "cliente_grupo", "Cliente (grupo)", "g_rec")
p1.cards([(R, "Faturado", NAVY, "Faturado no período"), (R, "Recebido", TEAL, "Recebido"), (R, "Saldo em Aberto", AMBER, "Saldo em aberto"),
          (R, "Saldo Vencido", RED, "Saldo vencido"), (R, "% Vencido", RED, "% vencido do saldo"), (R, "Prazo Médio de Recebimento (dias)", GRAY, "Prazo médio de recebimento (dias)")])
p1.chart("c_mes", "clusteredColumnChart", 20, 208, 760, 300, pc("Calendario", "Ano-Mês", active=True), [pm(R, "Faturado"), pm(R, "Recebido")],
         "Faturado x recebido, por mês de emissão do título", legenda=True)
p1.chart("c_status", "donutChart", 800, 208, 360, 300, pc(R, "status_pagamento", active=True), [pm(R, "Faturado")], "Faturado por situação do pagamento", legenda=True)
p1.chart("c_filial", "barChart", 1180, 208, 400, 300, pc(R, "filial", active=True), [pm(R, "Faturado")], "Faturado por filial", ordenar=sort_med(R, "Faturado"))
p1.tabela("t_clientes", 20, 524, 1560, 330,
          [pc(R, "cliente_grupo", "Cliente (grupo)"), pm(R, "Títulos"), pm(R, "Faturado"), pm(R, "Recebido"), pm(R, "Saldo em Aberto"), pm(R, "Saldo Vencido"),
           pm(R, "Atraso Médio (dias)"), pm(R, "% sem Documento")], "Clientes: faturado, recebido e saldo (ordenado pelo saldo em aberto)", ordenar=sort_med(R, "Saldo em Aberto"))
p1.texto("rodape", 20, 862, 1560, 34, "Fonte: hml_gold.vw_fato_titulo_receber (KMM contas a receber, uma linha por título, cancelados e estornados fora). "
         "Saldo = valor + juros − desconto − recebido. Aging calculado na data da última atualização dos dados.")

# ----- pagina 2: aging e vencidos (receber)
p2 = Page("a1b2c3d4e5f607182902", "Aging e vencidos (a receber)", "Quanto está a vencer e quanto está vencido, por faixa de atraso, filial e cliente")
slicers(p2, R, "cliente_grupo", "Cliente (grupo)", "g_age")
p2.cards([(R, "Saldo em Aberto", NAVY, "Saldo em aberto"), (R, "Saldo a Vencer", TEAL, "A vencer"), (R, "Saldo Vencido", RED, "Vencido"),
          (R, "Vencido > 90 dias", RED, "Vencido há mais de 90 dias"), (R, "Atraso Médio (dias)", AMBER, "Atraso médio (dias)"), (R, "Títulos Vencidos", GRAY, "Títulos vencidos")])
sem_saldo = [filtro_not_in(R, "faixa_aging", ["SEM SALDO"], "f_ss1")]
p2.chart("c_aging", "barChart", 20, 208, 760, 300, pc(R, "faixa_aging", active=True), [pm(R, "Saldo em Aberto")], "Saldo por faixa de aging", cor=AMBER, filtros=sem_saldo)
p2.chart("c_venc_fil", "barChart", 800, 208, 780, 300, pc(R, "filial", active=True), [pm(R, "Saldo Vencido")], "Saldo vencido por filial", cor=RED, ordenar=sort_med(R, "Saldo Vencido"))
p2.tabela("t_venc", 20, 524, 1560, 330,
          [pc(R, "cliente_grupo", "Cliente (grupo)"), pm(R, "Títulos Vencidos"), pm(R, "Saldo Vencido"), pm(R, "Vencido > 90 dias"), pm(R, "Atraso Médio (dias)"),
           pm(R, "Saldo a Vencer")], "Clientes com saldo vencido (ordenado pelo vencido)", ordenar=sort_med(R, "Saldo Vencido"),
          filtros=[filtro_in(R, "vencido", ["SIM"], "f_v1")])
p2.texto("rodape", 20, 862, 1560, 34, "Vencido = saldo > 0 e vencimento anterior à data da atualização. Faixas: a vencer, 1-30, 31-60, 61-90 e > 90 dias de atraso. Títulos sem saldo não entram no aging.")

# ----- pagina 3: contas a pagar
p3 = Page("a1b2c3d4e5f607182903", "Contas a pagar", "Títulos a pagar do KMM: valor, pago, saldo e vencidos, por fornecedor e filial")
slicers(p3, Q, "fornecedor", "Fornecedor", "g_pag")
p3.cards([(Q, "A Pagar (títulos)", NAVY, "A pagar (títulos emitidos)"), (Q, "Pago", TEAL, "Pago"), (Q, "Saldo a Pagar", AMBER, "Saldo a pagar"),
          (Q, "Saldo Vencido a Pagar", RED, "Saldo vencido"), (Q, "% Vencido a Pagar", RED, "% vencido do saldo"), (Q, "Prazo Médio de Pagamento (dias)", GRAY, "Prazo médio de pagamento (dias)")])
p3.chart("c_mes", "clusteredColumnChart", 20, 208, 760, 300, pc("Calendario", "Ano-Mês", active=True), [pm(Q, "A Pagar (títulos)"), pm(Q, "Pago")],
         "A pagar x pago, por mês de emissão do título", legenda=True)
p3.chart("c_status", "donutChart", 800, 208, 360, 300, pc(Q, "status_pagamento", active=True), [pm(Q, "A Pagar (títulos)")], "Por situação do pagamento", legenda=True)
p3.chart("c_aging", "barChart", 1180, 208, 400, 300, pc(Q, "faixa_aging", active=True), [pm(Q, "Saldo a Pagar")], "Saldo a pagar por faixa de aging", cor=AMBER,
         filtros=[filtro_not_in(Q, "faixa_aging", ["SEM SALDO"], "f_ss3")])
p3.tabela("t_forn", 20, 524, 1560, 330,
          [pc(Q, "fornecedor", "Fornecedor"), pm(Q, "Títulos a Pagar"), pm(Q, "A Pagar (títulos)"), pm(Q, "Pago"), pm(Q, "Saldo a Pagar"), pm(Q, "Saldo Vencido a Pagar"),
           pm(Q, "Atraso Médio a Pagar (dias)"), pm(Q, "Baixado por Desconto (pagar)")], "Fornecedores: a pagar, pago e saldo (ordenado pelo saldo)", ordenar=sort_med(Q, "Saldo a Pagar"))
p3.texto("rodape", 20, 862, 1560, 34, "Fonte: hml_gold.vw_fato_titulo_pagar (KMM contas a pagar, uma linha por título, estornados fora). 'Baixado por desconto': título sem amortização e saldo zero "
         "(em contratos de frete costuma ser compensação, confirmar com o financeiro).")

ids = [p1.pid, p2.pid, p3.pid]
json.dump({"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json", "pageOrder": ids, "activePageName": ids[0]},
          open(os.path.join(PAGES, "pages.json"), "w", encoding="utf-8"), indent=2)
print("relatorio ok")
