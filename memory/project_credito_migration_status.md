---
name: project-credito-migration-status
description: "Status of the \"Análise Exposição de Crédito\" Power BI migration to Athena and its git setup, as of 2026-08-12"
metadata: 
  node_type: memory
  type: project
  originSessionId: 26cde4d5-929c-4fd2-b64a-5e002e11dcbd
  modified: 2026-08-12T16:59:41.082Z
---

The "Análise Exposição de Crédito" Power BI report (file at
`C:\PowerBIClaudio\Analise Exposicao de Credito\`) was migrated from an OLTP ODBC source
(`kmm_prod`, schema `finan.*`) to the Athena Data Warehouse (`hml_gold.fato_exposicao_credito` +
`hml_gold.dim_cliente`, DSN `Athena_Cootravale_Producao`), following the method now captured in
[[powerbi-athena-migration-skill]].

As of 2026-08-12: the `.pbip` project at that path has been synced with the migrated model (via
`database_operations ExportToTmdlFolder`) and committed to a **local** git repo (`git init` +
initial commit `27de4e3`, `.pbix` excluded via `.gitignore`). **No remote is configured yet** — the
plan is to push to a Bitbucket repo, but there is no write-capable Bitbucket integration available:
the project's `.mcp.json` has no Bitbucket server, and the Rovo/Atlassian MCP (`cootravale.atlassian.net`)
is scoped only to Jira and Confluence, not Bitbucket.

**Why this matters:** don't assume the Bitbucket push happened — check `git -C "C:\PowerBIClaudio\Analise Exposicao de Credito" remote -v`
before referencing a remote. The user needs to either push manually or provide a Bitbucket PAT/SSH
credential for a future session to complete this.

**How to apply:** when resuming work on this report or on the Bitbucket/CI-CD deploy pipeline
discussion, pick up from "local commit exists, remote push still pending."
