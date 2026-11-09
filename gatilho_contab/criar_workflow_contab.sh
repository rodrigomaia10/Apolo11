#!/usr/bin/env bash
# Cria o Glue Workflow da contabilidade (bronze -> silver -> gold) em us-east-1.
# NÃO foi executado. Rode no WSL/CloudShell com permissão glue:CreateWorkflow / glue:CreateTrigger.
# Os jobs já têm ENV, FILE_JSON e BUCKET_GLUE como argumentos padrão (conferido em 2026-10-29), então os gatilhos não passam argumentos.
set -euo pipefail
R=us-east-1
WF=wf_contab_prd

# 1 execução por vez no workflow (o próprio Glue recusa a segunda)
aws glue create-workflow --region $R --name $WF \
  --description "Contabilidade: jdbc_to_bronze_contab -> bronze_to_silver_contab -> silver_to_gold_contab" \
  --max-concurrent-runs 1

# Passo 1: começa quando o workflow é iniciado
aws glue create-trigger --region $R --workflow-name $WF --name ${WF}_bronze \
  --type ON_DEMAND \
  --actions JobName=jdbc_to_bronze_contab

# Passo 2: só roda se o bronze terminar com sucesso
aws glue create-trigger --region $R --workflow-name $WF --name ${WF}_silver \
  --type CONDITIONAL --start-on-creation \
  --predicate '{"Logical":"AND","Conditions":[{"LogicalOperator":"EQUALS","JobName":"jdbc_to_bronze_contab","State":"SUCCEEDED"}]}' \
  --actions JobName=bronze_to_silver_contab

# Passo 3: só roda se o silver terminar com sucesso
aws glue create-trigger --region $R --workflow-name $WF --name ${WF}_gold \
  --type CONDITIONAL --start-on-creation \
  --predicate '{"Logical":"AND","Conditions":[{"LogicalOperator":"EQUALS","JobName":"bronze_to_silver_contab","State":"SUCCEEDED"}]}' \
  --actions JobName=silver_to_gold_contab

echo "Workflow $WF criado. Teste: aws glue start-workflow-run --region $R --name $WF"
