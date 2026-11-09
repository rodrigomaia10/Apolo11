---
name: feedback-generic-reusable-skills
description: "User wants process/harness documentation written as generic, reusable skills — not tied to one specific report's table/measure names"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 26cde4d5-929c-4fd2-b64a-5e002e11dcbd
  modified: 2026-08-12T16:59:30.277Z
---

When asked to document "how we did X" for future reuse (a migration method, a build process, a
recurring workflow), write it as a **generic, parameterized procedure** — no specific table names,
measure names, or business-domain facts from the one example that prompted the request. Use
placeholders (`<TabelaFato>`, `<coluna_chave>`) instead.

**Why:** first attempt at this (documenting the Power BI → Athena migration learned while migrating
the "Análise Exposição de Crédito" report) was rejected because it hardcoded that report's specific
DAX/table names. User: "vc fez especifico para este bi porem temos varios para migrar precisa de
skill mais em como fazer" — there are several BI reports to migrate, so the artifact needs to be the
*method*, not a record of one instance. See [[powerbi-athena-migration-skill]].

**How to apply:** when a request says "document this so the next one is easier" / "faça uma skill
para os próximos", default to writing a Skill (`.claude/skills/<name>/SKILL.md`), not a CLAUDE.md
loaded with this-session's specifics. Environment-level facts (available MCP servers, DSN names,
machine quirks) are fine to include since they're true regardless of which report — only business/
report-specific naming should be abstracted out.
