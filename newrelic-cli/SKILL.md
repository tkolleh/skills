---
name: newrelic-cli
description: >
  Query and manage New Relic observability data using the newrelic CLI across all
  your organization's accounts. Trigger on: newrelic, nrql, apm, deployment marker,
  alert policy, observability query, error rate, throughput, latency, SLO/SLI.
license: MIT
compatibility: opencode
metadata:
  audience: developers
  tools: [newrelic-cli]
---

## What this skill does

Translates natural-language observability questions into `newrelic` CLI commands,
resolving account names to numeric IDs automatically. It knows every
New Relic account, which environment and service slot each belongs to, and
which region (US/EU) to use.

## Account resolution

A bundled `accounts.json` (sibling to this file) maps every New Relic
account. Read it at the start of any task to resolve accounts.

### Resolution rules

1. If the user names an **environment** (e.g. "production", "test", "uk-prod"),
   match against the `environment` field.
2. If they name a **slot** (e.g. "services", "envoy", "cardinal"), match against
   the `slot` field within the target environment.
3. If they give a **numeric account ID**, use it directly.
4. If they name an **alias** (e.g. "Acme_Corp_1", "My_Org"), match
   against the `alias` field.
5. **Defaults** when no account is specified:
   - Service-specific queries (transactions, throughput, errors) ->
     `$DEFAULT_SERVICES_ACCOUNT`
   - General queries (infrastructure, custom events) ->
     `$DEFAULT_MAIN_ACCOUNT`

Always confirm which account you resolved to before running the query, e.g.:
"Querying **Services Production** ($ACCOUNT_ID)..."

## CLI command reference

### NRQL queries

The most common operation. Always include `--accountId` and default to
`--format JSON` for structured output.

```bash
newrelic nrql query --accountId <ID> --query '<NRQL>' --format JSON
```

**Example patterns:**

```bash
# Transaction throughput
newrelic nrql query --accountId $ACCOUNT_ID \
  --query "SELECT rate(count(*), 1 minute) FROM Transaction WHERE appName = 'my-service' TIMESERIES SINCE 1 hour ago" \
  --format JSON

# Error rate
newrelic nrql query --accountId $ACCOUNT_ID \
  --query "SELECT percentage(count(*), WHERE error IS true) FROM Transaction WHERE appName = 'my-service' SINCE 1 hour ago" \
  --format JSON

# P99 latency
newrelic nrql query --accountId $ACCOUNT_ID \
  --query "SELECT percentile(duration, 99) FROM Transaction WHERE appName = 'my-service' TIMESERIES SINCE 1 hour ago" \
  --format JSON
```

### Entity search

Find applications, hosts, containers, and other entities.

```bash
newrelic entity search --name <NAME>
newrelic entity search --name <NAME> --domain APM --type APPLICATION
newrelic entity search --tag "environment:production"
```

Useful filters: `--domain` (APM, INFRA, BROWSER, SYNTH, etc.),
`--type` (APPLICATION, HOST, CONTAINER, etc.), `--tag`, `--alert-severity`,
`--reporting`.

### APM operations

```bash
# Search for an application
newrelic apm application search --accountId <ID> --name <APP_NAME>

# Record a deployment
newrelic apm deployment create --applicationId <APP_ID> --revision <SHA>
```

### Profile management

Profiles store API keys and default account IDs for repeated use.

```bash
newrelic profile list
newrelic profile add --name <PROFILE> --apiKey <KEY> --region <US|EU> --accountId <ID>
newrelic profile default --name <PROFILE>
```

### NerdGraph (GraphQL)

For advanced queries not covered by built-in commands.

```bash
newrelic nerdgraph query '{ actor { user { email } } }'
```

### Custom events

```bash
newrelic events post --accountId <ID> --event '{"eventType":"Deployment","revision":"abc123"}'
```

## Environment variables

| Variable | Purpose |
|---|---|
| `NEW_RELIC_API_KEY` | Personal API key (NRAK-...) |
| `NEW_RELIC_ACCOUNT_ID` | Default account ID |
| `NEW_RELIC_REGION` | US (default) or EU |
| `NEW_RELIC_LICENSE_KEY` | License key (for posting events) |

## Workflow

1. **Parse intent**: What does the user want to know or do?
2. **Resolve account**: Read `accounts.json`, match environment/slot/alias.
3. **Build command**: Construct the `newrelic` CLI invocation.
4. **Show the user**: Display the resolved account and command before running.
5. **Execute**: Run via Bash and return results.
6. **Interpret**: Summarize the data in plain language -- highlight anomalies,
   trends, or notable values.

## Common NRQL patterns

These patterns cover the most frequent observability questions:

```sql
-- Service health overview
SELECT count(*), average(duration), percentage(count(*), WHERE error IS true)
FROM Transaction WHERE appName = '{service}'
SINCE 1 hour ago

-- Top slow transactions
SELECT average(duration), count(*)
FROM Transaction WHERE appName = '{service}'
FACET name SINCE 1 hour ago LIMIT 10

-- Error breakdown
SELECT count(*) FROM TransactionError
WHERE appName = '{service}' FACET error.class SINCE 1 hour ago

-- Infrastructure (CPU/memory) -- use main account
SELECT average(cpuPercent), average(memoryUsedPercent)
FROM SystemSample WHERE hostname LIKE '%{service}%'
SINCE 1 hour ago TIMESERIES

-- Kafka consumer lag -- use services account
SELECT average(consumer.totalLag)
FROM KafkaOffsetSample WHERE consumerGroup LIKE '%{service}%'
FACET topic SINCE 1 hour ago
```

## Multi-account queries

When a question spans multiple accounts (e.g. "compare prod vs test error
rates"), run separate queries against each account and present the results
side by side. Label each result clearly with the account name and environment.

## Error handling

- If `newrelic` is not installed, suggest: `brew install newrelic-cli`
- If authentication fails, check `newrelic profile list` and suggest
  `newrelic profile add`
- If an account ID is ambiguous (e.g. "services" without an environment),
  ask the user to clarify which environment
