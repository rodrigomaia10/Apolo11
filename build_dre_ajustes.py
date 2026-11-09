"""Adiciona ao Financeiro: tabela DreAjustesManuais (detalhe dos lancamentos manuais do DRE, sem origem no KMM), medidas, relacao e a pagina 'Ajustes manuais do DRE'.
Rodar com o Power BI Desktop FECHADO (depois de build_dre_contabil.py):  python build_dre_ajustes.py
Entradas (mesma pasta): dre_ajustes_manuais_20261019.json [mes, conta, historico, usuario, valor, linhas], dre_contas_20261019.csv, build_dre_contabil.py (dicionario SO_DRE).
Fonte dos dados: f_lancamentos do 'INFORMACOES GERENCIAIS.pbip' (linhas com Origem Descricao em branco, mai a set/26), extraidos em 19/10/2026.
Rollback: restaurar Financeiro.SemanticModel/Financeiro.Report de *_backup_20261019_c.
"""
import csv, json, os, re, shutil, uuid

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = r"C:\project\PowerBIClaudio\14 - Controladoria"
SM = os.path.join(BASE, "Financeiro.SemanticModel")
RP = os.path.join(BASE, "Financeiro.Report")
NL = "\n"
assert os.path.exists(os.path.join(SM, "definition", "tables", "DreContabil.tmdl")), "rode build_dre_contabil.py antes"
for pasta in (SM, RP):
    bk = pasta + "_backup_20261019_c"
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
    return "\t/// %s%s\tmeasure '%s' = %s%s\t\tformatString: %s%s\t\tdisplayFolder: Ajustes manuais do DRE%s\t\tlineageTag: %s%s%s" % (
        desc, NL, name, expr, NL, fmt, NL, NL, g(), NL, NL)

# descricoes das contas: Athena (csv) + contas que so existem no DRE (dicionario do build_dre_contabil.py)
desc = {}
for r in csv.DictReader(open(os.path.join(AQUI, "dre_contas_20261019.csv"), encoding="utf-8")):
    desc.setdefault(int(r["num_conta"]), r["conta_descricao"])
src = open(os.path.join(AQUI, "build_dre_contabil.py"), encoding="utf-8").read()
SO_DRE = {}
exec(re.search(r"SO_DRE = \{.*?\}\n", src, re.S).group(0))

def txt(s): return '"%s"' % str(s).replace('"', '""')
dados = [r for r in json.load(open(os.path.join(AQUI, "dre_ajustes_manuais_20261019.json"), encoding="utf-8")) if r[0] >= "2026-07"]
linhas = []
for mes, conta, hist, usuario, valor, n in dados:
    s = str(conta)
    cl = "%s.%s.%s.%s.%s" % (s[0], s[1], s[2], s[3:5], s[5:])
    d = desc.get(conta) or SO_DRE.get(conta) or "(conta só no DRE)"
    linhas.append("{%s, #date(%d, %d, 1), %d, %s, %s, %s, %s, %s, %d}" % (
        txt(mes), int(mes[:4]), int(mes[5:7]), conta, txt(cl), txt(d), txt(hist), txt(usuario), repr(float(valor)), n))
M = NL.join(["let",
             "    Fonte = #table(type table [mes = text, data_mes = date, num_conta = Int64.Type, classificacao = text, conta_descricao = text, historico = text, usuario = text, valor = number, linhas = Int64.Type], {",
             ("," + NL).join("        " + l for l in linhas), "    })", "in", "    Fonte"])
T = "DreAjustesManuais"
medidas = "".join([
    meas("Valor dos Ajustes Manuais", "SUM(DreAjustesManuais[valor])", MON,
         "Créditos menos débitos das linhas que o DRE gerencial tem e o KMM não tem (Origem em branco), jul a set/26. Positivo aumenta o resultado."),
    meas("Ajuste (módulo)", "ABS([Valor dos Ajustes Manuais])", MON, "Valor absoluto, para ordenar."),
    meas("Linhas de Ajuste Manual", "SUM(DreAjustesManuais[linhas])", "#,##0", "Quantidade de linhas (créditos e débitos) lançadas no DRE."),
])
colunas = "".join([col("mes", "string"), col("data_mes", "dateTime", "dd/MM/yyyy", True), col("num_conta", "int64", "0"), col("classificacao", "string"),
                   col("conta_descricao", "string"), col("historico", "string"), col("usuario", "string"), col("valor", "double", None, True), col("linhas", "int64", "0", True)])
particao = "\tpartition %s = m%s\t\tmode: import%s\t\tsource =%s%s%s%s\tannotation PBI_ResultType = Table%s" % (
    T, NL, NL, NL, NL.join("\t\t\t\t" + l for l in M.split(NL)), NL, NL, NL)
w(os.path.join(SM, "definition", "tables", T + ".tmdl"),
  "/// Detalhe dos lançamentos manuais do DRE gerencial (sem origem no KMM), por mês, conta, histórico e usuário, jul a set/26. Foto extraída do INFORMAÇÕES GERENCIAIS em 19/10/2026; não atualiza sozinha." + NL +
  "table %s%s\tlineageTag: %s%s%s" % (T, NL, g(), NL + NL, medidas + colunas + particao))

mp = os.path.join(SM, "definition", "model.tmdl")
t = open(mp, encoding="utf-8").read()
if "ref table " + T not in t:
    t = t.replace("ref table DreContabil", "ref table DreContabil" + NL + "ref table " + T)
    open(mp, "w", encoding="utf-8", newline="").write(t)
rp = os.path.join(SM, "definition", "relationships.tmdl")
r = open(rp, encoding="utf-8").read()
if T + "_data_mes" not in r:
    r = r.rstrip() + NL + NL + "relationship %s_data_mes_Calendario_Data" % T + NL + "\tfromColumn: %s.data_mes" % T + NL + "\ttoColumn: Calendario.Data" + NL
    open(rp, "w", encoding="utf-8", newline="").write(r)

# ---------------- pagina
fonte = open(os.path.join(AQUI, "build_financeiro.py"), encoding="utf-8").read().split("\n")
ini = next(i for i, l in enumerate(fonte) if l.startswith("# ====") and l.rstrip().endswith("relatorio"))
fim = next(i for i, l in enumerate(fonte) if l.startswith("# ----- pagina 1"))
exec("\n".join(fonte[ini:fim]))

PID = "a1b2c3d4e5f607182913"
pg = Page(PID, "Ajustes manuais do DRE", "Lançamentos que o DRE gerencial tem e o KMM não tem (sem origem): quem lançou, histórico e valor")
pg.slicer("sl_ano", "Ano", 740, 90, "Calendario", "Ano", "g_ano")
pg.slicer("sl_mes", "Mês", 840, 140, "Calendario", "Ano-Mês", "g_mes")
pg.slicer("sl_cta", "Conta", 990, 390, T, "conta_descricao", "g_aj_cta")
pg.slicer("sl_usr", "Lançado por", 1390, 190, T, "usuario", "g_aj_usr")
pg.cards([(T, "Valor dos Ajustes Manuais", AMBER, "Valor líquido dos ajustes manuais"), (T, "Linhas de Ajuste Manual", GRAY, "Linhas lançadas (créditos e débitos)")])
pg.chart("g_conta", "barChart", 20, 210, 620, 640, pc(T, "conta_descricao", "Conta"), [pm(T, "Valor dos Ajustes Manuais", "Ajuste líquido")],
         "Ajuste líquido por conta", cor=AMBER, ordenar=sort_med(T, "Ajuste (módulo)"))
pg.tabela("t_aj", 660, 210, 920, 640, [
    pc(T, "mes", "Mês"), pc(T, "classificacao", "Conta"), pc(T, "conta_descricao", "Descrição"), pc(T, "historico", "Histórico"), pc(T, "usuario", "Lançado por"),
    pm(T, "Valor dos Ajustes Manuais", "Valor"), pm(T, "Linhas de Ajuste Manual", "Linhas"),
], "Detalhe: o que foi lançado, por quem e por quê (histórico)", ordenar=sort_med(T, "Ajuste (módulo)"))
pg.texto("rodape", 20, 856, 1560, 40,
         "Linhas do DRE gerencial com Origem em branco (não vêm da contabilidade do KMM no Athena), extraídas em 19/10/2026 para jul a set/26; não atualizam sozinhas. "
         "O histórico agrupa linhas iguais (primeiros 60 caracteres). Valores = créditos menos débitos; positivo aumenta o resultado.", "8pt", GRAY)
pp = os.path.join(RP, "definition", "pages", "pages.json")
meta = json.load(open(pp, encoding="utf-8"))
if PID not in meta["pageOrder"]:
    i = meta["pageOrder"].index("a1b2c3d4e5f607182912")
    meta["pageOrder"].insert(i + 1, PID)
json.dump(meta, open(pp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("ok: tabela %s, %d grupos, pagina %s" % (T, len(linhas), PID))
