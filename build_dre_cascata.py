"""Adiciona ao Financeiro a CASCATA do DRE (ROB -> ROL -> Margem de Contribuicao -> Resultado Operacional -> Sobra Gerencial -> Sobra Contabil)
sobre a base KMM (DreContabil), com a comparacao com o DRE gerencial linha a linha, e a pagina 'DRE em cascata (base KMM)'.
Fonte da estrutura: 'Explicacao de Calculo - Contas DRE 3.docx' + dPlanoContas/d_gerencial do INFORMACOES GERENCIAIS.pbip (extraidos em 20/10/2026).
Rodar com o Power BI Desktop FECHADO:  python build_dre_cascata.py     (depois de build_dre_contabil.py)
Rollback: restaurar Financeiro.SemanticModel / Financeiro.Report de *_backup_20261020_f.
"""
import json, os, shutil, uuid

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = r"C:\project\PowerBIClaudio\14 - Controladoria"
SM = os.path.join(BASE, "Financeiro.SemanticModel")
RP = os.path.join(BASE, "Financeiro.Report")
NL = "\n"
assert os.path.exists(os.path.join(SM, "definition", "tables", "DreContabil.tmdl")), "rode build_dre_contabil.py antes"
for pasta in (SM, RP):
    bk = pasta + "_backup_20261020_f"
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
def meas(name, expr, fmt, desc, folder="DRE em cascata"):
    fmt_linha = ("		formatString: %s%s" % (fmt, NL)) if fmt else ""   # formatString vazio quebra o TMDL
    return "	/// %s%s	measure '%s' = %s%s%s		displayFolder: %s%s		lineageTag: %s%s%s" % (
        desc, NL, name, expr, NL, fmt_linha, folder, NL, g(), NL, NL)
def txt(s): return '"%s"' % str(s).replace('"', '""')

# ---------------- DrePlano (conta -> grupo do DRE e marcas de margem)
plano = json.load(open(os.path.join(AQUI, "dre_plano_20261020.json"), encoding="utf-8"))
linhas_plano = ["{%d, %s, %s, %s, %d, %s, %s, %s}" % (r["num_conta"], txt(r["descricao"]), txt(r["nivel_2"]), txt(r["nivel_1"]), r["ordem"], txt(r["mb"]), txt(r["mo"]), txt(r["mr"])) for r in plano]
M1 = NL.join(["let",
              "    Fonte = #table(type table [num_conta = Int64.Type, descricao_dre = text, nivel_2 = text, nivel_1 = text, ordem = Int64.Type, margem_bruta = text, margem_operacional = text, margem_repasse = text], {",
              ("," + NL).join("        " + l for l in linhas_plano), "    })", "in", "    Fonte"])
cols1 = "".join([col("num_conta", "int64", "0"), col("descricao_dre", "string"), col("nivel_2", "string"), col("nivel_1", "string"), col("ordem", "int64", "0"),
                 col("margem_bruta", "string"), col("margem_operacional", "string"), col("margem_repasse", "string")])
def particao(nome, m):
    return "\tpartition %s = m%s\t\tmode: import%s\t\tsource =%s%s%s%s\tannotation PBI_ResultType = Table%s" % (
        nome, NL, NL, NL, NL.join("\t\t\t\t" + l for l in m.split(NL)), NL, NL, NL)
w(os.path.join(SM, "definition", "tables", "DrePlano.tmdl"),
  "/// Plano de contas do DRE gerencial: cada conta com o grupo (nivel_1) e as marcas de margem (X / XD). Foto do INFORMAÇÕES GERENCIAIS de 20/10/2026." + NL +
  "table DrePlano" + NL + "\tlineageTag: %s" % g() + NL + NL + cols1 + particao("DrePlano", M1))

# ---------------- DreLinhas (as 14 linhas da cascata) + medidas
LINHAS = [(1, "RECEITA TOTAL (ROB)", 1, "="), (2, "INGRESSOS E RECEITAS DE FRETE", 0, "+"), (3, "REPASSE LÍQUIDO", 0, "+"), (4, "DEDUÇÕES DA RECEITA", 0, "-"),
          (5, "RECEITAS OPERACIONAIS LÍQUIDAS (ROL)", 1, "="), (6, "CUSTOS DOS SERVIÇOS PRESTADOS", 0, "-"), (7, "MARGEM DE CONTRIBUIÇÃO BRUTA", 1, "="),
          (8, "DESPESAS OPERACIONAIS", 0, "-"), (9, "INDEDUTÍVEIS E TRIBUTÁRIAS", 0, "-"), (10, "RESULTADO OPERACIONAL", 1, "="),
          (11, "RECEITAS E DESPESAS FINANCEIRAS", 0, "-"), (12, "SOBRA GERENCIAL", 1, "="), (13, "OUTRAS RECEITAS/DESPESAS", 0, "-"), (14, "SOBRA CONTÁBIL", 1, "=")]
M2 = NL.join(["let", "    Fonte = #table(type table [codigo = Int64.Type, linha = text, subtotal = Int64.Type, sinal = text], {",
              ("," + NL).join("        {%d, %s, %d, %s}" % (c, txt(l), s, txt(sg)) for c, l, s, sg in LINHAS), "    })", "in", "    Fonte"])
cols2 = "".join([col("codigo", "int64", "0"), col("linha", "string"), col("subtotal", "int64", "0", True), col("sinal", "string", None, True)])

def linha(filtro):
    grupos = [("ing", "INGRESSOS E RECEITAS DE FRETE"), ("rep", "REPASSE LIQUIDO"), ("ded", "DEDUÇÕES DA RECEITA"), ("csp", "CUSTOS DOS SERVIÇOS PRESTADOS"),
              ("dop", "DESPESAS OPERACIONAIS"), ("ind", "INDEDUTÍVEIS E TRIBUTÁRIAS"), ("fin", "RECEITAS E DESPESAS FINANCEIRAS"), ("out", "OUTRAS RECEITAS/DESPESAS")]
    v = "VAR c = SELECTEDVALUE(DreLinhas[codigo]) " + " ".join(
        'VAR %s = CALCULATE(SUM(DreContabil[valor]), %s, DrePlano[nivel_1] = "%s")' % (k, filtro, n) for k, n in grupos)
    sw = ("RETURN SWITCH(c, 1, ing + rep, 2, ing, 3, rep, 4, ded, 5, ing + rep + ded, 6, csp, 7, ing + rep + ded + csp, 8, dop, 9, ind, "
          "10, ing + rep + ded + csp + dop + ind, 11, fin, 12, ing + rep + ded + csp + dop + ind + fin, 13, out, 14, ing + rep + ded + csp + dop + ind + fin + out)")
    return v + " " + sw
F_KMM = 'DreContabil[fonte] = "KMM"'
F_DRE = 'DreContabil[fonte] = "DRE"'
F_AJ = 'DreContabil[fonte] = "DRE", DreContabil[status] = "AJUSTE MANUAL DO DRE"'
def margem(f, flag, base):
    return 'DIVIDE(CALCULATE(SUM(DreContabil[valor]), %s, DrePlano[%s] <> ""), CALCULATE(SUM(DreContabil[valor]), %s, DrePlano[%s] = "XD"))' % (f, flag, f, flag)
medidas = "".join([
    meas("DRE Linha (KMM)", linha(F_KMM), MON, "Valor da linha do DRE calculado só com a contabilidade do KMM (créditos menos débitos). Subtotais são cumulativos, como no DRE gerencial."),
    meas("DRE Linha (DRE)", linha(F_DRE), MON, "Valor da mesma linha no DRE gerencial (foto de 20/10/2026, jul a set/26)."),
    meas("DRE Linha (ajuste manual)", linha(F_AJ), MON, "Parte do DRE gerencial que não existe no KMM (linhas sem origem): ajustes manuais da controladoria."),
    meas("DRE Linha Diferença", "[DRE Linha (KMM)] - [DRE Linha (DRE)]", MON, "KMM menos DRE."),
    meas("DRE Linha Diferença sem Ajuste Manual", "[DRE Linha (KMM)] - ([DRE Linha (DRE)] - [DRE Linha (ajuste manual)])", MON,
         "KMM menos o DRE sem os ajustes manuais. Se não é zero, há diferença real entre o KMM e o DRE (hoje: NF de E/S de set)."),
    meas("DRE Linha % da ROB (KMM)", "DIVIDE([DRE Linha (KMM)], CALCULATE([DRE Linha (KMM)], DreLinhas[codigo] = 1))", "0.0%", "Linha dividida pela Receita Total (ROB) do KMM."),
    meas("DRE Linha Situação", 'VAR d = [DRE Linha Diferença sem Ajuste Manual] RETURN IF(ISBLANK(d), "", IF(ABS(d) < 1, "fecha com o DRE (após ajustes manuais)", "DIFERE R$ " & FORMAT(ABS(d), "#,##0.00")))', "",
         "Texto que diz se a linha fecha com o DRE depois de tirar os ajustes manuais."),
    meas("Margem de Contribuição Bruta (KMM)", "CALCULATE([DRE Linha (KMM)], DreLinhas[codigo] = 7)", MON, "Margem de Contribuição Bruta com a base KMM."),
    meas("Margem de Contribuição Bruta (DRE)", "CALCULATE([DRE Linha (DRE)], DreLinhas[codigo] = 7)", MON, "Margem de Contribuição Bruta do DRE gerencial."),
    meas("Margem de Contribuição % (KMM, método DRE)", margem(F_KMM, "margem_bruta", "XD"), "0.00%",
         "Mesma fórmula do DRE: soma das contas marcadas na margem bruta dividida pela soma das contas marcadas XD, com a base KMM."),
    meas("Margem de Contribuição % (DRE)", margem(F_DRE, "margem_bruta", "XD"), "0.00%", "Margem bruta % do DRE gerencial, recalculada aqui com a mesma fórmula."),
    meas("Margem Operacional % (KMM, método DRE)", margem(F_KMM, "margem_operacional", "XD"), "0.00%", "Margem operacional do DRE, com a base KMM."),
    meas("Margem Operacional % (DRE)", margem(F_DRE, "margem_operacional", "XD"), "0.00%", "Margem operacional % do DRE gerencial."),
    meas("Contas sem Grupo no DRE (KMM)", 'CALCULATE(SUM(DreContabil[valor]), ' + F_KMM + ', ISBLANK(DrePlano[nivel_1]))', MON,
         "Valor do KMM em contas que não estão no plano de contas do DRE (devem ser zero)."),
])
w(os.path.join(SM, "definition", "tables", "DreLinhas.tmdl"),
  "/// As 14 linhas da cascata do DRE (ROB, ROL, Margem de Contribuição Bruta, Resultado Operacional, Sobra Gerencial, Sobra Contábil) e as medidas que as calculam." + NL +
  "table DreLinhas" + NL + "\tlineageTag: %s" % g() + NL + NL + medidas + cols2 + particao("DreLinhas", M2))

mp = os.path.join(SM, "definition", "model.tmdl")
t = open(mp, encoding="utf-8").read()
for ref in ("DrePlano", "DreLinhas"):
    if "ref table " + ref not in t:
        t = t.replace("ref table DreAjustesManuais", "ref table DreAjustesManuais" + NL + "ref table " + ref)
open(mp, "w", encoding="utf-8", newline="").write(t)
rp = os.path.join(SM, "definition", "relationships.tmdl")
r = open(rp, encoding="utf-8").read()
if "DreContabil_num_conta_DrePlano" not in r:
    r = r.rstrip() + NL + NL + "relationship DreContabil_num_conta_DrePlano_num_conta" + NL + "\tfromColumn: DreContabil.num_conta" + NL + "\ttoColumn: DrePlano.num_conta" + NL
    open(rp, "w", encoding="utf-8", newline="").write(r)

# ---------------- pagina
fonte = open(os.path.join(AQUI, "build_financeiro.py"), encoding="utf-8").read().split("\n")
ini = next(i for i, l in enumerate(fonte) if l.startswith("# ====") and l.rstrip().endswith("relatorio"))
fim = next(i for i, l in enumerate(fonte) if l.startswith("# ----- pagina 1"))
exec("\n".join(fonte[ini:fim]))

PID = "a1b2c3d4e5f607182914"
T, DL, DP = "DreContabil", "DreLinhas", "DrePlano"
fm = [filtro_in("Calendario", "Ano-Mês", ["2026-07", "2026-08", "2026-09"], "f_meses")]
pg = Page(PID, "DRE em cascata (base KMM)", "ROB → ROL → Margem de Contribuição → Resultado → Sobra, só com a contabilidade do KMM e comparado ao DRE (jul a set/26)")
pg.slicer("sl_ano", "Ano", 1120, 90, "Calendario", "Ano", "g_ano")
pg.slicer("sl_mes", "Mês", 1220, 360, "Calendario", "Ano-Mês", "g_mes")
vm = lambda n, dn=None: pm(DL, n, dn)
pg.cards([(DL, "Margem de Contribuição Bruta (KMM)", TEAL, "Margem de contribuição (KMM)"),
          (DL, "Margem de Contribuição Bruta (DRE)", NAVY, "Margem de contribuição (DRE)"),
          (DL, "Margem de Contribuição % (KMM, método DRE)", TEAL, "Margem % (KMM)"),
          (DL, "Margem de Contribuição % (DRE)", NAVY, "Margem % (DRE)"),
          (DL, "Margem Operacional % (DRE)", AMBER, "Margem operacional % (DRE)")])
for i in range(5):
    p = os.path.join(pg.dir, "visuals", "a%d" % i, "visual.json")
    d = json.load(open(p, encoding="utf-8")); d["filterConfig"] = {"filters": fm}
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
pg.tabela("t_casc", 20, 210, 1560, 420, [
    pc(DL, "linha", "Linha do DRE"), vm("DRE Linha (KMM)", "KMM"), vm("DRE Linha (DRE)", "DRE gerencial"), vm("DRE Linha Diferença", "Diferença"),
    vm("DRE Linha (ajuste manual)", "Ajuste manual do DRE"), vm("DRE Linha Diferença sem Ajuste Manual", "Diferença sem ajuste manual"),
    vm("DRE Linha % da ROB (KMM)", "% da ROB"), vm("DRE Linha Situação", "Situação")],
    "A cascata do DRE: o que o KMM entrega, o que o DRE tem e o que explica a diferença",
    ordenar={"field": cref(DL, "codigo"), "direction": "Ascending"}, filtros=fm)
cat = pc("Calendario", "Ano-Mês", "Mês")
pg.chart("g_marg", "clusteredColumnChart", 20, 645, 770, 200, cat,
         [vm("Margem de Contribuição Bruta (KMM)", "KMM"), vm("Margem de Contribuição Bruta (DRE)", "DRE gerencial")],
         "Margem de contribuição bruta por mês", legenda=True, filtros=fm)
pg.texto("leitura", 810, 645, 770, 200,
         "Como ler: cada linha é a soma das contas do grupo no plano de contas do DRE; os subtotais (ROB, ROL, Margem de Contribuição, Resultado Operacional, Sobra Gerencial, Sobra Contábil) são cumulativos. "
         "O DRE gerencial tem lançamentos manuais da controladoria que não existem no KMM; a coluna 'Diferença sem ajuste manual' mostra o que sobra depois de tirá-los. "
         "O % de margem usa a fórmula do DRE (contas marcadas na margem bruta sobre as marcadas XD) e por isso difere do % sobre a ROB. Meses: jul a set/26.",
         "10pt", GRAY, container=pg.box("Leitura"))

pp = os.path.join(RP, "definition", "pages", "pages.json")
meta = json.load(open(pp, encoding="utf-8"))
if PID not in meta["pageOrder"]:
    i = meta["pageOrder"].index("a1b2c3d4e5f607182913")
    meta["pageOrder"].insert(i + 1, PID)
json.dump(meta, open(pp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("ok: DrePlano (%d contas), DreLinhas, relacao, pagina %s" % (len(plano), PID))
