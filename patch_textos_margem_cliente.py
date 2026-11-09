"""Alinha build_diretoria.py e build_memorando.py a margem de contribuicao por cliente (20/10/2026)."""
import re

NOVA = "% Margem de Contribuição do Cliente"


def le(n):
    return open(n, encoding="utf-8").read()


def grava(n, t):
    open(n, "w", encoding="utf-8", newline="").write(t)


def troca(t, a, b):
    assert t.count(a) == 1, (a[:80], t.count(a))
    return t.replace(a, b)


# ---------------- Diretoria
t = le("build_diretoria.py")
t = troca(t, '(DL, "Margem de Contribuição % (KMM, método DRE)", TEAL, "Margem de contribuição (lançamentos)")',
          '(L, "%s", TEAL, "Margem de contribuição (lançamentos)")' % NOVA)
t = troca(t, 'pm(DL, "Margem de Contribuição % (KMM, método DRE)", "Margem de contribuição")', 'pm(L, "%s", "Margem de contribuição")' % NOVA)
t = troca(t, 'pm(DOC, "Margem de Frete % (bruta)", "Margem financeira")', 'pm(L, "%s", "Margem de contribuição")' % NOVA)
t = troca(t, "A margem por cliente na tabela é a margem financeira: receita menos custo de frete e ocorrência, antes de impostos e repasse; serve para comparar clientes, não para somar. ",
          "Por cliente, a mesma margem de contribuição, com o que não liga a documento rateado pela receita de cada um; a soma dos clientes fecha com o total. ")
grava("build_diretoria.py", t)

# ---------------- memorando
m = le("build_memorando.py")
m = troca(m, '"faturamento, participação e margem financeira de cada cliente (receita menos custo de frete e ocorrência). Serve para comparar clientes entre si."',
          '"faturamento, participação e margem de contribuição de cada cliente, com o que não liga a documento rateado pela receita de cada um (a soma dos clientes fecha com o total)."')
m = troca(m, '("As duas margens (não confundir)"', '("A margem de contribuição (principal e por cliente)"')
m, n = re.subn(r'\("Margem financeira \(por cliente\):", ".*?"\),',
               '("Por cliente:", "a mesma regra, com o que não liga a documento (contratos de cargas de outros meses, repasse, outras receitas) rateado pela receita líquida de cada cliente. A margem direta, antes do rateio, fica em torno de 24% e só serve para comparar clientes; está na página Margem por cliente do Financeiro."),',
               m, count=1, flags=re.S)
assert n == 1
b2 = m.index('p2 = Page("a1b2c3d4e5f607182916"')
fim = m.index("    ], alt=255, passo=265)", b2)
caixa = '''("Margem por cliente", [
            "Receita líquida (receita mais as deduções dos próprios CT-e e NF), custo direto do contrato, margem direta e margem de contribuição por cliente, jul a set.",
            ("Regra:", "o que não liga a documento de cliente é a margem de contribuição total menos a soma das margens diretas, e é rateado pela receita líquida de cada cliente; a soma dos clientes fecha com o total. O cartão 'teste' deve dar zero."),
            ("Leitura:", "a margem direta serve para comparar clientes; a de contribuição é a comparável ao DRE. A curva respeita o filtro de cliente."),
        ]),
'''
m = m[:fim] + caixa + "    ], alt=190, passo=200)" + m[fim + len("    ], alt=255, passo=265)"):]
b3 = m.index('p3 = Page("a1b2c3d4e5f607182917"')
m, n = re.subn(r'\("Margem financeira \(por cliente\):", ".*?"\),',
               '("Margem por cliente:", "margem de contribuição com rateio do que não liga a documento; a margem direta (receita líquida menos custo direto) compara clientes."),',
               m, count=1, flags=re.S)
assert n == 1
m, n = re.subn(r'\("Margem por cliente:", "é a margem financeira de cada cliente; o DRE não abre por cliente\."\),',
               '("Margem por cliente:", "o DRE não abre por cliente; a margem de contribuição por cliente usa a regra do DRE com rateio do que não liga a documento."),', m, count=1)
assert n == 1
grava("build_memorando.py", m)
print("textos alinhados")
