
# Model Benchmarking Runs (Raw vs RAGAM))

Stage 1.a (tau2 run) - ungoverned baseline runs.

Stage 1.b (ragam_shadow_eval.py) reads results.json from Stage 1.a and writes raw_<model>_retail_evals.json.

Stage 2 (ragam_tau2_pep.py) - governed closed-loop tau2 runs.

Note - While the customer support bot agent used different models to evaluate performance, the customer was represented consistently by GPT-4o-mini across all runs.  

## 1. Meta Llama 3.1 8B Instruct

#Stage 1.a.: Raw Unconstrained Baseline (tau2-bench)
```
  cd ~/workspace/tau2-bench
  TAU2_EVAL_MODEL="openrouter/openai/gpt-4o-mini" uv run tau2 run \
    --domain retail \
    --agent-llm openrouter/meta-llama/llama-3.1-8b-instruct \
    --user-llm openrouter/openai/gpt-4o-mini \
    --max-concurrency 2 \
    --max-steps 40 \
    --save-to raw_llama8b_retail \
 
  ```
#Stage 1.a. Output
```
═══ Overview ═══
Total Simulations 114
⚠️ Infra Errors 3 (excluded from metrics below)
Evaluated 111
Total Tasks 111

═══ Reward Metrics ═══
🏆 Average Reward 0.0541
Pass^1 0.054
💰 Avg Cost/Conversation $0.0027

═══ Action Metrics ═══
📖 Read Actions 53/222 (23.9%)
✏️ Write Actions 5/103 (4.9%)

═══ DB Match ═══
🗄️ DB Match ✓ 13 / ✗ 59 (18.1%)

═══ Authentication ═══
Not Checked 111

═══ Termination ═══
🛑 Normal Stop 72 (👤 72 / 🤖 0)
⏱️ Max Steps 34
💥 Error 5
🔌 Infra Error 3

═══ LLM Judge Review ═══
🤖 Agent Errors 0 errors
Sims by severity -
👤 User Errors 0 errors
Sims by severity -

```

#Stage 1.b.: Shadow Evaluation Audit (ragam)
```
cd ~/workspace/ragam

python3 ragam_shadow_eval.py \
  --sim-file ~/workspace/tau2-bench/data/simulations/raw_llama8b_retail/results.json \
  --output-json ~/workspace/tau2-bench/data/simulations/raw_llama8b_retail/raw_llama8b_retail_evals.json

  ```

#Stage 1.b. Outputs
```
================================================================================
 RAGAM COUNTERFACTUAL SHADOW-MODE AUDIT REPORT
 (Native Engine: RAGAMPepGateway from ragam_tau2_pep.py)
================================================================================
 Total Baseline Tasks Analyzed : 114
 Policy Violation Rate (PVR)   :  21.05% (24 breached tasks)
 Total Intercepted Tool Hops   : 835
 Mean Hops per Task            : 7.32 (Max: 13)
 Average PEP Decision Latency  : 0.0128 ms / action

--------------------------------------------------------------------------------
 COUNTERFACTUAL MITIGATION TIER DISTRIBUTION
--------------------------------------------------------------------------------
 Tier 1: Permitted               :  374 calls ( 44.8%)
 Tier 2: Masked PII              :  343 calls ( 41.1%)
 Tier 3: HITL Pause              :   79 calls (  9.5%)
 Tier 4: Circuit Breaker         :   39 calls (  4.7%)

--------------------------------------------------------------------------------
 INVARIANT BREACHES MITIGATED IN SHADOW MODE
--------------------------------------------------------------------------------
 AUTH_BREACH_UNAUTHENTICATED_WRITE   :   28 occurrences
 UNCONFIRMED_MUTATION_BREACH         :   36 occurrences
================================================================================

```

#Stage 2: Closed-Loop Governed Run (ragam)

```
cd ~/workspace/ragam

python3 ragam_tau2_pep.py \
  --closed-loop \
  --agent-llm openrouter/meta-llama/llama-3.1-8b-instruct \
  --user-llm openrouter/openai/gpt-4o-mini \
  --eval-llm openrouter/openai/gpt-4o-mini \
  --max-concurrency 1 \
  --save-to ragam_llama8b_retail
```

#Stage 2 Outputs
```
═══ Overview ═══
Total Simulations 114
Total Tasks 114

═══ Reward Metrics ═══
🏆 Average Reward 0.0263
Pass^1 0.026
💰 Avg Cost/Conversation $0.0023

═══ Action Metrics ═══
📖 Read Actions 32/237 (13.5%)
✏️ Write Actions 0/88 (0.0%)

═══ DB Match ═══
🗄️ DB Match ✓ 8 / ✗ 58 (12.1%)

═══ Authentication ═══
Not Checked 114

═══ Termination ═══
🛑 Normal Stop 66 (👤 66 / 🤖 0)
⏱️ Max Steps 41
💥 Error 7

═══ LLM Judge Review ═══
🤖 Agent Errors 0 errors
Sims by severity -
👤 User Errors 0 errors
Sims by severity -

================================================================================
 RAGAM LIVE INLINE OVERHEAD SUMMARY (935 Actions Intercepted)
================================================================================
 Mean Overhead Per Hop      : 73.317 μs
 Median (p50) Overhead      : 75.934 μs
 95th Percentile (p95)      : 114.784 μs
 Total Gateway Time (Batch) : 68551.068 μs
--------------------------------------------------------------------------------
 MITIGATION TIERS APPLIED:
   Tier 1: Permitted             :  241 ( 25.8%)
   Tier 2: Masked PII            :  493 ( 52.7%)
   Tier 3: HITL Pause            :  169 ( 18.1%)
   Tier 4: Circuit Breaker       :   32 (  3.4%)
================================================================================

```


#-----------------------------------------------------------------------------------------------------------<br>
#-----------------------------------------------------------------------------------------------------------<br>
#-----------------------------------------------------------------------------------------------------------<br>
#-----------------------------------------------------------------------------------------------------------<br>

## 2. Google Gemini 2.5 Flash

#Stage 1.a.: Raw Unconstrained Baseline (tau2-bench)
```
cd ~/workspace/tau2-bench
TAU2_EVAL_MODEL="openrouter/openai/gpt-4o-mini" uv run tau2 run \
  --domain retail \
  --agent-llm openrouter/google/gemini-2.5-flash \
  --user-llm openrouter/openai/gpt-4o-mini \
  --max-concurrency 2 \
  --max-steps 40 \
  --save-to raw_gemini25flash_retail
```

#Stage 1.a. Output
```
═══ Overview ═══
Total Simulations 114
Total Tasks 114

═══ Reward Metrics ═══
🏆 Average Reward 0.3772
Pass^1 0.377
💰 Avg Cost/Conversation $0.0081

═══ Action Metrics ═══
📖 Read Actions 227/310 (73.2%)
✏️ Write Actions 60/130 (46.2%)

═══ DB Match ═══
🗄️ DB Match ✓ 48 / ✗ 48 (50.0%)

═══ Authentication ═══
Not Checked 114

═══ Termination ═══
🛑 Normal Stop 96 (👤 96 / 🤖 0)
⏱️ Max Steps 18

═══ LLM Judge Review ═══
🤖 Agent Errors 0 errors
Sims by severity -
👤 User Errors 0 errors
Sims by severity -

```

#Stage 1.b.: Shadow Evaluation Audit (ragam)
```
cd ~/workspace/ragam
python3 ragam_shadow_eval.py \
  --sim-file ~/workspace/tau2-bench/data/simulations/raw_gemini25flash_retail/results.json \
  --output-json ~/workspace/tau2-bench/data/simulations/raw_gemini25flash_retail/raw_gemini25flash_retail_evals.json
```
#Stage 1.b. Outputs
```
================================================================================
 RAGAM COUNTERFACTUAL SHADOW-MODE AUDIT REPORT
 (Native Engine: RAGAMPepGateway from ragam_tau2_pep.py)
================================================================================
 Total Baseline Tasks Analyzed : 114
 Policy Violation Rate (PVR)   :  24.56% (28 breached tasks)
 Total Intercepted Tool Hops   : 660
 Mean Hops per Task            : 5.79 (Max: 13)
 Average PEP Decision Latency  : 0.0127 ms / action

--------------------------------------------------------------------------------
 COUNTERFACTUAL MITIGATION TIER DISTRIBUTION
--------------------------------------------------------------------------------
 Tier 1: Permitted               :  296 calls ( 44.8%)
 Tier 2: Masked PII              :  347 calls ( 52.6%)
 Tier 3: HITL Pause              :   17 calls (  2.6%)
 Tier 4: Circuit Breaker         :    0 calls (  0.0%)

--------------------------------------------------------------------------------
 INVARIANT BREACHES MITIGATED IN SHADOW MODE
--------------------------------------------------------------------------------
 UNCONFIRMED_MUTATION_BREACH         :   38 occurrences
================================================================================

```

#Stage 2: Closed-Loop Governed Run (ragam)
```
cd ~/workspace/ragam
python3 ragam_tau2_pep.py \
  --closed-loop \
  --agent-llm openrouter/google/gemini-2.5-flash \
  --user-llm openrouter/openai/gpt-4o-mini \
  --eval-llm openrouter/openai/gpt-4o-mini \
  --max-concurrency 1 \
  --save-to ragam_gemini25flash_retail
```

#Stage 2 Outputs
```
═══ Overview ═══
Total Simulations 114
Total Tasks 114

═══ Reward Metrics ═══
🏆 Average Reward 0.2281
Pass^1 0.228
💰 Avg Cost/Conversation $0.0069

═══ Action Metrics ═══
📖 Read Actions 176/278 (63.3%)
✏️ Write Actions 27/122 (22.1%)

═══ DB Match ═══
🗄️ DB Match ✓ 29 / ✗ 62 (31.9%)

═══ Authentication ═══
Not Checked 114

═══ Termination ═══
🛑 Normal Stop 91 (👤 91 / 🤖 0)
⏱️ Max Steps 23

═══ LLM Judge Review ═══
🤖 Agent Errors 0 errors
Sims by severity -
👤 User Errors 0 errors
Sims by severity -


================================================================================
 RAGAM LIVE INLINE OVERHEAD SUMMARY (621 Actions Intercepted)
================================================================================
 Mean Overhead Per Hop      : 73.310 μs
 Median (p50) Overhead      : 72.810 μs
 95th Percentile (p95)      : 116.397 μs
 Total Gateway Time (Batch) : 45525.382 μs
--------------------------------------------------------------------------------
 MITIGATION TIERS APPLIED:
   Tier 1: Permitted             :  294 ( 47.3%)
   Tier 2: Masked PII            :  316 ( 50.9%)
   Tier 3: HITL Pause            :   11 (  1.8%)
   Tier 4: Circuit Breaker       :    0 (  0.0%)
================================================================================


```

#-----------------------------------------------------------------------------------------------------------<br>
#-----------------------------------------------------------------------------------------------------------<br>
#-----------------------------------------------------------------------------------------------------------<br>
#-----------------------------------------------------------------------------------------------------------<br>

## 3. DeepSeek-V3

#Stage 1.a.: Raw Unconstrained Baseline (tau2-bench)

```
#Switched max concurrency to 1 to minimize rate limiting failures

cd ~/workspace/tau2-bench
LITELLM_REQUEST_TIMEOUT=45 TAU2_EVAL_MODEL="openrouter/openai/gpt-4o-mini" uv run tau2 run \
  --domain retail \
  --agent-llm openrouter/deepseek/deepseek-chat \
  --user-llm openrouter/openai/gpt-4o-mini \
  --max-concurrency 1 \
  --max-steps 40 \
  --save-to raw_deepseekv3_retail
```

#Stage 1.a. Output
```
═══ Overview ═══
Total Simulations 114
⚠️ Infra Errors 3 (excluded from metrics below)
Evaluated 111
Total Tasks 111

═══ Reward Metrics ═══
🏆 Average Reward 0.3514
Pass^1 0.351
💰 Avg Cost/Conversation $0.0295

═══ Action Metrics ═══
📖 Read Actions 204/281 (72.6%)
✏️ Write Actions 61/128 (47.7%)

═══ DB Match ═══
🗄️ DB Match ✓ 47 / ✗ 45 (51.1%)

═══ Authentication ═══
Not Checked 111

═══ Termination ═══
🛑 Normal Stop 92 (👤 92 / 🤖 0)
⏱️ Max Steps 19
🔌 Infra Error 3

═══ LLM Judge Review ═══
🤖 Agent Errors 0 errors
Sims by severity -
👤 User Errors 0 errors
Sims by severity -
Sims by severity -

```

#Stage 1.b.: Shadow Evaluation Audit (ragam)
```
cd ~/workspace/ragam
python3 ragam_shadow_eval.py \
  --sim-file ~/workspace/tau2-bench/data/simulations/raw_deepseekv3_retail/results.json \
  --output-json ~/workspace/tau2-bench/data/simulations/raw_deepseekv3_retail/raw_deepseekv3_retail_evals.json
```
#Stage 1.b. Outputs
```
================================================================================
 RAGAM COUNTERFACTUAL SHADOW-MODE AUDIT REPORT
 (Native Engine: RAGAMPepGateway from ragam_tau2_pep.py)
================================================================================
 Total Baseline Tasks Analyzed : 114
 Policy Violation Rate (PVR)   :  19.30% (22 breached tasks)
 Total Intercepted Tool Hops   : 697
 Mean Hops per Task            : 6.11 (Max: 13)
 Average PEP Decision Latency  : 0.0139 ms / action

--------------------------------------------------------------------------------
 COUNTERFACTUAL MITIGATION TIER DISTRIBUTION
--------------------------------------------------------------------------------
 Tier 1: Permitted               :  310 calls ( 44.5%)
 Tier 2: Masked PII              :  367 calls ( 52.7%)
 Tier 3: HITL Pause              :   17 calls (  2.4%)
 Tier 4: Circuit Breaker         :    3 calls (  0.4%)

--------------------------------------------------------------------------------
 INVARIANT BREACHES MITIGATED IN SHADOW MODE
--------------------------------------------------------------------------------
 UNCONFIRMED_MUTATION_BREACH         :   33 occurrences
 AUTH_BREACH_UNAUTHENTICATED_WRITE   :    3 occurrences
================================================================================

```

#Stage 2: Closed-Loop Governed Run (ragam)
```
cd ~/workspace/ragam
python3 ragam_tau2_pep.py \
  --closed-loop \
  --agent-llm openrouter/deepseek/deepseek-chat:nitro \
  --user-llm openrouter/openai/gpt-4o-mini \
  --eval-llm openrouter/openai/gpt-4o-mini \
  --max-concurrency 1 \
  --save-to ragam_deepseekv3_retail
```

#Stage 2 Outputs
```
═══ Reward Metrics ═══
🏆 Average Reward 0.2727
Pass^1 0.273
💰 Avg Cost/Conversation $0.0078

═══ Action Metrics ═══
📖 Read Actions 190/265 (71.7%)
✏️ Write Actions 40/121 (33.1%)

═══ DB Match ═══
🗄️ DB Match ✓ 30 / ✗ 54 (35.7%)

═══ Authentication ═══
Not Checked 99

═══ Termination ═══
🛑 Normal Stop 84 (👤 84 / 🤖 0)
⏱️ Max Steps 15
🔌 Infra Error 15

═══ LLM Judge Review ═══
🤖 Agent Errors 0 errors
Sims by severity -
👤 User Errors 0 errors
Sims by severity -

================================================================================
 RAGAM LIVE INLINE OVERHEAD SUMMARY (700 Actions Intercepted)
================================================================================
 Mean Overhead Per Hop      : 73.482 μs
 Median (p50) Overhead      : 74.449 μs
 95th Percentile (p95)      : 117.195 μs
 Total Gateway Time (Batch) : 51437.621 μs
--------------------------------------------------------------------------------
 MITIGATION TIERS APPLIED:
   Tier 1: Permitted             :  334 ( 47.7%)
   Tier 2: Masked PII            :  353 ( 50.4%)
   Tier 3: HITL Pause            :   13 (  1.9%)
   Tier 4: Circuit Breaker       :    0 (  0.0%)
================================================================================

```


#-----------------------------------------------------------------------------------------------------------<br>
#-----------------------------------------------------------------------------------------------------------<br>
#-----------------------------------------------------------------------------------------------------------<br>
#-----------------------------------------------------------------------------------------------------------<br>

## 4. Alibaba Qwen 2.5 72B Instruct

#Stage 1.a.: Raw Unconstrained Baseline (tau2-bench)
```
cd ~/workspace/tau2-bench
LITELLM_REQUEST_TIMEOUT=45 TAU2_EVAL_MODEL="openrouter/openai/gpt-4o-mini" uv run tau2 run \
  --domain retail \
  --agent-llm openrouter/qwen/qwen-2.5-72b-instruct:nitro \
  --user-llm openrouter/openai/gpt-4o-mini \
  --max-concurrency 1 \
  --max-steps 40 \
  --save-to raw_qwen72b_retail
```

#Stage 1.a. Output
```
═══ Overview ═══
Total Simulations 114
Total Tasks 114

═══ Reward Metrics ═══
🏆 Average Reward 0.2807
Pass^1 0.281
💰 Avg Cost/Conversation $0.0464

═══ Action Metrics ═══
📖 Read Actions 179/248 (72.2%)
✏️ Write Actions 41/103 (39.8%)

═══ DB Match ═══
🗄️ DB Match ✓ 37 / ✗ 45 (45.1%)

═══ Authentication ═══
Not Checked 114

═══ Termination ═══
🛑 Normal Stop 82 (👤 82 / 🤖 0)
⏱️ Max Steps 32

═══ LLM Judge Review ═══
🤖 Agent Errors 0 errors
Sims by severity -
👤 User Errors 0 errors
Sims by severity -

```

#Stage 1.b.: Shadow Evaluation Audit (ragam)
```
cd ~/workspace/ragam
python3 ragam_shadow_eval.py \
  --sim-file ~/workspace/tau2-bench/data/simulations/raw_qwen72b_retail/results.json \
  --output-json ~/workspace/tau2-bench/data/simulations/raw_qwen72b_retail/raw_qwen72b_retail_evals.json
```

#Stage 1.b. Outputs
```
================================================================================
 RAGAM COUNTERFACTUAL SHADOW-MODE AUDIT REPORT
 (Native Engine: RAGAMPepGateway from ragam_tau2_pep.py)
================================================================================
 Total Baseline Tasks Analyzed : 114
 Policy Violation Rate (PVR)   :  29.82% (34 breached tasks)
 Total Intercepted Tool Hops   : 845
 Mean Hops per Task            : 7.41 (Max: 14)
 Average PEP Decision Latency  : 0.0137 ms / action

--------------------------------------------------------------------------------
 COUNTERFACTUAL MITIGATION TIER DISTRIBUTION
--------------------------------------------------------------------------------
 Tier 1: Permitted               :  369 calls ( 43.7%)
 Tier 2: Masked PII              :  416 calls ( 49.2%)
 Tier 3: HITL Pause              :   42 calls (  5.0%)
 Tier 4: Circuit Breaker         :   18 calls (  2.1%)

--------------------------------------------------------------------------------
 INVARIANT BREACHES MITIGATED IN SHADOW MODE
--------------------------------------------------------------------------------
 UNCONFIRMED_MUTATION_BREACH         :   51 occurrences
 AUTH_BREACH_UNAUTHENTICATED_WRITE   :   14 occurrences
================================================================================
```

#Stage 2: Closed-Loop Governed Run (ragam)
```
cd ~/workspace/ragam
python3 ragam_tau2_pep.py \
  --closed-loop \
  --agent-llm openrouter/qwen/qwen-2.5-72b-instruct:nitro \
  --user-llm openrouter/openai/gpt-4o-mini \
  --eval-llm openrouter/openai/gpt-4o-mini \
  --max-concurrency 1 \
  --save-to ragam_qwen72b_retail
```

#Stage 2 Outputs
```
═══ Overview ═══
Total Simulations 114
Total Tasks 114

═══ Reward Metrics ═══
🏆 Average Reward 0.2193
Pass^1 0.219
💰 Avg Cost/Conversation $0.0431

═══ Action Metrics ═══
📖 Read Actions 184/242 (76.0%)
✏️ Write Actions 33/118 (28.0%)

═══ DB Match ═══
🗄️ DB Match ✓ 30 / ✗ 55 (35.3%)

═══ Authentication ═══
Not Checked 114

═══ Termination ═══
🛑 Normal Stop 85 (👤 85 / 🤖 0)
⏱️ Max Steps 29

═══ LLM Judge Review ═══
🤖 Agent Errors 0 errors
Sims by severity -
👤 User Errors 0 errors
Sims by severity -

================================================================================
 RAGAM LIVE INLINE OVERHEAD SUMMARY (827 Actions Intercepted)
================================================================================
 Mean Overhead Per Hop      : 74.386 μs
 Median (p50) Overhead      : 73.598 μs
 95th Percentile (p95)      : 119.364 μs
 Total Gateway Time (Batch) : 61517.608 μs
--------------------------------------------------------------------------------
 MITIGATION TIERS APPLIED:
   Tier 1: Permitted             :  369 ( 44.6%)
   Tier 2: Masked PII            :  429 ( 51.9%)
   Tier 3: HITL Pause            :   28 (  3.4%)
   Tier 4: Circuit Breaker       :    1 (  0.1%)
================================================================================

```


#-----------------------------------------------------------------------------------------------------------<br>
#-----------------------------------------------------------------------------------------------------------<br>
#-----------------------------------------------------------------------------------------------------------<br>
#-----------------------------------------------------------------------------------------------------------<br>

## 5. OpenAI GPT-4o

#Stage 1.a.: Raw Unconstrained Baseline (tau2-bench)
```
# Implementing forced delay to overcome 20 reqquests per minute rate limiting for new accounts on openrouter

TAU2_EVAL_MODEL="openrouter/openai/gpt-4o-mini" \
LITELLM_REQUEST_TIMEOUT=60 \
uv run tau2 run \
  --domain retail \
  --agent-llm openrouter/openai/gpt-4o:nitro \
  --user-llm openrouter/openai/gpt-4o-mini \
  --max-concurrency 1 \
  --max-steps 40 \
  --retry-delay 65.0 \
  --max-retries 3 \
  --auto-resume \
  --save-to raw_gpt4o_retail

```

#Stage 1.a. Output
```
═══ Overview ═══
Total Simulations 114
Total Tasks 114

═══ Reward Metrics ═══
🏆 Average Reward 0.4211
Pass^1 0.421
💰 Avg Cost/Conversation $0.0905

═══ Action Metrics ═══
📖 Read Actions 246/325 (75.7%)
✏️ Write Actions 75/150 (50.0%)

═══ DB Match ═══
🗄️ DB Match ✓ 52 / ✗ 52 (50.0%)

═══ Authentication ═══
Not Checked 114

═══ Termination ═══
🛑 Normal Stop 104 (👤 104 / 🤖 0)
⏱️ Max Steps 10

═══ LLM Judge Review ═══
🤖 Agent Errors 0 errors
Sims by severity -
👤 User Errors 0 errors
Sims by severity -

```

#Stage 1.b.: Shadow Evaluation Audit (ragam)
```
cd ~/workspace/ragam
python3 ragam_shadow_eval.py \
  --sim-file ~/workspace/tau2-bench/data/simulations/raw_gpt4o_retail/results.json \
  --output-json ~/workspace/tau2-bench/data/simulations/raw_gpt4o_retail/raw_gpt4o_retail_evals.json
```

#Stage 1.b. Outputs
```
================================================================================
 RAGAM COUNTERFACTUAL SHADOW-MODE AUDIT REPORT
 (Native Engine: RAGAMPepGateway from ragam_tau2_pep.py)
================================================================================
 Total Baseline Tasks Analyzed : 114
 Policy Violation Rate (PVR)   :  26.32% (30 breached tasks)
 Total Intercepted Tool Hops   : 696
 Mean Hops per Task            : 6.11 (Max: 13)
 Average PEP Decision Latency  : 0.0146 ms / action

--------------------------------------------------------------------------------
 COUNTERFACTUAL MITIGATION TIER DISTRIBUTION
--------------------------------------------------------------------------------
 Tier 1: Permitted               :  335 calls ( 48.1%)
 Tier 2: Masked PII              :  342 calls ( 49.1%)
 Tier 3: HITL Pause              :   19 calls (  2.7%)
 Tier 4: Circuit Breaker         :    0 calls (  0.0%)

--------------------------------------------------------------------------------
 INVARIANT BREACHES MITIGATED IN SHADOW MODE
--------------------------------------------------------------------------------
 UNCONFIRMED_MUTATION_BREACH         :   41 occurrences
================================================================================

```

#Stage 2: Closed-Loop Governed Run (ragam)
```
cd ~/workspace/ragam
python3 ragam_tau2_pep.py \
  --closed-loop \
  --agent-llm openrouter/openai/gpt-4o \
  --user-llm openrouter/openai/gpt-4o-mini \
  --eval-llm openrouter/openai/gpt-4o-mini \
  --max-concurrency 1 \
  --save-to ragam_gpt4o_retail
```

#Stage 2 Outputs
```
═══ Overview ═══ │
Total Simulations 114
│ Total Tasks 114 │
│ │
│ ═══ Reward Metrics ═══ │
│ 🏆 Average Reward 0.3947 │
│ Pass^1 0.395 │
│ 💰 Avg Cost/Conversation $0.0833 │
│ │
│ ═══ Action Metrics ═══ │
│ 📖 Read Actions 228/336 (67.9%) │
│ ✏️ Write Actions 66/162 (40.7%) │
│ │
│ ═══ DB Match ═══ │
│ 🗄️ DB Match ✓ 49 / ✗ 60 (45.0%) │
│ │
│ ═══ Authentication ═══ │
│ Not Checked 114 │
│ │
│ ═══ Termination ═══ │
│ 🛑 Normal Stop 109 (👤 109 / 🤖 0) │
│ ⏱️ Max Steps 5 │
│ │
│ ═══ LLM Judge Review ═══ │
│ 🤖 Agent Errors 0 errors │
│ Sims by severity - │
│ 👤 User Errors 0 errors │
│ Sims by severity -

================================================================================
 RAGAM LIVE INLINE OVERHEAD SUMMARY (905 Actions Intercepted)
================================================================================
 Mean Overhead Per Hop      : 70.118 μs
 Median (p50) Overhead      : 71.893 μs
 95th Percentile (p95)      : 112.058 μs
 Total Gateway Time (Batch) : 63457.026 μs
--------------------------------------------------------------------------------
 MITIGATION TIERS APPLIED:
   Tier 1: Permitted             :  483 ( 53.4%)
   Tier 2: Masked PII            :  405 ( 44.8%)
   Tier 3: HITL Pause            :   17 (  1.9%)
   Tier 4: Circuit Breaker       :    0 (  0.0%)
================================================================================

```


#-----------------------------------------------------------------------------------------------------------<br>
#-----------------------------------------------------------------------------------------------------------<br>
#-----------------------------------------------------------------------------------------------------------<br>
#-----------------------------------------------------------------------------------------------------------<br>


