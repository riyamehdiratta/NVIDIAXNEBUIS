#!/usr/bin/env bash
set -euo pipefail

policy="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/verification-policy.yaml"
result="$(openshell sandbox create \
  --from alpine:3.20 \
  --name tl-verify \
  --policy "$policy" \
  --no-keep -- /bin/sh -lc '
    busybox wget -q -T 8 -O /dev/null http://example.com
    echo ALLOW_OK
    if busybox wget -q -T 8 -O /dev/null http://example.org; then
      echo DENY_UNEXPECTED
      exit 1
    else
      echo DENY_BLOCKED
    fi
  ')"
printf '%s\n' "$result"
grep -q 'ALLOW_OK' <<<"$result"
grep -q 'DENY_BLOCKED' <<<"$result"
