"""Adiciona ao Financeiro: tabela DreContabil (contabilidade KMM + referencia do DRE + status), medidas, relacao e a pagina 'DRE contabil'.
Rodar com o Power BI Desktop FECHADO:  python build_dre_contabil.py
Entradas (na mesma pasta): dre_referencia_20261019.json (mes, num_conta, origem, valor do DRE) e dre_contas_20261019.csv (descricoes do Athena).
Rollback: restaurar Financeiro.SemanticModel/Financeiro.Report do backup *_20261019_b feito antes de rodar.
"""
import csv, json, os, shutil, uuid

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = r"C:\project\PowerBIClaudio\14 - Controladoria"
SM = os.path.join(BASE, "Financeiro.SemanticModel")
RP = os.path.join(BASE, "Financeiro.Report")
NL = "\n"
for pasta in (SM, RP):  # backup antes de mexer
    bk = pasta + "_backup_20261019_b"
    if not os.path.exists(bk):
        shutil.copytree(pasta, bk)

def g(): return str(uuid.uuid4())
def w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "wb").write(text.encode("utf-8"))

MON = '"R$"\\ #,##0.00;-"R$"\\ #,##0.00'
def col(name, typ, fmt=None, hidden=False):
    L = ["\tcolumn %s" % name, "\t\tdataType: %s" % typ]
    if fmt: L.append("\t\tformatString: %s" % fmt)
    if hidden: L.append("\t\tisHidden")
    L += ["\t\tlineageTag: %s" % g(), "\t\tsummarizeBy: none", "\t\tsourceColumn: %s" % name]
    return NL.join(L) + NL + NL
def meas(name, expr, fmt, desc):
    return "\t/// %s%s\tmeasure '%s' = %s%s\t\tformatString: %s%s\t\tdisplayFolder: DRE contábil%s\t\tlineageTag: %s%s%s" % (
        desc, NL, name, expr, NL, fmt, NL, NL, g(), NL, NL)

# ---------------- dados de referencia (DRE) -> linhas M
ref = [r for r in json.load(open(os.path.join(AQUI, "dre_referencia_20261019.json"), encoding="utf-8")) if r[0] >= "2026-07"]
desc = {}
for r in csv.DictReader(open(os.path.join(AQUI, "dre_contas_20261019.csv"), encoding="utf-8")):
    desc.setdefault(int(r["num_conta"]), r["conta_descricao"])
SO_DRE = {3110100014: "Ingresso Fretes Nao Cooperados", 3110100017: "Ingressos Reemissoes - Anulacoes", 3110100023: "Receita com Bonificacao de Clientes",
          3110200006: "COFINS s/Faturamento Nao Cooperados", 3110200008: "PIS s/Faturamento Nao Cooperados", 3110200011: "PIS s/ Faturamento",
          3110200013: "COFINS s/ Faturamento", 3120500021: "Dispendios com Onus de Clientes", 3211000001: "Salarios", 3211000002: "Horas Extras",
          3211000006: "Comissoes e Gratificacoes", 3211000011: "Aviso Previo Indenizado", 3211000013: "Ferias", 3211000014: "13 Salario",
          3211000028: "Pro-Labore", 3211000029: "FGTS s/Folha de Pagamento", 3211000035: "PIS s/Folha de Pagamento", 3211000040: "Vale Refeicao",
          3211100055: "Processos Judiciais - Provisões", 3211900007: "PARCELAMENTO REFIS - 3870", 3211900008: "PARCELAMENTO REFIS - 3926",
          3211900010: "PARCELAMENTO REFIS - 4743", 3512000007: "Juros sobre Financiamento", 3512100006: "Juros recebidos sobre capital"}
def txt(s): return '"%s"' % str(s).replace('"', '""')
linhas = []
for mes, conta, origem, valor in ref:
    s = str(conta)
    cl = "%s.%s.%s.%s.%s" % (s[0], s[1], s[2], s[3:5], s[5:])
    d = desc.get(conta) or SO_DRE.get(conta) or "(conta só no DRE)"
    y, m = int(mes[:4]), int(mes[5:7])
    linhas.append("{%s, #date(%d, %d, 1), %s, %d, %s, %s, %s, %s, null, %s, \"DRE\"}" % (
        txt(mes), y, m, txt(cl), conta, txt(d), txt(cl[:3]), txt(cl[:8]), txt(origem), repr(float(valor))))

M = NL.join([
    "let",
    '    Fonte = Odbc.Query("dsn=Athena_Cootravale_Producao", "select mes_lancamento as mes, data_mes, classificacao, num_conta, conta_descricao, nivel_1, nivel_2, origem, centro_custo, valor, \'KMM\' as fonte from hml_gold.vw_fato_dre_contabil where mes_lancamento >= \'2026-07\'"),',
    '    Kmm = Table.TransformColumnTypes(Fonte, {{"data_mes", type date}, {"num_conta", Int64.Type}, {"valor", type number}}),',
    "    Ref = #table(type table [mes = text, data_mes = date, classificacao = text, num_conta = Int64.Type, conta_descricao = text, nivel_1 = text, nivel_2 = text, origem = text, centro_custo = text, valor = number, fonte = text], {",
    ("," + NL).join("        " + l for l in linhas),
    "    }),",
    '    Junta = Table.Combine({Kmm, Ref}),',
    '    ComChave = Table.AddColumn(Junta, "chave", each [mes] & "|" & Text.From([num_conta]) & "|" & [origem], type text),',
    '    Soma = Table.Group(ComChave, {"chave"}, {{"v_kmm", each List.Sum(Table.SelectRows(_, each [fonte] = "KMM")[valor]), type number}, {"v_dre", each List.Sum(Table.SelectRows(_, each [fonte] = "DRE")[valor]), type number}, {"mes_k", each List.Min([mes]), type text}, {"origem_k", each List.Min([origem]), type text}}),',
    '    Situacao = Table.AddColumn(Soma, "status", each let d = (if [v_kmm] = null then 0 else [v_kmm]) - (if [v_dre] = null then 0 else [v_dre]) in if [mes_k] < "2026-07" or [mes_k] > "2026-09" then "FORA DO PERÍODO DE REFERÊNCIA" else if Number.Abs(d) < 1 then "OK" else if [origem_k] = "(sem origem)" then "AJUSTE MANUAL DO DRE" else "DIVERGENTE", type text),',
    '    Final = Table.ExpandTableColumn(Table.NestedJoin(ComChave, {"chave"}, Table.SelectColumns(Situacao, {"chave", "status"}), {"chave"}, "s", JoinKind.LeftOuter), "s", {"status"})',
    "in",
    "    Final"])

V = "DreContabil[valor]"
medidas = "".join([
    meas("Valor Contábil (KMM)", 'CALCULATE(SUM(DreContabil[valor]), DreContabil[fonte] = "KMM")', MON,
         "Valor lançado na contabilidade do KMM (créditos menos débitos, deduplicado por contabilizacao_id)."),
    meas("Valor DRE (referência)", 'CALCULATE(SUM(DreContabil[valor]), DreContabil[fonte] = "DRE")', MON,
         "Valor do DRE gerencial (INFORMAÇÕES GERENCIAIS.pbip), extraído em 19/10/2026 para jul a set/26, por mês, conta e origem."),
    meas("Diferença KMM x DRE", "[Valor Contábil (KMM)] - [Valor DRE (referência)]", MON, "KMM menos DRE."),
    meas("Diferença (módulo)", "ABS([Diferença KMM x DRE])", MON, "Valor absoluto da diferença, para ordenar."),
    meas("Combinações divergentes", 'CALCULATE(DISTINCTCOUNT(DreContabil[chave]), DreContabil[status] = "DIVERGENTE")', "#,##0",
         "Quantidade de combinações mês x conta x origem do KMM cujo valor não bate com o DRE (fora os ajustes manuais do DRE)."),
    meas("Valor das divergências (módulo)",
         'VAR t = ADDCOLUMNS(CALCULATETABLE(SUMMARIZE(DreContabil, DreContabil[chave]), DreContabil[status] = "DIVERGENTE"), "d", [Diferença KMM x DRE]) RETURN SUMX(t, ABS([d]))', MON,
         "Soma, em módulo, das diferenças das combinações divergentes."),
    meas("Ajustes manuais do DRE (líquido)", '-CALCULATE([Diferença KMM x DRE], DreContabil[status] = "AJUSTE MANUAL DO DRE")', MON,
         "Valor que o DRE tem e o KMM não tem (linhas sem origem no KMM), líquido; positivo aumenta o resultado do DRE."),
    meas("Combinações que batem", 'CALCULATE(DISTINCTCOUNT(DreContabil[chave]), DreContabil[status] = "OK")', "#,##0",
         "Combinações mês x conta x origem que batem dentro de R$ 1 com o DRE."),
    meas("% combinações que batem",
         'DIVIDE(CALCULATE(DISTINCTCOUNT(DreContabil[chave]), DreContabil[status] = "OK"), CALCULATE(DISTINCTCOUNT(DreContabil[chave]), DreContabil[status] <> "FORA DO PERÍODO DE REFERÊNCIA"))',
         "0.0%", "Combinações mês x conta x origem que batem dentro de R$ 1 com o DRE, sobre todas as comparadas (jul a set/26)."),
])
colunas = "".join([col("mes", "string"), col("data_mes", "dateTime", "dd/MM/yyyy", True), col("classificacao", "string"), col("num_conta", "int64", "0"),
                   col("conta_descricao", "string"), col("nivel_1", "string"), col("nivel_2", "string"), col("origem", "string"), col("centro_custo", "string"),
                   col("valor", "double", None, True), col("fonte", "string"), col("chave", "string", None, True), col("status", "string")])
particao = "\tpartition DreContabil = m" + NL + "\t\tmode: import" + NL + "\t\tsource =" + NL + NL.join("\t\t\t\t" + l for l in M.split(NL)) + NL + NL + "\tannotation PBI_ResultType = Table" + NL
w(os.path.join(SM, "definition", "tables", "DreContabil.tmdl"),
  "/// DRE contábil: contas de resultado do KMM por mês, conta, origem e centro de custo, com o DRE gerencial como referência (jul a set/26) e o status da comparação. Fonte: hml_gold.vw_fato_dre_contabil." + NL +
  "table DreContabil" + NL + "\tlineageTag: %s" % g() + NL + NL + medidas + colunas + particao)

# modelo e relacao
mp = os.path.join(SM, "definition", "model.tmdl")
t = open(mp, encoding="utf-8").read()
if "ref table DreContabil" not in t:
    t = t.replace("ref table LigacaoContabil", "ref table LigacaoContabil" + NL + "ref table DreContabil")
    open(mp, "w", encoding="utf-8", newline="").write(t)
rp = os.path.join(SM, "definition", "relationships.tmdl")
r = open(rp, encoding="utf-8").read()
if "DreContabil_data_mes" not in r:
    r = r.rstrip() + NL + NL + "relationship DreContabil_data_mes_Calendario_Data" + NL + "\tfromColumn: DreContabil.data_mes" + NL + "\ttoColumn: Calendario.Data" + NL
    open(rp, "w", encoding="utf-8", newline="").write(r)

# ---------------- pagina
fonte = open(os.path.join(AQUI, "build_financeiro.py"), encoding="utf-8").read().split("\n")
ini = next(i for i, l in enumerate(fonte) if l.startswith("# ====") and l.rstrip().endswith("relatorio"))
fim = next(i for i, l in enumerate(fonte) if l.startswith("# ----- pagina 1"))
exec("\n".join(fonte[ini:fim]))

PID = "a1b2c3d4e5f607182912"
T = "DreContabil"
pg = Page(PID, "DRE contábil", "Contas de resultado do KMM x DRE gerencial (jul a set/26): o que não bate aparece primeiro")
pg.slicer("sl_ano", "Ano", 740, 90, "Calendario", "Ano", "g_ano")
pg.slicer("sl_mes", "Mês", 840, 140, "Calendario", "Ano-Mês", "g_mes")
pg.slicer("sl_ori", "Origem do lançamento", 990, 300, T, "origem", "g_dre_ori")
pg.slicer("sl_sit", "Situação", 1300, 280, T, "status", "g_dre_sit")
pg.cards([
    (T, "Combinações divergentes", RED, "Combinações que NÃO batem com o DRE"),
    (T, "Valor das divergências (módulo)", RED, "Valor das divergências"),
    (T, "Ajustes manuais do DRE (líquido)", AMBER, "Ajustes manuais do DRE (fora do KMM)"),
    (T, "Combinações que batem", NAVY, "Combinações que batem com o DRE"),
    (T, "% combinações que batem", TEAL, "% das combinações que batem"),
])
vm = lambda n, dn: pm(T, n, dn)
pg.tabela("t_div", 20, 210, 1560, 235, [
    pc(T, "mes", "Mês"), pc(T, "num_conta", "Conta"), pc(T, "conta_descricao", "Descrição"), pc(T, "origem", "Origem"),
    vm("Valor Contábil (KMM)", "KMM"), vm("Valor DRE (referência)", "DRE"), vm("Diferença KMM x DRE", "Diferença"),
], "O que não bate com o DRE (origens do KMM) - olhar aqui primeiro",
    ordenar=sort_med(T, "Diferença (módulo)", "Descending"), filtros=[filtro_in(T, "status", ["DIVERGENTE"], "f_div")])
pg.tabela("t_dre", 20, 460, 1560, 390, [
    pc(T, "mes", "Mês"), pc(T, "classificacao", "Classificação"), pc(T, "conta_descricao", "Descrição"), pc(T, "origem", "Origem"), pc(T, "status", "Situação"),
    vm("Valor Contábil (KMM)", "KMM"), vm("Valor DRE (referência)", "DRE"), vm("Diferença KMM x DRE", "Diferença"),
], "DRE contábil por mês, conta e origem (todas as situações)",
    ordenar={"field": cref(T, "classificacao"), "direction": "Ascending"})
pg.texto("rodape", 20, 856, 1560, 40,
         "KMM = contabilidade do Athena (contas de resultado, deduplicada por contabilizacao_id). DRE = valores do DRE gerencial extraídos em 19/10/2026 (jul a set/26); não atualizam sozinhos. "
         "Ajuste manual do DRE = linhas que o DRE tem e o KMM não tem (sem origem). Maio e junho ficam fora: a carga do Athena só é completa a partir de julho. Diferença dentro de R$ 1 conta como OK.", "8pt", GRAY)

pp = os.path.join(RP, "definition", "pages", "pages.json")
meta = json.load(open(pp, encoding="utf-8"))
if PID not in meta["pageOrder"]:
    i = meta["pageOrder"].index("a1b2c3d4e5f607182911")
    meta["pageOrder"].insert(i + 1, PID)
json.dump(meta, open(pp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("ok: tabela DreContabil, relacao, %d linhas de referencia, pagina %s" % (len(linhas), PID))
