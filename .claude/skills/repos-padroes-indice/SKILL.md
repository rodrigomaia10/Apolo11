---
name: repos-padroes-indice
description: Indice das skills, agents e regras que ficam na raiz de cada repositorio em C:\project. Use SEMPRE que a tarefa for alterar, ler ou propor mudanca em outro repositorio (datalake-glue, airflow-prod-dags, etc.) a partir de uma sessao aberta em Apolo11, antes de escrever qualquer arquivo nele.
---

# Indice de padroes por repositorio

A sessao do usuario abre em `C:\project\Apolo11`, mas o trabalho passa por varios repositorios. **Skills, agents, roles e regras de cada repositorio ficam na raiz dele** (`<repo>\.claude\...`), nao aqui. A sessao em Apolo11 nao carrega essas skills sozinha: antes de mexer em um repositorio, leia o `SKILL.md` dele (e os agents, se houver) e siga.

| Repositorio | Onde estao as regras | Ler quando |
|---|---|---|
| `C:\project\datalake-glue` | `.claude\skills\etl-datalake-glue-padroes\SKILL.md` | criar/alterar SQL silver/gold, JSON de fontes, jobs Glue, traduzir Athena->Spark, validar deploy |
| `C:\project\airflow-prod-dags` | `.claude\skills\airflow-dags-padroes\SKILL.md` | criar/ler/propor DAG, disparar bronze/silver/gold, encadear a contabilidade |

## Como manter
- Regra nova de um repositorio vai para a skill **dele**, no repo. Em Apolo11 so entra a linha da tabela acima.
- Repositorio novo: criar `.claude\skills\<nome>\SKILL.md` e um `CLAUDE.md` curto (apontando para a skill) na raiz do repo, e acrescentar uma linha aqui.
- `datalake-glue` e `airflow-prod-dags` ja tem `CLAUDE.md` na raiz, para sessoes abertas direto neles.
- Conduta que vale para todos: **testes sempre em `hml`, nunca em `prd`** (executar job/DAG/DDL em prd so pelo deploy do usuario); commit/push so a pedido; nao editar DAG/repo de orquestracao nem criar recurso na AWS sem pedido explicito (perguntar quando a frase for ambigua).
