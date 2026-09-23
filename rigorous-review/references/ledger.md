# The prior-findings ledger — retrieval mechanics

Phase 3 of `SKILL.md` states the rule: enumerate prior findings before analysing, and account for every unresolved one before stating a verdict. This file is how you get the data, and the specific ways the forge will hand you a plausible-looking subset of it.

## Findings live in three places, and no single call returns them all

A pull request stores review prose in three separate collections. They do not overlap, and the one most reviewers reach for is the one most likely to be empty:

| Where | Endpoint | Holds |
|---|---|---|
| Review summary bodies | `gh pr view <n> --json reviews` | the top-level paragraph of each review — **no inline comments** |
| Inline review comments | `gh api .../pulls/<n>/comments --paginate` | findings anchored to a file and line — where the substance usually is |
| Issue-style discussion | `gh api .../issues/<n>/comments --paginate` | general PR conversation, bot summaries, **blocking policy-check results**, notices that a review bot stopped running |

**`gh pr view --json reviews` is the trap.** It succeeds, returns well-formed JSON, and shows every review — while silently omitting every inline comment attached to them. Nothing in the output marks the omission, so it reads as complete data. This is a silent partial success, and it is more dangerous than an error: a 404 makes you look again, a stub body does not.

The failure is not hypothetical, and it is the norm rather than the edge case. On the PR behind the open-threads gate below, the reviewer who filed all seven live findings posted them as inline comments under this summary body:

> *"Review notes on the serious/major findings."*

Measured across that PR: **30 of its 44 review bodies are empty**, and the non-empty ones are mostly stubs like the line above. Zero findings appear in the bodies; 27 appear in the inline comments. A review that read only the bodies saw one uninformative sentence and correctly concluded it contained nothing — then wrongly concluded there was nothing to find.

Batching findings as inline comments under a stub body is exactly what a well-built review tool does, so the better the reviewer you are following, the emptier `--json reviews` looks.

**The issue-level collection is not optional padding.** On that same PR it was the only source carrying two *blocking* policy checks that were failing at the reviewed SHA, and a notice that the review bot had auto-paused after round 5 — so the four most recent rounds, containing every current finding, received no bot review at all. A bot that has gone quiet reads exactly like a bot with nothing to say. Check whether it is still running before you take its silence as a signal.

**Query all three, always, and `--paginate` every one.** The default page size is 30; this PR had 69 inline comments, so an unpaginated call drops more than half and gives no indication it did. Reconcile the three into one ledger keyed on thread identity. The GraphQL query below returns the inline threads with their resolved state and is the one to lead with; use the REST endpoints to fill in bodies and issue-level discussion.

```bash
# Every review thread with its resolved state. GraphQL, not REST: the REST
# /pulls/{n}/comments endpoint has no isResolved field at all.
GH_HOST=<forge-host> gh api graphql -f query='
{ repository(owner:"<owner>", name:"<repo>") {
    pullRequest(number:<n>) {
      reviewThreads(last:100) { totalCount nodes {
        isResolved isOutdated
        comments(first:1){nodes{ databaseId author{login} path line body }}
      } } } } }' \
  --jq '.data.repository.pullRequest.reviewThreads.nodes[]
        | "resolved=\(.isResolved) outdated=\(.isOutdated) \(.comments.nodes[0].author.login) \(.comments.nodes[0].path):\(.comments.nodes[0].line) id=\(.comments.nodes[0].databaseId)"'

# Inline comment bodies, paginated. This is where the findings are.
GH_HOST=<forge-host> gh api "repos/<owner>/<repo>/pulls/<n>/comments" --paginate \
  --jq '.[] | "[\(.id)] reply_to=\(.in_reply_to_id // "NONE") \(.user.login) \(.path):\(.line // .original_line)\n\(.body)\n---"'

# Review summary bodies — context and verdicts, rarely the findings themselves.
GH_HOST=<forge-host> gh api "repos/<owner>/<repo>/pulls/<n>/reviews" --paginate \
  --jq '.[] | "\(.submitted_at) \(.user.login) \(.state)\n\(.body)\n---"'

# Issue-level discussion: bot summaries, CI notices, general conversation.
GH_HOST=<forge-host> gh api "repos/<owner>/<repo>/issues/<n>/comments" --paginate \
  --jq '.[] | "\(.created_at) \(.user.login)\n\(.body)\n---"'
```

Sanity-check the retrieval before trusting it. `totalCount` is in the query for this: compare it against the number of nodes returned, and compare the inline comments you fetched against both. If any two disagree you are missing a page — not looking at a quiet PR. Where `totalCount` exceeds the window, page with `before:` until you have them all.

**Count the unresolved threads from the full set, not from what fits on your screen.** Truncating the output with `tail` or `head` and counting what remains reproduces the same bug one layer up: on the PR below, the visible tail showed 7 unresolved threads while the true count was 27 — the other 20 were unresolved *and* outdated, scrolled off the top. Let `jq` do the counting:

```bash
--jq '.data.repository.pullRequest.reviewThreads
      | "total=\(.totalCount) unresolved=\([.nodes[]|select(.isResolved==false)]|length)"'
```

Three properties of this data decide how you must handle it, and each has burned a real review:

- **`isResolved` is GraphQL-only.** Query REST and every thread looks alike, so an open finding is indistinguishable from a settled one.
- **An outdated thread reports `line: null`.** Merging findings by line number silently drops exactly the threads that have survived the most rounds. **Key the ledger on thread identity — the root comment's `databaseId` — never on a line.**
- **Two threads on the same line are usually two defects.** Co-location is not duplication: on the PR below, two threads sat on one expression, and fixing the first left the second still leaking. Collapsing them would have hidden a live defect behind a fix that looked complete. Merge two threads only when they describe the same wrong behaviour, and verify each independently even then.
- **`resolved=false, outdated=true` is the dangerous quadrant**, not a stale one: a finding the author replied "Done" to but never resolved, on code that has since moved. It is still open.

On an enterprise forge every one of these calls needs a literal `GH_HOST=<host>` prefix. Without it `gh api` returns **404, not an empty list** — and a 404 read as "no prior comments" is how a reviewer concludes a heavily-reviewed PR has never been reviewed. See `references/publishing.md`.
