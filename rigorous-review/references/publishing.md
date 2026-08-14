# Publishing

Only reached when the user explicitly asks for the review to be posted. Everything here has an irreversible, externally-visible side effect.

## Confirmation gate

Before posting, show the user:

1. The exact review body.
2. Every inline comment, with its file and line.
3. The review event you intend to use.

Get explicit approval for that content. Approval to "post the review" is not approval for a set of comments the user has not read.

Default to the `COMMENT` event. `APPROVE` and `REQUEST_CHANGES` are judgements on the author's work with process consequences — never pick one on the user's behalf.

## Register

The posted text is read by a colleague, not by you.

**State the bug. Show the fix. Stop.**

- No compliments, opening or closing. Not "nice work, but…", not "otherwise this looks great."
- No nits. If it does not change behaviour or cost, it does not get posted.
- Every comment says the concern **and why it matters** — the consequence, in one clause.
- Plain text. No emoji.

Drop borderline items rather than padding the review. A short review that is entirely load-bearing gets acted on; a long one gets skimmed.

## Posting with `gh`

Build the payload as a file rather than inline, so quoting and newlines survive:

```bash
# review body
cat > /tmp/review-body.md <<'EOF'
### Review

<findings summary>

### Checked, no concern

- ...
EOF
```

Post body plus inline comments in one review, so the author gets a single notification:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/reviews \
  --method POST \
  --field event=COMMENT \
  --field body="$(cat /tmp/review-body.md)" \
  --field 'comments[][path]=src/filters/rowMatch.ts' \
  --field 'comments[][line]=42' \
  --field 'comments[][side]=RIGHT' \
  --field 'comments[][body]=The predicate matches the raw accessor, so derived-label columns are unsearchable and fail silently.'
```

For more than a couple of comments, build the JSON and pipe it:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/reviews --method POST --input review.json
```

Inline-comment rules that cause most failures:

- `line` must fall within the PR's diff hunks. A line outside them is rejected.
- `side=RIGHT` for the new version, `LEFT` for the old. Default to `RIGHT`.
- Use `start_line` with `line` for a multi-line comment.
- Anchor to the reviewed head SHA; if the author pushes mid-review, re-derive the lines rather than posting stale anchors.

## Citing code

When referring to code from the body rather than an inline comment, use a permalink with the **full** commit SHA. A branch-name link rots when the branch moves.

```
https://{host}/{owner}/{repo}/blob/{full-40-char-sha}/path/to/file.ts#L41-L44
```

- Full SHA, not a short one and not a branch name.
- `#L<start>-L<end>`, and include at least one line of context either side of the line you mean.
- Build the URL with a resolved literal SHA. Command substitution inside the comment body does not execute — it posts as literal text.

## Verify server-side after posting

**The transcript is not evidence that the post succeeded.** A partial failure — body accepted, inline comments rejected for out-of-range lines — is easy to miss and looks like success locally.

After posting, read it back:

```bash
# review landed, and in the intended state
gh api repos/{owner}/{repo}/pulls/{number}/reviews --jq '.[-1] | {id, state, user: .user.login}'

# inline comments actually attached
gh api repos/{owner}/{repo}/pulls/{number}/comments --jq 'length'
```

Compare the returned count against the number you intended to post. Report the actual numbers to the user. If they do not match, say so and name which comments are missing — do not re-post the whole review, which double-notifies the author.

## Other forges

The shape is the same everywhere: one review object carrying a body plus line-anchored comments, then a read-back to confirm. Only the endpoint changes. Do not assume a host is GitHub — check the remote first, and if the API is unfamiliar, produce the report and let the user post it rather than guessing at an endpoint.
