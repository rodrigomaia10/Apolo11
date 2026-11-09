"""Cria as paginas de MEMORANDO dentro dos relatorios:
  Financeiro.Report: 3 paginas ("Memorando 1/3: recebimentos e pagamentos", "2/3: conciliacao, contabilidade e DRE", "3/3: estrutura do modelo e regras")
  Diretoria.Report : 1 pagina ("Memorando")
Uso:  python build_memorando.py diretoria     (Desktop da Diretoria fechado)
      python build_memorando.py financeiro    (Desktop do Financeiro fechado)
Cada pagina e so texto (sem campos do modelo). Atualizar o texto quando uma pagina mudar. Revisao: 20/10/2026.
"""
import json, os, shutil, sys

alvo = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
assert alvo in ("diretoria", "financeiro"), "informe: diretoria ou financeiro"
BASE = r"C:\project\PowerBIClaudio\14 - Controladoria"
RP = os.path.join(BASE, "Diretoria.Report" if alvo == "diretoria" else "Financeiro.Report")
AQUI = os.path.dirname(os.path.abspath(__file__))
bk = RP + "_backup_20261020_m"
if not os.path.exists(bk):
    shutil.copytree(RP, bk)

fonte = open(os.path.join(AQUI, "build_financeiro.py"), encoding="utf-8").read().split("\n")
ini = next(i for i, l in enumerate(fonte) if l.startswith("# ====") and l.rstrip().endswith("relatorio"))
fim = next(i for i, l in enumerate(fonte) if l.startswith("# ----- pagina 1"))
exec("\n".join(fonte[ini:fim]))


def memo(pg, nome, x, y, wd, h, titulo, itens, tam="9pt"):
    """caixa com titulo e varios paragrafos; cada item e (rotulo, texto) ou so texto"""
    pars = []
    for it in itens:
        rot, txt = it if isinstance(it, tuple) else (None, it)
        runs = []
        if rot:
            runs.append({"value": rot + " ", "textStyle": {"fontFamily": "Segoe UI", "fontSize": tam, "color": NAVY, "fontWeight": "bold"}})
        runs.append({"value": txt, "textStyle": {"fontFamily": "Segoe UI", "fontSize": tam, "color": GRAY}})
        pars.append({"textRuns": runs, "horizontalTextAlignment": "Left"})
    v = {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": pars}}]}}
    pg.put(nome, x, y, wd, h, v, pg.box(titulo))


def grade(pg, caixas, colunas=2, topo=90, alt=190, passo=200, larg=770):
    for i, (titulo, itens) in enumerate(caixas):
        c, l = i % colunas, i // colunas
        memo(pg, "m%d" % i, 20 + c * (larg + 20), topo + l * passo, larg, alt, titulo, itens)


def registrar(pids, depois):
    pp = os.path.join(RP, "definition", "pages", "pages.json")
    meta = json.load(open(pp, encoding="utf-8"))
    for pid in pids:
        if pid not in meta["pageOrder"]:
            meta["pageOrder"].append(pid)
    json.dump(meta, open(pp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


if alvo == "diretoria":
    pg = Page("d1a2b3c4d5e6f7081903", "Memorando", "O que este relatório mostra, de onde vêm os números e o que ainda está em validação (revisão de 20/10/2026)")
    grade(pg, [
        ("Para que serve", [
            "Visão resumida para decisão: faturamento, margem, concentração de clientes, caixa e prazos. Os detalhes, as conferências e as divergências ficam no relatório da Controladoria (Financeiro).",
            ("Meses:", "só jul, ago e set/26, os meses em que a contabilidade do KMM está completa e conferida com o DRE gerencial."),
        ]),
        ("Página 1: Visão da diretoria", [
            ("Cartões:", "faturamento operacional, margem de contribuição (regra do DRE, calculada dos lançamentos), peso dos 5 maiores clientes, peso do maior cliente e fretes anulados em % da receita."),
            ("Gráficos:", "faturamento x custo de frete por mês e margem de contribuição por mês."),
            ("Tabela de clientes:", "faturamento, participação e margem após impostos de cada cliente (receita menos custo de frete e ocorrência e menos os impostos do documento). Serve para comparar clientes; a margem de contribuição do DRE é da empresa."),
        ]),
        ("Página 2: Caixa e prazos", [
            ("Cartões:", "entradas e saídas dos últimos 30 dias, resultado de 30 e 90 dias, caixa projetado (estimativa pelo ritmo dos últimos 90 dias), vencidos a receber e a pagar, prazos médios e ciclo financeiro."),
            ("Data de corte:", "o cartão no canto superior direito mostra até que dia os dados de caixa chegam. As janelas partem dela."),
            ("Atenção:", "as saídas somam todas as baixas de títulos a pagar (folha, tributos, contratos, empréstimos). Não é o saldo bancário; validar com a tesouraria antes de decidir."),
        ]),
        ("Duas margens, dois usos", [
            ("Margem de contribuição (principal):", "receita líquida menos custos dos serviços, repasse, fretes anulados e abatimentos, pela fórmula do DRE, calculada com os lançamentos do KMM. Fica em torno de 9,5% a 10,8% de janeiro a setembro e fecha com a margem do DRE."),
            ("Margem de frete (por cliente):", "receita menos custo de frete e ocorrência, antes de impostos e repasse; fica em torno de 19%. Depois dos impostos do documento (margem após impostos) fica em torno de 14%. A margem de contribuição do DRE (cerca de 9%) é da empresa e fecha com a soma dos clientes mais a linha 'não ligado a cliente'."),
        ]),
        ("De onde vêm os números", [
            "Títulos, baixas, conciliação de documentos e cargas e lançamentos contábeis do KMM, lidos do Athena (camada gold). A margem do DRE só entra como conferência na Controladoria.",
            ("Selo de confiança:", "mostra quanto da receita está conciliado com a contabilidade."),
            "O relatório usa o mesmo modelo de dados do Financeiro, então os números são os mesmos nos dois.",
        ]),
        ("O que ainda está em validação", [
            ("Caixa:", "o saldo recente negativo precisa ser confirmado com a tesouraria e o extrato bancário."),
            ("Lançamentos manuais do KMM:", "agora vêm do Postgres do KMM (folha, encargos, provisões, reclassificações). Com eles a margem de contribuição fecha com a do DRE de janeiro a setembro; sem eles ela oscilaria até 3 pontos."),
            ("Fora do período:", "maio e junho (conferência contábil incompleta) e outubro (faturamento ainda na versão anterior da conciliação)."),
        ]),
    ], alt=255, passo=265)
    registrar([pg.pid], None)
    print("Memorando da Diretoria criado")
else:
    DATA = "revisão de 20/10/2026"
    p1 = Page("a1b2c3d4e5f607182915", "Memorando 1/3: recebimentos e pagamentos", "Páginas de contas a receber e a pagar, uma linha por título do KMM (%s)" % DATA)
    grade(p1, [
        ("Os 5 números", [
            "Faturado, entradas e saídas de caixa, saldo vencido e ciclo financeiro, com variação contra o mês e o ano anteriores.",
            ("Leitura:", "entradas = títulos a receber baixados no mês; saídas = todo o pago realizado (folha, tributos e contratos), por isso o resultado não é o saldo bancário. Selecione um mês para ver as variações."),
        ]),
        ("Visão do mês (a receber)", [
            "Faturado, recebido e saldo dos títulos a receber; gráficos por filial, por mês de emissão e por situação do pagamento; clientes ordenados pelo saldo em aberto.",
            ("Regra:", "saldo = valor + juros − desconto − recebido. Fonte: vw_fato_titulo_receber (cancelados e estornados fora)."),
        ]),
        ("Aging e vencidos (a receber)", [
            "Quanto está a vencer e quanto está vencido, por faixa (a vencer, 1-30, 31-60, 61-90 e mais de 90 dias), por filial e cliente.",
            ("Regra:", "vencido = saldo maior que zero e vencimento anterior à data da atualização; títulos sem saldo não entram."),
        ]),
        ("Contas a pagar", [
            "Valor, pago, saldo e vencidos dos títulos a pagar, por fornecedor e filial. Fonte: vw_fato_titulo_pagar (estornados fora).",
            ("Atenção:", "com filtro de cliente o a pagar da empresa fica em branco (título a pagar não tem cliente). 'Baixado por desconto' = título sem amortização e saldo zero; em contrato de frete costuma ser compensação."),
        ]),
        ("A pagar bloqueado", [
            "Títulos que exigem liberação de pagamento e ainda não têm valor liberado no KMM, por filial, situação e mês.",
            ("Regra:", "o bloqueado continua somado no total a pagar; aqui ele só é destacado. Parte aparece e parte some em telas do KMM; o BI mostra todos."),
        ]),
        ("Descontos e juros", [
            "Descontos e juros das baixas do contas a receber (sem estornos), % de desconto, devoluções e títulos liquidados só por desconto.",
            ("Regra:", "liquidado só por desconto = título sem pagamento cujo desconto cobre 100% do valor."),
        ]),
        ("Títulos sem documento", [
            "Faturas que não têm CT-e ou nota ligados na conciliação: quanto são, de que tipo e de quem.",
            ("Causas comuns:", "fatura de documento de outro período, título avulso (tipos TT, AC, AT) ou documento fora do Multi. A conciliação cobre só documentos de 2026."),
        ]),
        ("Conferência por tipo de documento", [
            "A pagar e a receber por tipo de documento do título (docto_id), para conferir com a tela do KMM.",
            ("Regra:", "'visão do sistema' tira do a pagar as NF de consultoria (histórico 106 e tipo de pagamento 13), que a tela do usuário não lista."),
        ]),
    ])
    p2 = Page("a1b2c3d4e5f607182916", "Memorando 2/3: conciliação, contabilidade e DRE", "Do faturamento operacional à contabilidade e ao DRE gerencial (%s)" % DATA)
    grade(p2, [
        ("Curva operacional x financeiro", [
            "Compara o faturamento operacional (CT-e e NF do painel, pelo mês de emissão do documento) com o faturado, a vencer, recebido e previsto, e mostra o custo dos contratos por mês (pago, previsto e liquidado por desconto).",
            ("Margens:", "dois cartões: a margem de contribuição da empresa (regra do DRE, dos lançamentos do KMM inclusive os manuais, jan a set; fecha com o DRE) e a margem após impostos do cliente selecionado (receita menos custo de frete e ocorrência e menos os impostos do documento)."),
            ("Fonte:", "Documentos (conciliação Multi x KMM), CustoData, títulos e DreContabil/DreLinhas."),
        ]),
        ("Conferência com a tela", [
            "Ponte entre o total a pagar do BI e a tela do contas a pagar do sistema, em set/26: total do BI R$ 74,09 mi, menos 28 NF de consultoria (R$ 0,62 mi), menos 7 avulsos (R$ 9,2 mil), igual a R$ 73,46 mi da tela.",
            ("Uso:", "explicar por que o BI mostra mais que a tela e listar os títulos que a tela esconde."),
        ]),
        ("Conferência contábil", [
            "Liga cada documento do faturamento operacional à contabilidade do KMM: receita (conta 3.1.1.01) e custo do contrato (conta 3.1.2.05).",
            ("Chaves:", "CT-e e NF por número + CNPJ do tomador + mês; contrato pelo ID que aparece no histórico do lançamento. Fonte: vw_fato_ligacao_contabil."),
            ("Resultado:", "em jul a set a receita contábil cobre 99,4% a 99,96% do faturamento operacional. Out/26 ainda sem contabilidade; maio e junho incompletos."),
        ]),
        ("DRE contábil (só conferência)", [
            "Contabilidade do KMM (contas de resultado) comparada ao DRE gerencial, por mês, conta e origem do lançamento (jul a set). O DRE é uma foto de 20/10/2026, usada só para comparar; nenhum indicador depende dela.",
            ("Situações:", "OK (diferença menor que R$ 1), lançamento manual ausente no Athena (só existe na base do DRE), divergente e fora do período. A tabela do topo mostra o que não bate; hoje são só as NF de serviço de set (R$ 2.703,74 líquido)."),
        ]),
        ("Lançamentos manuais (só conferência)", [
            "Detalhe dos lançamentos que a base do DRE tem e a tabela do Athena não tem (origem em branco): conta, histórico e quem lançou. Foto de 20/10/2026 para jul a set, extraída do BI do DRE; usada só para comparar.",
            ("O que são:", "lançamentos manuais do próprio KMM (permite editar), como folha, encargos, seguro, juros, provisões e reclassificações de receita. Agora entram na contabilidade lida do Postgres, em \"(sem origem)\"; a foto do DRE serve só para comparar."),
        ]),
        ("DRE em cascata (só conferência)", [
            "ROB, ROL, margem de contribuição, resultado operacional, sobra gerencial e sobra contábil calculados com a contabilidade do KMM, ao lado do DRE (a contabilidade já inclui os lançamentos manuais).",
            ("Uso:", "provar que a regra de cálculo está certa. A coluna 'diferença sem ajuste manual' zera em todas as linhas, exceto o efeito das NF de serviço de set. A margem de contribuição da curva usa essa mesma regra, só com a tabela de lançamentos; a foto do DRE serve apenas para comparar."),
        ]),
("Margem por cliente (seção da página Curva operacional x financeiro)", [
            "Receita dos documentos, custo de frete e ocorrência, margem de frete, deduções (impostos) do documento e margem após impostos por cliente, mais um gráfico mensal que respeita o filtro de cliente.",
            ("Regra:", "margem de frete = receita menos custo de frete e ocorrência. Margem após impostos = margem de frete menos as deduções lançadas no próprio documento (ICMS etc.). Sem rateio."),
            ("Fora da margem:", "o quadro à direita lista o que não entra na margem por cliente (anulações e reemissões, perdas de crédito, pedágio e carga/descarga, seguros e demais custos operacionais, frete de não cooperados, impostos sem documento e diferenças de base), com os valores das contas do DRE; a soma dessas linhas mais a margem após impostos dos clientes é a margem de contribuição do DRE."),
        ]),
    ], alt=190, passo=200)
    p3 = Page("a1b2c3d4e5f607182917", "Memorando 3/3: estrutura do modelo e regras", "Fontes, tabelas, relações, atualização e limitações conhecidas (%s)" % DATA)
    grade(p3, [
        ("Fontes de dados (Athena, camada gold)", [
            "Títulos: vw_fato_titulo_receber, vw_fato_titulo_pagar, vw_fato_baixa_pagar (uma linha por baixa) e vw_fato_custo_data (custo dos contratos por data do custo).",
            "Documentos: fato_conciliacao_multi_kmm (conciliação Multi x KMM, versionada à mão; hoje v54, de 13/10).",
            "Contabilidade: vw_fato_ligacao_contabil e vw_fato_dre_contabil, que leem kmm_listas_contab_lancamentos_incremental deduplicada por contabilizacao_id (o log repete cada item várias vezes).",
        ]),
        ("Tabelas do modelo", [
            ("Fatos:", "TituloReceber, TituloPagar, BaixaPagar, CustoData, Documentos, LigacaoContabil e DreContabil. Calendario é a dimensão de datas."),
            ("Medidas:", "Diretoria (caixa, concentração, selo de confiança) e DreLinhas (as 14 linhas do DRE, usadas na conferência)."),
            ("Fotos estáticas, só para comparar:", "DrePlano (plano de contas do DRE), DreAjustesManuais e a referência do DRE dentro de DreContabil. Extraídas do BI do DRE em 19 e 20/10/2026; não atualizam sozinhas e nenhum indicador depende delas."),
        ]),
        ("Relações e filtros", [
            "Cada fato liga ao Calendario pela sua data (emissão, baixa, custo ou mês do lançamento). DreContabil liga ao DrePlano pela conta; DreLinhas é solta e só lista as linhas.",
            ("Filtro de cliente:", "grupo do tomador, via Documentos. Medidas do a pagar da empresa ficam em branco com cliente selecionado; o custo por cliente usa o custo operacional da conciliação ou o custo dos contratos."),
            ("Filial:", "não vale para o custo por data do custo nem para a contabilidade."),
        ]),
        ("Atualização e datas de corte", [
            "Os dados vêm do Athena (DSN Athena_Cootravale_Producao) a cada atualização do relatório. Durante a carga do pipeline, não atualizar: os totais podem vir incompletos.",
            ("Caixa:", "vai até a data de corte (última baixa realizada nos dois lados); as janelas de 30 e 90 dias partem dela."),
            ("Conciliação:", "regerada à mão (atualizar_conciliacao.py); o faturamento operacional só avança quando ela é refeita."),
            ("Contabilidade:", "lida do Postgres do KMM, jan a out/26 completa; margem de contribuição validada contra o DRE de jan a set; ligação com documentos validada em jul a set."),
        ]),
        ("Definições usadas", [
            ("Faturamento operacional:", "receita bruta dos CT-e e NF do painel (status A ou S), cada documento uma vez, pelo mês de emissão."),
            ("Margem de contribuição (principal):", "fórmula do DRE (contas marcadas na margem bruta sobre as marcadas XD) aplicada aos lançamentos do KMM; é a margem da curva e da Diretoria."),
            ("Margem por cliente:", "margem após impostos: receita dos documentos menos custo de frete e ocorrência e menos os impostos do documento; a soma dos clientes mais a linha 'não ligado a cliente' fecha com a margem de contribuição do DRE."),
            ("Saídas de caixa:", "todas as baixas de títulos a pagar (folha, tributos, contratos, empréstimos); não é o saldo bancário."),
        ]),
        ("Limitações conhecidas e pendências", [
            ("Lançamentos manuais do KMM:", "agora vêm do Postgres (cerca de 4 mil itens manuais por mês). Eles deslocam a margem de contribuição entre -2,9 e +1,7 ponto por mês; com eles ela fecha com o DRE."),
            ("NF de serviço de set/26:", "3 notas (856, 866 e 868; R$ 2.703,74) foram lançadas duas vezes no KMM e o log do Athena guarda as duas; só a origem pode corrigir."),
            ("ND sem lançamento:", "32 notas de débito (R$ 261 mil em set) sem lançamento contábil pelo número e CNPJ."),
            ("Caixa:", "saldo recente negativo a validar com a tesouraria."),
            ("Períodos:", "maio e junho (conferência contábil incompleta) e outubro (faturamento defasado até a nova versão da conciliação)."),
            ("Margem por cliente:", "o DRE não abre por cliente; por cliente usamos a margem após impostos e mostramos à parte o que não liga a cliente, sem ratear."),
        ]),
    ], alt=255, passo=265)
    registrar([p1.pid, p2.pid, p3.pid], None)
    print("Memorando do Financeiro criado (3 paginas)")
