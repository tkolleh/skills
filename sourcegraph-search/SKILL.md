---
name: sourcegraph-search
description: Search code, commits, and diffs across millions of open source and private repositories using the Sourcegraph CLI (src).
license: MIT
compatibility: opencode
metadata:
  audience: developers
  tool: src
---
## What I do
I help you perform large-scale code analysis and discovery by searching Sourcegraph. I use the `src` CLI to execute precise queries that can match literal strings, regular expressions, or structural code patterns. I can filter results by repository, file type, language, commit history, and time ranges. I am particularly effective at finding usage examples, security vulnerabilities, deprecated patterns, and architectural inconsistencies across massive codebases.

## When to use me
Use this skill when:
- You need to search across a large codebase or multiple repositories for specific patterns, functions, or dependencies.
- You need to find real-world usage examples of a function or API across many repositories.
- You are auditing a codebase for security tokens, keys, or vulnerable dependencies.
- You want to perform "structural search" to match code patterns regardless of whitespace or formatting (e.g., finding all try-catch blocks with empty catches).
- You need to track recent changes or history using `type:diff` or `type:commit` (e.g., "what changed in the last week").
- You want to find projects that use specific dependencies (e.g., "who relies on `lodash` version 4.17.19").
- You need to identify repositories that are contributor-friendly (e.g., contain `CONTRIBUTING.md`).

## Instructions

### 1. Basic Search
Execute searches using the `src search` command. **Always** use the `-json` flag to ensure the output is machine-readable and easy to parse. Enclose your query in single quotes to prevent shell expansion.

```bash
src search -json 'query'

```

### 2. Advanced Filtering

Refine your search results using these standard filters within your query string:

* **Repository**: `repo:^github\.com/owner/name$` (supports regex)
* **File**: `file:\.js$` or `file:package\.json`
* **Language**: `lang:TypeScript`
* **Content**: `content:"string to find"` (optional, content is searched by default)
* **Boolean Operators**: `AND`, `OR`, `NOT` (e.g., `error AND NOT file:test`)

### 3. Structural Search

Use `patternType:structural` to match code structures rather than exact strings. This is powerful for finding code regardless of line breaks or formatting.

* **Syntax**: Use `:[name]` as a placeholder (hole) to match any code between delimiters.
* **Example**: Find `console.log` with any argument:
```bash
src search -json 'console.log(:[args]) patternType:structural'

```


### 4. Search Tricks & Best Practices

Use these specific patterns for high-value tasks:

**Find Usage of a Method (Structural)**
Find where a method is called, even with different arguments or formatting.

```bash
src search -json 'myMethod(:[args]) patternType:structural'

```

**Find Security Vulnerabilities (Regex)**
Scan for potential leaked secrets or keys.

```bash
src search -json '(key|secret|token)-[\w+]{32,} patternType:regexp'

```

**Find Specific Dependency Versions**
Check `package.json` files for a specific vulnerable library version.

```bash
src search -json 'file:package.json lodash 4.17.19'

```

**Find Recent Changes (Diffs/Commits)**
See what changed in a repository recently.

```bash
src search -json 'repo:^github\.com/owner/repo$ type:diff after:"1 week ago"'

```

**Find Contributor-Friendly Projects**
Locate repositories with contribution guidelines.

```bash
src search -json 'contributing lang:Markdown'

```

### 5. Output Interpretation

The `-json` output will provide a list of matches. Key fields to observe:

* `repository`: The repository name.
* `file`: The path to the matching file.
* `lineMatches`: Specific lines and line numbers where the match occurred.
* `commit`: If searching history, the commit hash and author.
