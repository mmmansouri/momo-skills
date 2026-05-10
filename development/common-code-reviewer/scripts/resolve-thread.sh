#!/usr/bin/env bash
# Resolve a GitHub PR review thread via GraphQL.
# Usage: resolve-thread.sh <thread_id>
# Example: resolve-thread.sh PRRT_kwDOABCDEF123

set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 <thread_id>" >&2
  exit 1
fi

THREAD_ID="$1"

gh api graphql \
  --field threadId="$THREAD_ID" \
  -f query='
    mutation($threadId: ID!) {
      resolveReviewThread(input: {threadId: $threadId}) {
        thread { isResolved }
      }
    }'
