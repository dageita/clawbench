#!/usr/bin/env bash
# Apply ClawBench-friendly OpenClaw config for local vLLM and clear stale run cache.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_CFG="$ROOT/config/openclaw.clawbench.vllm.json"
DEST="${OPENCLAW_STATE_DIR:-$HOME/.openclaw}/openclaw.json"
CACHE_DIR="${CLAWBENCH_RUN_CACHE_DIR:-/data/run_cache}"

if [[ ! -f "$SRC_CFG" ]]; then
  echo "missing $SRC_CFG" >&2
  exit 1
fi

mkdir -p "$(dirname "$DEST")"
cp "$SRC_CFG" "$DEST"
chmod 600 "$DEST"
echo "Wrote ClawBench vLLM config -> $DEST"

if [[ -d "$CACHE_DIR" ]]; then
  rm -rf "$CACHE_DIR"/vllm_Qwen3-32B "$CACHE_DIR"/vllm_Meta-Llama-3.1-8B-Instruct || true
  echo "Cleared stale cache under $CACHE_DIR/vllm_Qwen3-32B (and legacy llama cache)"
fi

cat <<'EOF'

Next steps (required):
1) vLLM must expose >=32768 context AND tool calling, e.g.:
   vllm serve /models/Qwen3-32B \
     --served-model-name Qwen3-32B \
     --max-model-len 32768 \
     --enable-auto-tool-choice \
     --tool-call-parser qwen3_coder \
     --port 8001

2) Cold-restart OpenClaw Gateway so it reloads openclaw.json:
   openclaw gateway stop || true
   export OPENCLAW_GATEWAY_TOKEN=$(python3 - <<'PY'
import json, os
from pathlib import Path
p = Path(os.environ.get("OPENCLAW_STATE_DIR", Path.home()/".openclaw")) / "openclaw.json"
print(json.loads(p.read_text())["gateway"]["auth"]["token"])
PY
)
   openclaw gateway run --port 18789

3) Run smoke test (fresh, no cache):
   cd /src/clawbench
   export OPENCLAW_GATEWAY_TOKEN=...
   uv run clawbench run \
     --model vllm/Qwen3-32B \
     --task t1-fs-quick-note \
     --runs 1 \
     -o results/smoke_test.json
EOF
