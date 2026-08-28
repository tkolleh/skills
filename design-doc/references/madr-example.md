# MADR Format

Use this structure for every Architecture Decision Record captured in State 2. MADR
(Markdown Architecture Decision Records) keeps each decision self-contained and skimmable —
a future reader should understand *why* without re-reading the whole TDD.

## Template

```markdown
## ADR-{N}: {Decision Title}

**Status:** Accepted
**Context:** {The forces at play — constraints from State 1, not restated generically.}
**Decision:** {The single sentence stating what was chosen.}
**Alternatives Considered:**
- {Alternative A} — {why it lost}
- {Alternative B} — {why it lost}
**Consequences:** {What becomes easier or harder because of this choice. Include the
downside honestly — an ADR with no listed cost reads as unexamined.}
```

## Worked Example

```markdown
## ADR-1: Use WebSockets for Live Order Status Updates

**Status:** Accepted
**Context:** Product requires order status changes to reach the customer's device within
2 seconds of the change occurring. Expected concurrent connections at launch: ~8k, growing
to ~50k within a year. The existing mobile client already maintains a persistent connection
for chat, so a second persistent-connection mechanism isn't a new operational category.
**Decision:** Use WebSockets (via the existing `realtime-gateway` service) rather than
polling.
**Alternatives Considered:**
- Short-interval polling (5s) — meets the latency bar only at the cost of ~10x the request
  volume at 50k concurrent users; rejected on infra cost grounds.
- Server-Sent Events — simpler than WebSockets and sufficient for one-directional updates,
  but the client would need a second connection type alongside the existing WebSocket used
  for chat; rejected to avoid two live-connection mechanisms in one client.
**Consequences:** Adds order-status message handling to `realtime-gateway`, which is
already a shared dependency — an outage there now affects both chat and order status
instead of just chat. Rollout plan (State 4) must account for this coupling.
```

Notice the worked example never states a decision without naming what it cost — that's the
part that makes an ADR worth reading later, rather than just a record that a meeting
happened.
