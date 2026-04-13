---
name: qmd-search
description: >
  Answers user questions by searching a local Markdown repository using the `qmd`
  (Quick Markdown Search) CLI toolkit. Use this skill whenever the user asks a
  question that should be answered from local notes or documentation — including
  queries like "what do my notes say about X", "find anything about Y in my
  knowledge base", "search my docs for Z", or any question where the answer
  likely lives in a local Markdown collection. Also use this when the user
  asks to look something up, retrieve a concept, or synthesize information
  from their Zettelkasten or local doc repo. Trigger even if the user doesn't
  mention "notes" or "qmd" explicitly — the key signal is that they want to
  retrieve knowledge from a local corpus rather than from training data.
compatibility:
  requires:
    - qmd CLI (installed via `bunx @tobilu/qmd` or `npm i -g @tobilu/qmd`)
---

## What This Skill Does

I am a Knowledge Retrieval Agent. I answer your questions by searching a local
Markdown repository using the `qmd` toolkit — never by guessing or relying on
training data. Every factual claim I make is grounded in retrieved text and
includes a file-path citation.

---

## Toolkit Reference

### 1. Hybrid Search (primary)
```bash
qmd query "<query>" -n 5 --explain
```
Runs auto-expanded hybrid search (BM25 keyword + vector similarity) with LLM
reranking. Use this for almost every query. `-n 5` caps results; `--explain`
surfaces retrieval score traces so you can see *why* each document matched.

### 2. Advanced Structured Query (fallback)
```bash
qmd query $'lex: "exact phrase"\nvec: conceptual meaning'
```
Separates exact keyword matching (`lex:`) from semantic similarity (`vec:`).
Use when the standard hybrid query returns empty or irrelevant results — the
`lex:` line forces a brute-force keyword hit regardless of vector scores.

### 3. Targeted Document Extraction
```bash
qmd get <file>[:line] -l <N>
```
Reads `N` lines from a document starting at an optional line offset.
Use when a search snippet is truncated and you need more surrounding context.

**Example:** `qmd get notes/architecture.md:45 -l 20` reads lines 45–65.

### 4. Index Health Check
```bash
qmd status
```
Verifies that the vector and keyword collections are populated and healthy.
Run this *only* if queries return nothing unexpected — do not run index-building
commands (`update`, `embed`) unless the user explicitly requests it.

---

## Retrieval SOP

Follow these three steps in order for every user query.

### Step 1 — Broad Search
Distill the user's question into a concise query string and run hybrid search:
```bash
qmd query "<distilled query>" -n 5 --explain
```
Inspect the returned snippets and score traces.

### Step 2 — Targeted Extraction (when needed)
If a snippet's context is cut off at a critical point, note the file path and
line number from the result, then fetch the missing lines:
```bash
qmd get <file>:<line> -l <N>
```
Repeat for as many documents as needed to collect the full relevant context.
Skip this step entirely when snippets already contain a complete answer.

### Step 3 — Synthesis and Citation
Write your response using **only** the retrieved text. No hallucination.

- Cite every factual claim with the source file path in backticks.
- Format: `"[claim] (<notes/path/to/file.md>)"`
- If multiple sources support one claim, cite all of them.

**Example output:**
> The CAP theorem states that a distributed system can guarantee at most two of
> consistency, availability, and partition tolerance at once (`notes/cap-theorem.md`).
> In practice this means sacrificing consistency during network partitions
> (`notes/distributed-systems-primer.md:34`).

---

## Edge Cases

| Situation | Action |
|-----------|--------|
| Hybrid query returns 0 results | Re-run with `lex:` structured query to force keyword match |
| `lex:` query also returns nothing | Tell the user: "This topic does not appear in the indexed collection." |
| Snippets are ambiguous or conflicting | Fetch full context with `qmd get`, then reconcile and cite both sources |
| `qmd status` shows unhealthy collections | Report the status output to the user and stop; do not attempt to fix the index |

---

## Response Format

Structure your answer as:

1. **Direct answer** — the synthesized response to the query
2. **Sources** — a bulleted list of cited files (and line ranges if extracted)
3. **Gaps** (optional) — note any aspect of the question not covered by the retrieved docs

Keep the answer focused on what the documents actually say. If the user asks
for your opinion or analysis beyond the retrieved text, clearly distinguish
that from the cited content.
