"""Margem de contribuicao POR CLIENTE (decisao do usuario em 20/10/2026), regra do DRE aplicada aos lancamentos do KMM:
  receita liquida do cliente = receita contabil (3.1.1.01) + deducoes (3.1.1.02) dos proprios documentos
  custo direto = custo do contrato (3.1.2.05) + itens, rateado pelas cargas
  margem direta = receita liquida - custo direto
  resultado nao atribuido = margem de contribuicao TOTAL (DreLinhas, base KMM) - soma das margens diretas
  rateio = resultado nao atribuido x (receita liquida do cliente / receita liquida total)  ->  a soma dos clientes fecha com o total
A foto do DRE nao e usada nas medidas (so em conferencias).
Rodar com o Financeiro e a Diretoria FECHADOS, depois de aplicar a view (36 colunas):  python build_margem_cliente.py
Backup: Financeiro.SemanticModel / Report *_backup_20261020_j.   Depois: build_diretoria.py e build_memorando.py ja usam os nomes novos.
"""
import json, os, re, shutil, uuid

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = r"C:\project\PowerBIClaudio\14 - Controladoria"
SM = os.path.join(BASE, "Financeiro.SemanticModel")
RP = os.path.join(BASE, "Financeiro.Report")
NL = "\n"
for pasta in (SM, RP):
    bk = pasta + "_backup_20261020_j"
    if not os.path.exists(bk):
        shutil.copytree(pasta, bk)


def g(): return str(uuid.uuid4())


MON = '"R$"\\ #,##0.00;-"R$"\\ #,##0.00'


def meas(name, expr, fmt, desc, folder="Margem por cliente"):
    fmt_linha = ("\t\tformatString: %s%s" % (fmt, NL)) if fmt else ""
    return "\t/// %s%s\tmeasure '%s' = %s%s%s\t\tdisplayFolder: %s%s\t\tlineageTag: %s%s%s" % (desc, NL, name, expr, NL, fmt_linha, folder, NL, g(), NL, NL)


def col(name, typ):
    return NL.join(["\tcolumn %s" % name, "\t\tdataType: %s" % typ, "\t\tisHidden", "\t\tlineageTag: %s" % g(), "\t\tsummarizeBy: none", "\t\tsourceColumn: %s" % name]) + NL + NL


F = 'LigacaoContabil[tipo_analise] IN {"CT-e", "NF"}, LigacaoContabil[con_status] IN {"A", "S"}, LigacaoContabil[no_painel] = "SIM"'


def cli(expr):
    return ('VAR cli = CALCULATETABLE(VALUES(Documentos[grupo_tomador]), REMOVEFILTERS(Calendario)) RETURN IF(ISFILTERED(Documentos[grupo_tomador]), '
            'CALCULATE(%s, %s, TREATAS(cli, LigacaoContabil[grupo_tomador])), CALCULATE(%s, %s))' % (expr, F, expr, F))


RL = "SUM(LigacaoContabil[receita_contabil_rateada]) + SUM(LigacaoContabil[deducoes_contabeis_rateadas])"
medidas = "".join([
    meas("Receita Líquida dos Documentos", cli(RL), MON,
         "Receita contábil (conta 3.1.1.01) mais as deduções (ICMS, crédito presumido, ISS, PIS/COFINS) lançadas nos próprios CT-e/NF do painel, pelo mês da emissão. Segue o filtro de cliente."),
    meas("Custo Direto dos Documentos", "[Custo Contábil Total]", MON, "Custo do contrato (frete e itens) ligado às cargas dos documentos; igual ao Custo Contábil Total."),
    meas("Margem Direta", "[Receita Líquida dos Documentos] - [Custo Direto dos Documentos]", MON, "Receita líquida dos documentos menos o custo direto do contrato, antes de ratear o que não liga a cliente."),
    meas("% Margem Direta", "DIVIDE([Margem Direta], [Receita Líquida dos Documentos])", "0.0%", "Margem direta sobre a receita líquida dos documentos. Serve para comparar clientes; fica acima da margem do DRE."),
    meas("Margem de Contribuição Total (KMM)", "[Margem de Contribuição Bruta (KMM)]", MON, "Margem de contribuição da empresa pela regra do DRE, com os lançamentos do KMM (não depende de cliente)."),
    meas("Margem Direta Total", "CALCULATE([Margem Direta], REMOVEFILTERS(Documentos[grupo_tomador]))", MON, "Soma da margem direta de todos os clientes no período."),
    meas("Receita Líquida Total", "CALCULATE([Receita Líquida dos Documentos], REMOVEFILTERS(Documentos[grupo_tomador]))", MON, "Soma da receita líquida dos documentos de todos os clientes no período."),
    meas("Resultado Não Atribuído a Clientes", "[Margem de Contribuição Total (KMM)] - [Margem Direta Total]", MON,
         "Parte da margem de contribuição que não liga a documento de cliente: contratos de cargas de outros meses, repasse, outras receitas e custos de serviço. Negativo = custos maiores que receitas não ligadas."),
    meas("Rateio do Não Atribuído", "[Resultado Não Atribuído a Clientes] * DIVIDE([Receita Líquida dos Documentos], [Receita Líquida Total])", MON,
         "Resultado não atribuído dividido entre os clientes pela receita líquida de cada um. A soma dos clientes é o resultado não atribuído total."),
    meas("Margem de Contribuição do Cliente", "[Margem Direta] + [Rateio do Não Atribuído]", MON, "Margem direta mais o rateio. A soma dos clientes fecha com a margem de contribuição total."),
    meas("% Margem de Contribuição do Cliente", "DIVIDE([Margem de Contribuição do Cliente], [Receita Líquida dos Documentos])", "0.0%",
         "Margem de contribuição sobre a receita líquida dos documentos. Sem cliente selecionado é a margem da empresa; com cliente, a do cliente. É a margem comparável ao DRE."),
    meas("Teste: Soma dos Clientes menos Total", "SUMX(VALUES(Documentos[grupo_tomador]), [Margem de Contribuição do Cliente]) - [Margem de Contribuição Total (KMM)]", MON,
         "Deve ser zero (ou perto de zero): a soma da margem de contribuição dos clientes fecha com o total."),
])
p = os.path.join(SM, "definition", "tables", "LigacaoContabil.tmdl")
t = open(p, encoding="utf-8").read()
if "Receita Líquida dos Documentos" not in t:
    a = " qtd_linhas_contrato from hml_gold.vw_fato_ligacao_contabil"
    assert t.count(a) == 1
    t = t.replace(a, " qtd_linhas_contrato, deducoes_contabeis_documento, deducoes_contabeis_rateadas from hml_gold.vw_fato_ligacao_contabil")
    m = re.search(r"^\tcolumn ", t, re.M)
    t = t[:m.start()] + medidas + t[m.start():]
    k = t.index("\tpartition LigacaoContabil")
    t = t[:k] + col("deducoes_contabeis_documento", "double") + col("deducoes_contabeis_rateadas", "double") + t[k:]
    open(p, "w", encoding="utf-8", newline="").write(t)

# ---------------- pagina "Margem por cliente"
fonte = open(os.path.join(AQUI, "build_financeiro.py"), encoding="utf-8").read().split("\n")
ini = next(i for i, l in enumerate(fonte) if l.startswith("# ====") and l.rstrip().endswith("relatorio"))
fim = next(i for i, l in enumerate(fonte) if l.startswith("# ----- pagina 1"))
exec("\n".join(fonte[ini:fim]))
PID = "a1b2c3d4e5f607182918"
LC, DOC = "LigacaoContabil", "Documentos"
fm = [filtro_in("Calendario", "Ano-Mês", ["2026-07", "2026-08", "2026-09"], "f_meses")]
pg = Page(PID, "Margem por cliente", "Margem de contribuição por cliente (regra do DRE, lançamentos do KMM) com o rateio do que não liga a documento (jul a set/26)")
pg.slicer("sl_ano", "Ano", 1120, 90, "Calendario", "Ano", "g_ano")
pg.slicer("sl_mes", "Mês", 1220, 360, "Calendario", "Ano-Mês", "g_mes")
pg.cards([(LC, "Receita Líquida Total", NAVY, "Receita líquida dos documentos"), (LC, "Margem Direta Total", NAVY, "Margem direta (antes do rateio)"),
          (LC, "Resultado Não Atribuído a Clientes", AMBER, "Resultado não atribuído a clientes"), (LC, "Margem de Contribuição Total (KMM)", TEAL, "Margem de contribuição total"),
          (LC, "Teste: Soma dos Clientes menos Total", GRAY, "Teste: soma dos clientes − total (deve ser 0)")])
for i in range(5):
    pa = os.path.join(pg.dir, "visuals", "a%d" % i, "visual.json")
    d = json.load(open(pa, encoding="utf-8")); d["filterConfig"] = {"filters": fm}
    json.dump(d, open(pa, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
lm = lambda n, dn=None: pm(LC, n, dn)
pg.tabela("t_cli", 20, 210, 1560, 440, [
    pc(DOC, "grupo_tomador", "Cliente (grupo)"), lm("Receita Líquida dos Documentos", "Receita líquida"), lm("Custo Direto dos Documentos", "Custo direto"),
    lm("Margem Direta", "Margem direta"), lm("% Margem Direta", "% direta"), lm("Rateio do Não Atribuído", "Rateio do não atribuído"),
    lm("Margem de Contribuição do Cliente", "Margem de contribuição"), lm("% Margem de Contribuição do Cliente", "% de contribuição")],
    "Margem por cliente: direta (para comparar) e de contribuição com rateio (comparável ao DRE)",
    ordenar=sort_med(LC, "Receita Líquida dos Documentos"), filtros=fm)
cat = pc("Calendario", "Ano-Mês", "Mês")
pg.chart("g_pct", "lineChart", 20, 665, 770, 185, cat, [lm("% Margem de Contribuição do Cliente", "% de contribuição"), lm("% Margem Direta", "% direta")],
         "Margem por mês (respeita o filtro de cliente)", legenda=True, filtros=fm)
pg.texto("leitura", 810, 665, 770, 185,
         "Como ler: receita líquida = receita contábil mais as deduções dos próprios CT-e/NF; custo direto = custo do contrato ligado às cargas do cliente. A margem direta (acima de 20%) serve para comparar clientes. "
         "O que não liga a cliente (contratos de cargas de outros meses, repasse, outras receitas e custos de serviço) é a diferença entre a margem de contribuição total e a soma das margens diretas, e é rateado pela receita líquida de cada cliente. "
         "Assim a soma dos clientes fecha com a margem de contribuição total (cartão 'teste' deve dar zero). Os lançamentos manuais do KMM ainda não chegam ao Athena e deslocam a margem total em cerca de -0,2 a +1,7 ponto em relação ao DRE.",
         "10pt", GRAY, container=pg.box("Leitura"))
pp = os.path.join(RP, "definition", "pages", "pages.json")
meta = json.load(open(pp, encoding="utf-8"))
if PID not in meta["pageOrder"]:
    meta["pageOrder"].insert(meta["pageOrder"].index("a1b2c3d4e5f607182914") + 1, PID)
json.dump(meta, open(pp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ---------------- curva: cartao e coluna passam a responder ao filtro de cliente
vis = os.path.join(RP, "definition", "pages", "a1b2c3d4e5f607182908", "visuals")
NOVA = "% Margem de Contribuição do Cliente"


def ref(tab, med, dn):
    return {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": tab}}, "Property": med}}, "queryRef": "%s.%s" % (tab, med), "nativeQueryRef": med, "displayName": dn}


pa = os.path.join(vis, "a5", "visual.json")
d = json.load(open(pa, encoding="utf-8"))
d["visual"]["query"]["queryState"]["Values"]["projections"] = [ref(LC, NOVA, "Margem de contribuição % (lançamentos, jul a set)")]
json.dump(d, open(pa, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
pa = os.path.join(vis, "t_curva", "visual.json")
d = json.load(open(pa, encoding="utf-8"))
for x in d["visual"]["query"]["queryState"]["Values"]["projections"]:
    if "Measure" in x["field"] and x["field"]["Measure"]["Property"] == "Margem de Contribuição % (KMM, método DRE)":
        x["field"]["Measure"]["Expression"]["SourceRef"]["Entity"] = LC
        x["field"]["Measure"]["Property"] = NOVA
        x["queryRef"] = "%s.%s" % (LC, NOVA)
        x["nativeQueryRef"] = NOVA
json.dump(d, open(pa, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("ok: colunas, %d medidas, pagina %s e curva ajustada" % (12, PID))
