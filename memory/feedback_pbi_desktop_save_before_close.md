---
name: feedback-pbi-desktop-save-before-close
description: Always get the user to save (Ctrl+S) in Power BI Desktop before asking them to close/reopen it — unsaved model changes made via XMLA are lost
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c43a3c23-526e-4a61-a376-d49dd62bd6ed
  modified: 2026-08-17T15:38:31.467Z
---

Changes made to a Power BI Desktop model via the `powerbi-desktop-mcp`/`pbi-connection` XMLA tools
(`table_operations Create/Update`, `relationship_operations Create`, etc.) only live in the Desktop's
in-memory session until the user actually saves the file (Ctrl+S). If the Desktop is closed without
saving, everything done via MCP since the last save is gone — reopening the `.pbip` reloads from the
on-disk TMDL, which never had the changes.

**Why:** During the [[project_torre_controle_migration]] work, a Mashup/Power Query cache got stuck
after updating a table's M partition (row count frozen at the pre-edit value despite `modifiedTime`
advancing — see [[reference_torre_controle_docs]]'s migration skill for the general gotcha). The fix
required closing and reopening Power BI Desktop to reset the Mashup engine. The user was asked to close
without first being told to save — losing 4 full phases of migration work (12 new tables, all
relationships) that only existed in the live session.

**How to apply:** Before asking the user to close/reopen Power BI Desktop for ANY reason (cache reset,
crash recovery, etc.), always first explicitly ask them to save (Ctrl+S) and confirm the save completed.
More broadly, during any multi-step Power BI Desktop model migration via MCP, proactively suggest saving
checkpoints after each validated phase — don't wait for a forced restart to discover unsaved work is at
risk.

**Second, distinct gotcha (also from [[project_torre_controle_migration]]):** the reverse is also true —
report-layer JSON files (`.Report/definition/**/visual.json`, `page.json`, `bookmark.json`, etc.) look
like plain files safe to hand-edit anytime since PBIP always keeps them as human-readable JSON on disk,
but **Power BI Desktop caches the report layer in memory while the project is open and can overwrite
external edits to those files** (observed: a bulk PowerShell text-replace across ~200 visual/bookmark
JSON files was silently reverted after the user later saved/reopened). The edit only stuck once redone
with Desktop fully closed for that file (confirmed via `connection_operations ListLocalInstances`
showing no entry for that window title before editing). **Rule: never hand-edit report-layer JSON while
any live MCP connection to that same file is open — close Desktop first, edit, then have the user
reopen** — this applies independently of whether the model side has already been safely saved.
