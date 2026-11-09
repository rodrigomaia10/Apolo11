"""Consolida a margem por cliente DENTRO da pagina 'Curva operacional x financeiro' (20/10/2026) e remove a pagina 'Margem por cliente'.
Cria a tabela ForaDaMargem (o que nao entra na margem por cliente, valores exatos das contas do DRE no modelo) e as medidas.
Rodar com Financeiro e Diretoria FECHADOS:  python build_curva_margem_cliente.py      Backup: *_backup_20261020_q
"""
import json, os, re, shutil, uuid

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = r"C:\project\PowerBIClaudio\14 - Controladoria"
SM = os.path.join(BASE, "Financeiro.SemanticModel")
RP = os.path.join(BASE, "Financeiro.Report")
NL = "\n"
for pasta in (SM, RP):
    bk = pasta + "_backup_20261020_q"
    if not os.path.exists(bk):
        shutil.copytree(pasta, bk)
FMT = '\t\tformatString: "R$"\\ #,##0.00;-"R$"\\ #,##0.00'

# ---------------- 1) tabela ForaDaMargem
SOMA = 'CALCULATE(SUM(DreContabil[valor]), DreContabil[fonte] = "KMM", %s)'
linhas = [
    (1, "Fretes anulados, reemissões e abatimentos da receita",
     "Anulações e reemissões de CT-e/NF e abatimentos lançados no DRE; o documento anulado já saiu do painel.",
     SOMA % 'DrePlano[descricao_dre] IN {"(-) ANULACOES/REEMISSOES", "(-) ABATIMENTOS DA RECEITA"}'),
    (2, "Perdas no recebimento de créditos",
     "Perda contábil de recebíveis; não pertence a um documento do painel.",
     SOMA % 'DrePlano[descricao_dre] = "(-) PERDAS NO RECEBIMENTO DE CRÉDITOS"'),
    (3, "Pedágio e carga/descarga (dispêndios)",
     "Dispêndios de serviço repassados ao cliente; a receita correspondente fica em outras receitas e não no CT-e.",
     SOMA % 'DrePlano[nivel_1] = "INGRESSOS E RECEITAS DE FRETE", DrePlano[margem_bruta] = "X", NOT(DrePlano[descricao_dre] IN {"(-) ANULACOES/REEMISSOES", "(-) ABATIMENTOS DA RECEITA"})'),
    (4, "Seguros, risco, sinistros, avarias e outros custos operacionais",
     "Custos dos serviços prestados que não são frete nem perda de crédito (seguro, gerenciamento de risco, sinistros, avarias, carretas, INSS autônomo etc.).",
     SOMA % 'DrePlano[nivel_1] = "CUSTOS DOS SERVIÇOS PRESTADOS", DrePlano[margem_bruta] <> "", NOT(DrePlano[descricao_dre] IN {"(-) CUSTO FRETES COOPERADOS", "(-) CUSTO FRETES NÃO COOPERADOS", "(-) PERDAS NO RECEBIMENTO DE CRÉDITOS"})'),
    (5, "Frete de não cooperados",
     "Custo de frete pago a transportadores não cooperados; não vem dos contratos ligados ao documento.",
     SOMA % 'DrePlano[descricao_dre] = "(-) CUSTO FRETES NÃO COOPERADOS"'),
    (6, "Impostos sem documento",
     "Deduções da receita no DRE (ICMS, ISS, crédito presumido) menos as deduções que ligam ao CT-e/NF do cliente.",
     'CALCULATE(SUM(DreContabil[valor]), DreContabil[fonte] = "KMM", DrePlano[nivel_1] = "DEDUÇÕES DA RECEITA", DrePlano[margem_bruta] <> "") - CALCULATE([Deduções do Documento], REMOVEFILTERS(Documentos[grupo_tomador]))'),
    (7, "Diferenças de base (receita, custo e repasse líquido)",
     "Receita de frete lançada na contabilidade menos a receita dos documentos, custo de frete contábil menos o custo operacional da conciliação, mais o repasse líquido (diesel, pneus, seguro contra terceiros).",
     '(CALCULATE(SUM(DreContabil[valor]), DreContabil[fonte] = "KMM", DrePlano[descricao_dre] IN {"(+) RECEITA FRETES COOPERADOS", "(+) RECEITA FRETES NAO COOPERADOS"}) - CALCULATE([Receita dos Documentos (KMM)], REMOVEFILTERS(Documentos[grupo_tomador]))) '
     '+ (CALCULATE(SUM(DreContabil[valor]), DreContabil[fonte] = "KMM", DrePlano[descricao_dre] = "(-) CUSTO FRETES COOPERADOS") + CALCULATE([Custo Operacional], REMOVEFILTERS(Documentos[grupo_tomador]))) '
     '+ CALCULATE(SUM(DreContabil[valor]), DreContabil[fonte] = "KMM", DrePlano[nivel_1] = "REPASSE LIQUIDO", DrePlano[margem_bruta] <> "")'),
]
t = ["/// O que NÃO entra na margem por cliente e explica a diferença até a margem de contribuição do DRE (empresa, lançamentos do KMM). Cada linha é uma medida calculada com as contas do DRE no próprio modelo; a soma das linhas é a Margem Não Ligada a Cliente.",
     "table ForaDaMargem", "\tlineageTag: %s" % uuid.uuid4(), ""]
for o, nome, _, expr in linhas:
    t += ["\t/// %s" % nome, "\tmeasure 'Fora M%d' = %s" % (o, expr), FMT, "\t\tdisplayFolder: Fora da margem por cliente", "\t\tisHidden", "\t\tlineageTag: %s" % uuid.uuid4(), ""]
t += ["\t/// Valor da linha selecionada (itens que ficam fora da margem por cliente).",
      "\tmeasure 'Fora da Margem (valor)' = VAR o = SELECTEDVALUE(ForaDaMargem[ordem]) RETURN SWITCH(o, 1, [Fora M1], 2, [Fora M2], 3, [Fora M3], 4, [Fora M4], 5, [Fora M5], 6, [Fora M6], 7, [Fora M7], 8, [Fora M1] + [Fora M2] + [Fora M3] + [Fora M4] + [Fora M5] + [Fora M6] + [Fora M7])",
      FMT, "\t\tdisplayFolder: Fora da margem por cliente", "\t\tlineageTag: %s" % uuid.uuid4(), "",
      "\t/// Linha dividida pela receita dos documentos da empresa.",
      "\tmeasure 'Fora da Margem %' = DIVIDE([Fora da Margem (valor)], CALCULATE([Receita dos Documentos (KMM)], REMOVEFILTERS(Documentos[grupo_tomador])))",
      "\t\tformatString: 0.0%;-0.0%;0.0%", "\t\tdisplayFolder: Fora da margem por cliente", "\t\tlineageTag: %s" % uuid.uuid4(), "",
      "\t/// Confere: total das linhas menos Margem Não Ligada a Cliente. Deve ser zero.",
      "\tmeasure 'Fora da Margem (conferência)' = ([Fora M1] + [Fora M2] + [Fora M3] + [Fora M4] + [Fora M5] + [Fora M6] + [Fora M7]) - [Margem Não Ligada a Cliente]",
      FMT, "\t\tdisplayFolder: Fora da margem por cliente", "\t\tlineageTag: %s" % uuid.uuid4(), "",
      "\tcolumn ordem", "\t\tdataType: int64", "\t\tformatString: 0", "\t\tlineageTag: %s" % uuid.uuid4(), "\t\tsummarizeBy: none", "\t\tsourceColumn: ordem", "",
      "\tcolumn item", "\t\tdataType: string", "\t\tlineageTag: %s" % uuid.uuid4(), "\t\tsummarizeBy: none", "\t\tsourceColumn: item", "\t\tsortByColumn: ordem", "",
      "\tcolumn explicacao", "\t\tdataType: string", "\t\tlineageTag: %s" % uuid.uuid4(), "\t\tsummarizeBy: none", "\t\tsourceColumn: explicacao", "",
      "\tpartition ForaDaMargem = m", "\t\tmode: import", "\t\tsource =", "\t\t\t\tlet",
      "\t\t\t\t    Fonte = #table(type table [ordem = Int64.Type, item = text, explicacao = text], {"]
reg = ['\t\t\t\t        {%d, "%s", "%s"}' % (o, n, e) for o, n, e, _ in linhas]
reg.append('\t\t\t\t        {8, "Total fora da margem por cliente (fecha com o DRE)", "Soma das linhas: margem de contribuição do DRE menos a soma da margem após impostos de todos os clientes."}')
t += [",\n".join(reg), "\t\t\t\t    })", "\t\t\t\tin", "\t\t\t\t    Fonte", "", "\tannotation PBI_ResultType = Table", ""]
open(os.path.join(SM, "definition", "tables", "ForaDaMargem.tmdl"), "w", encoding="utf-8", newline="").write(NL.join(t))
pm_ = os.path.join(SM, "definition", "model.tmdl")
mt = open(pm_, encoding="utf-8").read()
if "ref table ForaDaMargem" not in mt:
    assert mt.count("ref table DrePlano") == 1
    mt = mt.replace("ref table DrePlano", "ref table DrePlano" + NL + "ref table ForaDaMargem")
    open(pm_, "w", encoding="utf-8", newline="").write(mt)

# ---------------- 2) framework de paginas
fonte = open(os.path.join(AQUI, "build_financeiro.py"), encoding="utf-8").read().split("\n")
ini = next(k for k, l in enumerate(fonte) if l.startswith("# ====") and l.rstrip().endswith("relatorio"))
fim = next(k for k, l in enumerate(fonte) if l.startswith("# ----- pagina 1"))
exec("\n".join(fonte[ini:fim]))

# ---------------- 3) pagina Curva: nova secao embaixo
PID = "a1b2c3d4e5f607182908"
dpag = os.path.join(PAGES, PID)
pj = os.path.join(dpag, "page.json")
d = json.load(open(pj, encoding="utf-8"))
d["height"], d["displayOption"] = 1480, "FitToWidth"
json.dump(d, open(pj, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
pg = Page.__new__(Page)
pg.pid, pg.dir, pg.z = PID, dpag, 5000

# rodape para o fim da pagina
pr = os.path.join(dpag, "visuals", "rodape", "visual.json")
dr = json.load(open(pr, encoding="utf-8"))
dr["position"]["y"] = 1440
json.dump(dr, open(pr, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

DOC, DL, LIG, FM = "Documentos", "DreLinhas", "LigacaoContabil", "ForaDaMargem"
fm = [filtro_in("Calendario", "Ano-Mês", ["2026-07", "2026-08", "2026-09"], "f_meses_mc")]
Y0 = 884
pg.texto("mc_titulo", 20, Y0, 1560, 30, "Margem por cliente (jul a set): do frete até o DRE", "15pt", NAVY, True, "Segoe UI Semibold")
pg.texto("mc_sub", 20, Y0 + 30, 1560, 24,
         "Margem de frete = receita menos custo de frete e ocorrência. Margem após impostos = menos as deduções lançadas no próprio documento. A margem de contribuição do DRE é da empresa e não muda com o cliente.",
         "10pt", GRAY)
lista = [(DOC, "Margem de Frete % (bruta)", TEAL, "Margem de frete %"), (LIG, "Deduções do Documento", AMBER, "Deduções (impostos) do documento"),
         (DOC, "Margem após Impostos %", TEAL, "Margem após impostos %"),
         (DL, "Margem de Contribuição % (KMM, método DRE)", AMBER, "Margem de contribuição % da empresa (DRE)"),
         (DOC, "Margem Não Ligada a Cliente", AMBER, "Não ligado a cliente (empresa)")]
wd = round((1560 - 20 * (len(lista) - 1)) / len(lista), 1)
for i, (t_, m_, c_, dn_) in enumerate(lista):
    pg.card("mc_a%d" % i, t_, m_, round(20 + i * (wd + 20), 1), wd, c_, dn_, y=Y0 + 62, h=100)
    p_ = os.path.join(dpag, "visuals", "mc_a%d" % i, "visual.json")
    dd = json.load(open(p_, encoding="utf-8"))
    dd["filterConfig"] = {"filters": fm}
    json.dump(dd, open(p_, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
dm = lambda n, dn=None: pm(DOC, n, dn)
pg.tabela("mc_t_cli", 20, Y0 + 180, 930, 350, [
    pc(DOC, "grupo_tomador", "Cliente (grupo)"), dm("Receita dos Documentos (KMM)", "Receita dos documentos"), dm("Custo Operacional", "Custo de frete e ocorrência"),
    dm("Margem de Frete % (bruta)", "Margem de frete %"), pm(LIG, "Deduções do Documento", "Deduções do documento"),
    dm("Margem após Impostos", "Margem após impostos"), dm("Margem após Impostos %", "Margem após impostos %")],
    "Margem por cliente: antes e depois dos impostos do documento", ordenar=sort_med(DOC, "Receita dos Documentos (KMM)"), filtros=fm)
pg.tabela("mc_t_fora", 970, Y0 + 180, 610, 350, [
    pc(FM, "item", "O que NÃO entra na margem por cliente"), pm(FM, "Fora da Margem (valor)", "R$"), pm(FM, "Fora da Margem %", "% da receita")],
    "O que não entra na margem por cliente (empresa) e explica a diferença até o DRE", filtros=fm)
pg.texto("mc_leitura", 20, Y0 + 545, 1560, 70,
         "Como ler: margem após impostos da empresa (soma dos clientes) + linha 'Total fora da margem por cliente' = margem de contribuição do DRE. As linhas à direita usam as contas do próprio DRE, sem rateio. "
         "O que fica fora: anulações e reemissões, perdas de crédito, pedágio e carga/descarga, seguros e demais custos operacionais, frete de não cooperados, impostos sem documento e diferenças de base entre a contabilidade e a conciliação. "
         "A contabilidade do KMM só está completa de julho a setembro (lançamentos manuais ainda não chegam ao Athena). A tabela de clientes respeita os filtros de ano, mês e grupo da página.",
         "10pt", GRAY, container=pg.box("Leitura"))

# ---------------- 4) remove a pagina separada
OLD = "a1b2c3d4e5f607182918"
dold = os.path.join(PAGES, OLD)
if os.path.exists(dold):
    shutil.rmtree(dold)
pp = os.path.join(PAGES, "pages.json")
meta = json.load(open(pp, encoding="utf-8"))
meta["pageOrder"] = [x for x in meta["pageOrder"] if x != OLD]
json.dump(meta, open(pp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("ok: secao de margem por cliente na Curva; pagina Margem por cliente removida")
