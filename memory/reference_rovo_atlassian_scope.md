---
name: reference-rovo-atlassian-scope
description: "The Rovo/Atlassian MCP server available in this project only covers Jira and Confluence, not Bitbucket"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 26cde4d5-929c-4fd2-b64a-5e002e11dcbd
  modified: 2026-08-12T16:59:55.632Z
---

The Atlassian/Rovo MCP server connected to this project (tools prefixed `mcp__atlassian__*`) has
access to a single site, `cootravale.atlassian.net`, with OAuth scopes limited to:
`read/write:jira-work` and `read/write:page|comment|space:confluence`. There is no Bitbucket scope
and no Bitbucket-specific tool in the set — confirmed via `getAccessibleAtlassianResources`.

**Why:** user asked whether this MCP ("temos o mcp rovo") could be used to create/push to a
Bitbucket repo for [[project-credito-migration-status]]. It cannot — don't suggest it as a path for
Bitbucket repo creation or git push. If Bitbucket access is needed, it has to come from a manual push
by the user or a separate credential (PAT/SSH), not from this MCP connection.

Also note: the Atlassian MCP server itself returned a deprecation notice for its HTTP+SSE transport
endpoint (`https://mcp.atlassian.com/v1/sse`, sunset after 2026-06-30, migrate to
`https://mcp.atlassian.com/v1/mcp`) — relevant to whoever administers this MCP config, not to report
content.
