"""Margem de contribuicao da empresa passa a jan-set/26 (21/10/2026): lancamentos do Postgres (incl. manuais) validados contra o DRE em jan-set.
Mexe so no que e MC da empresa; documentos x contabilidade, margem por cliente e conferencias com a foto do DRE continuam jul-set.
Rodar com Financeiro e Diretoria FECHADOS:  python patch_jan_set_mc.py     Backup: *_backup_20261021_s
"""
import json, os, re, shutil

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = r"C:\project\PowerBIClaudio\14 - Controladoria"
SM = os.path.join(BASE, "Financeiro.SemanticModel")
RP = os.path.join(BASE, "Financeiro.Report")
RD = os.path.join(BASE, "Diretoria.Report")
for pasta in (SM, RP, RD):
    bk = pasta + "_backup_20261021_s"
    if not os.path.exists(bk):
        shutil.copytree(pasta, bk)


def troca(t, a, b, n=1):
    assert t.count(a) == n, (a[:80], t.count(a))
    return t.replace(a, b)


def jl(p):
    return json.load(open(p, encoding="utf-8"))


def jg(p, d):
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


# ---------------- 1) modelo: DreContabil le de 2026-01 ate o mes corrente
p = os.path.join(SM, "definition", "tables", "DreContabil.tmdl")
t = open(p, encoding="utf-8").read()
t = troca(t, "from hml_gold.vw_fato_dre_contabil where mes_lancamento >= '2026-07'",
          "from hml_gold.vw_fato_dre_contabil where mes_lancamento >= '2026-01' and mes_lancamento <= date_format(current_date, '%Y-%m')")
open(p, "w", encoding="utf-8", newline="").write(t)

# ---------------- 2) Curva (Financeiro): cartao a5 e rodape
MESES = ["2026-%02d" % m for m in range(1, 10)]
pa = os.path.join(RP, "definition", "pages", "a1b2c3d4e5f607182908", "visuals")
a5 = os.path.join(pa, "a5", "visual.json")
d5 = jl(a5)
f = next(x for x in d5["filterConfig"]["filters"] if x["name"] == "f_meses")
f["filter"]["Where"][0]["Condition"]["In"]["Values"] = [[{"Literal": {"Value": "'%s'" % m}}] for m in MESES]
d5["visual"]["query"]["queryState"]["Values"]["projections"][0]["displayName"] = "Margem de contribuição % da empresa (jan a set)"
jg(a5, d5)
rd = os.path.join(pa, "rodape", "visual.json")
s = open(rd, encoding="utf-8").read()
s = troca(s, "lançamentos do KMM (jul a set); fica perto da margem do DRE (pode diferir em até cerca de 2 pontos por causa dos lançamentos manuais ainda ausentes no Athena) e não muda com o filtro de cliente.",
          "lançamentos do KMM, inclusive os manuais (jan a set); fecha com a margem do DRE e não muda com o filtro de cliente.")
open(rd, "w", encoding="utf-8").write(s)

# ---------------- 3) pagina 'Margem: o que nao entra' (jul-set): textos
pg = os.path.join(RP, "definition", "pages", "a1b2c3d4e5f607182919", "visuals", "leitura", "visual.json")
s = open(pg, encoding="utf-8").read()
s = troca(s, " Lançamentos manuais do KMM ainda não chegam ao Athena e podem deslocar a margem do DRE em alguns pontos.",
          " Os lançamentos manuais do KMM entram em \\\"(sem origem)\\\" e fazem parte do resultado; esta página compara só jul a set porque a ligação com documentos foi validada nesse período.")
open(pg, "w", encoding="utf-8").write(s)

# ---------------- 4) scripts da Diretoria e do memorando
d = open(os.path.join(AQUI, "build_diretoria.py"), encoding="utf-8").read()
d = troca(d, 'fm = [filtro_in("Calendario", "Ano-Mês", MESES, "f_meses")]',
          'fm = [filtro_in("Calendario", "Ano-Mês", MESES, "f_meses")]\nMESES_MC = ["2026-%02d" % m for m in range(1, 10)]\nfm_mc = [filtro_in("Calendario", "Ano-Mês", MESES_MC, "f_meses_mc")]')
d = troca(d, 'for i in range(5): filtrar(p1, "c92_%d" % i, fm)', 'for i in range(5): filtrar(p1, "c92_%d" % i, fm_mc if i == 1 else fm)')
d = troca(d, '"Margem de contribuição por mês (fórmula do DRE sobre os lançamentos)", cor=TEAL, filtros=fm)',
          '"Margem de contribuição por mês, jan a set (fórmula do DRE sobre os lançamentos)", cor=TEAL, filtros=fm_mc)')
d = troca(d, '"Jul a set/26 (meses validados): faturamento, margem de frete e clientes"',
          '"Margem de contribuição: jan a set/26. Faturamento e clientes: jul a set/26 (meses validados)"')
d = troca(d, "Ela fica perto da margem do DRE, mas pode ficar até cerca de 2 pontos abaixo ou acima porque os lançamentos manuais do KMM (folha, encargos, provisões) ainda não chegam ao Athena. ",
          "Ela fecha com a margem do DRE de janeiro a setembro, porque inclui os lançamentos manuais do KMM (folha, encargos, provisões, reclassificações). ")
open(os.path.join(AQUI, "build_diretoria.py"), "w", encoding="utf-8", newline="").write(d)

m = open(os.path.join(AQUI, "build_memorando.py"), encoding="utf-8").read()
m = troca(m, "Fica em torno de 9% a 10% em jul a set, perto da margem do DRE.", "Fica em torno de 9,5% a 10,8% de janeiro a setembro e fecha com a margem do DRE.")
m = troca(m, "ainda não chegam ao Athena (folha, encargos, provisões). Por isso a margem de contribuição pode diferir da do DRE em até cerca de 2 pontos; a carga completa foi pedida ao time de dados.",
          "agora vêm do Postgres do KMM (folha, encargos, provisões, reclassificações). Com eles a margem de contribuição fecha com a do DRE de janeiro a setembro; sem eles ela oscilaria até 3 pontos.")
m = troca(m, "(regra do DRE, dos lançamentos do KMM, jul a set; pode diferir do DRE em até cerca de 2 pontos por causa dos lançamentos manuais ainda ausentes no Athena)",
          "(regra do DRE, dos lançamentos do KMM inclusive os manuais, jan a set; fecha com o DRE)")
m = troca(m, "lançamentos manuais do próprio KMM (permite editar), como folha, encargos, seguro, juros, provisões e reclassificações de receita. Ainda não chegam ao Athena; a carga completa foi pedida ao time de dados.",
          "lançamentos manuais do próprio KMM (permite editar), como folha, encargos, seguro, juros, provisões e reclassificações de receita. Agora entram na contabilidade lida do Postgres, em \\\"(sem origem)\\\"; a foto do DRE serve só para comparar.")
m = troca(m, "ao lado do DRE e dos lançamentos manuais ausentes no Athena.", "ao lado do DRE (a contabilidade já inclui os lançamentos manuais).")
m = troca(m, "disponível desde 01/05/2026 e confiável em jul a set/26.", "lida do Postgres do KMM, jan a out/26 completa; margem de contribuição validada contra o DRE de jan a set; ligação com documentos validada em jul a set.")
m = troca(m, "não chegam ao Athena (1 item manual contra mais de 11 mil linhas na base do DRE em jul a set). Afetam o resultado contábil e deslocam a margem de contribuição em cerca de -0,2 a +1,7 ponto; carga completa pedida ao time de dados.",
          "agora vêm do Postgres (cerca de 4 mil itens manuais por mês). Eles deslocam a margem de contribuição entre -2,9 e +1,7 ponto por mês; com eles ela fecha com o DRE.")
open(os.path.join(AQUI, "build_memorando.py"), "w", encoding="utf-8", newline="").write(m)
print("ok: DreContabil jan+; a5 e g_mar/c92_1 jan-set; textos atualizados (rodar build_diretoria.py e build_memorando.py diretoria|financeiro em seguida)")
