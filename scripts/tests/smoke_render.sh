#!/usr/bin/env bash
# Smoke test of the Docker image: renders the demo fixture of each tool with the official `render`
# command (the ggtime one runs real R code with ggtime) and checks that Claude Code can log in.
#
#   scripts/tests/smoke_render.sh            (from the repository root, after `docker build -t tig-eval:1 env/`)
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
IMAGE="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["image"])' "$ROOT/scripts/run_config.json")"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fail=0

echo "== versions in $IMAGE"
docker run --rm "$IMAGE" cat /opt/versions.txt || { echo "image $IMAGE not found: docker build -t $IMAGE env/"; exit 1; }

for tool_file in "vega-lite spec.vl.json" "time-i-gram spec.json" "d3 index.html" "ggtime plot.R"; do
  set -- $tool_file
  mkdir -p "$TMP/$1" && chmod 777 "$TMP/$1"
  cp "$ROOT"/gallery/fixtures/runs/E2/"$1"/*/"$2" "$TMP/$1/"
  echo; echo "== render $1 ($2)"
  if docker run --rm -v "$TMP/$1:/work" -w /work "$IMAGE" render "$2"; then
    echo "-> OK, screenshot: $TMP/$1/render.png"
  else
    echo "-> FAILED"; fail=1
  fi
done
mkdir -p "$ROOT/results/smoke"
for t in vega-lite time-i-gram d3 ggtime; do [ -f "$TMP/$t/render.png" ] && cp "$TMP/$t/render.png" "$ROOT/results/smoke/$t.png"; done
echo; echo "Screenshots copied to results/smoke/ (look at them)."

echo; echo "== Claude Code login"
[ -f "$ROOT/.env" ] && set -a && . "$ROOT/.env" && set +a
if [ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ] && [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  echo "Both CLAUDE_CODE_OAUTH_TOKEN and ANTHROPIC_API_KEY are set: keep only one."; exit 1
fi
VAR=CLAUDE_CODE_OAUTH_TOKEN; [ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" ] && VAR=ANTHROPIC_API_KEY
if [ -z "${!VAR:-}" ]; then echo "No credential in .env (see env/README.md)."; exit 1; fi
MODEL="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["model"])' "$ROOT/scripts/run_config.json")"
docker run --rm -e "$VAR" "$IMAGE" claude -p "Reply with the single word OK." --model "$MODEL" --max-turns 1 \
  && echo "-> Claude Code works with $VAR and model $MODEL" || { echo "-> Claude Code FAILED"; fail=1; }
exit $fail
