"""Alinha build_memorando.py e build_diretoria.py a margem apos impostos por cliente (20/10/2026)."""
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
t = troca(t, 'pm(DOC, "Margem de Frete % (bruta)", "Margem de frete")', 'pm(DOC, "Margem após Impostos %", "Margem após impostos")')
t = troca(t, "Por cliente, a margem de frete: receita menos custo de frete e ocorrência, antes de impostos e repasse, sem rateio nem outras receitas; serve para comparar clientes. ",
          "Por cliente, a margem após impostos: receita menos custo de frete e ocorrência e menos os impostos lançados no próprio documento; fica acima da margem de contribuição porque ainda não desconta repasse, fretes anulados e impostos sem documento. ")
grava("build_diretoria.py", t)

# ---------------- memorando
m = le("build_memorando.py")
m = troca(m, "faturamento, participação e margem de frete de cada cliente (receita menos custo de frete e ocorrência, antes de impostos e repasse). Serve para comparar clientes; a margem de contribuição só existe para a empresa.",
          "faturamento, participação e margem após impostos de cada cliente (receita menos custo de frete e ocorrência e menos os impostos do documento). Serve para comparar clientes; a margem de contribuição do DRE é da empresa.")
m = troca(m, "receita menos custo de frete e ocorrência, antes de impostos e repasse; sem rateio nem outras receitas. Fica em 26% a 28% e só serve para comparar clientes. A margem de contribuição é da empresa e não muda com o cliente.",
          "receita menos custo de frete e ocorrência, antes de impostos e repasse; fica em torno de 19%. Depois dos impostos do documento (margem após impostos) fica em torno de 14%. A margem de contribuição do DRE (cerca de 9%) é da empresa e fecha com a soma dos clientes mais a linha 'não ligado a cliente'.")
m = troca(m, "dois cartões: a margem de contribuição da empresa (regra do DRE, dos lançamentos do KMM, jul a set; pode diferir do DRE em até cerca de 2 pontos por causa dos lançamentos manuais ainda ausentes no Athena) e a margem de frete do cliente selecionado (receita menos custo de frete e ocorrência, antes de impostos e repasse).",
          "dois cartões: a margem de contribuição da empresa (regra do DRE, dos lançamentos do KMM, jul a set; pode diferir do DRE em até cerca de 2 pontos por causa dos lançamentos manuais ainda ausentes no Athena) e a margem após impostos do cliente selecionado (receita menos custo de frete e ocorrência e menos os impostos do documento).")
i = m.index('("Margem por cliente", [')
j = m.index("        ]),", i) + len("        ]),")
m = m[:i] + '''("Margem por cliente", [
            "Receita dos documentos, custo de frete e ocorrência, margem de frete, deduções (impostos) do documento e margem após impostos por cliente, mais um gráfico mensal que respeita o filtro de cliente.",
            ("Regra:", "margem de frete = receita menos custo de frete e ocorrência. Margem após impostos = margem de frete menos as deduções lançadas no próprio documento (ICMS etc.). Sem rateio."),
            ("Fechamento:", "a soma dos clientes (margem após impostos) mais a linha 'não ligado a cliente' (impostos sem documento, fretes anulados, repasse e outras receitas) é a margem de contribuição do DRE."),
        ]),''' + m[j:]
m = troca(m, "margem de frete: receita dos documentos menos custo de frete e ocorrência, antes de impostos e repasse; compara clientes.",
          "margem após impostos: receita dos documentos menos custo de frete e ocorrência e menos os impostos do documento; a soma dos clientes mais a linha 'não ligado a cliente' fecha com a margem de contribuição do DRE.")
m = troca(m, "o DRE não abre por cliente; por cliente usamos a margem de frete, sem ratear custos que não ligam a cliente.",
          "o DRE não abre por cliente; por cliente usamos a margem após impostos e mostramos à parte o que não liga a cliente, sem ratear.")
grava("build_memorando.py", m)
print("textos v3 alinhados")
