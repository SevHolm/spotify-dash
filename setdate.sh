#!/usr/bin/env bash
set -euo pipefail
: "${WHEN:?Set WHEN like 2025-08-19T14:00:00-0500}"
GIT_AUTHOR_DATE="$WHEN" GIT_COMMITTER_DATE="$WHEN" \
  git commit --amend --no-edit --date "$WHEN" >/dev/null
