---
name: feedback-athena-views-over-pbi-workarounds
description: User prefers filtering in an Athena view per-dashboard rather than working around filter issues inside Power BI
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 26cde4d5-929c-4fd2-b64a-5e002e11dcbd
  modified: 2026-08-12T18:34:23.894Z
---

When a Power BI table needs a filtered slice of a larger Athena table/view, default to proposing a
dedicated Athena view (`CREATE OR REPLACE VIEW <schema>.vw_<nome> AS SELECT ... WHERE <condição>`)
that the user creates, rather than building the filter into the Power BI model (M `Table.SelectRows`,
a staging table + DAX calculated table, etc.).

**Why:** during the `Documentos_Sem_Vinculo_De_Cargas` migration ([[powerbi-athena-migration-skill]]),
a real bug was found where the Power BI ODBC/Mashup path silently drops or miscomputes a filter on a
computed Athena column (`Table.SelectRows` in M, and even a `WHERE` in the native SQL text, both gave
wrong row counts — 1,600 instead of the true 3,408 — while the same condition via `run_athena_query`
or raw ODBC in PowerShell was always correct). A staging-table + DAX-calculated-table workaround fixed
it but pulls the full unfiltered table (693k rows) into the model just to filter it back down — wasteful
and inelegant. The user's own habit — "eu já uso assim, fazendo view com o filtro que preciso para cada
dash" — turned out to be the actually-correct fix: hiding the filter inside a server-side view means
Power BI only ever issues a plain unfiltered `select *`, which is the one pattern proven to always work
correctly through this ODBC path.

**How to apply:** for any future Power BI/Athena migration where the report needs a filtered subset of
a bigger table, propose an Athena view first (ask which schema — `prd_gold`/`hml_gold` per this user's
prd_/hml_-only convention) and have the user create it, before reaching for any Power-BI-side filtering
workaround. Only fall back to the staging+calculated-table pattern if creating a view isn't possible.
