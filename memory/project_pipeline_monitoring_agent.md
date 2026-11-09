---
name: project-pipeline-monitoring-agent
description: Status of the Airflow/Glue/Athena/Power BI monitoring agent project (Fase 1 = alert-only via Telegram)
metadata: 
  node_type: memory
  type: project
  originSessionId: ce4a71f5-3779-4e1b-aa9c-c09ab85f710d
  modified: 2026-08-23T15:13:12.853Z
---

User approved a plan (2026-08-23) for a monitoring agent covering the whole data pipeline (see [[reference_data_pipeline_architecture]]). Plan file: `C:\Users\rodrigo.maia\.claude\plans\eu-gostaria-de-planejar-purrfect-snowflake.md`.

**Phased approach (user's explicit choice, not just a suggestion):**
- **Fase 1 (build now)**: alert-only. Checks 3 sources (Athena `tb_log_exec`/`tb_log_job_exec` for Glue errors, Airflow DAG failures, `Relatorio_Atualizacao_Datasets.xlsx` for Power BI refresh errors) and sends a consolidated Telegram message for anything new (dedup via a local JSON state file of last-notified execution_id/dag_run_id/refresh). Runs as a Claude Code scheduled routine (`/schedule`/`CronCreate`) on this Windows machine (has AWS/VPN gateway access + runs the PowerShell governance scripts already) — deliberately NOT a standalone script, so Fase 2 can extend the same routine instead of a rewrite.
- **Fase 2 (later, only after Fase 1 alerts are validated as reliable)**: same routine proposes known fixes (Airflow task retry — not `trigger_glue_job`'s direct boto3 call, which desyncs Airflow's DAG state; Power BI dataset refresh trigger) and waits for user approval via a Telegram reply before executing.

**Open technical unknown before coding Fase 1's Airflow check**: whether this machine can reach the Airflow metadata Postgres (`172.31.28.247:5432`) directly (VPN/gateway) — if not, must fall back to the Airflow REST API (Simple Auth Manager credentials, not yet located).

**How to apply:** when resuming this work, check the plan file first, then verify Airflow Postgres connectivity as the first implementation step (per the plan's own instructions) before writing the Airflow-status query.
