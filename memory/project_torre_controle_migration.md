---
name: project-torre-controle-migration
description: Status of the Central Torre de Controle PBI migration from legacy SQL Server/Azure SQL to Athena prd_gold
metadata: 
  node_type: memory
  type: project
  originSessionId: c43a3c23-526e-4a61-a376-d49dd62bd6ed
  modified: 2026-08-17T20:14:39.700Z
---

Migrating `C:\PowerBIClaudio\Central Torre de Controle` (pbip) off legacy ODBC sources
(`hs132.scp.tec.br,12143`/ATSSmartWeb and `sql-mg-nst-core-eus-prd-bi.database.windows.net`/
sqldb-cootravale-prd) onto Athena `prd_gold`/`prd_silver`, full-report scope (not just GPS core).
Full plan at `C:\Users\rodrigo.maia\.claude\plans\vast-sleeping-conway.md`. See
[[reference_torre_controle_docs]] for the ER/architecture doc, [[feedback_no_new_dw_tables]] for a hard
constraint (never create tables/views in Athena itself), and [[feedback_pbi_desktop_save_before_close]]
for why this migration had to be redone from scratch twice.

**Status as of 2026-08-16 (redone after 2 full data-loss incidents — see below):**
- **Fases 1–4 — DONE and validated**, third time recreating. Tables in the model (all Import via
  `Odbc.Query` DSN `Athena_Cootravale_Producao`, no DDL against Athena):
  - Fase 1 (núcleo GPS): `fato_viagem`, `fato_coleta_entrega`, `dim_filial`, `dim_cliente`,
    `dim_cooperado`, `dim_veiculo` + 8 sk_*-based relationships. `dim_filial`'s M query excludes
    `nome_origem` in `('I_TAJAI (inativo/duplicado)', 'TANGARA DA SERRA')` from the start now (matches
    legacy `_dFiliais` behavior model-wide — the earlier "fix in Fase 5" plan is now moot since it's
    baked into the source query directly).
  - Fase 2 (Camera/CargasMulti): source is `prd_silver.operacional_por_carga` (grain=1 row per
    `car_codigo`) joined with `prd_silver.carga_ocorrencia` (`oco_codigo=33`) for Camera. Created
    `CargasMulti_novo`, `Camera_novo`, related to `dim_filial` via `ccv_codigo`.
  - Fase 3 (Integracao/Usuarios): `silver_multi.dbo_t_carga_dados_transporte_integracao` is STALE
    (frozen ~2026-02-19) — bypassed it for `prd_bronze.multi_dbo_t_carga_dados_transporte_integracao`
    (fresh) + `prd_bronze.multi_dbo_t_carga_carga_integracao` + `prd_silver.operacional_por_carga`.
    **Worth flagging to whoever owns the DW ETL** — other `silver_multi` tables may have the same
    staleness bug. Created `Integracao_novo`, `Usuarios_novo` (latter from
    `prd_bronze.atss_dbo_view_alerta` joined to a per-viagem MIN() aggregate of
    `prd_bronze.atss_dbo_view_viagem`). Accepted simplification: `Integracao_novo.mensagem_geral` drops
    the legacy JSON-parsing branch (`ISJSON`/`JSON_VALUE`) for structured error messages.
  - Fase 4: `Tabela_novo` and `zz_TabelaValidacaoIntegracoes_novo` as calculated (DAX) tables over the
    new tables.
  - Row counts fluctuate slightly between recreation attempts (natural data growth — Athena keeps
    ingesting) but are always within ~0.5–3% of the legacy live numbers, consistent across every
    validation pass. Business-logic spot checks (houve_espelhamento split, TemJustificativa/
    TemExcessoVelocidade/TemCamera counts) also consistently in the same ballpark.
- **Not started yet:** Fase 5 (rewire relationships/measures off old tables onto the `_novo` ones,
  cleanup — retire `Camera`/`CargasMulti`/`Integracao`/`Usuarios`/`Tabela`/`zz_TabelaValidacaoIntegracoes`
  originals; `Usuarios_novo`/`Integracao_novo` don't have date-table/dim relationships wired yet, unlike
  Fase 1/2 tables). The ~22 measures to rewrite/recreate onto new tables were drafted in-conversation
  but not yet applied — see conversation history for the full DAX (fato_viagem gets _Sucesso/
  _%Espelhamento/_TotalCargas_Esp/_JornadaAdequada/_%Jornada/_JornadaNaoAderente/_totalViagemAdequada/
  _%VeloAdequada/_CargasExcessoVelocidade/_TotalCargas; fato_coleta_entrega gets _TotalColetapraz/
  _TotalEntregapraz; Integracao_novo gets _Total Sucesso/_%Sucesso; Usuarios_novo needs a computed
  column `_Tempo_Alerta` + measure _Média_Alerta_Tempo; Tabela_novo/zz_novo get straight column-name-
  compatible copies of the original 7+1 measures; dim_filial gets 7 thin-wrapper measures matching the
  old `_dFiliais` ones).

**Critical operational gotchas hit during this migration (generically useful beyond this project):**
1. **[[feedback_pbi_desktop_save_before_close]]** — closing PBI Desktop without Ctrl+S first discards
   ALL unsaved XMLA-driven model changes. This happened TWICE on this migration (once to clear a stuck
   Mashup cache, once for an unclear/unconfirmed reason), wiping out Fases 1–4 each time.
2. **New gotcha, not yet in the skill doc: after deleting/recreating a dimension table that other tables
   have relationships to (or after recreating several interdependent tables/relationships in one
   session), calculated tables/DAX queries that traverse those relationships can fail with
   "a relação... não contém dados porque precisa ser recalculada" (relationship needs Process Recalc)
   even though `table_operations Get`/`RefreshWithXMLA` report `state: Ready`/no error — the refresh
   silently doesn't fix it, and the calculated table's partition stays stuck at `state: CalculationNeeded`
   forever (modifiedTime updates, data doesn't). **Fix:** run
   `partition_operations RefreshWithXMLA` with `refreshType: "Calculate"` explicitly listing ALL the
   tables involved in the affected relationships (both fact and dimension sides) — a plain
   `table_operations RefreshWithXMLA` on just the calculated table is not enough. Diagnose by running the
   calculated table's DAX body directly as an ad-hoc `EVALUATE` query (wrapped in `CALCULATETABLE`/`TOPN`
   to limit rows) via `dax_query_operations Execute` — the real DAX engine error message
   ("relação... precisa ser recalculada") only surfaces this way; `table_operations Get` on the stuck
   partition just shows `errorMessage: ""`.

**Fase 5 progress (2026-08-16, same session as the redo):**
- Created 30 measures on the new tables (had to suffix every one with `_novo` — TOM measure names must
  be unique across the WHOLE model, not per table, and all 30 collided with legacy names).
- Did a "rename takeover" for the 6 tables with a clean 1:1 legacy mapping: deleted old `Camera`,
  `CargasMulti`, `Integracao`, `Usuarios`, `Tabela`, `zz_TabelaValidacaoIntegracoes`, renamed their
  `_novo` counterparts to take the exact old names, renamed columns/measures to match legacy naming
  exactly. Zero visual JSON edits needed for these 6 — old visuals kept working since Entity+Property
  became byte-identical to before.
- For the harder N:1 consolidation (Viagens+Jornada+Velocidade+Espelhamento→`fato_viagem`,
  ColetaEntrega→`fato_coleta_entrega`, `_dFiliais`→`dim_filial`): discovered the report has **29 pages**,
  ~193 visual.json files + 16 bookmark.json files reference these old tables — and `pbi_visual_where`/
  `pbi_page_list` (the tools meant to make this safe) return empty/broken for this report. Also
  discovered many legacy columns (Jornada's `Alerta` text, `Frota`, `IdPlanoViagem`,
  `IdTecnologiaRastreamento`, `Ativo`, Espelhamento's cryptic `Numero`, `MesAbrev`/`AnoAbrev`) have NO
  equivalent in the gold layer at all — added ~59 alias/RELATED()-based calculated columns on
  `fato_viagem`/`fato_coleta_entrega`/`dim_filial` using the EXACT legacy column names (so the rebind
  only needs to swap the Entity/table name, not the property/column name) to cover everything that DOES
  have an underlying equivalent; the genuinely unrecoverable ones were left out (no column created) —
  any visual using exactly those will still point at a name that no longer resolves.
  **Gotcha to remember: TOM column names are case-insensitive-unique per table** — `cavalo` and `Cavalo`
  collide even though they're created in the same batch; hit this twice (had to drop `id viagem`/keep
  `ID Viagem`, `condutor`/keep `Condutor`, `cnpj_tomador`/keep `CNPJ_Tomador`, and had to *rename* not
  *alias* `fato_coleta_entrega.cavalo`→`Cavalo` and `.alerta`→`Alerta` since those base columns already
  existed under the lowercase name).
- Did the actual rebind via a PowerShell bulk text-replace (`[System.IO.File]::ReadAllText` /
  `.Replace(...)` / `WriteAllText` with `UTF8Encoding($false)` to avoid BOM issues) across every
  `visual.json`/`page.json`/`report.json`/`filters.json` under `definition/`, PLUS a separate pass over
  `definition/bookmarks/*.bookmark.json` (easy to miss — bookmarks are a distinct folder, not nested
  under pages, and reference the same old Entity names). Confirmed 0 remaining `"Entity": "..."` matches
  for the old table names afterward. Leftover raw-text matches after that are only cosmetic
  `queryRef`/`nativeQueryRef` label strings (e.g. `"Velocidade.Consulta1.TipoTerceiro"`) — harmless,
  intentionally left alone.
- **Important distinction**: report-layer JSON files (visuals/bookmarks/pages) are written straight to
  disk in PBIP format — no Ctrl+S needed for those. But all the model-side work (new columns, table
  renames/measure renames) still only lives in the live Desktop session until saved — so the
  save-before-close rule ([[feedback_pbi_desktop_save_before_close]]) still fully applies.
- **Not yet done:** visual QA (never opened the report to look, per this being a headless MCP session —
  ask the user to eyeball a few pages), decide whether to now delete
  `Viagens`/`Jornada`/`Velocidade`/`Espelhamento`/`ColetaEntrega`/`_dFiliais`/`Grupos_Cliente`/
  `Consulta1`/`fallbackMulti` (confirmed zero direct visual dependency on the latter 3; the former 6
  should be safe now given the 0-remaining-Entity-match check, but haven't pulled the trigger on
  deleting them yet — do that only after the user confirms the report actually looks right).

**How to apply:** resume from wherever Fase 5 left off above. If tables are missing again on resume,
assume another unsaved-close data loss and check `table_operations List` count (44 = back to legacy-only,
work lost) before doing anything else. If the report-layer rebind looks lost/reverted, check whether the
`.Report/definition` JSON files on disk still have the `fato_viagem`/`fato_coleta_entrega`/`dim_filial`
Entity names (that part doesn't need a Ctrl+S and shouldn't be lost by a Desktop restart) before
concluding it needs to be redone.

**"Closed out" 2026-08-16 turned out to be premature — the report-layer rebind silently reverted.**
User came back 2026-08-17 saying the migration "não deu certo." Root cause: the belief above that
PBIP report-layer JSON (`visual.json`/`bookmark.json`/etc.) "doesn't need Ctrl+S, safe to hand-edit on
disk anytime" was **wrong** — Power BI Desktop caches the report layer in memory while a project is
open and can overwrite external edits to those files (e.g. on its own save/reload cycles), so my direct
PowerShell text-replace got clobbered. Symptom when the user reopened: the model-side work (new tables/
columns/measures) HAD persisted correctly (confirmed via `model.tmdl` `ref table` list and a live
connection), but every visual was back to referencing the old, since-deleted tables → **blank visuals**
report-wide (screenshot showed a "Detalhes" visual with the classic "Há algo errado em um ou mais
campos" error and the field list showing which specific fields were unresolved).

**Fix that actually stuck:** redo the same PowerShell Entity-rename bulk-replace, but only after
confirming (a) the user had saved the model via Ctrl+S, and (b) `connection_operations
ListLocalInstances` showed the "Central Torre de Controle" PID/port **gone** (Desktop fully closed, not
just minimized) — verified via `ListLocalInstances` returning zero entries for that title before
editing, and the 0-remaining-`"Entity":"..."`-match grep held after the user reopened and reported
visuals working again. **Rule going forward: any report-layer (`.Report/definition/**`) JSON edit must
be done with Power BI Desktop fully closed for that file — never while a live MCP connection to it is
open, no matter how far into the model-side (TMDL) changes have already been safely saved.**

**Two more missing-column gaps found via user screenshot** (a field-list red-triangle in a visual is the
actual ground truth — model validation via DAX doesn't catch "does some field a visual references
exist"): `fato_viagem` was missing plain `Cliente` (client display name — recovered via
`CALCULATE(FIRSTNONBLANK(fato_coleta_entrega[cliente_tomador],1), FILTER(fato_coleta_entrega,
fato_coleta_entrega[numero_carga]=fato_viagem[numero_carga]))`, i.e. borrowed from the coleta/entrega
fact by shared `numero_carga`, since `dim_cliente` has no name field at all) and plain
`HouveEspelhamento` (the un-prefixed version — `Espelhamento.HouveEspelhamento` had been aliased, but
Espelhamento's own un-prefixed column name was overlooked). **Takeaway: the ~59-column alias sweep from
2026-08-16 was necessarily incomplete — treat "visual shows a field-not-found error" reports as the
real spec, not the earlier from-TMDL column inventory, and fix incrementally as they surface.**

**Also renamed the 19 measures that still had `_novo`** (fato_viagem's 10, fato_coleta_entrega's 2,
dim_filial's 7) back to their plain legacy names, now that `Espelhamento`/`Jornada`/`Velocidade`/
`ColetaEntrega`/`_dFiliais` are confirmed deleted and the names are free. Renaming a measure via
`measure_operations Rename` does **not** rewrite other measures' DAX text that reference it by
`[OldName]` — had to separately `Update` the 3 fato_viagem measures and 4 dim_filial measures whose
expressions cross-referenced the just-renamed `_novo` measure names, or they'd have broken. No visual
JSON changes were needed for the measure rename — visuals were always bound to the plain names (the
`_novo` suffix only ever existed inside this migration's intermediate state, never something a visual
referenced).

**Current state (2026-08-17): old `Viagens`/`Jornada`/`Velocidade`/`Espelhamento`/`ColetaEntrega`/
`_dFiliais`/`Grupos_Cliente`/`Consulta1`/`fallbackMulti` tables are confirmed DELETED** (both live model
and saved `model.tmdl`) — this happened between the 08-16 "finalizamos" and 08-17 return, presumably the
user cleaned them up via the Desktop UI.

**Field-by-field visual QA round (2026-08-17), fixed via user screenshots one at a time** — this is the
realistic way this kind of rebind gets finished: text-search inventories the column list, but only a
screenshot of the actual rendered error catches gaps like "this specific field, in this specific visual,
resolves to nothing." Fixed in this round:
- `fato_viagem.HouveEspelhamento` (plain, un-prefixed — only `Espelhamento.HouveEspelhamento` had been
  aliased before)
- `fato_viagem.Cliente` (client display name — `dim_cliente` has no name field at all, so borrowed from
  `fato_coleta_entrega[cliente_tomador]` via `CALCULATE(FIRSTNONBLANK(...), FILTER(...numero_carga match))`)
- `fato_viagem.Pts` (displayed as "LimitePontos" in the Velocidade grid — alias to `pontos_tolerancia`)
- `fato_viagem.Cliente Tomador` (alias to the `Cliente` column above)
- `fato_viagem.Alerta` (Jornada's alert-type text — genuinely absent from gold's `alerta_jornada` flag;
  recovered via a lookup into the `Usuarios` table by `ID Viagem Vinculo` + the same
  `Justificativa = "JOR - Excesso de jornada confirmado."` filter the legacy Jornada SQL used)
- `fato_coleta_entrega._DateFiltro` (first column of the Coleta e Entrega grid, displayed as "Data" —
  simple alias to `data_cadastro_viagem`, which is already date-only in the gold schema)
- `condutor` (lowercase) on the Jornada grid turned out to self-resolve once Power BI Desktop reloaded/
  saved — TOM's case-insensitive column-name uniqueness does eventually let case-mismatched Property
  strings resolve, just not instantly inside the same live session where the alias was just created.

**Validation technique worth reusing:** when a value looks "off" between two Power BI files hitting the
same Athena tables, don't guess — query Athena directly for both schemas over the same date cutoff (here,
`hml_gold.fato_viagem` vs `prd_gold.fato_viagem`, `WHERE data_cadastro_viagem <= same date`) and diff with
`EXCEPT` both directions. Confirmed 0 rows different — the apparent mismatch was purely two Power BI
files having been refreshed at different times (one stalled 2026-07-28, ours current to 2026-08-07), not
a real data problem.

**Bonus context, not yet fully explored:** the user has a separate, older file open — window title
"Central Torre de Controle_pre" — which turns out to be an independent EARLIER migration attempt (by
someone else, dated 2026-07-17, modified 2026-07-17–28), NOT a legacy pre-migration snapshot as the name
suggests. It sources `aws_fato_viagem`/`aws_fato_coleta_entrega`/`aws_dim_*` from **`hml_gold`** (not
`prd_gold` — worth flagging per [[feedback_prd_over_hml_schema]]) and consolidates measures into a single
disconnected `_medidas` table (pattern: `Row("Column", BLANK())` calculated table, then all report
measures live there) — a cleaner pattern than scattering them across fact tables, worth considering for
a future cleanup pass. It only migrated the GPS core (no Camera/Usuarios/Integracao/CargasMulti rebuild),
and the user says it also has "inconsistent/null fields" of its own — so treat it as a secondary reference
for column-mapping sanity-checks, not as ground truth.

User's read as of this point: **"acho que deu boa"** (thinks it's turning out well) — report is not yet
declared fully done, keep fixing specific fields as screenshots surface them. **If this comes up again:**
don't assume clean — ask what's currently broken (get a screenshot of the exact error/field list, it's
far more precise than guessing from the TMDL), fix the specific gap, and remember the
Desktop-must-be-closed rule for any further report-layer JSON edit.
