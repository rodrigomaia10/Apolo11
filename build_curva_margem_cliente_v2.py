"""Margem por cliente na Curva SEM rolagem (20/10/2026): desfaz a secao longa da pagina Curva, volta a 1 tela, poe a margem apos impostos
nos cartoes e na tabela mensal (por cliente, mes a mes) e cria a pagina 'Margem: o que nao entra' (1 tela) com o quadro de itens fora.
Rodar com Financeiro e Diretoria FECHADOS (e o Desktop SALVO):  python build_curva_margem_cliente_v2.py      Backup: *_backup_20261020_r
"""
import json, os, shutil

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = r"C:\project\PowerBIClaudio\14 - Controladoria"
SM = os.path.join(BASE, "Financeiro.SemanticModel")
RP = os.path.join(BASE, "Financeiro.Report")
for pasta in (SM, RP):
    bk = pasta + "_backup_20261020_r"
    if not os.path.exists(bk):
        shutil.copytree(pasta, bk)

# ---------------- 0) garante a Fora M3 corrigida no TMDL (caso o Desktop nao tenha sido salvo)
pf = os.path.join(SM, "definition", "tables", "ForaDaMargem.tmdl")
t = open(pf, encoding="utf-8").read()
velha = 'DrePlano[descricao_dre] IN {"(-) DISPENDIOS DE PEDAGIO", "(-) DISPENDIOS DE CARGA E DESCARGA"}'
nova = 'DrePlano[nivel_1] = "INGRESSOS E RECEITAS DE FRETE", DrePlano[margem_bruta] = "X", NOT(DrePlano[descricao_dre] IN {"(-) ANULACOES/REEMISSOES", "(-) ABATIMENTOS DA RECEITA"})'
if velha in t:
    t = t.replace(velha, nova)
r_velha = 'DrePlano[descricao_dre] = "(+) RECEITA FRETES COOPERADOS") - CALCULATE([Receita dos Documentos (KMM)]'
r_nova = 'DrePlano[descricao_dre] IN {"(+) RECEITA FRETES COOPERADOS", "(+) RECEITA FRETES NAO COOPERADOS"}) - CALCULATE([Receita dos Documentos (KMM)]'
if r_velha in t:
    t = t.replace(r_velha, r_nova)
open(pf, "w", encoding="utf-8", newline="").write(t)

# ---------------- 1) framework
fonte = open(os.path.join(AQUI, "build_financeiro.py"), encoding="utf-8").read().split("\n")
ini = next(k for k, l in enumerate(fonte) if l.startswith("# ====") and l.rstrip().endswith("relatorio"))
fim = next(k for k, l in enumerate(fonte) if l.startswith("# ----- pagina 1"))
exec("\n".join(fonte[ini:fim]))

# ---------------- 2) pagina Curva: volta a 1 tela
PID = "a1b2c3d4e5f607182908"
dpag = os.path.join(PAGES, PID)
pj = os.path.join(dpag, "page.json")
d = json.load(open(pj, encoding="utf-8"))
d["height"], d["displayOption"] = 900, "FitToPage"
json.dump(d, open(pj, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
vis = os.path.join(dpag, "visuals")
for n in os.listdir(vis):
    if n.startswith("mc_"):
        shutil.rmtree(os.path.join(vis, n))
pr = os.path.join(vis, "rodape", "visual.json")
dr = json.load(open(pr, encoding="utf-8"))
dr["position"]["y"] = 862
run = dr["visual"]["objects"]["general"][0]["properties"]["paragraphs"][0]["textRuns"][0]
if "MARGEM APÓS IMPOSTOS" not in run["value"]:
    run["value"] += (" MARGEM APÓS IMPOSTOS % = margem de frete menos as deduções (ICMS etc.) lançadas no próprio documento; segue o filtro de cliente e o mês. "
                     "O que não entra na margem por cliente está na página 'Margem: o que não entra'.")
json.dump(dr, open(pr, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# cartao a4 (A Pagar) -> Margem apos impostos %
DOC, DL, LIG, FM = "Documentos", "DreLinhas", "LigacaoContabil", "ForaDaMargem"
p4 = os.path.join(vis, "a4", "visual.json")
d4 = json.load(open(p4, encoding="utf-8"))
d4["visual"]["query"]["queryState"]["Values"]["projections"] = [pm(DOC, "Margem após Impostos %", "Margem após impostos % (segue o cliente)")]
json.dump(d4, open(p4, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# tabela mensal: acrescenta deducoes e margem apos impostos logo depois da margem de frete %
pt = os.path.join(vis, "t_curva", "visual.json")
dt = json.load(open(pt, encoding="utf-8"))
proj = dt["visual"]["query"]["queryState"]["Values"]["projections"]
props = [x["field"].get("Measure", x["field"].get("Column"))["Property"] for x in proj]
if "Margem após Impostos %" not in props:
    k = props.index("Margem de Frete % (bruta)") + 1
    novas = [pm(LIG, "Deduções do Documento", "Deduções do documento"), pm(DOC, "Margem após Impostos", "Margem após impostos"),
             pm(DOC, "Margem após Impostos %", "Margem após impostos %")]
    proj[k:k] = novas
json.dump(dt, open(pt, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ---------------- 3) pagina nova (1 tela): o que nao entra na margem por cliente
NEW = "a1b2c3d4e5f607182919"
dn = os.path.join(PAGES, NEW)
if os.path.exists(dn):
    shutil.rmtree(dn)
pg = Page(NEW, "Margem: o que não entra", "Da margem de frete ao DRE: o que fica fora da margem por cliente (empresa, jul a set)")
pg.slicer("sl_ano", "Ano", 1120, 90, "Calendario", "Ano", "g_ano")
pg.slicer("sl_mes", "Mês", 1220, 360, "Calendario", "Ano-Mês", "g_mes")
pg.cards([(DOC, "Margem de Frete % (bruta)", TEAL, "Margem de frete %"), (LIG, "Deduções do Documento", AMBER, "Deduções do documento (R$)"),
          (DOC, "Margem após Impostos %", TEAL, "Margem após impostos % (soma dos clientes)"),
          (DL, "Margem de Contribuição % (KMM, método DRE)", AMBER, "Margem de contribuição % da empresa (DRE)"),
          (DOC, "Margem Não Ligada a Cliente", AMBER, "Total fora da margem por cliente (R$)")])
fm = [filtro_in("Calendario", "Ano-Mês", ["2026-07", "2026-08", "2026-09"], "f_meses")]
for i in range(5):
    p_ = os.path.join(pg.dir, "visuals", "a%d" % i, "visual.json")
    dd = json.load(open(p_, encoding="utf-8"))
    dd["filterConfig"] = {"filters": fm}
    json.dump(dd, open(p_, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
pg.tabela("t_fora", 20, 210, 1560, 380, [
    pc(FM, "item", "O que NÃO entra na margem por cliente"), pm(FM, "Fora da Margem (valor)", "R$"), pm(FM, "Fora da Margem %", "% da receita"),
    pc(FM, "explicacao", "Por que fica fora")],
    "O que não entra na margem por cliente (empresa) e explica a diferença até a margem de contribuição do DRE", filtros=fm)
pg.texto("leitura", 20, 605, 1560, 245,
         "Como ler: a margem por cliente (página Curva operacional x financeiro) é a margem após impostos: receita dos documentos menos custo de frete e ocorrência e menos as deduções lançadas no próprio documento. "
         "Somando todos os clientes dá a margem após impostos da empresa. A margem de contribuição do DRE é menor porque desconta ainda o que não liga a documento de cliente, listado acima, sem nenhum rateio. "
         "Margem após impostos da empresa + 'Total fora da margem por cliente' = margem de contribuição do DRE (a linha total do quadro e o cartão à direita são o mesmo valor). "
         "Valores calculados com as contas do DRE dentro do modelo, lançamentos do KMM, jul a set. Lançamentos manuais do KMM ainda não chegam ao Athena e podem deslocar a margem do DRE em alguns pontos.",
         "10pt", GRAY, container=pg.box("Leitura"))
pp = os.path.join(PAGES, "pages.json")
meta = json.load(open(pp, encoding="utf-8"))
if NEW not in meta["pageOrder"]:
    meta["pageOrder"].insert(meta["pageOrder"].index("a1b2c3d4e5f607182908") + 1, NEW)
json.dump(meta, open(pp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("ok: curva em 1 tela com margem apos impostos; pagina %s criada" % NEW)
