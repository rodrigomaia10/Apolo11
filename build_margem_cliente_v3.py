"""Margem apos impostos por cliente (20/10/2026): receita - custo de frete e ocorrencia + deducoes lancadas no proprio documento (ICMS etc.).
Adiciona a coluna deducoes_contabeis_rateadas na LigacaoContabil, medidas novas e reconstroi a pagina 'Margem por cliente'.
Rodar com o Financeiro e a Diretoria FECHADOS:  python build_margem_cliente_v3.py      Backup: *_backup_20261020_n
"""
import json, os, re, shutil, uuid

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = r"C:\project\PowerBIClaudio\14 - Controladoria"
SM = os.path.join(BASE, "Financeiro.SemanticModel")
RP = os.path.join(BASE, "Financeiro.Report")
NL = "\n"
for pasta in (SM, RP):
    bk = pasta + "_backup_20261020_n"
    if not os.path.exists(bk):
        shutil.copytree(pasta, bk)
FMT = '\t\tformatString: "R$"\\ #,##0.00;-"R$"\\ #,##0.00'

# ---------------- 1) LigacaoContabil: coluna + medida de deducoes
pl = os.path.join(SM, "definition", "tables", "LigacaoContabil.tmdl")
t = open(pl, encoding="utf-8").read()
if "column deducoes_contabeis_rateadas" not in t:
    col = ("\tcolumn deducoes_contabeis_rateadas" + NL + "\t\tdataType: double" + NL + "\t\tisHidden" + NL + "\t\tlineageTag: %s" % uuid.uuid4() + NL +
           "\t\tsummarizeBy: none" + NL + "\t\tsourceColumn: deducoes_contabeis_rateadas" + NL + NL)
    k = t.index("\tpartition LigacaoContabil")
    t = t[:k] + col + t[k:]
    a = ", qtd_linhas_contrato from hml_gold.vw_fato_ligacao_contabil"
    assert t.count(a) == 1
    t = t.replace(a, ", qtd_linhas_contrato, deducoes_contabeis_rateadas from hml_gold.vw_fato_ligacao_contabil")
if "measure 'Deduções do Documento'" not in t:
    base = 'LigacaoContabil[tipo_analise] IN {"CT-e", "NF"}, LigacaoContabil[con_status] IN {"A", "S"}, LigacaoContabil[no_painel] = "SIM"'
    soma = "SUM(LigacaoContabil[deducoes_contabeis_rateadas])"
    med = ("\t/// Deduções da receita (ICMS, PIS/COFINS, ISS, menos crédito presumido) lançadas no próprio CT-e/NF, valor negativo. Mesma base do Faturamento Operacional (Painel). Segue o filtro de cliente." + NL +
           "\tmeasure 'Deduções do Documento' = VAR cli = CALCULATETABLE(VALUES(Documentos[grupo_tomador]), REMOVEFILTERS(Calendario)) RETURN IF(ISFILTERED(Documentos[grupo_tomador]), "
           "CALCULATE(%s, %s, TREATAS(cli, LigacaoContabil[grupo_tomador])), CALCULATE(%s, %s))" % (soma, base, soma, base) + NL +
           FMT + NL + "\t\tdisplayFolder: Margem por cliente" + NL + "\t\tlineageTag: %s" % uuid.uuid4() + NL + NL)
    k = t.index("\tcolumn ")
    t = t[:k] + med + t[k:]
open(pl, "w", encoding="utf-8", newline="").write(t)

# ---------------- 2) Documentos: margem apos impostos e linha de fechamento
pd = os.path.join(SM, "definition", "tables", "Documentos.tmdl")
t = open(pd, encoding="utf-8").read()
if "measure 'Margem após Impostos' =" not in t:
    bl = ("\t/// Margem após impostos: receita dos documentos menos custo de frete e ocorrência e menos as deduções lançadas no próprio documento (ICMS etc.). Ainda antes de repasse, anulações e outras receitas, que não ligam a documento. Segue o filtro de cliente." + NL +
          "\tmeasure 'Margem após Impostos' = [Receita dos Documentos (KMM)] - [Custo Operacional] + [Deduções do Documento]" + NL + FMT + NL +
          "\t\tdisplayFolder: Margem por cliente" + NL + "\t\tlineageTag: %s" % uuid.uuid4() + NL + NL +
          "\t/// Margem após impostos dividida pela receita dos documentos." + NL +
          "\tmeasure 'Margem após Impostos %' = DIVIDE([Margem após Impostos], [Receita dos Documentos (KMM)])" + NL + "\t\tformatString: 0.0%" + NL +
          "\t\tdisplayFolder: Margem por cliente" + NL + "\t\tlineageTag: %s" % uuid.uuid4() + NL + NL +
          "\t/// Linha de fechamento: margem de contribuição da empresa (regra do DRE, lançamentos do KMM) menos a soma da margem após impostos de todos os clientes. É o que não liga a cliente: impostos sem documento, fretes anulados, repasse e outras receitas. Não muda com o filtro de cliente." + NL +
          "\tmeasure 'Margem Não Ligada a Cliente' = [Margem de Contribuição Bruta (KMM)] - CALCULATE([Margem após Impostos], REMOVEFILTERS(Documentos[grupo_tomador]))" + NL + FMT + NL +
          "\t\tdisplayFolder: Margem por cliente" + NL + "\t\tlineageTag: %s" % uuid.uuid4() + NL + NL)
    m = re.search(r"^\tcolumn ", t, re.M)
    t = t[:m.start()] + bl + t[m.start():]
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
DOC, DL, LIG = "Documentos", "DreLinhas", "LigacaoContabil"
pg = Page(PID, "Margem por cliente", "Margem de frete e margem após impostos por cliente; a empresa fecha com a margem de contribuição do DRE")
pg.slicer("sl_ano", "Ano", 1120, 90, "Calendario", "Ano", "g_ano")
pg.slicer("sl_mes", "Mês", 1220, 360, "Calendario", "Ano-Mês", "g_mes")
pg.cards([(DOC, "Receita dos Documentos (KMM)", NAVY, "Receita dos documentos"), (DOC, "Custo Operacional", NAVY, "Custo de frete e ocorrência"),
          (DOC, "Margem de Frete % (bruta)", TEAL, "Margem de frete %"), (LIG, "Deduções do Documento", AMBER, "Deduções (impostos) do documento"),
          (DOC, "Margem após Impostos %", TEAL, "Margem após impostos %"),
          (DL, "Margem de Contribuição % (KMM, método DRE)", AMBER, "Margem de contribuição % da empresa (DRE)"),
          (DOC, "Margem Não Ligada a Cliente", AMBER, "Não ligado a cliente (empresa)")])
fm = [filtro_in("Calendario", "Ano-Mês", ["2026-07", "2026-08", "2026-09"], "f_meses")]
pa = os.path.join(pg.dir, "visuals", "a4", "visual.json")
d = json.load(open(pa, encoding="utf-8"))
d["filterConfig"] = {"filters": fm}
json.dump(d, open(pa, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
dm = lambda n, dn=None: pm(DOC, n, dn)
pg.tabela("t_cli", 20, 210, 1560, 440, [
    pc(DOC, "grupo_tomador", "Cliente (grupo)"), dm("Receita dos Documentos (KMM)", "Receita dos documentos"), dm("Custo Operacional", "Custo de frete e ocorrência"),
    dm("Margem de Frete", "Margem de frete"), dm("Margem de Frete % (bruta)", "Margem de frete %"),
    pm(LIG, "Deduções do Documento", "Deduções do documento"), dm("Margem após Impostos", "Margem após impostos"), dm("Margem após Impostos %", "Margem após impostos %")],
    "Margem por cliente: antes e depois dos impostos do documento", ordenar=sort_med(DOC, "Receita dos Documentos (KMM)"))
cat = pc("Calendario", "Ano-Mês", "Mês")
pg.chart("g_pct", "lineChart", 20, 665, 770, 185, cat, [dm("Margem de Frete % (bruta)", "Margem de frete %"), dm("Margem após Impostos %", "Margem após impostos %")],
         "Margem de frete e margem após impostos por mês (respeita o filtro de cliente)", cor=TEAL)
pg.texto("leitura", 810, 665, 770, 185,
         "Como ler: a margem de frete é receita menos custo de frete e ocorrência (antes de impostos). A margem após impostos desconta também as deduções lançadas no próprio documento (ICMS etc.). "
         "O cartão de margem de contribuição é da empresa (regra do DRE) e não muda com o cliente. O cartão 'não ligado a cliente' é o que falta para fechar com o DRE: impostos sem documento, "
         "fretes anulados, repasse (diesel, pneus, seguro, pedágio) e outras receitas. Soma dos clientes (margem após impostos) + essa linha = margem de contribuição do DRE.",
         "10pt", GRAY, container=pg.box("Leitura"))
pp = os.path.join(RP, "definition", "pages", "pages.json")
meta = json.load(open(pp, encoding="utf-8"))
if PID not in meta["pageOrder"]:
    meta["pageOrder"].insert(meta["pageOrder"].index("a1b2c3d4e5f607182914") + 1, PID)
json.dump(meta, open(pp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("ok: modelo e pagina %s atualizados" % PID)
