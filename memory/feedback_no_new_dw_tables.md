---
name: feedback-no-new-dw-tables
description: Never create new tables/views in the Athena DW itself during a PBI migration unless explicitly asked
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c43a3c23-526e-4a61-a376-d49dd62bd6ed
  modified: 2026-10-08T16:08:07.906Z
---

Do not create new tables or views inside the Athena Data Warehouse (any `prd_*`/`hml_*`/`gold`/`silver`
schema) as part of a Power BI migration, even as a workaround (e.g. the `CREATE OR REPLACE VIEW` filter
workaround described in [[powerbi-athena-migration]]'s Passo 5). Creating tables **inside the Power BI
model** that read from *existing* Athena tables via `Odbc.Query` is fine and expected — the restriction
is specifically about not adding new objects to the DW/Athena catalog itself.

**Why:** User interrupted a migration mid-flight with "não crie novas tabelas no dw" right after several
`table_operations Create` calls in Power BI (which only read from pre-existing `prd_gold` tables, no DDL
against Athena). Confirmed via follow-up question: the concern was scoped to Athena/DW objects only —
Power BI-side model tables were fine to keep.

**Reinforced 2026-10-08:** "se for criar tabela no dw, tem que ser no hml, e me pergunte antes para eu autorizar" — any new Athena
table/view goes ONLY in an `hml_*` schema and needs the user's explicit OK first. Exception that is already the standing workflow: the
`hml_gold.fato_conciliacao_multi_kmm_vNN` CTAS rebuilds + SET LOCATION swap ([[project-conciliacao-multi-kmm-workflow]]). Calculated tables
inside the Power BI model (e.g. `DRE_Linhas` DATATABLE of labels) are not DW objects, but say so explicitly when creating them.

**How to apply:** During any [[project_torre_controle_migration]]-style migration, if a proposed step
would need `CREATE TABLE`/`CREATE VIEW` (or any DDL) run against Athena, stop and confirm explicitly with
the user first — do not treat it as a routine step of the skill, even though the skill document presents
the view-workaround as a normal option.
