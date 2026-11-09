---
name: feedback-prd-over-hml-schema
description: Never source a Power BI table from hml_ schema when a prd_ equivalent exists in the Athena DW
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5d86525b-4720-41ff-8189-f79d0a7054df
  modified: 2026-08-13T13:32:20.151Z
---

Don't use `hml_*` schema tables in a Power BI model if the same table exists in `prd_*`. Only fall back to `hml_*` when there is genuinely no `prd_*` equivalent, and flag that explicitly to the user as a gap rather than silently using homolog data.

**Why:** User's explicit rule (2026-08-13, during Contratos MultiTMS e KMM migration): homologation schemas aren't meant to back production reports. In practice, `hml_bronze` and `prd_bronze` often mirror the same underlying data (verified via row counts/max dates matching almost exactly), so switching costs nothing — but the source of truth should always be `prd_` when available.

**How to apply:** Before wiring up any Athena table in a `.pbip` migration ([[powerbi-athena-migration]] skill, step 3), check both `hml_<layer>` and `prd_<layer>` for the table. If both exist, compare counts/max-date to confirm they're equivalent, then use `prd_`. If only `hml_` exists, tell the user before using it as an official source — don't assume it's fine just because it's the only option. This complements [[feedback_athena_views_over_pbi_workarounds]] but is a separate concern (schema/environment choice vs. where filter logic lives).
