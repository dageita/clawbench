#!/usr/bin/env bash
# Preflight checks before running ClawBench against local vLLM.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE="${OPENCLAW_STATE_DIR:-$HOME/.openclaw}"
CFG="$STATE/openclaw.json"
TOKEN="${OPENCLAW_GATEWAY_TOKEN:-}"

if [[ -z "$TOKEN" && -f "$CFG" ]]; then
  TOKEN="$(python3 - <<PY
import json
from pathlib import Path
print(json.loads(Path("$CFG").read_text())["gateway"]["auth"]["token"])
PY
)"
fi

fail=0
warn() { echo "WARN: $*"; }
die() { echo "ERROR: $*"; fail=1; }

echo "== ClawBench vLLM preflight =="

if [[ ! -f "$CFG" ]]; then
  die "missing $CFG — run bash scripts/setup_vllm_clawbench.sh"
else
  echo "OK  openclaw.json -> $CFG"
fi

BASE_URL="$(python3 - <<PY 2>/dev/null || true
import json
from pathlib import Path
cfg = json.loads(Path("$CFG").read_text())
print(cfg["models"]["providers"]["vllm"]["baseUrl"].rstrip("/"))
PY
)"
if [[ -z "$BASE_URL" ]]; then
  die "could not read models.providers.vllm.baseUrl from $CFG"
else
  echo "OK  vLLM baseUrl -> $BASE_URL"
fi

if curl -sf --connect-timeout 3 "$BASE_URL/models" >/dev/null; then
  echo "OK  vLLM reachable at $BASE_URL"
else
  die "vLLM not reachable at $BASE_URL"
fi

if [[ -n "$TOKEN" ]] && curl -sf -H "Authorization: Bearer $TOKEN" http://127.0.0.1:18789/health >/dev/null; then
  echo "OK  OpenClaw gateway health"
else
  die "OpenClaw gateway not healthy on :18789 (set OPENCLAW_GATEWAY_TOKEN and start gateway)"
fi

TOOL_NONE="$(python3 - <<PY 2>/dev/null || true
import json
from pathlib import Path
cfg = json.loads(Path("$CFG").read_text())
models = cfg.get("agents", {}).get("defaults", {}).get("models", {})
for ref, spec in models.items():
    tc = spec.get("params", {}).get("extra_body", {}).get("tool_choice")
    if tc == "none":
        print(ref)
PY
)"
if [[ -n "$TOOL_NONE" ]]; then
  die "tool_choice=none still set for: $TOOL_NONE (ClawBench tasks need file/edit tools)"
else
  echo "OK  no tool_choice=none override on vLLM model"
fi

if [[ "$fail" -ne 0 ]]; then
  echo
  echo "Preflight failed. Fix the items above, then:"
  echo "  export PATH=/usr/bin:\$PATH   # OpenClaw needs Node >=22"
  echo "  bash $ROOT/scripts/setup_vllm_clawbench.sh"
  echo "  openclaw gateway run --port 18789"
  exit 1
fi

echo "Preflight passed. Example run:"
echo "  cd $ROOT"
echo "  export OPENCLAW_GATEWAY_TOKEN=$TOKEN"
echo "  uv run clawbench run --model vllm/Qwen3-32B --task t1-fs-quick-note --runs 1 -o results/smoke_test.json"
