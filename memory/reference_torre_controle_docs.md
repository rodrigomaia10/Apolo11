---
name: reference-torre-controle-docs
description: "Where to find the DW architecture doc and ER diagram for the \"Central Torre de Controle\" Power BI"
metadata: 
  node_type: memory
  type: reference
  originSessionId: c43a3c23-526e-4a61-a376-d49dd62bd6ed
  modified: 2026-08-15T14:49:31.566Z
---

The Power BI project "Central Torre de Controle" lives at `C:\PowerBIClaudio\Central Torre de Controle` (pbip). Its semantic model has 44 tables including `Viagens`, `Jornada`, `Velocidade`, `ColetaEntrega`, `Camera`, `Integracao`, `_dFiliais`.

Supporting DW/architecture documentation for this BI:
- `C:\PowerBIClaudio\VISUALIZADOR_DIAGRAMAS_POWERBI.html` — ER diagram viewer, includes a "Torre de Controle" section.
- `C:\PowerBIClaudio\Guia de Boas Práticas Power BI.docx` — general Power BI best-practices guide.
- A zip inside the project folder (`ENC_ Modelagem - Arquitetura de dados Cootravale..zip`) just bundles copies of the same two files — no need to open it separately.

**How to apply:** when working on modeling, migration, or DW-alignment tasks for the Torre de Controle BI, consult the ER viewer HTML first to understand entity relationships before touching measures/tables.
