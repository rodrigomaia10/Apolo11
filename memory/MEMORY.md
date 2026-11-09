# Memory Index

- [Generic reusable skills preference](feedback_generic_reusable_skills.md) — write harness docs as parameterized skills, not tied to one BI's tables/measures
- [Crédito migration status](project_credito_migration_status.md) — pbip migrated + local git commit done, Bitbucket remote push still pending
- [Rovo/Atlassian MCP scope](reference_rovo_atlassian_scope.md) — Jira/Confluence only, no Bitbucket access
- [Prefer Athena views](feedback_athena_views_over_pbi_workarounds.md) — filter in a view server-side, not inside Power BI
- [Prefer prd_ over hml_ schema](feedback_prd_over_hml_schema.md) — never source from hml_ if a prd_ equivalent exists
- [Contratos MultiTMS/KMM migration](project_contratos_multitms_kmm_migration.md) — in-progress fact/gold-first rebuild, resume from "still open"
- [Torre de Controle docs](reference_torre_controle_docs.md) — ER diagram + best-practices doc at C:\PowerBIClaudio for this BI
- [No new DW tables](feedback_no_new_dw_tables.md) — never CREATE TABLE/VIEW in Athena during a migration unless explicitly asked; PBI-side model tables reading existing DW tables are fine
- [Torre de Controle migration status](project_torre_controle_migration.md) — restarting Fases 1-4 (all work lost when PBI Desktop closed unsaved), see save-before-close feedback
- [Save before closing PBI Desktop](feedback_pbi_desktop_save_before_close.md) — always get user to Ctrl+S before asking them to close/reopen Desktop; unsaved XMLA changes vanish
- [CCPAGAR Conta Corrente migration](project_ccpagar_conta_corrente_migration.md) — done 2026-08-21; pessoa_atributo_dado gap resolved via cod_pessoa join (business-logic tradeoff, user-approved)
- [source_kmm schema not queryable](reference_source_kmm_schema_not_queryable.md) — Athena source_kmm.datalake_* tables list fine but SELECT fails; use prd_bronze/hml_bronze kmm_* instead
- [Data pipeline architecture](reference_data_pipeline_architecture.md) — Airflow EC2/Glue/Athena log tables/PowerShell governance repo locations + known bugs
- [Pipeline monitoring agent](project_pipeline_monitoring_agent.md) — Fase 1 (Telegram alert-only) plan approved 2026-08-23, resume from Airflow connectivity check
- [Conciliação Multi x KMM workflow](project_conciliacao_multi_kmm_workflow.md) — vNN CTAS + SET LOCATION in hml_gold (schema must match), painel bridge closes all months, data pitfalls, PBIP/MCP tips; live v53, next v54
