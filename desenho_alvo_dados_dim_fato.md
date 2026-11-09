# Desenho-alvo dos dados: dimensões, fatos e camadas (rascunho de 20/10/2026)

Objetivo: tirar a regra de negócio e a limpeza de dados de dentro das views e das planilhas, e entregar ao Power BI tabelas materializadas em estrela, mais rápidas de atualizar e mais baratas de consultar. Este documento não cria nada no Athena; é a proposta para aprovar objeto a objeto.

## 1. Diagnóstico (números medidos em 20/10/2026)

| Fonte | Volume | Observação |
|---|---|---|
| `prd_bronze.kmm_listas_contab_lancamentos_incremental` | 157,5 mi de linhas, 7,7 GiB, 43 arquivos | É um log: ~36 versões de cada item |
| Itens distintos (`contabilizacao_id`) | 4,32 mi | Só 0,61 mi (14%) são contas de resultado (3.*) |
| `vw_fato_titulo_receber` / `vw_fato_titulo_pagar` / `vw_fato_baixa_pagar` | 443 mil / 313 mil / 311 mil | Pequenas; o custo é da regra, não do volume |
| `fato_conciliacao_multi_kmm` (hml_gold) | 335 mil linhas, 105 colunas | Regerada à mão (vNN + SET LOCATION), hoje v54 de 13/10 |

Problemas que a estrutura resolve:
1. **Deduplicação a cada consulta.** As views `vw_fato_dre_contabil` e `vw_fato_ligacao_contabil` varrem os 157 mi de linhas a cada atualização do BI.
2. **Regra escondida em view e DAX.** Deduplicação, chaves CT-e/NF/contrato, rateio do custo do contrato, alinhamento por mês: tudo recalculado.
3. **Fotos de planilha dentro do modelo.** Plano de contas do DRE, ajustes manuais e referência do DRE são estáticos e envelhecem.
4. **Lançamentos substituídos no log.** NF de serviço relançada com valor corrigido fica duplicada (R$ 2.703,74 em set/26); nenhuma regra segura resolve sem marca na origem.
5. **Tudo em `hml_gold`.** Os fatos de produção do BI não têm equivalente em `prd_`.

Sobre custo em dinheiro: uma varredura completa do log (7,7 GiB) custa na faixa de centavos de dólar (preço por TB varrido). O ganho real é **tempo de atualização e disputa de recursos com o pipeline**, não a fatura.

## 2. Princípios

- **Estrela para o BI.** Fatos materializados (parquet, particionados por mês) + dimensões conformadas compartilhadas.
- **Tabela larga só onde já existe e funciona** (a conciliação por documento/carga). Não montar uma tabela larga única para tudo: duplica atributos e complica as medidas de cliente e de a pagar.
- **Regra no dado, não no relatório.** Deduplicação, chaves e rateio entram nas camadas silver/gold e são testadas lá.
- **Camadas:** bronze (como veio) → silver (limpo, uma linha por entidade, estado atual) → gold (modelo para consumo).
- **Promoção `hml_` → `prd_`** só depois de bater com os números de validação.

## 3. Fatos

| Tabela alvo | Grão | Origem | Partição | Observação |
|---|---|---|---|---|
| `silver.contab_lancamento_atual` | 1 item contábil (`contabilizacao_id`) | log `_incremental` | mês do lançamento | Última versão do item; ~4,3 mi linhas. Exige marca de lançamento substituído/excluído na origem para resolver as NFs relançadas |
| `gold.fato_contab_resultado` | 1 item de conta de resultado | silver acima, contas `3.*` | mês | ~0,6 mi linhas; substitui o que `vw_fato_dre_contabil` calcula |
| `gold.fato_dre_mensal` | mês × conta × origem × centro de custo | `fato_contab_resultado` | mês | Pequena; alimenta DRE contábil e cascata |
| `gold.fato_documento_contabil` | 1 carga/documento | conciliação + contabilidade | mês de emissão | Substitui `vw_fato_ligacao_contabil` (chave: número + CNPJ + mês; contrato pelo ID no histórico; custo total e rateado) |
| `gold.fato_titulo_receber` | 1 título | `vw_fato_titulo_receber` materializada | mês de emissão | |
| `gold.fato_titulo_pagar` | 1 título | `vw_fato_titulo_pagar` materializada | mês de emissão | |
| `gold.fato_baixa_pagar` | 1 baixa | `vw_fato_baixa_pagar` materializada | mês da baixa | |
| `gold.fato_custo_data` | 1 parcela de custo por data | `vw_fato_custo_data` materializada | mês do custo | Regra: baixa antes de hoje = pago; depois = previsto; desconto no vencimento |
| `gold.fato_conciliacao_multi_kmm` | 1 documento/carga | existente | mês de emissão | Manter; automatizar a regeração quando aprovado |

## 4. Dimensões conformadas

| Dimensão | Chave | Atributos principais | Origem hoje |
|---|---|---|---|
| `dim_calendario` | data | ano, mês, ano-mês, dia útil | tabela do BI |
| `dim_cliente` | grupo do tomador | CNPJ, nome, grupo | colunas soltas nos fatos |
| `dim_filial` | centro de custo | CNPJ, nome, unidade de negócio, UF | KMM (organograma) e texto nos fatos |
| `dim_fornecedor` | código | nome, CNPJ, tipo | colunas soltas |
| `dim_tipo_documento` | docto_id | descrição, natureza | texto nos fatos |
| `dim_conta_dre` | número da conta | descrição, grupo (nível 1), subgrupo (nível 2), ordem, marcas de margem bruta/operacional/repasse | **foto** `DrePlano` (165 contas) |
| `dim_linha_dre` | código da linha | as 14 linhas (ROB a Sobra Contábil), sinal, subtotal | **foto** `DreLinhas` |

## 5. Dados que hoje são planilha e precisam de dono

- **Plano de contas do DRE** (nível 1/2, marcas de margem): propor virar `dim_conta_dre`, mantida pela controladoria com versão.
- **Ajustes manuais do DRE** (R$ 6,34 mi líquidos em jul a set/26: folha, seguro, juros, provisões, reclassificação da receita de frete): propor `fato_ajuste_gerencial`, carregada da planilha da controladoria com data de competência, responsável e versão. Sem isso, a conciliação com o DRE continua dependendo de foto.

## 6. Regras que migram do relatório para o dado

1. Deduplicação da contabilidade por `contabilizacao_id` (e tratamento de lançamento substituído).
2. Chaves: CT-e/NF por número + CNPJ + mês; contrato pelo ID entre colchetes no histórico; fatura pelo número.
3. Rateio do custo do contrato entre as linhas do contrato.
4. Filtros de status: **uniformizar** o filtro de `con_status` (A/S) entre receita e custo, hoje diferente na margem por cliente.
5. Data de corte do caixa (última baixa realizada).

## 7. Migração em fases e critérios de aceite

Cada fase só avança quando a tabela nova **reproduz os números já validados** (diferença zero):

| Fase | Entrega | Teste de aceite |
|---|---|---|
| 1 | `silver.contab_lancamento_atual` | 4,3 mi itens; set/26: receita de CT-e (3.1.1.01) R$ 44.082.724 e custo de contrato (3.1.2.05) R$ 37.087.067 |
| 2 | `fato_contab_resultado` e `fato_dre_mensal` | 590 combinações iguais ao DRE em jul a set; divergentes só as NF de serviço de set |
| 3 | `dim_conta_dre` e `dim_linha_dre` | cascata de set/26: ROB 43.995.688,64; ROL 41.074.177,15; margem 4.677.995,60 (DRE) |
| 4 | `fato_documento_contabil` | set/26: 34.733 de 34.747 CT-e com receita; 99,4% a 99,96% da receita conciliada |
| 5 | Fatos de título/baixa/custo materializados | totais de ago/set iguais aos do BI atual (ex.: faturamento operacional ago R$ 45.696.030,88) |
| 6 | Dimensões de cliente, filial, fornecedor, tipo de documento | filtros do BI sem mudança de resultado |
| 7 | BI aponta para as tabelas novas; views antigas ficam como reserva por um ciclo | comparação lado a lado e rollback pronto |

## 8. Performance no Power BI

- Atualização incremental por período nos fatos grandes (contabilidade, documentos, títulos).
- Relações de estrela com dimensões pequenas; remover colunas de texto repetidas dos fatos.
- Manter as medidas nas tabelas de medidas (`Diretoria`, `DreLinhas`), sem lógica de limpeza.

## 9. Governança

- Objetos novos nascem em `hml_`, com script `aplicar_*` e rollback; promoção para `prd_` após validação.
- Agendamento no Airflow para as cargas incrementais (a conciliação continua manual até aprovação).
- Testes automáticos com os números de aceite acima, rodados a cada carga.
- Documentar donos: dados (pipeline), regras de DRE (controladoria), conciliação (financeiro/controladoria).

## 10. Riscos e decisões em aberto

1. **Marca de lançamento substituído/excluído na origem** (KMM ou carga): sem ela, as NFs relançadas continuam duplicadas.
2. **Dono dos ajustes manuais e do plano de contas do DRE:** definir antes da fase 3.
3. **Onde publicar:** `prd_gold` (60 objetos) ou novo schema por assunto; alinhar com o time de dados.
4. **Maio e junho/26:** recarga da contabilidade (itens inseridos antes de 01/06) para a base ficar completa.
5. **Custo da conciliação regerada à mão:** definir periodicidade e responsável antes de automatizar.
