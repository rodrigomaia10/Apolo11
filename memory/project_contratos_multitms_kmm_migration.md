---
name: project-contratos-multitms-kmm-migration
description: "In-progress migration/rebuild of the \"Contratos MultiTMS e KMM.pbip\" reconciliation report"
metadata: 
  node_type: memory
  type: project
  originSessionId: 5d86525b-4720-41ff-8189-f79d0a7054df
  modified: 2026-08-13T14:44:50.969Z
---

Migrating/rebuilding the Power BI report "Contratos MultiTMS e KMM" (a reconciliation report that flags contracts/CTes present in MultiTMS but missing or diverging in KMM, and vice versa). Started 2026-08-13.

**Status as of 2026-08-13**: report already reads from Athena via ODBC (DSN `Athena_Cootravale_Producao`), mixing `hml_bronze` (5 of 7 tables) and `prd_bronze` (1 table). User's direction: first check whether a dim/fato (gold) layer already covers this need before touching the model — see [[feedback_prd_over_hml_schema]] for the separate schema-naming rule.

Findings so far:
- `core_gold.dimcontratofreteterceiro`/`fatocontratofreteterceiro` (MultiTMS contract fact) exists but is **~8 months stale** (frozen 2025-11-24) — not usable for this transitory/reconciliation use case.
- `silver_kmn.contrato_contrato_transp` (closest thing to curated KMM data) is also stale (~6 months behind bronze) — not usable either.
- `prd_gold.fato_operacional` (CTe/document grain, NOT the same as unprefixed `gold.fato_operacional` which is viagem-grain) **is fresh (current as of today)** and has `con_codigo`, `cte` (chave), `con_status`, `data_emissao`, `car_codigo_carga_embarcador` — validated replacement candidate for `Ctes_TMS`/`NFse_TMS`.
- For contracts, no fresh gold/fact exists at the right grain — `prd_bronze.multi_dbo_t_contrato_frete_terceiro` (bronze) is the validated source (cft_numero_contrato, cli_cgccpf_terceiro, cft_contrato_frete, cft_data_emissao_contrato).
- KMM contract side: `prd_bronze.kmm_listas_lista_contrato_transp` is a richer flat table (num_formulario, serie_formulario, cnpj_cpf_proprietario_veiculo, data_cancelamento, contrato_quitado, status_codigo) validated as better than the currently-used `kmm_contrato_contrato_transp`.
- Reconciliation key logic validated: match by `cft_numero_contrato = num_formulario` **without** filtering by serie_formulario (filtering to REPOMFRETE/U only produced false positives — 18% "missing" vs real ~0.01%). CNPJ comparison requires LPAD to 11 (CPF) or 14 (CNPJ) digits since `cli_cgccpf_terceiro` is stored as `double` and silently drops leading zeros — raw comparison without padding showed ~23% false divergence, corrected to 1.4% real divergence after padding.
- Still open: validate a KMM-side source for CTe/NFse (currently `kmm_sefaz_documento` + `kmm_sefaz_documento_status`) to pair with the now-validated `prd_gold.fato_operacional` on the Multi side.

**How to apply**: Don't restart this investigation from scratch in a future session — resume from "still open" above. Don't default to a schema swap (hml→prd) as the deliverable; the user explicitly wants the dim/fact/gold layer evaluated first, and only bronze when gold/silver prove stale for this specific transitory use case.
