# ClawBench KVCOMM lane（薄封装）

**主开发位置**：[`KVCOMM/openclaw/`](../../KVCOMM/openclaw/README.md)

本目录将 benchmark 调用转发至 KVCOMM 项目的 `openclaw` 模块，不在此重复维护 spawn/TTFT 逻辑。

## 用法

```bash
cd tasks-kvcomm
npm run dry-run
npm run run -- --agent-count 3 --measure-runs 10 --model vllm/Qwen3-32B
```

Sidecar 模式：

```bash
# 在 KVCOMM/openclaw 启动 sidecar + setup sidecar profile 后
npm run run -- \
  --inference-mode kv_reuse \
  --inference-backend kvcomm_sidecar \
  --warmup-runs 2 \
  --measure-runs 10 \
  --model kvcomm/Qwen3-32B
```

## 前置

- OpenClaw Gateway 运行中
- 配置由 `KVCOMM/openclaw/scripts/setup-openclaw.sh` 应用
- 预检：`KVCOMM/openclaw/scripts/preflight.sh`
