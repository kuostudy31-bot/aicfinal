#!/usr/bin/env bash
# Build <studentID>-final-project.zip from this folder, including the full hidden .git/.
# Usage: scripts/make_submission.sh <studentID>
set -euo pipefail
ID="${1:?usage: scripts/make_submission.sh <studentID>}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

[ "$(git rev-parse --is-shallow-repository)" = "false" ] || { echo "shallow clone: run 'git fetch --unshallow' first"; exit 1; }
[ -z "$(git status --porcelain)" ] || { echo "uncommitted changes: commit them first"; git status --short; exit 1; }
if git grep -nIE 'sk-ant-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY' -- . ':!scripts/make_submission.sh' >/dev/null; then
  echo "possible secret found in tracked files; aborting"; exit 1
fi
python3 scripts/check.py >/dev/null 2>&1 || { echo "tests fail: fix before submitting"; exit 1; }

NAME="$(basename "$ROOT")"
OUT="$(dirname "$ROOT")/${ID}-final-project.zip"
rm -f "$OUT"
cd "$(dirname "$ROOT")"
# Includes hidden files and .git; leaves out re-creatable caches and local logs.
zip -qr "$OUT" "$NAME" -x "$NAME/temp/*" "$NAME/data/cache/*" "$NAME/.logs/*" "$NAME/.state/*" "*/__pycache__/*"
echo "wrote $OUT ($(du -h "$OUT" | cut -f1)); commits: $(git -C "$ROOT" rev-list --count HEAD)"
unzip -l "$OUT" | grep -c "$NAME/.git/" | xargs -I{} echo "{} entries under .git/"
