"""Bridge ClawBench CLI to KVCOMM OpenClaw bench drivers."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _kvcomm_openclaw_root() -> Path:
    env = os.environ.get("KVCOMM_OPENCLAW_ROOT", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    # clawbench package lives at /src/clawbench; KVCOMM is sibling /src/KVCOMM
    return Path(__file__).resolve().parents[2] / "KVCOMM" / "openclaw"


def _tasks_kvcomm_root() -> Path:
    return Path(__file__).resolve().parents[1].parent / "tasks-kvcomm"


def _default_dataset(task_profile: str) -> Path:
    bench_root = _kvcomm_openclaw_root().parent / "experiments" / "bench"
    if task_profile == "clawbench":
        return bench_root / "datasets" / "tier1_clawbench.jsonl"
    return bench_root / "datasets" / "tier0_copy.jsonl"


def _build_cli_command(
    *,
    capability: bool,
    model: str,
    runs: int,
    warmup_runs: int,
    agent_count: int,
    task_id: str | None,
    output: str | None,
    output_dir: str | None,
    experiment_id: str,
    agent_id: str,
    inference_mode: str,
    inference_backend: str,
    dry_run: bool,
    scenario: str | None,
    dataset: str | None,
    task_profile: str = "copy",
    judge_model: str = "",
    skip_score: bool = False,
) -> list[str]:
    cli = _kvcomm_openclaw_root() / "cli.mjs"
    subcommand = "bench run-clawbench" if capability else "bench run"
    cmd = ["node", str(cli), *subcommand.split()]

    if agent_count:
        cmd.extend(["--agent-count", str(agent_count)])
    if runs:
        cmd.extend(["--measure-runs", str(runs)])
    if warmup_runs:
        cmd.extend(["--warmup-runs", str(warmup_runs)])
    if model:
        cmd.extend(["--model", model])
    if task_id:
        cmd.extend(["--task-id", task_id])
    if output:
        cmd.extend(["--output", output])
    if output_dir:
        cmd.extend(["--output-dir", output_dir])
    if experiment_id:
        cmd.extend(["--experiment-id", experiment_id])
    if agent_id:
        cmd.extend(["--agent-id", agent_id])
    if inference_mode:
        cmd.extend(["--inference-mode", inference_mode])
    if inference_backend:
        cmd.extend(["--inference-backend", inference_backend])
    if dry_run:
        cmd.append("--dry-run")
    if scenario:
        cmd.extend(["--scenario", scenario])
    if capability:
        dataset_path = dataset or str(_default_dataset("clawbench"))
    else:
        dataset_path = dataset or str(_default_dataset(task_profile))
    cmd.extend(["--dataset", dataset_path])
    if not capability and task_profile:
        cmd.extend(["--task-profile", task_profile])
    if capability and judge_model:
        cmd.extend(["--judge-model", judge_model])
    if capability and skip_score:
        cmd.append("--skip-score")
    return cmd


def run_kvcomm_bench(
    *,
    model: str = "",
    runs: int = 1,
    warmup_runs: int = 0,
    agent_count: int = 3,
    topology: str = "chain",
    task_id: str | None = None,
    output: str | None = None,
    output_dir: str | None = None,
    experiment_id: str = "kvcomm-openclaw",
    agent_id: str = "main",
    inference_mode: str = "dense_prefill",
    inference_backend: str = "vllm_direct",
    dry_run: bool = False,
    scenario: str | None = None,
    dataset: str | None = None,
    gateway_token: str = "",
    task_profile: str = "copy",
) -> tuple[int, Path | None, Path | None]:
    del topology  # chain-only for now; scenario file defines topology
    if gateway_token:
        os.environ["OPENCLAW_GATEWAY_TOKEN"] = gateway_token

    if output_dir is None:
        output_dir = str(_tasks_kvcomm_root() / "results")

    cmd = _build_cli_command(
        capability=False,
        model=model,
        runs=runs,
        warmup_runs=warmup_runs,
        agent_count=agent_count,
        task_id=task_id,
        output=output,
        output_dir=output_dir,
        experiment_id=experiment_id,
        agent_id=agent_id,
        inference_mode=inference_mode,
        inference_backend=inference_backend,
        dry_run=dry_run,
        scenario=scenario,
        dataset=dataset,
        task_profile=task_profile,
    )

    proc = subprocess.run(cmd, cwd=str(_kvcomm_openclaw_root()), check=False)
    jsonl_path, summary_path = _resolve_output_paths(output, output_dir, experiment_id)
    return proc.returncode, jsonl_path, summary_path


def run_kvcomm_clawbench(
    *,
    model: str = "",
    runs: int = 1,
    warmup_runs: int = 0,
    agent_count: int = 3,
    task_id: str | None = None,
    output: str | None = None,
    output_dir: str | None = None,
    experiment_id: str = "clawbench-chain",
    agent_id: str = "main",
    inference_mode: str = "dense_prefill",
    inference_backend: str = "vllm_direct",
    dry_run: bool = False,
    scenario: str | None = None,
    dataset: str | None = None,
    gateway_token: str = "",
    judge_model: str = "",
    skip_score: bool = False,
) -> tuple[int, Path | None, Path | None]:
    if gateway_token:
        os.environ["OPENCLAW_GATEWAY_TOKEN"] = gateway_token

    if output_dir is None:
        output_dir = str(_tasks_kvcomm_root() / "results")

    cmd = _build_cli_command(
        capability=True,
        model=model,
        runs=runs,
        warmup_runs=warmup_runs,
        agent_count=agent_count,
        task_id=task_id,
        output=output,
        output_dir=output_dir,
        experiment_id=experiment_id,
        agent_id=agent_id,
        inference_mode=inference_mode,
        inference_backend=inference_backend,
        dry_run=dry_run,
        scenario=scenario,
        dataset=dataset,
        judge_model=judge_model,
        skip_score=skip_score,
    )

    proc = subprocess.run(cmd, cwd=str(_kvcomm_openclaw_root()), check=False)
    jsonl_path, summary_path = _resolve_output_paths(output, output_dir, experiment_id)
    return proc.returncode, jsonl_path, summary_path


def _resolve_output_paths(
    output: str | None,
    output_dir: str | None,
    experiment_id: str,
) -> tuple[Path | None, Path | None]:
    if not output_dir:
        return None, None
    base_dir = Path(output_dir)
    if output:
        name = output.removesuffix(".jsonl").removesuffix(".summary.json")
        if "/" in name or "\\" in name:
            jsonl = Path(name).with_suffix(".jsonl")
        else:
            jsonl = base_dir / f"{name}.jsonl"
    else:
        jsonl = None
        summary = None
        if base_dir.exists():
            candidates = sorted(base_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
            if candidates:
                jsonl = candidates[0]
        if jsonl is None:
            return None, None
    summary = jsonl.with_suffix(".summary.json")
    return jsonl, summary if summary.exists() else None
