# Atualização da base de conciliação Multi x KMM (hml_gold)

Tabela real: `hml_gold.fato_conciliacao_multi_kmm` (externa, Parquet GZIP, 92 colunas).
Definição: `conciliacao_multi_kmm.sql` (somente SELECT, ~105 KB).

## Padrão de versionamento

1. Gera uma tabela nova `fato_conciliacao_multi_kmm_vNN` via CTAS.
2. Valida contra a versão anterior.
3. Aponta a tabela real para a nova versão com `ALTER TABLE ... SET LOCATION`
   (Athena não renomeia tabela externa).
4. Versões antigas ficam no S3/Glue; rollback = novo `SET LOCATION`.

## Execução de 2026-10-05 (v38)

- Antes: tabela real → `_v36`; `_v37` (02/10) existia mas não estava em uso.
- CTAS `fato_conciliacao_multi_kmm_v38` a partir do SQL de 29/09. Demorou ~10 min.
- Validação: 92 colunas (igual à v37); 325.251 linhas (v37: 321.602; v36: 317.169);
  distribuição de `status_integracao` proporcional à v37.
- Troca feita; `SELECT count(*)` na tabela real = 325.251.
- Só hml. `prd_gold` não foi alterada (as views `vw_conciliacao_*` de lá não leem esta tabela).

## Incidente v38 -> v39 (2026-10-05)

A v38 (CTAS direto do SQL) quebrou o refresh do Power BI (`HIVE_CURSOR_ERROR: Failed to read Parquet file`).
`SET LOCATION` NÃO muda o schema da tabela real: ela mantém o schema do Glue (tipos/ordem da v36),
e os arquivos da v38 tinham outros tipos (decimal em vez de double/bigint). O `count(*)` passou
porque não lê colunas — só um `select *` completo revela o problema. Rollback para a v36 foi feito.

Correção: v39 = mesmo SQL, mas com `SELECT CAST(...) ... FROM ( <sql> ) t` na ordem e tipos da tabela real:
`kmm_doc_id` -> bigint; `valor_contrato_bruto`, `valor_contrato_liquido`, `valor_titulo_pagar`,
`valor_pago_pagar`, `valor_juro_pagar`, `valor_desconto_pagar` -> double; `varchar(n)` ok como string.
Após `SET LOCATION` na v39, `select * from hml_gold.fato_conciliacao_multi_kmm` rodou OK.
Tabela real hoje -> `_v39` (325.251 linhas). v37 e v38 têm o schema "ruim" (decimal) — não apontar para elas.

**Regra:** a tabela real é sempre `hml_gold.fato_conciliacao_multi_kmm`; a versão nova precisa ter
schema IDÊNTICO (nome, tipo, ordem) ao dela, então o CTAS deve fazer CAST para esses tipos.

## Bug da chave decimal (corrigido na v40, 2026-10-05)

`prd_bronze.kmm_fiscal_conhecimento.num_conhecimento` e `kmm_fiscal_nf_es.num_nota_fiscal` são
`decimal(38,18)`. `CAST(... AS varchar)` gera `100-42246.000000000000000000`, que nunca iguala o
`cte` do Multi (`100-42246`) -> o P1 (serie+numero+CNPJ) não casava NENHUM CT-e; só o P2 (CNPJ+valor+data)
integrava. Resultado: 61% dos CT-e ativos (164 mil) apareciam como `NAO INTEGRADO` sem ser gap real
(98% tinham contrato e título a pagar; 99,97% tinham a chave no KMM).
Fix: `CAST(CAST(num_conhecimento AS bigint) AS varchar)` em `kmm_enriquecido.cte_chave` e
`try_cast(try_cast(kn.num_nota_fiscal AS bigint) AS varchar)` no join de NF.
Efeito v39 -> v40: NAO INTEGRADO 175.383 -> 8.799; INTEGRADO 121.170 -> 295.598.
Ao ver colunas decimal(38,18) no bronze (mudança de tipo na ingestão), sempre passar por bigint antes de montar chave textual.
Pendente: NF tipo NDA ainda 8.147 de 8.179 NAO INTEGRADO (investigar: modelo ND/X1 no KMM).

## Ajustes de NF na v41 (2026-10-05)

- Notas canceladas no KMM (`kmm_fiscal_nf_es.data_cancelamento`) deixaram de ser descartadas no match;
  o desempate prefere o candidato com o MESMO status do Multi (ex: NFS 1-10042 reemitida, carga 225870).
  Cancelado nos dois lados = `INTEGRADO`; status diferente = `DIVERGENCIA`.
- Nova regra P8 (`match_confianca = BAIXA`): numero + modelo + CNPJ + data <= 3 dias + valor <= R$ 0,05, sem serie.
- NDA tratada como NAO FISCAL (decisão do negócio, não analisar) -> `NAO APLICAVEL - DOC NAO FISCAL`.
- Efeito v40 -> v41: NAO INTEGRADO 8.799 -> 733; CANCELADO SEM KMM 1.222 -> 319;
  DIVERGENCIA (cancelado Multi/valido KMM) 88 -> 115; (valido Multi/cancelado KMM) 7 -> 14.
- Tabela real -> `_v41`.

## Fix do documento do transportador em OCORRENCIA (v42, 2026-10-05)

`multi_dbo_t_carga.cli_cgccpf_terceiro` às vezes traz um código interno de 15 dígitos
(`1` + zeros + id, ex. `100000000004315`) em vez do CNPJ/CPF -> 230 pagamentos / 82 transportadores
em 2026 caíam em `NAO INTEGRADO - PESSOA SEM CADASTRO KMM` (carga 209600 era um caso; NÃO era zero à esquerda,
a comparação é por bigint). O documento real está em `multi_dbo_t_cliente.cli_cnpjcpf` (cli_cgccpf é chave única).
Fix em `avulso_multi`: `COALESCE(try_cast(NULLIF(trim(cli.cli_cnpjcpf),'') AS bigint), try_cast(cu.cli_cgccpf_terceiro AS bigint))`
com LEFT JOIN em `multi_dbo_t_cliente`. Efeito v41 -> v42: PESSOA SEM CADASTRO 231 -> 1; INTEGRADO +219; NAO INTEGRADO +11
(pessoas agora achadas, mas sem contrato correspondente — gaps reais de OCORRENCIA). Linhas por tipo inalteradas.
Tabela real -> `_v42`.

## Custo: somar TODOS os títulos do contrato (v43, 2026-10-05)

Um contrato de frete pode ter 2+ títulos a pagar (adiantamento + saldo, mesmo `num_docto`).
`titulo_pagar_por_lancto` pegava só 1 (rn=1) -> custo pela metade (ex.: contrato 199628 = 2 x R$ 600 = R$ 1.200,
BI mostrava R$ 600). Nova CTE `pagar_agregado` soma os títulos distintos por `lancto_id` (estornados só entram se
não houver ativo; data_ref = a do último título). O bloco OCORRENCIA continua usando `titulo_pagar_por_lancto`.
Validação: custo total (linha_custo_carga=SIM, INTEGRADO) R$ 151,8 Mi -> R$ 258,6 Mi, contra R$ 262,6 Mi de contrato bruto;
título = contrato (±1%) em 31.046 -> 49.536 cargas; 17 contratos com título > contrato (R$ 38 mil de excesso).
Receita no BI = só documentos ativos (`con_status` A/S) — cancelados nos dois lados são INTEGRADO mas não geram receita.
Pendente: regra "valor da fatura do contas a receber/pagar, senão operacional" para a receita por documento
(valor_fatura é o total da fatura repetido em cada documento; valor_parcela do vínculo veio vazio na carga 206915).
Tabela real -> `_v43`.

## Receita líquida e margem no BI (2026-10-05)

A fatura do contas a receber traz o valor BRUTO (inclui ICMS). Ex.: CT-e 100-14800 (carga 233269) fatura R$ 7.614,95,
ICMS R$ 913,79 -> receita líquida R$ 6.701,16 (= `vlr_receita_liquida` do fato_operacional) e custo R$ 6.165,06 -> margem 8,0%
(sobre a bruta daria 19%). No modelo `AnaliseDocumentos`: `Receita Bruta` = SUM(valor_documento_kmm); `Receita Documentos`
(líquida) = bruta - valor_icms_kmm - valor_iss_kmm, só INTEGRADO com con_status A/S; `Margem Bruta Total` = líquida - título a pagar
- ocorrência; `Margem Bruta %` = margem / líquida. Total 2026: líquida R$ 351,0 Mi, custo R$ 258,6 Mi, margem 20,6%.
Coluna `Cliente (grupo)` (grupo_tomador, senão nome_tomador) nas tabelas; filtro de Carga sincronizado entre páginas.

## Custo só em documento válido (v44, 2026-10-06)

Contrato/título/pagamento são da carga e valem para os documentos VÁLIDOS. Documento cancelado de carga ativa herdava
o custo (ex.: carga 228292, CT-e 30-24153 cancelado mostrava contrato 220547 / R$ 17.735,34 / pago R$ 14.188,27).
Regra nos blocos CT-e e NF: `situacao_carga = 'ATIVA'` virou `(situacao_carga = 'ATIVA' AND con_status IN ('A','S'))` (36 pontos).
Efeito: CT-e/NF cancelados com contrato 1.189 -> 0. Cargas sem NENHUM documento válido deixam de ter custo no BI
(~R$ 0,6 Mi na v43: 96 CT-e R$ 494,9 mil + 58 NF R$ 107,5 mil) — não há documento para carregar o custo.
Tabela real -> `_v44`.

## Faturas: o que é nível de fatura e o que é nível de documento (2026-10-06)

Verificado no KMM/tabela: a fatura (contas a receber) = soma dos documentos dela (ex.: fatura 412798 = 86 CT-e, R$ 796.295,91 = soma
dos valor_documento_kmm). `valor_fatura`, `valor_juro_receber`, `valor_desconto_receber` e `valor_pago_receber` são da FATURA e se repetem em
cada documento dela na tabela -> nunca somar direto; `valor_icms_kmm`/`valor_iss_kmm` são do DOCUMENTO e somam normalmente.
83% dos documentos têm fatura de 1 documento só (220 mil faturas); 4.047 faturas agrupam 45 mil documentos; 4.280 documentos sem fatura.
Medidas (pasta "5. Faturas", cada fatura contada uma vez: `SUMX(VALUES(num_fatura), MAX(...))` com `KEEPFILTERS(num_fatura <> BLANK())` —
sem o KEEPFILTERS o filtro anula o contexto da linha): Valor Faturado, Juros da Fatura, Descontos da Fatura, Recebido da Fatura,
Saldo em Aberto da Fatura, Faturas (qtd), Documentos Faturados, ICMS dos Documentos, ISS dos Documentos. Total 2026: 226.297 faturas,
R$ 357,46 Mi faturado, R$ 37,3 mil de juros, R$ 4,65 Mi de descontos, R$ 289,3 Mi recebido, ICMS R$ 23,8 Mi, ISS R$ 0,2 Mi.
Página "Faturas" no BI: uma linha por fatura. Receita Documentos = bruta (valor do documento/fatura); Receita Líquida = bruta - ICMS/ISS; margem sobre a líquida.

## Origem do lançamento no KMM: sistema x manual (v45, 2026-10-06)

Nova coluna `usuario_doc_kmm` (93ª, no FIM da tabela) = `user_insert` de quem lançou o documento no KMM: `kmm_fiscal_conhecimento.user_insert`
(CT-e), `kmm_fiscal_nf_es.user_insert` (NF), `kmm_contrato_contrato_transp.user_insert` (ocorrência, contrato avulso); NULL em "SEM DOCUMENTO".
Regra (definida pelo usuário): SISTEMA = `INTEGRADOR_MULTI` + `KSS` (KSS é processo interno do KMM, também é sistema); MANUAL = demais usuários (pessoas).
Título a pagar: mesma regra sobre `usuario_titulo_pagar`. Fatura (contas a receber) é sempre manual (faturamento) — não entra.
2026: documentos ativos integrados 286.609 via sistema (99,8%) x 643 manuais (0,2%); títulos 66.024 via sistema x 353 manuais;
custo R$ 257,4 Mi via sistema x R$ 1,53 Mi manual (99,4%). Manuais por usuário: GABRIELA.CUNHA 440, THIAGO.SILVA 65, LARISSA.SOUZA 51...
COMO SUBIR COLUNA NOVA: `ALTER TABLE hml_gold.fato_conciliacao_multi_kmm ADD COLUMNS (usuario_doc_kmm string)` ANTES do SET LOCATION; no
CTAS, a coluna nova vai no fim do SELECT; o arquivo de tipos (`fato_conciliacao_multi_kmm_v38.txt`) e o schema atual têm 93 colunas.
No modelo do BI a coluna precisa existir no TMDL (`column usuario_doc_kmm ... sourceColumn`); medidas na pasta "6. Origem do Lançamento"
(usam `KEEPFILTERS` no usuário, senão a tabela por usuário repete o total). Página "Origem do lançamento".

## Documento duplicado no Multi: aparece na lista, não duplica receita nem fatura (2026-10-06)

Causa: `multi_dbo_t_carga_cte` tem o mesmo (car_codigo, con_codigo) mais de uma vez (ex.: CT-e 49-3816, con_codigo 892851, carga 231896,
2 linhas iguais; há con_codigo com até 18). O SQL junta `ciot_por_documento` por essa tabela e repete a linha. Na tabela final: 813 CT-e e
6 NF com con_codigo repetido (~970 linhas a mais). Decisão do usuário: a lista de documentos continua mostrando a duplicidade (é dado do Multi);
receita, impostos e fatura contam o documento UMA vez (faturamos uma vez só).
BI: `Receita Documentos`/`Receita Bruta`/`ICMS dos Documentos`/`ISS dos Documentos` = `SUMX(SUMMARIZE(tabela, tipo_analise, kmm_doc_id), MAX(valor))`
(chave = tipo + kmm_doc_id, porque id de CT-e e de NF podem coincidir); `Documentos Faturados` = COUNTROWS(SUMMARIZE(...)); nova medida
`Linhas Duplicadas (Multi)` = linhas - documentos distintos (971). Conferência: fatura 433008 = 188 documentos distintos (189 linhas), soma
dos documentos R$ 551.075,02 = valor da fatura. Receita 2026 caiu R$ 1,73 Mi (375,87 -> 374,13 Mi); margem 20,3%.
Se um dia quiser corrigir na fonte: `SELECT DISTINCT` em `ciot_por_documento` (e checar outros joins por `multi_dbo_t_carga_cte`).

## Gap sem fatura a receber só de documento ativo + "Tipo de Gap" (2026-10-06)

`Gap Sem Fatura a Receber` contava CT-e/NF CANCELADOS (sem fatura por natureza): 13.882 CT-e, só 4.197 ativos. Agora exige `con_status IN {A,S}`
(mesma regra em `Documentos com Gap`): gaps de faturamento a receber 13,9 mil -> 4.266; Total de Gaps 16,5 mil -> ~6,7 mil.
Clicar numa barra de MEDIDA num gráfico só filtra pela categoria (tipo_analise), nunca pelo tipo de gap -> a lista mostrava poucos documentos
(a tabela só filtrava status de integração). Solução: coluna calculada `Tipo de Gap` (prioridade única: Não integrado > Divergência > Sem fatura a
receber > Sem fatura a pagar > Sem carga > Sem gap). Gráfico da Visão Executiva = barra por tipo de documento com série `Tipo de Gap`
(medida Total Documentos); tabela filtra `Tipo de Gap` <> "Sem gap". Cartões continuam por medida e podem se sobrepor (~120 documentos com 2+ gaps).

## Atualização 2026-10-07 (v46)

Rebuild completo com o SQL atual (sem mudança de regra), 93 colunas (schema = tabela real, inclusive `usuario_doc_kmm`). Tabela real -> `_v46`:
329.447 linhas (v45: 326.542); INTEGRADO 299.704; NAO INTEGRADO 837 (v45: 614, documentos novos ainda sem par); PESSOA SEM CADASTRO 0.
Conferência: cargas 228292, 233269 e 236590 corretas. Observação: `max(data_emissao)` = 2026-10-24 (data futura) em v45 e v46 — documento com data de emissão
errada no Multi; vale investigar. Para o BI ver os dados novos: atualizar o `DocumentosFato`.

## Conciliação sistêmica (BI, 2026-10-08)

Página "Conciliação sistêmica" (medidas na pasta "7. Conciliação"). Universo = Documentos Analisados − CANCELADO SEM KMM (documentos que deveriam estar no KMM).
Conciliados via Sistema = INTEGRADO com usuário INTEGRADOR_MULTI/KSS; Conciliados Manuais = INTEGRADO com usuário pessoa; Sem Conciliação = Gap Não Integrado
(sem par no KMM); Divergência é à parte. Fecha: via sistema + manuais + divergência + sem conciliação = universo (v46: 298.704 + 1.000 + 134 + 837 = 300.675).
v46: 99,34% sistêmica, 0,33% manual, 0,28% sem conciliação. Por usuário: `Docs Conciliados (usuário)` e `% do Total Conciliado` (ALL na coluna do usuário);
INTEGRADOR_MULTI 99,0%, KSS 0,7%, GABRIELA.CUNHA 0,2%.

## Regra P8 só para documento ativo (v47, 2026-10-08)

Descoberto na página "Qualidade do casamento" (lista de regra fraca): o P8 (sem série, valor ±R$ 0,05) valia também para NF CANCELADA no Multi e
casava com a nota ATIVA da reemissão -> 38 'DIVERGENCIA - CANCELADO MULTI / VALIDO KMM' falsas (ex.: NF 100-432). Fix: P8 exige
`(nm.con_status IN ('A','S') OR kn.cancelada = 1)`; cancelado do Multi sem nota cancelada no KMM vira 'CANCELADO SEM KMM'.
Efeito isolado (regra 8, Multi cancelado): 38 -> 0; NF 100-432 cancelada = CANCELADO SEM KMM. Tabela real -> `_v47` (331.210 linhas).
Nível do casamento (v46): regra forte 285 mil (95,0%), por contrato/ocorrência 15 mil (4,9%), regra fraca 196 (0,07%).
Pendente investigar: 129 notas do KMM ligadas a 2+ documentos do Multi (NF).

## Reestruturação do BI: Visão geral + DRE + Dicionário (2026-10-08)

Problema: cada página contava "documento" de um jeito (9 contagens diferentes: linhas, analisados, universo, integrados, via sistema, ativos distintos, faturados...).
Solução: uma definição única = CT-e/NF ativo no Multi (con_status A/S), distinto por (tipo_analise, con_codigo), sem "não fiscal / sem documento / inutilizado".
Medidas da escada (pasta "9. Visão Geral"): Docs Ativos no Multi (275.960) = Com Par (275.775) + Sem Par (185); Com Par = Integrados (275.760) + Divergência (15);
Integrados = Faturados (271.764) + Sem Fatura (3.996); Recebidos (quitados) 232.300 (85,5% dos faturados). Conferências (✔/✖, medidas `Conf. *`): escada, conciliação,
fatura = soma dos documentos (tol. 0,5%), custo ≈ contratos (tol. 3%; hoje −1,5%).
Abas: Visão geral, DRE operacional, Integração · sistema x manual / por usuário / qualidade, Faturas, Exceções (gaps; era "Visão Executiva"), Detalhe (oculta),
Conciliados (oculta), Dicionário. DRE = tabela calculada `DRE_Linhas` (DATATABLE só no modelo do Power BI — nada criado no DW) + medidas `DRE Valor` e `DRE % da Líquida`.
DRE v47: receita bruta 378,01 Mi; ICMS/ISS 24,14 Mi; líquida 353,88 Mi; custo de frete 261,68 Mi; ocorrência 20,37 Mi; margem 71,82 Mi (20,3%).
Observação por filial: FLORESTAL sem custo de frete (margem 84,5%) e Juiz de Fora quase sem ocorrência — custo possivelmente não lançado no KMM.
REGRA DO USUÁRIO (2026-10-08): qualquer tabela nova no DW só em `hml_*` e SEMPRE perguntar antes de criar.

## Conciliação com o faturamento operacional (v49, 2026-10-08)

Painel de Faturamento (app.powerbi.com) = `SUM(vw_fato_operacional_painel_filial[vlr_receita_bruta])` filtrado por tipo de documento (COMPL FRETE, CT-e, ND, NFS, NFS-e).
A view (`prd_gold.vw_fato_operacional_painel_filial`) já filtra: con_status='A'; car_situacao NOT IN (18,13); ped_situacao<>2; sem CIOT CANCELADO; sem TRANSBORDO/REUTILIZACAO/
REPASSE(CT-e); oco_anulacao null/0; mod_abreviacao não nulo e fora de DV/OST; tipo_documento fora de CV/OST/NDA/DV; regra has_true/flag_anulacao/max_con_anulacao.
Ponte de setembro/2026 (fecha exato): view c/ filtro de tipos 45.556.478,42 − anulações (operacao_anulacao='S', 80 docs) 274.626,41 − ND 'CVIR / REPASSE DE VALOR CIOT' (16 docs;
filtro inferido, soma exata) 159.324,09 = 45.122.527,92 = painel. Documentos distintos no painel = 45.080.898,77; a diferença (41.629,15) é repetição de linhas na própria view.
DECISÃO DO USUÁRIO: nada é retirado da nossa conta; cada documento mostra se está no faturamento operacional e o motivo. Colunas novas (v49, 99 no total):
`tipo_operacao`, `doc_anulacao`, `con_anulacao_ref`, `vlr_receita_bruta_multi`, `no_painel` (SIM/NAO), `motivo_fora_painel` (ANULACAO, REPASSE DE VALOR CIOT, TIPO DE DOCUMENTO FORA DO PAINEL,
STATUS <> A, CARGA/PEDIDO CANCELADO, CIOT CANCELADO, TRANSBORDO/REUTILIZACAO/REPASSE, OCORRENCIA DE ANULACAO, REGRA DE ANULACAO DA VIEW, SEM TIPO DE OPERACAO).
Ano 2026 (Multi): receita bruta R$ 431,89 Mi; no painel R$ 379,90 Mi (88,0%); fora R$ 51,99 Mi, dos quais NDA/tipos fora do painel 15.652 docs R$ 48,45 Mi; custo de frete dos docs fora R$ 144 mil.
NDA TEM RECEITA (R$ 48 Mi no ano) — fica fora do painel porque a view exclui NDA/CV/OST/DV.
BI: aba "Faturamento operacional" (medidas "11. Faturamento Operacional"); coluna calculada `Situação no Painel`.
ARMADILHA: o relatório tinha um filtro de NÍVEL DE RELATÓRIO (criado pelo usuário em 06/10) escondendo status NAO APLICAVEL (não fiscal, inutilizado, sem documento) — ele não aparece nas consultas DAX
(MCP ignora filtros de relatório), então a tela mostrava menos que o modelo. Movi o filtro para cada página (exceto Faturamento operacional) para a aba mostrar tudo.

## REPASSE no mesmo grupo das demais exclusões (v50, 2026-10-08)

Pedido do usuário: o "REPASSE DE VALOR CIOT" tem de aparecer no mesmo motivo das outras exclusões por texto da operação (a view tem NOT LIKE '%REPASSE%').
`motivo_fora_painel` agora devolve 'TRANSBORDO / REUTILIZACAO / REPASSE' para qualquer tipo de operação que contenha REPASSE, TRANSBORDO ou REUTILIZACAO e esteja dentro da view
(o motivo separado 'REPASSE DE VALOR CIOT' deixou de existir: 76 -> 101 documentos no grupo). Observação técnica: na view o filtro de REPASSE só vale para CT-e
(`AND tipo_documento = 'CT-e'`); os ND de repasse passam pela view e o painel os tira por outro filtro (a soma de set/2026 fecha exata). Tabela real -> `_v50` (99 colunas, 331.210 linhas).

## Passo a passo (próxima versão = v51)

0. Exporte o schema atual da tabela real (`aws glue get-table ... Columns[].[Name,Type]`) e gere o
   SELECT final com `CAST(col AS tipo_real) AS col` nas colunas cujo tipo mudou, na ordem da tabela real,
   envolvendo o SQL: `SELECT <cols> FROM ( <conciliacao_multi_kmm.sql> ) t`.
   (No Windows, `tr -d '\r'` nos arquivos antes de comparar/diff.)

Ambiente: AWS us-east-1, workgroup `cootravale-s3-athena`, database `hml_gold`,
bucket `s3://cootravale-layer-gold/hml/gold/`.

**Atenção:** `~/.aws/config` tem `output = aws` (inválido) e quebra a CLI com
`Unknown output type: aws`. Use `export AWS_DEFAULT_OUTPUT=json` antes dos comandos.

### 1. CTAS

Monte o arquivo com este cabeçalho + o conteúdo do `.sql`:

```sql
CREATE TABLE hml_gold.fato_conciliacao_multi_kmm_v39
WITH (format='PARQUET', parquet_compression='GZIP',
      external_location='s3://cootravale-layer-gold/hml/gold/fato_conciliacao_multi_kmm_v39/') AS
<conteúdo de conciliacao_multi_kmm.sql>
```

A query é grande demais para argumento de linha de comando (`Argument list too long`).
Envie por JSON:

```bash
python -c "import json;q=open('ctas.sql',encoding='utf-8').read();json.dump({'QueryString':q,'WorkGroup':'cootravale-s3-athena','QueryExecutionContext':{'Database':'hml_gold'}},open('ctas.json','w'))"
aws athena start-query-execution --cli-input-json file://ctas.json
aws athena get-query-execution --query-execution-id <id> --query QueryExecution.Status.State
```

Antes de rodar, confirme que o prefixo `.../fato_conciliacao_multi_kmm_v39/` está vazio no S3.

### 2. Validar contra a versão anterior

- Schema idêntico ao da tabela real: nomes, tipos e ordem (`aws glue get-table` nas duas, diff).
- Depois do `SET LOCATION`, rodar `select * from hml_gold.fato_conciliacao_multi_kmm` completo
  (não só `count(*)`); se falhar, rollback imediato para a versão anterior.
- `count(*)`, `count(distinct con_codigo)` e `linha_custo_carga = 'SIM'` próximos da versão anterior.
- Distribuição de `status_integracao` proporcional (sem salto estranho em NAO INTEGRADO).

### 3. Trocar a tabela real

```sql
ALTER TABLE hml_gold.fato_conciliacao_multi_kmm
SET LOCATION 's3://cootravale-layer-gold/hml/gold/fato_conciliacao_multi_kmm_v39/';
```

Conferir: `SELECT count(*) FROM hml_gold.fato_conciliacao_multi_kmm` e
`aws glue get-table ... Table.StorageDescriptor.Location`.

### Rollback

Repetir o `ALTER TABLE ... SET LOCATION` apontando para a versão anterior.

## Notas

- O SQL filtra o ano de 2026 (`year(...) = 2026`) em `doc_multi`, `avulso_multi` e `carga_sem_documento`.
  Na virada do ano, revisar essas janelas.
- Consumo direto desta tabela deve filtrar `linha_custo_carga = 'SIM'` antes de somar custo/margem
  (custo da carga se repete em cada documento).

## Linhas repetidas na view do painel (v51, 2026-10-08)
Autorizado pelo usuário. Colunas novas no fim (101 no total): `qtd_linhas_painel` (bigint, nº de linhas do documento em `prd_gold.vw_fato_operacional_painel_filial`) e `vlr_painel_view` (double, SUM(vlr_receita_bruta) dessas linhas). Fazem a ponte DRE -> painel fechar ao centavo: em set/2026 soma de `vlr_painel_view` por con_codigo (no_painel=SIM, CT-e/NF, A/S) = 45.122.527,92 = painel; documentos distintos = 45.080.898,77; diferença 41.629,15 = 77 docs repetidos na view. Tabela real -> `_v51` (331.262 linhas). Próxima versão = v52.
Medidas da ponte (DocumentosFato, pasta "12. Ponte DRE x Painel"): Ponte 1..8 (DRE, valor Multi x KMM, anulação, regra anulação view, transbordo/repasse, ND não fiscal, sem par KMM, painel distintos).

## Alerta de variação de datas das cargas (v52, 2026-10-09)
Autorizado pelo usuário. Colunas novas no fim (103 no total): `variacao_dias_cargas` (bigint, dias entre a carga mais antiga e a mais nova ligadas ao documento na view do painel, só quando o documento tem 2+ linhas; data = multi_dbo_t_carga.car_data_criacao) e `alerta_variacao_30d` ('SIM' se > 30 dias; NULL para OCORRENCIA/SEM DOCUMENTO). Em 2026: 4 documentos em alerta (2 CT-e, 2 NFS; máx 696 dias = NFS 1-2132, cargas de 2024). Tabela real -> `_v52` (332.174 linhas). Próxima versão = v53.
Descoberta: dos 77 docs repetidos na view, 6 NFS são legítimas (valor KMM = soma das linhas: cada linha é a parte da carga) e 71 CT-e contam a mais (KMM = 1 linha; R$ 75.659,12 no ano). SQL de correção proposto (não aplicado): `vw_fato_operacional_painel_filial_rateio.sql` (rateia só CT-e + alerta > 30 dias).

## Ponte DRE -> Painel fechando todos os meses (2026-10-09)
Conferência com o export do painel de agosto (data.xlsx, 34.831 linhas, R$ 45.696.030,88): a v52, nos docs com no_painel=SIM, soma vlr_painel_view = 45.696.030,88 documento a documento (dados corretos). A diferença de R$ 24.510,60 estava na PONTE: faltavam (a) "Outros motivos fora do painel" (ex.: OCORRENCIA DE ANULACAO, integrados com no_painel=NAO e motivo diferente de ANULACAO/REGRA/TRANSBORDO) e (b) "Outros status no painel" (no_painel=SIM com status_integracao fora de INTEGRADO/NAO INTEGRADO/NAO APLICAVEL*). Medidas: `Ponte 5b Outros motivos fora do painel`, `Ponte 7b Outros status no painel` (Ponte 8 as inclui; Ponte_Linhas agora tem 13 linhas). Com isso jan-out/2026 fecham ao centavo.
O painel (view prd) também NÃO conta ND 'CVIR / REPASSE DE VALOR CIOT' (4 docs, R$ 25.987,58 em ago/2026): confirma o filtro inferido de REPASSE para ND.

## Contas a receber: status por desconto e chave do título (v53, 2026-10-09)
Autorizado pelo usuário. Validação da base KMM (2026): sem duplicidade em contas_receber/amort/juro/desc; títulos quitados fecham pago = valor + juros − desconto ao centavo (203.628 títulos, R$ 314,2 mi). Achados: (1) 24.420 títulos (R$ 25,26 mi) liquidados 100% por desconto sem pagamento apareciam 'EM ABERTO' (saldo já zero) -> novo status `LIQUIDADO POR DESCONTO` (1.544 linhas / 1.089 faturas na v53); (2) o mesmo num_fatura (num_docto) tem VÁRIOS títulos (parcelas) com valores diferentes e cada documento aponta para o seu — as 20 faturas 'QUITADO com saldo' eram artefato de agrupar por num_fatura. Chave correta do título: nova coluna `ids_titulo_receber` (contas_receber_id); (3) `valor_desconto_devolucao_receber` separa desconto marcado como devolução (só 6 títulos / R$ 97 mil no KMM). Colunas novas (105 no total). Tabela real -> `_v53` (332.126 linhas). Próxima versão = v54.

## Views do BI Financeiro (hml_gold, 2026-10-09)
Autorizado pelo usuário (receber + pagar juntos, só em hml). Arquivo: `C:\project\Apolo11\vw_financeiro_titulos.sql`. Views, UMA LINHA POR TÍTULO, a partir de 2025-01-01, fonte prd_bronze.kmm_*:
- `hml_gold.vw_fato_titulo_receber` (431.932 títulos): contas_receber_id, num_docto, parc_docto, tipo_docto, datas, cliente/grupo, filial, valor_titulo, valor_pago, valor_juro, valor_desconto, valor_desconto_devolucao, saldo_aberto, status_pagamento (QUITADO | LIQUIDADO POR DESCONTO | PAGAMENTO PARCIAL | EM ABERTO), prazo_dias, dias_ate_recebimento, vencido, dias_atraso, faixa_aging, qtd_documentos, tem_documento. Filtro: cancelado=0 e data_estorno IS NULL.
- `hml_gold.vw_fato_titulo_pagar` (308.115 títulos): idem para fornecedor, + aprovado, tem_contrato_transporte, dias_ate_pagamento. Filtro: data_estorno IS NULL (não existe campo cancelado).
Validação 2026 receber: 264.832 títulos, R$ 415,46 mi, quitados 203.628 (R$ 314,24 mi, pago R$ 313,67 mi) = base crua. Filial: o mapeamento por centro de custo do KMM só resolve 23 de 271 centros, então a filial vem da tabela de conciliação (receber via kmm_doc_id, pagar via contrato = num_formulario), com fallback no mapa KMM; ficam sem filial ~12% do valor a receber (maioria sem documento) e ~49% do valor a pagar (contratos/títulos sem documento de 2026).
Achado pagar: 27.609 títulos CF (contrato de frete, R$ 47,3 mi em 2026) são baixados 100% por desconto/compensação sem amortização (status LIQUIDADO POR DESCONTO) — o pagamento não passa por amortização desses títulos; confirmar com o financeiro o que é.
Títulos a receber sem documento na conciliação: R$ 4 a 8 mi/mês (tipos TT, CT, AC, NS, AT, NC, NF).
Cuidado ao editar o SQL: não usar ';' em comentário (o corte em script pára no primeiro ';').

## BI Financeiro (PBIP novo, 2026-10-09)
Projeto: `C:\PowerBIClaudio\14 - Controladoria\Financeiro.pbip` (modelo `Financeiro.SemanticModel`, relatório `Financeiro.Report`), gerado por script (`build_financeiro.py` no scratchpad da sessão) no mesmo padrão visual do AnaliseDocumentos. Modelo: `TituloReceber` e `TituloPagar` (importam `hml_gold.vw_fato_titulo_receber/pagar` via ODBC dsn Athena_Cootravale_Producao), `Calendario` (calculada, 2025 a 2031), relacionamentos por data de emissão (ativos) e vencimento (inativos). Medidas por pasta: Faturado, Recebido, Juros, Descontos, Devoluções, Taxa de Recebimento, Saldo em Aberto/Vencido/a Vencer, Vencido > 90 dias, % Vencido, Atraso Médio, Prazo Médio de Recebimento e Concedido, % sem Documento (receber); A Pagar, Pago, Saldo a Pagar, Vencido, Prazo Médio de Pagamento etc. (pagar). Páginas: Visão do mês (a receber), Aging e vencidos (a receber), Contas a pagar.
Validação do modelo carregado: receber 431.932 títulos / R$ 906.202.990,64 / saldo R$ 78.462.690,20; pagar 308.115 / R$ 1.305.474.016,34 / saldo R$ 41.272.092,91 = Athena. Títulos TT com emissão futura (2027 a 2031, R$ 3,9 mi) existem no receber: calendário vai até 2031.
Atenção: o prazo médio de recebimento dos meses recentes é viesado para baixo (só entram títulos já quitados). Faltam as páginas "Descontos e juros" e "Sem documento" (o modelo já tem as medidas).

## BI Financeiro: páginas 4 e 5 (2026-10-09)
Adicionadas "Descontos e juros" e "Títulos sem documento" (gerador `add_paginas_fin.py`, medidas novas % Desconto, Títulos com Desconto, Títulos sem Documento, Saldo sem Documento). Totais 2025+: Descontos R$ 53,74 mi (5,9% do faturado, R$ 51,38 mi deles em títulos liquidados só por desconto, 57.723 títulos), Juros R$ 80,9 mil, Devoluções 0, sem documento R$ 76,71 mi (8,5%, 57.261 títulos, saldo R$ 11,98 mi), pagar baixado por desconto R$ 124,4 mi.
Achado: dos títulos a receber liquidados só por desconto, TT = R$ 32,4 mi (45.222, nenhum com documento), CT = R$ 14,75 mi (2.668, todos com documento), NS = R$ 3,57 mi. TT/AC/AT parecem títulos internos/de compensação e inflam o "Faturado" — confirmar com o financeiro e considerar filtro por tipo_docto no BI.
Cuidado operacional: não abrir o .pbip no Desktop enquanto eu edito os arquivos (aconteceu de subirem duas instâncias; só a do disco novo vale).

## Contas a pagar: BI x tela do sistema, setembro/2026 (2026-10-09)
Usuário viu R$ 72.856.598,89 (export `custo.xlsx`, 15.356 títulos, Nº lançamento = contas_pagar_id) contra R$ 74.086.225,75 no BI (= todos os títulos ativos de emissão em set/2026 no KMM, 15.785). Diferença: 429 títulos ativos (R$ 1.229.626,86), 395 CF parcela 2 do INTEGRADOR_MULTI (R$ 601.771,26) + 34 outros (28 NF quitadas R$ 619.837,26). Não explicada por unidade/empresa/centro de custo, status, contrato (todos aprovados/ativos), campos nulos, hora no vencimento ou data de criação. Lista em `titulos_pagar_set_fora_do_arquivo.csv`. Pendente: usuário conferir na tela o filtro/motivo. A coluna `aprovado` das views é inútil (aprovacao vem nula no KMM para todos).

## Contas a pagar: por que a tela do KMM esconde títulos (set/2026, 2026-10-09)
Dos 429 títulos ativos de setembro que o KMM tem e a tela do usuário não lista (R$ 1.229.626,86), explicados: (1) 394 títulos CF parcela 2 (INTEGRADOR_MULTI), R$ 600.561,26, com `exige_liberacao_pagamento = 1` e SEM registro em `kmm_finan_finan_contas_pagar_liberacao` = bloqueados / não liberados (usuário achou 3 deles em `data_bloqueados.xlsx`); mas há 93 títulos iguais (R$ 77,8 mil) que aparecem na tela, então a tela tem mais um critério de liberação; (2) 28 NF de consultoria/assessoria, histórico 106 + tipo de pagamento 13 (débito), lançadas por JESSICA.CEREGATTI, R$ 619.837,26 — 100% das NF com essa combinação ficam fora da tela (restrição de acesso/histórico); (3) 7 títulos avulsos, R$ 9.228,34, sem causa identificada. Lista da Jessica: `titulos_jessica_setembro.csv` (74 títulos, coluna "Aparece no arquivo").
View `hml_gold.vw_fato_titulo_pagar` ganhou `exige_liberacao`, `valor_liberado` e `status_liberacao` (NAO EXIGE | LIBERADO | LIBERADO PARCIAL | BLOQUEADO). Bloqueados: set/2026 = 487 títulos (R$ 678,4 mil), out/2026 = 1.170 (R$ 1,6 mi). Modelo Financeiro: colunas novas em TituloPagar e medidas `A Pagar Bloqueado`, `Títulos Bloqueados`, `Saldo Bloqueado`.

## Conferência BI x tela do sistema: contas a pagar set/2026 (2026-10-09)
Valor correto na tela do usuário: R$ 73.457.160,15 (a tela mostra os 394 bloqueados). BI = R$ 74.086.225,75. Diferença R$ 629.065,60 = 28 NF histórico 106 + tipo pagto 13 (R$ 619.837,26, lançadas por JESSICA.CEREGATTI) + 7 avulsos (R$ 9.228,34: 4 tributos retidos da NF 2 do mesmo fornecedor R$ 3.228,92, 2 folhas R$ 4.789,42 e 1 contrato Repom R$ 1.210,00). Lista: `titulos_fora_da_tela_setembro.csv`.
Views: `status_liberacao` agora só marca BLOQUEADO se ainda há saldo (1.737 títulos, saldo R$ 2.381.424,39, 1.165 vencidos R$ 1.205.357,33); pagos sem registro de liberação = 'PAGO SEM LIBERACAO REGISTRADA' (860). Adicionados `tipo_docto_descricao` (nomes vindos da tela do contas a pagar: CF contrato de transporte, CR contrato Repom, NF despesas NFT, TR tributo, AT acerto do transportador, DA despesas bancárias, FI financiamento, TT taxa do transportador, JA juros antecipação clientes, AV adto colaborador, FL folha, FR fatura Repom, AF adto fornecedor, CP cotas capital; códigos CT/NS/AC/NC do a receber sem nome) e, no pagar, `cod_historico` e `cod_tipo_pagamento`.
BI Financeiro: página "A pagar bloqueado", filtro "Tipo de documento" em todas as páginas, página "Conferência por tipo de documento", medidas `A Pagar (visão do sistema)` (set = R$ 73.466.388,49) e `A Pagar Restrito na Tela`. Scripts: `add_pagina_bloqueado.py`, `ajusta_tipo_fin.py`.
