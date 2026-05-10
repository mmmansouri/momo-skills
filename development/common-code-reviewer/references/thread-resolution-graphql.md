# Thread Resolution via GraphQL

GitHub's REST API does not expose review-thread resolution. Use the GraphQL mutations below.

## Table of Contents

- [Resolve a Thread](#resolve-a-thread)
- [Unresolve a Thread](#unresolve-a-thread)
- [Query Thread Status](#query-thread-status)
- [Error Handling](#error-handling)

---

## Resolve a Thread

Preferred path: `scripts/resolve-thread.sh <thread_id>` — single source of truth, easier to patch if the API evolves.

Direct invocation (only when scripting from inside an agent run that cannot shell out to the bundled script):
```bash
gh api graphql \
  --field threadId="<PRRT_xxx>" \
  -f query='
    mutation($threadId: ID!) {
      resolveReviewThread(input: {threadId: $threadId}) {
        thread { isResolved }
      }
    }'
```

---

## Unresolve a Thread

```bash
gh api graphql \
  --field threadId="<PRRT_xxx>" \
  -f query='
    mutation($threadId: ID!) {
      unresolveReviewThread(input: {threadId: $threadId}) {
        thread { isResolved }
      }
    }'
```

---

## Query Thread Status

```bash
gh api graphql \
  --field nodeId="<PRRT_xxx>" \
  -f query='
    query($nodeId: ID!) {
      node(id: $nodeId) {
        ... on PullRequestReviewThread {
          isResolved
          isOutdated
          comments(first: 1) {
            nodes { body path line }
          }
        }
      }
    }'
```

---

## Error Handling

If a mutation fails:
1. Log the GraphQL error with the thread ID.
2. Add a PR comment noting that manual resolution is required, citing the thread ID.
3. Continue with remaining threads — never abort the review pass for a single failed resolution.
