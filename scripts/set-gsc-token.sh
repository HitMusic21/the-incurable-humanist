#!/usr/bin/env bash
# Install the Google Search Console verification token and deploy.
#
#   ./scripts/set-gsc-token.sh <token>
#
# The token is the `content` value from Search Console's "HTML tag" method:
#   <meta name="google-site-verification" content="THIS_PART" />
#
# Exists because the token cannot be guessed — a wrong value fails verification
# silently, so it has to come from you rather than be invented.
set -euo pipefail

TOKEN="${1:-}"
if [[ -z "$TOKEN" ]]; then
  echo "usage: $0 <gsc-token>" >&2
  echo "get it from https://search.google.com/search-console → Settings →" >&2
  echo "Ownership verification → HTML tag (copy only the content= value)" >&2
  exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INDEX="$ROOT/frontend/index.html"

if ! grep -q 'REPLACE_WITH_GSC_TOKEN' "$INDEX"; then
  echo "note: placeholder not found in $INDEX — token may already be set:" >&2
  grep -o '<meta name="google-site-verification"[^>]*>' "$INDEX" >&2
  exit 1
fi

# LC_ALL/-i '' keeps this portable on macOS's BSD sed.
LC_ALL=C sed -i '' "s|REPLACE_WITH_GSC_TOKEN|${TOKEN}|" "$INDEX"
echo "set token in frontend/index.html"

cd "$ROOT/frontend"
# API_URL must point at a live backend or the build silently ships 0 essays.
API_URL="${API_URL:-http://localhost:8010}" npm run build

cd "$ROOT"
rm -rf worker/public
cp -r frontend/dist worker/public

cd "$ROOT/worker"
uv run pywrangler deploy

echo
echo "verifying live…"
sleep 8
curl -s --max-time 30 https://theincurablehumanist.com/ \
  | grep -o '<meta name="google-site-verification"[^>]*>' \
  || echo "WARNING: tag not found on live site"
