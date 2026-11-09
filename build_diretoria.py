"""Cria Diretoria.pbip: relatorio fino (byPath) sobre o modelo Financeiro.SemanticModel, 2 paginas para a diretoria.
Rodar com o Power BI Desktop do Financeiro FECHADO (adiciona 1 medida a tabela Diretoria no TMDL):  python build_diretoria.py
Rollback: apagar Diretoria.pbip / Diretoria.Report e restaurar Financeiro.SemanticModel de *_backup_20261019_e.
"""
import json, os, re, shutil, uuid

BASE = r"C:\project\PowerBIClaudio\14 - Controladoria"
SM = os.path.join(BASE, "Financeiro.SemanticModel")
SRC_RP = os.path.join(BASE, "Financeiro.Report")
RP = os.path.join(BASE, "Diretoria.Report")
AQUI = os.path.dirname(os.path.abspath(__file__))
NL = "\n"
assert os.path.exists(os.path.join(SM, "definition", "tables", "Diretoria.tmdl")), "tabela Diretoria nao esta salva no modelo"
bk = SM + "_backup_20261019_e"
if not os.path.exists(bk):
    shutil.copytree(SM, bk)

# ---- 1 medida nova no modelo (TMDL)
tp = os.path.join(SM, "definition", "tables", "Diretoria.tmdl")
t = open(tp, encoding="utf-8").read()
if "Participação na Receita Operacional" not in t:
    bloco = ("\t/// Participação do cliente (grupo) no Faturamento Operacional (Painel) do período." + NL +
             "\tmeasure 'Participação na Receita Operacional' = DIVIDE([Faturamento Operacional (Painel)], CALCULATE([Faturamento Operacional (Painel)], REMOVEFILTERS(Documentos[grupo_tomador])))" + NL +
             "\t\tformatString: 0.0%" + NL + "\t\tdisplayFolder: Receita e qualidade" + NL + "\t\tlineageTag: %s" % uuid.uuid4() + NL + NL)
    m = re.search(r"^\t(column|partition) ", t, re.M)
    t = t[:m.start()] + bloco + t[m.start():]
    open(tp, "w", encoding="utf-8", newline="").write(t)

# ---- projeto
def w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "wb").write(text.encode("utf-8"))
w(os.path.join(BASE, "Diretoria.pbip"), json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
    "version": "1.0", "artifacts": [{"report": {"path": "Diretoria.Report"}}], "settings": {"enableAutoRecovery": True}}, indent=2))
w(os.path.join(RP, ".platform"), json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
    "metadata": {"type": "Report", "displayName": "Diretoria"}, "config": {"version": "2.0", "logicalId": str(uuid.uuid4())}}, indent=2))
w(os.path.join(RP, "definition.pbir"), json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
    "version": "4.0", "datasetReference": {"byPath": {"path": "../Financeiro.SemanticModel"}}}, indent=2))
if not os.path.exists(os.path.join(RP, "StaticResources")):
    shutil.copytree(os.path.join(SRC_RP, "StaticResources"), os.path.join(RP, "StaticResources"))
os.makedirs(os.path.join(RP, "definition"), exist_ok=True)
shutil.copy(os.path.join(SRC_RP, "definition", "version.json"), os.path.join(RP, "definition", "version.json"))
rep = json.load(open(os.path.join(SRC_RP, "definition", "report.json"), encoding="utf-8"))
rep.pop("filterConfig", None)
json.dump(rep, open(os.path.join(RP, "definition", "report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ---- framework de paginas (de build_financeiro.py)
fonte = open(os.path.join(AQUI, "build_financeiro.py"), encoding="utf-8").read().split("\n")
ini = next(i for i, l in enumerate(fonte) if l.startswith("# ====") and l.rstrip().endswith("relatorio"))
fim = next(i for i, l in enumerate(fonte) if l.startswith("# ----- pagina 1"))
exec("\n".join(fonte[ini:fim]))

D, L, R, P = "Diretoria", "LigacaoContabil", "TituloReceber", "TituloPagar"
DL = "DreLinhas"
DOC = "Documentos"

def filtrar(pg, nome, filtros):
    p = os.path.join(pg.dir, "visuals", nome, "visual.json")
    d = json.load(open(p, encoding="utf-8")); d["filterConfig"] = {"filters": filtros}
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def card_texto(pg, nome, tabela, medida, x, y, wd, h, tam="12D"):
    v = {"visualType": "card", "query": {"queryState": {"Values": {"projections": [pm(tabela, medida)]}}},
         "objects": {"labels": [{"properties": {"fontSize": lit(tam), "color": colr(NAVY)}}], "categoryLabels": [{"properties": {"show": lit("false")}}]}}
    pg.put(nome, x, y, wd, h, v, pg.box())

def cartoes(pg, lista, y, h=100):
    n = len(lista); wd = round((1560 - 20 * (n - 1)) / n, 1)
    for i, (t, m, c, dn) in enumerate(lista):
        pg.card("c%d_%d" % (y, i), t, m, round(20 + i * (wd + 20), 1), wd, c, dn, y=y, h=h)

# ================= pagina 1: visao da diretoria
MESES = ["2026-07", "2026-08", "2026-09"]
fm = [filtro_in("Calendario", "Ano-Mês", MESES, "f_meses")]
MESES_MC = ["2026-%02d" % m for m in range(1, 10)]
fm_mc = [filtro_in("Calendario", "Ano-Mês", MESES_MC, "f_meses_mc")]
p1 = Page("d1a2b3c4d5e6f7081901", "Visão da diretoria", "Margem de contribuição: jan a set/26. Faturamento e clientes: jul a set/26 (meses validados)")
p1.slicer("sl_mes", "Mês", 1300, 280, "Calendario", "Ano-Mês", "g_dir_mes")
cartoes(p1, [(DOC, "Faturamento Operacional (Painel)", NAVY, "Faturamento operacional"),
             (DL, "Margem de Contribuição % (KMM, método DRE)", TEAL, "Margem de contribuição (empresa)"),
             (D, "Top 5 Clientes % da Receita Operacional", AMBER, "Top 5 clientes"),
             (D, "Maior Cliente % da Receita Operacional", AMBER, "Maior cliente"),
             (D, "% Fretes Anulados", RED, "Fretes anulados (% da receita)")], 92)
for i in range(5): filtrar(p1, "c92_%d" % i, fm_mc if i == 1 else fm)
cat = pc("Calendario", "Ano-Mês", "Mês")
p1.chart("g_fat", "clusteredColumnChart", 20, 210, 770, 300, cat,
         [pm(DOC, "Faturamento Operacional (Painel)", "Faturamento operacional"), pm(DOC, "Custo Operacional", "Custo de frete e ocorrência")],
         "Faturamento e custo de frete por mês", legenda=True, filtros=fm)
p1.chart("g_mar", "lineChart", 810, 210, 770, 300, cat, [pm(DL, "Margem de Contribuição % (KMM, método DRE)", "Margem de contribuição")],
         "Margem de contribuição por mês, jan a set (fórmula do DRE sobre os lançamentos)", cor=TEAL, filtros=fm_mc)
p1.tabela("t_cli", 20, 525, 1000, 320, [
    pc(DOC, "grupo_tomador", "Cliente (grupo)"), pm(DOC, "Faturamento Operacional (Painel)", "Faturamento"),
    pm(D, "Participação na Receita Operacional", "Participação"), pm(DOC, "Margem após Impostos %", "Margem após impostos")],
    "Clientes: quanto faturam, quanto pesam e que margem deixam", ordenar=sort_med(DOC, "Faturamento Operacional (Painel)"), filtros=fm)
card_texto(p1, "selo", D, "Selo de Confiança da Base", 1040, 525, 540, 120)
p1.texto("leitura", 1040, 655, 540, 190,
         "Como ler: a margem de contribuição segue a regra do DRE (receita líquida menos custos dos serviços, repasse, fretes anulados e abatimentos), calculada com os lançamentos do KMM. "
         "Ela fecha com a margem do DRE de janeiro a setembro, porque inclui os lançamentos manuais do KMM (folha, encargos, provisões, reclassificações). "
         "Por cliente, a margem após impostos: receita menos custo de frete e ocorrência e menos os impostos lançados no próprio documento; fica acima da margem de contribuição porque ainda não desconta repasse, fretes anulados e impostos sem documento. "
         "Maio, junho e outubro ficam de fora porque a conferência com a contabilidade só está completa de julho a setembro.",
         "10pt", GRAY, container=p1.box("Leitura"))

# ================= pagina 2: caixa e prazos
p2 = Page("d1a2b3c4d5e6f7081902", "Caixa e prazos", "Entradas e saídas realizadas, projeção estimada, vencidos e ciclo financeiro")
cartoes(p2, [(D, "Entradas Realizadas 30d", TEAL, "Entradas, últimos 30 dias"), (D, "Saídas Realizadas 30d", RED, "Saídas, últimos 30 dias"),
             (D, "Resultado de Caixa 30d", RED, "Resultado, 30 dias"), (D, "Resultado de Caixa 90d", RED, "Resultado, 90 dias"),
             (D, "Caixa Projetado 30d (estimado)", AMBER, "Caixa projetado 30 dias (estimado)")], 92)
cartoes(p2, [(R, "Saldo Vencido", RED, "A receber vencido"), (P, "Vencido em Aberto Hoje", RED, "A pagar vencido"),
             (R, "Prazo Médio de Recebimento (dias)", NAVY, "Prazo médio de recebimento (dias)"), (P, "Prazo Médio de Pagamento (dias)", NAVY, "Prazo médio de pagamento (dias)"),
             (R, "Ciclo Financeiro (dias)", AMBER, "Ciclo financeiro (dias)")], 204)
fm2 = [filtro_in("Calendario", "Ano-Mês", ["2026-%02d" % m for m in range(5, 13)], "f_meses2")]
p2.chart("g_cx", "clusteredColumnChart", 20, 320, 770, 380, cat,
         [pm(R, "Entradas de Caixa", "Entradas"), pm(R, "Saídas de Caixa", "Saídas")], "Entradas e saídas de caixa por mês (o último mês é parcial)", legenda=True, filtros=fm2)
p2.chart("g_res", "lineChart", 810, 320, 770, 380, cat, [pm(R, "Resultado de Caixa", "Resultado do mês")], "Resultado de caixa por mês (o último mês é parcial)", cor=NAVY, filtros=fm2)
p2.texto("atencao", 20, 715, 1560, 125,
         "Atenção: as saídas somam todas as baixas de títulos a pagar. Podem incluir tributos, empréstimos e transferências além da operação, e as entradas só contam títulos a receber. "
         "Antes de decidir com base no caixa, validar com a tesouraria e o extrato bancário. O caixa projetado é uma estimativa: o ritmo líquido médio dos últimos 90 dias (entradas menos saídas) mantido pelos próximos dias; "
         "não é orçamento. As janelas de 30 e 90 dias partem da data de corte dos dados, mostrada no canto superior direito.", "10pt", RED, container=p2.box("Atenção"))

card_texto(p2, "dados_ate", D, "Dados até", 1180, 14, 400, 50, "11D")

meta = {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
        "pageOrder": ["d1a2b3c4d5e6f7081901", "d1a2b3c4d5e6f7081902"], "activePageName": "d1a2b3c4d5e6f7081901"}
json.dump(meta, open(os.path.join(RP, "definition", "pages", "pages.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("Diretoria.pbip criado com 2 paginas")
