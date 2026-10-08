# RAGAM Artifact Repository: Runtime Agentic Governance, Assessment, and Mitigation

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Benchmark: tau2-bench](https://img.shields.io/badge/benchmarks-tau2--bench-orange.svg)](https://github.com/sierra-research/tau2-bench)

This repository contains the source code, empirical simulation logs, execution audit ledgers, and analytical evaluation pipelines for the research paper:

> **RAGAM: Runtime Control Architecture for Autonomous AI Agents**

---

## 📁 Repository Structure

The artifact is organized into two primary root folders:

```text
.
├── ragam/
│   ├── ragam_tau2_pep.py          # Primary RAGAM PEP Gateway & in-process runner
│   ├── ragam_shadow_eval.py       # Counterfactual shadow auditor (PVR & drift engine)
│   ├── ragam_analysis.ipynb       # Jupyter notebook for cross-model verification & figures
│
└── tau2-bench/                    # Instrumented tau2-bench benchmark repository
    ├── data/
    │   ├── retail/                # Retail domain task definitions (114 tasks), db.json, policy.md
    │   └── simulations/           # Experimental simulation directories
    │       ├── raw_llama8b_retail/           # Stage 1.a raw baseline (Llama 3.1 8B Instruct)
    │       ├── raw_gemini25flash_retail/     # Stage 1.a raw baseline (Gemini 2.5 Flash)
    │       ├── raw_deepseekv3_retail/        # Stage 1.a raw baseline (DeepSeek-V3)
    │       ├── raw_qwen72b_retail/           # Stage 1.a raw baseline (Qwen 2.5 72B Instruct)
    │       ├── raw_gpt4o_retail/             # Stage 1.a raw baseline (GPT-4o)
    │       ├── ragam_llama8b_retail/         # Stage 2 governed run (Llama 3.1 8B Instruct)
    │       ├── ragam_gemini25flash_retail/   # Stage 2 governed run (Gemini 2.5 Flash)
    │       ├── ragam_deepseekv3_retail/      # Stage 2 governed run (DeepSeek-V3)
    │       ├── ragam_qwen72b_retail/         # Stage 2 governed run (Qwen 2.5 72B Instruct)
    │       └── ragam_gpt4o_retail/           # Stage 2 governed run (GPT-4o)
    ├── pyproject.toml
    └── src/
```

## 🔬 Experimental Lifecycle Overview

The empirical evaluation tests autonomous agent models across all 114 multi-turn tasks in the standardized retail domain of the $\tau^2$-bench benchmark suite:

| Stage | Mode | Execution Command / Script | Primary Artifacts Produced |
| :--- | :--- | :--- | :--- |
| **Stage 1.a** | Unconstrained Baseline | `tau2 run` via `tau2-bench` | `results.json` (unassisted agent execution trace and dialogue turns) |
| **Stage 1.b** | Counterfactual Shadow Audit | `python3 ragam_shadow_eval.py` | `raw_<model>_retail_evals.json` (computed Policy Violation Rates, invariant breach counts, and counterfactual tier breakdown) |
| **Stage 2** | Live Closed-Loop Governance | `python3 ragam_tau2_pep.py --closed-loop` | • `results.json` (governed dialogue and task outcomes)<br>• `ledger_<model>_ragam.jsonl` (per-action audit telemetry)<br>• `ragam_overhead.json` (authoritative latency percentiles and tier distribution) |

> **User Simulator Standard:** Across all benchmark evaluations (both unconstrained baselines and governed closed-loop runs), the customer was consistently simulated by `gpt-4o-mini` at temperature `0.0` to ensure uniform scenario difficulty and conversational consistency.


## 🚀 Quickstart: Reproducing Evaluation Results & Plots

Reviewers can inspect the complete empirical evaluation, verify statistical parity, and reproduce all figures without executing new LLM inferences.

### 1. Environment Setup


### 1. Environment Setup

```
bash

cd ragam
python3 -m venv venv
source venv/bin/activate
pip install notebook pandas matplotlib numpy
```

### 2. Launch the Analysis Notebook
```
bash
jupyter notebook ragam_analysis.ipynb
```

**Execute cells sequentially**:
- **Cell 1 (Environment Setup & Ingestion)**: Loads simulation artifacts (`results.json`, `ragam_overhead.json`, `ledger_*.jsonl`) for the active model directly from tau2-bench/data/simulations/.
- **Cell 2 (Latency Profiling)**: Computes deterministic gateway traversal latency ($t_{\text{det}}$) and live auxiliary semantic drift latency ($t_{\text{sem}}$).
- **Cell 3 (Autonomy Preservation & Continuity):** Ingests the authoritative `mitigation_tier_distribution` directly from `ragam_overhead.json` (with audit ledger cross-verification) to quantify workflow continuity preserved by Tier 2 in-flight PII masking.- **Cell 4a & 4b (Qualitative Trace Auditors)**: Provides step-by-step audit trails and conversational transcript inspection for high-severity escalations (Tiers 3 & 4) and compliant tool hops (Tiers 1 & 2).
- **Cell 5 (Multi-Model Metric Compiler):** Iterates across all five evaluated foundation models, ingesting their authoritative runtime summary files (`ragam_overhead.json`, `results.json`) and raw execution ledgers to compile cross-model governance benchmarks, tier distributions, and latency percentiles into consolidated DataFrames (`df_phase3_overview` and `df_phase3_tiers`).
- **Cell 6 (Visualizations)**: Generates publication-ready figures displaying four-tier mitigation distributions and runtime latency bounds.

**⚠️ Note on Reproducibility & Variance**
- **Model Inference Non-Determinism**: LLM generations are inherently stochastic; live re-runs of Stage 1.a or Stage 2 with commercial model APIs will produce variations in natural-language dialogue, hop counts, and reasoning paths.
- **Deterministic Log Analysis**: All analytical summaries, tier distributions, and breach audits derived from the recorded simulation logs are 100% deterministic and match the figures presented in the paper.
- **Empirical Latency Variance**: Live gateway latency ($t_{\text{det}}$) and semantic feature-hashing passes ($t_{\text{sem}}$) are measured at microsecond resolution ($\mu\text{s}$) and will naturally fluctuate depending on the evaluator's host CPU architecture, clock scaling, and operating system scheduling jitter. As shown in the paper, all configurations remain strictly within sub-millisecond $\mathcal{O}(1)$ bounds.

## ⚡ Step-by-Step Guide: Executing New Model Runs
To execute fresh simulations, configure your API keys:
```
bash
export OPENROUTER_API_KEY="sk-or-v1-..."
```
**Step 1: Stage 1.a — Execute Raw Unconstrained Baseline**
Run an unassisted agent across the 114 retail tasks:
```
bash
cd tau2-bench

# Example: Meta Llama 3.1 8B Instruct
TAU2_EVAL_MODEL="openrouter/openai/gpt-4o-mini" uv run tau2 run \
  --domain retail \
  --agent-llm openrouter/meta-llama/llama-3.1-8b-instruct \
  --user-llm openrouter/openai/gpt-4o-mini \
  --max-concurrency 1 \
  --max-steps 40 \
  --save-to raw_llama8b_retail
```

**Step 2: Stage 1.b — Counterfactual Shadow-Mode Audit**
Replay the unassisted baseline trajectory through the RAGAM PEP engine to evaluate intrinsic Policy Violation Rates (PVR) without intervening in execution:
```
bash
cd ragam

# Audit the unassisted Llama 3.1 8B baseline
python3 ragam_shadow_eval.py \
  --sim-file ../tau2-bench/data/simulations/raw_llama8b_retail/results.json \
  --output-json ../tau2-bench/data/simulations/raw_llama8b_retail/raw_llama8b_retail_evals.json
```

**Step 3: Stage 2 — Active Closed-Loop Governed Execution**
Deploy the model under live, synchronous RAGAM in-process policy enforcement:
```
bash
cd ragam

# Execute governed run for Llama 3.1 8B Instruct
python3 ragam_tau2_pep.py \
  --closed-loop \
  --agent-llm openrouter/meta-llama/llama-3.1-8b-instruct \
  --user-llm openrouter/openai/gpt-4o-mini \
  --eval-llm openrouter/openai/gpt-4o-mini \
  --max-concurrency 1 \
  --save-to ragam_llama8b_retail
```
Outputs produced in `tau2-bench/data/simulations/ragam_llama8b_retail/`:

1. `results.json`: Complete simulation traces under active governance.
2. `ledger_meta-llama_llama-3.1-8b-instruct_ragam.jsonl`: Real-time line-delimited audit ledger of each intercepted action.
3. `ragam_overhead.json`: Authoritative latency percentiles and mitigation tier counts.

Executing Other Foundation Models
To evaluate other models, substitute the --agent-llm and --save-to parameters as documented. 


## 📊 Authoritative Empirical Telemetry Summary

The table below summarizes the authoritative multi-model benchmark telemetry compiled across all 3,988 synchronously intercepted actions in Stage 2:

| Foundation Model | Evaluated Actions | Tier 1 (Permitted) | Tier 2 (Masked PII) | Tier 3 (HITL Pause) | Tier 4 (Circuit Breaker) | Continuity (T1+T2) | Gateway Latency ($t_{\text{det}}$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Meta Llama 3.1 8B** | 935 | 241 (25.8%) | 493 (52.7%) | 169 (18.1%) | 32 (3.4%) | **78.50%** | $73.32\,\mu\text{s}$ |
| **Google Gemini 2.5 Flash** | 621 | 294 (47.3%) | 316 (50.9%) | 11 (1.8%) | 0 (0.0%) | **98.23%** | $73.31\,\mu\text{s}$ |
| **DeepSeek-V3** | 700 | 339 (48.4%) | 348 (49.7%) | 13 (1.9%) | 0 (0.0%) | **98.14%** | $73.48\,\mu\text{s}$ |
| **Alibaba Qwen 2.5 72B** | 827 | 379 (45.8%) | 425 (51.4%) | 22 (2.7%) | 1 (0.1%) | **97.22%** | $74.39\,\mu\text{s}$ |
| **OpenAI GPT-4o** | 905 | 483 (53.4%) | 405 (44.8%) | 17 (1.9%) | 0 (0.0%) | **98.12%** | $70.12\,\mu\text{s}$ |
| **Total / Macro Average** | **3,988** | **1,736 (43.5%)** | **1,987 (49.8%)** | **232 (5.8%)** | **33 (0.8%)** | **93.36%** | **$72.92\,\mu\text{s}$** |


## 🔒 Execution Audit Ledger Schema
Each line in `ledger_<model>_ragam.jsonl` contains an atomic telemetry event emitted by the PEP gateway:

```
JSON
{
  "timestamp": "2026-09-18T10:15:20.716779",
  "task_id": "1",
  "attempt": 1,
  "hop": 7,
  "tool_name": "exchange_delivered_order_items",
  "auth_verified": true,
  "s_asset": 7.5,
  "t_dest": 0.85,
  "a_agent": 2.0,
  "d_stat": 0.0,
  "d_goal": 0.3,
  "gamma_context": 1.485,
  "rs_base": 4.195,
  "dynamic_risk_score": 6.23,
  "w1": 0.5,
  "w2": 0.3,
  "w3": 0.2,
  "beta1": 2.5,
  "beta2": 1.5,
  "mitigation_tier": "Tier 2: Masked PII",
  "action_status": "MASKED_PAYLOAD",
  "detected_pii": [],
  "latency_us": 95.364
}
```

