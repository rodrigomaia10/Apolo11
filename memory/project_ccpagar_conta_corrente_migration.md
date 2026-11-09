---
name: project-ccpagar-conta-corrente-migration
description: "Migration of the 'Conta Corrente CCPAGAR' Power BI report from ODBC/kmm_prod to Athena"
metadata: 
  node_type: memory
  type: project
  originSessionId: a1cf8380-5784-452a-a02e-9e8947cd6c0d
  modified: 2026-08-21T19:03:06.878Z
---

Migrated `C:\PowerBIClaudio\08 - Contas a Pagar\Conta Corrente CCPAGAR.pbip` (single table `Consulta1`, no measures) from a direct ODBC query against `kmm_prod` Postgres to Athena (DSN `Athena_Cootravale_Producao`). Completed 2026-08-21.

Original query joined `kss.pessoa_juridica` + `kss.pessoa_cliente` (dead join, never selected/filtered) + `kss.pessoa_atributo_dado` (filtered `ATRIBUTO_ID='1032'`, used to pick **one specific** conta corrente per pessoa) + `finan.ccorrente`.

**Key finding — `kss.pessoa_atributo_dado` does not exist anywhere in the DW** (checked `source_kmm`, `prd_bronze`, `hml_bronze`, `silver_kmn`, and the `datalake-glue` repo's `sources/*.json` configs). Almost certainly a Postgres *view* in the source system, not a physical table, so no replication pipeline (neither the wide `source_kmm.datalake_*` mirror nor the Glue `bronze_sources.json`-driven pipeline) ever captured it. See [[reference_source_kmm_schema_not_queryable]] for a related gap in the same investigation.

**Business-logic change made (user-approved, "pode mudar" after explaining the tradeoff):** replaced the attribute-based single-account lookup with a direct `kmm_finan_ccorrente.cod_pessoa = kmm_kss_pessoa.cod_pessoa` join. This is **not equivalent** — ~1,630 pessoas (of 111k) have more than one conta corrente (one has 47), and no available flag (`ativo`, `disp_pagamento`, `disp_recebimento`, `controla_lancamentos`) disambiguates "the CCPAGAR one" — so those pessoas now appear once per linked account instead of once total. Accepted as a known, intentional tradeoff, not a bug.

Created `prd_gold.vw_ccpagar_conta_corrente_pessoa_juridica` (per [[feedback_athena_views_over_pbi_workarounds]], explicitly authorized despite [[feedback_no_new_dw_tables]] via "use tudo do athena, se precisar crie a view"): joins `prd_bronze.kmm_kss_pessoa` (filtered `tipo_pessoa=0` for legal entities) to `prd_bronze.kmm_finan_ccorrente`, deriving `CNPJ_BASICO`/`CNPJ_ORDEM`/`CNPJ_DV` via `substr(cnpj_cpf, ...)` since only `prd_bronze` has a combined `cnpj_cpf` field (no split columns). `NOME_FANTASIA` has no source anywhere in Athena for pessoa jurídica — left as `NULL` in the view, user informed and accepted.

**How to apply:** if this report needs revisiting (e.g. someone asks why a supplier appears more than once), point to this memory rather than re-deriving the cause. If a future migration needs `pessoa_atributo_dado`-style EAV data, don't assume it's just missing from the replication config — check whether it's a view in the source system first.
