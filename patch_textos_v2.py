"""Alinha build_diretoria.py e build_memorando.py a margem de frete por cliente (sem rateio) e margem de contribuicao da empresa (20/10/2026)."""
import re


def le(n):
    return open(n, encoding="utf-8").read()


def grava(n, t):
    open(n, "w", encoding="utf-8", newline="").write(t)


def troca(t, a, b):
    assert t.count(a) == 1, (a[:90], t.count(a))
    return t.replace(a, b)


# ---------------- Diretoria
t = le("build_diretoria.py")
t = troca(t, '(L, "% Margem de Contribuição do Cliente", TEAL, "Margem de contribuição (lançamentos)")',
          '(DL, "Margem de Contribuição % (KMM, método DRE)", TEAL, "Margem de contribuição (empresa)")')
ic = t.index('p1.chart("g_mar"')
it = t.index('p1.tabela("t_cli"')
antes, meio, depois = t[:ic], t[ic:it], t[it:]
assert meio.count('pm(L, "% Margem de Contribuição do Cliente", "Margem de contribuição")') == 1
meio = meio.replace('pm(L, "% Margem de Contribuição do Cliente", "Margem de contribuição")', 'pm(DL, "Margem de Contribuição % (KMM, método DRE)", "Margem de contribuição")')
assert depois.count('pm(L, "% Margem de Contribuição do Cliente", "Margem de contribuição")') == 1
depois = depois.replace('pm(L, "% Margem de Contribuição do Cliente", "Margem de contribuição")', 'pm(DOC, "Margem de Frete % (bruta)", "Margem de frete")')
t = antes + meio + depois
t = troca(t, "Por cliente, a mesma margem de contribuição, com o que não liga a documento rateado pela receita de cada um; a soma dos clientes fecha com o total. ",
          "Por cliente, a margem de frete: receita menos custo de frete e ocorrência, antes de impostos e repasse, sem rateio nem outras receitas; serve para comparar clientes. ")
grava("build_diretoria.py", t)

# ---------------- memorando
m = le("build_memorando.py")
m = troca(m, '"faturamento, participação e margem de contribuição de cada cliente, com o que não liga a documento rateado pela receita de cada um (a soma dos clientes fecha com o total)."',
          '"faturamento, participação e margem de frete de cada cliente (receita menos custo de frete e ocorrência, antes de impostos e repasse). Serve para comparar clientes; a margem de contribuição só existe para a empresa."')
m = troca(m, '("A margem de contribuição (principal e por cliente)"', '("Duas margens, dois usos"')
m, n = re.subn(r'\("Por cliente:", ".*?"\),',
               '("Margem de frete (por cliente):", "receita menos custo de frete e ocorrência, antes de impostos e repasse; sem rateio nem outras receitas. Fica em 26% a 28% e só serve para comparar clientes. A margem de contribuição é da empresa e não muda com o cliente."),',
               m, count=1, flags=re.S)
assert n == 1
b2 = m.index('p2 = Page("a1b2c3d4e5f607182916"')
ini = m.index('("Margem:", "o cartão principal é a margem de contribuição pela regra do DRE', b2)
fim = m.index('("Fonte:", "Documentos (conciliação Multi x KMM), CustoData, títulos e DreContabil/DreLinhas (lançamentos).")', ini)
m = m[:ini] + '("Margens:", "dois cartões: a margem de contribuição da empresa (regra do DRE, dos lançamentos do KMM, jul a set; pode diferir do DRE em até cerca de 2 pontos por causa dos lançamentos manuais ainda ausentes no Athena) e a margem de frete do cliente selecionado (receita menos custo de frete e ocorrência, antes de impostos e repasse)."),\n            ' + m[fim:]
m = troca(m, '("Fonte:", "Documentos (conciliação Multi x KMM), CustoData, títulos e DreContabil/DreLinhas (lançamentos).")',
          '("Fonte:", "Documentos (conciliação Multi x KMM), CustoData, títulos e DreContabil/DreLinhas.")')
i = m.index('("Margem por cliente", [', b2)
j = m.index("    ], alt=190, passo=200)", i)
m = m[:i] + '''("Margem por cliente", [
            "Receita dos documentos, custo de frete e ocorrência, margem de frete em R$ e em % por cliente, e um gráfico mensal que respeita o filtro de cliente.",
            ("Regra:", "receita menos custo de frete e ocorrência, antes de impostos e repasse. Não entram impostos, anulações, outras receitas (pedágio, descarga), repasse nem rateio; cada valor liga a um documento e a um contrato."),
            ("Leitura:", "serve para comparar clientes. O cartão de margem de contribuição é da empresa (regra do DRE) e não muda com o cliente."),
        ]),
''' + m[j:]
m, n = re.subn(r'\("Margem por cliente:", "margem de contribuição com rateio.*?"\),',
               '("Margem por cliente:", "margem de frete: receita dos documentos menos custo de frete e ocorrência, antes de impostos e repasse; compara clientes."),', m, count=1, flags=re.S)
assert n == 1
m, n = re.subn(r'\("Margem por cliente:", "o DRE não abre por cliente; a margem de contribuição por cliente.*?"\),',
               '("Margem por cliente:", "o DRE não abre por cliente; por cliente usamos a margem de frete, sem ratear custos que não ligam a cliente."),', m, count=1, flags=re.S)
assert n == 1
grava("build_memorando.py", m)
print("textos v2 alinhados")
