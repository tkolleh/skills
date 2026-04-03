---
name: software-system-analyzer
description: Detects repository context, maps dependencies (enterprise-specific or general), and generates/persists architectural documentation.
license: MIT
compatibility: opencode
metadata:
  audience: developers
  tools: [gh, src, diagramming-d2, serena, openmemory]
---

## What I do
I analyze the current repository to determine its origin and architecture. If it is hosted on a private enterprise Sourcegraph instance, I execute a deep internal discovery protocol using the /sourcegraph-search skill. Otherwise, I perform a comprehensive local audit of language, frameworks, and public dependencies.

## When to use me
Trigger this skill immediately upon entering a new repository or when the user asks "How does this system work?", "What is the architecture", "What are the system dependencies?", or "What should I know to work on this codebase?".

## Operational Workflow

### Phase 1: Context Detection
Run `gh repo view --json url` or inspect the local `.git/config` to check the remote host.
- **IF host is a private enterprise Sourcegraph instance:** Proceed to Phase 2 (Enterprise Protocol).
- **OTHERWISE:** Proceed to Phase 3 (General Protocol).

### Phase 2: Enterprise Sourcegraph Discovery Protocol
Use `src search` to map the ecosystem. Adapt the repo patterns to your organization's Sourcegraph instance:
1. **Contracts:** Search for the organization's interface definition contracts repository for Thrift IDL, Proto schema, GraphQL, etc...
2. **Message Queues:** Search for message broker (e.g., Kafka) infrastructure-as-code repositories.
3. **Cloud/IAM:** Search for cloud infrastructure bootstrap or service provisioning repositories.
4. **Data Pipelines:** Search for ETL job or data pipeline deployer repositories.
5. **Data Stores:** Search for database schema or storage infrastructure repositories.

### Phase 3: General Discovery Protocol
1. **Identify Project Type:** Detect primary language (e.g., `package.json`, `build.sbt`, `go.mod`).
2. **Scan Local Entry Points:** Use `serena.search_code` to find Main classes, server initializations, or API routes.
3. **Map Local Dependencies:** Parse dependency files to identify external services (e.g., AWS SDKs, database drivers, third-party APIs).

### Phase 4: Documentation & Persistence
1. **Generate `AGENT.md`:** Create or update the root `AGENT.md`.
2. **Visualize:** Call the `diagramming-d2` skill to generate a system map.
3. **Mandatory Memory Save:** You MUST save the summarized project architecture (business goal, technical stack, and key dependencies) to your long-term memory. This ensures you do not need to re-run the full discovery in future sessions.

## Constraints
* **Evidence-Based:** Every dependency listed must be cited with its `src` search result or local file reference.
* **Privacy:** Never save sensitive strings, keys, or secrets to memory.
