"""Margem POR CLIENTE = margem de frete (decisao do usuario em 20/10/2026): receita menos custo de frete e ocorrencia, antes de impostos e repasse.
Sem rateio, sem deducoes, sem anulacoes, sem outras receitas. Empresa: margem de contribuicao pela regra do DRE (cartao rotulado 'empresa').
Remove do modelo as medidas/colunas da versao com rateio, recria a pagina 'Margem por cliente' e reorganiza a curva.
Rodar com o Financeiro e a Diretoria FECHADOS:  python build_margem_cliente_v2.py      Backup: *_backup_20261020_k
"""
import copy, json, os, re, shutil, uuid

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = r"C:\project\PowerBIClaudio\14 - Controladoria"
SM = os.path.join(BASE, "Financeiro.SemanticModel")
RP = os.path.join(BASE, "Financeiro.Report")
NL = "\n"
for pasta in (SM, RP):
    bk = pasta + "_backup_20261020_k"
    if not os.path.exists(bk):
        shutil.copytree(pasta, bk)

# ---------------- 1) LigacaoContabil.tmdl: tira medidas e colunas da versao com rateio
p = os.path.join(SM, "definition", "tables", "LigacaoContabil.tmdl")
linhas = open(p, encoding="utf-8").read().split("\n")
saida, i, removidas = [], 0, 0
while i < len(linhas):
    l = linhas[i]
    if l.startswith("\t///") or l.startswith("\tmeasure "):
        j = i
        while j < len(linhas) and linhas[j].startswith("\t///"):
            j += 1
        if j < len(linhas) and linhas[j].startswith("\tmeasure "):
            k = j + 1
            while k < len(linhas) and linhas[k].startswith("\t\t"):
                k += 1
            bloco = linhas[i:k]
            if any("displayFolder: Margem por cliente" in x for x in bloco):
                removidas += 1
                i = k + 1 if k < len(linhas) and linhas[k] == "" else k
                continue
            saida.extend(bloco)
            i = k
            continue
    if l.startswith("\tcolumn deducoes_contabeis_"):
        k = i + 1
        while k < len(linhas) and linhas[k].startswith("\t\t"):
            k += 1
        i = k + 1 if k < len(linhas) and linhas[k] == "" else k
        continue
    saida.append(l)
    i += 1
t = "\n".join(saida).replace(", deducoes_contabeis_documento, deducoes_contabeis_rateadas", "")
open(p, "w", encoding="utf-8", newline="").write(t)
print("medidas removidas da LigacaoContabil:", removidas)

# ---------------- 2) Documentos.tmdl: medida 'Margem de Frete' (R$)
pd = os.path.join(SM, "definition", "tables", "Documentos.tmdl")
t = open(pd, encoding="utf-8").read()
if "measure 'Margem de Frete' =" not in t:
    bloco = ("\t/// Margem de frete em reais: receita dos documentos menos custo de frete e ocorrência (Custo Operacional), antes de impostos e repasse. Segue o filtro de cliente." + NL +
             "\tmeasure 'Margem de Frete' = [Receita dos Documentos (KMM)] - [Custo Operacional]" + NL +
             '\t\tformatString: "R$"\\ #,##0.00;-"R$"\\ #,##0.00' + NL + "\t\tdisplayFolder: Curva operacional x financeiro" + NL + "\t\tlineageTag: %s" % uuid.uuid4() + NL + NL)
    m = re.search(r"^\tcolumn ", t, re.M)
    t = t[:m.start()] + bloco + t[m.start():]
    open(pd, "w", encoding="utf-8", newline="").write(t)

# ---------------- 3) framework de paginas
fonte = open(os.path.join(AQUI, "build_financeiro.py"), encoding="utf-8").read().split("\n")
ini = next(k for k, l in enumerate(fonte) if l.startswith("# ====") and l.rstrip().endswith("relatorio"))
fim = next(k for k, l in enumerate(fonte) if l.startswith("# ----- pagina 1"))
exec("\n".join(fonte[ini:fim]))

# ---------------- 4) pagina "Margem por cliente" (recriada)
PID = "a1b2c3d4e5f607182918"
dir_pag = os.path.join(RP, "definition", "pages", PID)
if os.path.exists(dir_pag):
    shutil.rmtree(dir_pag)
DOC, DL = "Documentos", "DreLinhas"
pg = Page(PID, "Margem por cliente", "Margem de frete por cliente: receita menos custo de frete e ocorrência, antes de impostos e repasse")
pg.slicer("sl_ano", "Ano", 1120, 90, "Calendario", "Ano", "g_ano")
pg.slicer("sl_mes", "Mês", 1220, 360, "Calendario", "Ano-Mês", "g_mes")
pg.cards([(DOC, "Receita dos Documentos (KMM)", NAVY, "Receita dos documentos"), (DOC, "Custo Operacional", NAVY, "Custo de frete e ocorrência"),
          (DOC, "Margem de Frete", TEAL, "Margem de frete"), (DOC, "Margem de Frete % (bruta)", TEAL, "Margem de frete %"),
          (DL, "Margem de Contribuição % (KMM, método DRE)", AMBER, "Margem de contribuição % da empresa (jul a set)")])
fm = [filtro_in("Calendario", "Ano-Mês", ["2026-07", "2026-08", "2026-09"], "f_meses")]
pa = os.path.join(pg.dir, "visuals", "a4", "visual.json")
d = json.load(open(pa, encoding="utf-8"))
d["filterConfig"] = {"filters": fm}
json.dump(d, open(pa, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
dm = lambda n, dn=None: pm(DOC, n, dn)
pg.tabela("t_cli", 20, 210, 1560, 440, [
    pc(DOC, "grupo_tomador", "Cliente (grupo)"), dm("Receita dos Documentos (KMM)", "Receita dos documentos"), dm("Custo Operacional", "Custo de frete e ocorrência"),
    dm("Margem de Frete", "Margem de frete"), dm("Margem de Frete % (bruta)", "Margem de frete %")],
    "Margem de frete por cliente (antes de impostos e repasse)", ordenar=sort_med(DOC, "Receita dos Documentos (KMM)"))
cat = pc("Calendario", "Ano-Mês", "Mês")
pg.chart("g_pct", "lineChart", 20, 665, 770, 185, cat, [dm("Margem de Frete % (bruta)", "Margem de frete %")], "Margem de frete por mês (respeita o filtro de cliente)", cor=TEAL)
pg.texto("leitura", 810, 665, 770, 185,
         "Como ler: por cliente, a margem é receita dos documentos menos custo de frete e ocorrência (o contrato pago aos cooperados), antes de impostos e repasse. Cada valor tem linhagem até o documento e o contrato. "
         "Não entram impostos, anulações, outras receitas (pedágio, descarga), repasse nem rateio. Serve para comparar clientes. "
         "O cartão de margem de contribuição é da empresa (regra do DRE) e não muda com o cliente; ele fica em torno de 9% a 10%, mais baixo porque desconta impostos e os demais custos de serviço.",
         "10pt", GRAY, container=pg.box("Leitura"))
pp = os.path.join(RP, "definition", "pages", "pages.json")
meta = json.load(open(pp, encoding="utf-8"))
if PID not in meta["pageOrder"]:
    meta["pageOrder"].insert(meta["pageOrder"].index("a1b2c3d4e5f607182914") + 1, PID)
json.dump(meta, open(pp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ---------------- 5) curva: 7 cartoes (empresa x cliente) e tabela
vis = os.path.join(RP, "definition", "pages", "a1b2c3d4e5f607182908", "visuals")


def ref(tab, med, dn):
    return {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": tab}}, "Property": med}}, "queryRef": "%s.%s" % (tab, med), "nativeQueryRef": med, "displayName": dn}


MC = "Margem de Contribuição % (KMM, método DRE)"
MF = "Margem de Frete % (bruta)"
a5 = os.path.join(vis, "a5", "visual.json")
d5 = json.load(open(a5, encoding="utf-8"))
d5["visual"]["query"]["queryState"]["Values"]["projections"] = [ref(DL, MC, "Margem de contribuição % da empresa (jul a set)")]
json.dump(d5, open(a5, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
d6 = copy.deepcopy(d5)
d6["name"] = "a6"
d6["visual"]["query"]["queryState"]["Values"]["projections"] = [ref(DOC, MF, "Margem de frete % (segue o cliente)")]
d6.pop("filterConfig", None)
os.makedirs(os.path.join(vis, "a6"), exist_ok=True)
json.dump(d6, open(os.path.join(vis, "a6", "visual.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
wd = round((1560 - 6 * 20) / 7, 1)
for k in range(7):
    pa = os.path.join(vis, "a%d" % k, "visual.json")
    dk = json.load(open(pa, encoding="utf-8"))
    dk["position"]["x"] = round(20 + k * (wd + 20), 1)
    dk["position"]["width"] = wd
    if k == 6:
        dk["position"]["z"] = dk["position"]["z"] + 100
        dk["position"]["tabOrder"] = dk["position"]["z"]
    json.dump(dk, open(pa, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

pa = os.path.join(vis, "t_curva", "visual.json")
d = json.load(open(pa, encoding="utf-8"))
for x in d["visual"]["query"]["queryState"]["Values"]["projections"]:
    if "Measure" in x["field"]:
        prop = x["field"]["Measure"]["Property"]
        if prop == "% Margem de Contribuição do Cliente":
            x["field"]["Measure"]["Expression"]["SourceRef"]["Entity"] = DL
            x["field"]["Measure"]["Property"] = MC
            x["queryRef"] = "%s.%s" % (DL, MC)
            x["nativeQueryRef"] = MC
            x["displayName"] = "Margem de contribuição % (empresa)"
        elif prop == MF:
            x["displayName"] = "Margem de frete % (antes de impostos e repasse)"
json.dump(d, open(pa, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

pa = os.path.join(vis, "rodape", "visual.json")
d = json.load(open(pa, encoding="utf-8"))
r = d["visual"]["objects"]["general"][0]["properties"]["paragraphs"][0]["textRuns"][0]
k = r["value"].find(" MARGEM DE CONTRIBUIÇÃO %")
if k >= 0:
    r["value"] = r["value"][:k]
r["value"] += (" MARGEM DE CONTRIBUIÇÃO % DA EMPRESA = fórmula do DRE aplicada aos lançamentos do KMM (jul a set); fica perto da margem do DRE (pode diferir em até cerca de 2 pontos por causa dos "
               "lançamentos manuais ainda ausentes no Athena) e não muda com o filtro de cliente. MARGEM DE FRETE % = receita dos documentos menos custo de frete e ocorrência, antes de impostos e repasse; "
               "segue o filtro de cliente e serve para comparar clientes.")
json.dump(d, open(pa, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("ok: pagina %s recriada, curva com 7 cartoes, modelo limpo" % PID)
