#!/usr/bin/env bash
# Report which Substack posts still canonicalize to themselves.
#
#   ./scripts/check-substack-canonicals.sh          # summary
#   ./scripts/check-substack-canonicals.sh --list   # list every unfixed post
#
# Setting the canonical must be done by hand in Substack's admin UI (Post →
# Settings → SEO → Canonical URL). Substack's API exposes `canonical_url` for
# reading but rejects unauthenticated writes, so this script only VERIFIES.
#
# Run it as you work through docs/substack-canonical-checklist.md to see the
# remaining count drop.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECKLIST="$ROOT/docs/substack-canonical-checklist.md"
LIST_MODE="${1:-}"

if [[ ! -f "$CHECKLIST" ]]; then
  echo "missing $CHECKLIST" >&2
  exit 1
fi

fixed=0
unfixed=0
errors=0

# Column 3 of the checklist is the Substack URL; column 4 is the target.
while IFS='|' read -r _ _ _ sub target _; do
  sub="$(echo "$sub" | xargs)"
  target="$(echo "$target" | xargs)"
  [[ "$sub" == https://* ]] || continue

  slug="${sub##*/}"
  body="$(curl -s --max-time 20 \
    "https://theincurablehumanist.substack.com/api/v1/posts/${slug}" 2>/dev/null)"

  current="$(printf '%s' "$body" | python3 -c '
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get("search_engine_url") or d.get("canonical_url") or "")
except Exception:
    print("__ERROR__")
' 2>/dev/null)"

  if [[ "$current" == "__ERROR__" || -z "$current" ]]; then
    errors=$((errors + 1))
  elif [[ "$current" == *theincurablehumanist.com* ]]; then
    fixed=$((fixed + 1))
  else
    unfixed=$((unfixed + 1))
    [[ "$LIST_MODE" == "--list" ]] && echo "TODO  $sub"
  fi
  sleep 0.4   # be polite; Substack rate-limits sustained polling
done < "$CHECKLIST"

echo
echo "canonicalized to theincurablehumanist.com : $fixed"
echo "still self-canonicalizing on Substack     : $unfixed"
[[ $errors -gt 0 ]] && echo "unreadable (404 / rate-limited)           : $errors"
echo
[[ $unfixed -eq 0 && $fixed -gt 0 ]] && echo "All done." || \
  echo "Set the remaining ones in Substack → Post → Settings → SEO → Canonical URL"
