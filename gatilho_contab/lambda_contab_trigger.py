"""Lambda (Function URL) que inicia o workflow da contabilidade.

Variáveis de ambiente: GLUE_REGION (us-east-1), WORKFLOW_NAME (wf_contab_prd), TOKEN.
Chamada:  <function-url>?acao=contab&token=<TOKEN>&usuario=<nome opcional>
Permissões da role: glue:StartWorkflowRun, glue:GetWorkflowRuns (no workflow) e glue:GetJobRuns (nos jobs do fluxo diário).
"""
import hmac
import html
import os

import boto3

glue = boto3.client("glue", region_name=os.environ.get("GLUE_REGION", "us-east-1"))
WORKFLOW = os.environ["WORKFLOW_NAME"]
TOKEN = os.environ["TOKEN"]

# Jobs do fluxo diário do Airflow: se algum estiver rodando, não inicia (evita reescrever tabelas ao mesmo tempo).
JOBS_FLUXO_DIARIO = ["jdbc_to_bronze", "bronze_to_silver", "silver_to_gold"]


def resposta(codigo, texto):
    corpo = f"<html><body style='font-family:sans-serif'><h3>{html.escape(texto)}</h3></body></html>"
    return {"statusCode": codigo, "headers": {"Content-Type": "text/html; charset=utf-8"}, "body": corpo}


def fluxo_diario_rodando():
    for job in JOBS_FLUXO_DIARIO:
        runs = glue.get_job_runs(JobName=job, MaxResults=5)["JobRuns"]
        if any(r["JobRunState"] in ("STARTING", "RUNNING", "STOPPING", "WAITING") for r in runs):
            return job
    return None


def handler(event, context):
    q = event.get("queryStringParameters") or {}
    if not hmac.compare_digest(q.get("token", ""), TOKEN):
        return resposta(403, "Acesso negado")
    if q.get("acao") != "contab":  # ação fixa; nunca aceitar nome de job pela URL
        return resposta(400, "Ação inválida")

    em_andamento = glue.get_workflow_runs(Name=WORKFLOW, MaxResults=1)["Runs"]
    if em_andamento and em_andamento[0].get("Status") == "RUNNING":
        return resposta(409, "A atualização da contabilidade já está em andamento")

    job = fluxo_diario_rodando()
    if job:
        return resposta(409, f"O fluxo diário está em execução ({job}). Tente quando terminar")

    try:
        run = glue.start_workflow_run(Name=WORKFLOW, RunProperties={"solicitante": q.get("usuario", "")[:80]})
    except glue.exceptions.ConcurrentRunsExceededException:
        return resposta(409, "A atualização da contabilidade já está em andamento")
    return resposta(200, "Atualização da contabilidade iniciada. Código: " + run["RunId"])
