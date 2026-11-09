---
name: reference-source-kmm-schema-not-queryable
description: "The Athena schema source_kmm is catalogued (~1641 tables, datalake_<schema>_<table> naming) but SELECTs against it fail"
metadata: 
  node_type: memory
  type: reference
  originSessionId: a1cf8380-5784-452a-a02e-9e8947cd6c0d
  modified: 2026-08-21T19:03:13.728Z
---

The Athena database `source_kmm` lists a very wide 1:1-looking mirror of the KMM Postgres source (tables named `datalake_<schema>_<table>`, e.g. `datalake_kss_pessoa_juridica`, `datalake_finan_ccorrente`). `information_schema.columns` returns correct-looking column metadata for these tables, which makes them look usable.

**They are not queryable.** Any `SELECT` (even `SELECT * ... LIMIT 1` or `count(*)`) against a `source_kmm.datalake_*` table fails with `HIVE_UNSUPPORTED_FORMAT: Unable to create input format`. Discovered 2026-08-21 during [[project_ccpagar_conta_corrente_migration]].

**How to apply:** don't trust `source_kmm` table existence alone as proof a source is usable in a PBI migration — always test with a real `SELECT ... LIMIT 1` before building a view or M query on top of it. The tables actually usable for KMM data are the curated ones under `prd_bronze`/`hml_bronze` (prefixed `kmm_...`, driven by the `datalake-glue` repo's `sources/bronze_sources.json` / `kmm_1.json` / `kmm_2.json` configs at `C:\project\datalake-glue`) — if a KMM table isn't in those JSON configs, it likely isn't replicated anywhere queryable, regardless of what `source_kmm` appears to show.
