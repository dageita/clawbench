#!/usr/bin/env node
/**
 * ClawBench thin wrapper — delegates to KVCOMM openclaw module (canonical implementation).
 *
 * Usage (from clawbench repo):
 *   cd tasks-kvcomm && npm run run -- --agent-count 3 --measure-runs 10
 */

import { spawn } from "node:child_process";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const CLAWBENCH_ROOT = resolve(__dirname, "../..");
const KVCOMM_CLI = resolve(CLAWBENCH_ROOT, "../KVCOMM/openclaw/cli.mjs");

const args = process.argv.slice(2);
const child = spawn(process.execPath, [KVCOMM_CLI, "bench", "run", ...args], {
  stdio: "inherit",
  env: process.env,
});

child.on("exit", (code) => process.exit(code ?? 1));
