#!/usr/bin/env python3
"""
RAGAM Policy Enforcement Point (PEP) Gateway & Live Closed-Loop Runner
Implements dynamic risk scoring (RS_dyn), graduated mitigations (Tiers 1-4),
Track A microbenchmarking, and in-process closed-loop execution for tau2-bench.
"""

# ==============================================================================
# SECTION 1: IMPORTS, SYSTEM CONSTANTS & POLICY INVARIANTS
# ==============================================================================

import os
import sys
import json
import time
import re
import argparse
import inspect
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import hashlib
import math

MUTATING_TOOLS = {
    "cancel_pending_order",
    "modify_pending_order_items",
    "modify_pending_order_address",
    "modify_pending_order_payment",
    "modify_user_address",
    "return_delivered_order_items",
    "exchange_delivered_order_items",
}

PII_KEYS = {"email", "phone", "credit_card", "card_number", "ssn", "billing_address"}


# ==============================================================================
# SECTION 2: REPOSITORY RESOLUTION & DATA LOADERS
# ==============================================================================

def resolve_tau2_bench_root(override_path: Optional[str] = None) -> Path:
    candidates = [
        override_path,
        os.environ.get("TAU2_DATA_DIR"),
        str(Path.home() / "workspace" / "tau2-bench"),
        str(Path.home() / "workspace" / "tau2-bench" / "data"),
        "./data",
    ]
    for c in candidates:
        if not c:
            continue
        p = Path(c).expanduser().resolve()
        if p.name == "data" and (p / "retail").exists():
            return p.parent
        if (p / "data" / "retail").exists() or (p / "retail").exists():
            return p if (p / "data").exists() else p.parent
    return Path.home() / "workspace" / "tau2-bench"


def load_tau2_policy(repo_root: Path) -> str:
    path = repo_root / "data" / "retail" / "policy.md"
    if not path.exists():
        path = repo_root / "retail" / "policy.md"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "Default Retail Invariant Policy: Identity authentication and affirmative consent required."


def load_tau2_db(repo_root: Path) -> Dict[str, Any]:
    path = repo_root / "data" / "retail" / "db.json"
    if not path.exists():
        path = repo_root / "retail" / "db.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# ==============================================================================
# SECTION 3: CORE RAGAM PEP GATEWAY
# ==============================================================================

class LightweightSemanticEngine:
    """Computes fixed-dimension token vectors for sub-millisecond cosine drift checks."""
    def __init__(self, vocab_size: int = 512):
        self.vocab_size = vocab_size

    def vectorize(self, text: str) -> List[float]:
        tokens = re.findall(r"\w+", text.lower())
        vec = [0.0] * self.vocab_size
        if not tokens:
            return vec
        for token in tokens:
            idx = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % self.vocab_size
            vec[idx] += 1.0
        norm = math.sqrt(sum(v * v for v in vec))
        return [v / norm for v in vec] if norm > 0 else vec

    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        return max(0.0, min(1.0, sum(x * y for x, y in zip(a, b))))


class RAGAMPepGateway:
    """
    Inline Policy Enforcement Point (PEP) executing tool-specific risk profiles,
    semantic policy drift evaluation, regex PII data masking, and 4-tier graduated mitigations.
    """
    # Class-level attempt tracking across transient session re-instantiations
    _task_attempts: Dict[str, int] = {}

    def __init__(
            self,
            policy_text: str = "",
            window_size: int = 3,
            burst_limit: int = 6,
            model_name: Optional[str] = None,
            run_mode: str = "ragam",
            output_dir: Optional[str] = None,
        ):
            self.policy_text = policy_text
            self.window_size = window_size
            self.burst_limit = burst_limit
            self.run_mode = run_mode

            # Format model slug dynamically; fall back to "unknown_model" if None
            raw_name = model_name or "unknown_model"
            clean_model = (
                raw_name.replace("openrouter/", "")
                .replace("/", "_")
                .replace(":", "-")
            )
            ledger_filename = f"ledger_{clean_model}_{self.run_mode}.jsonl"

            # Route directly into the simulation's --save-to folder
            if output_dir:
                self.ledger_dir = Path(output_dir).resolve()
            else:
                self.ledger_dir = (Path.home() / "workspace" / "tau2-bench" / "data" / "simulations" / "default").resolve()

            self.ledger_dir.mkdir(parents=True, exist_ok=True)
            self.audit_file_path = str(self.ledger_dir / ledger_filename)
            
            self.semantic = LightweightSemanticEngine()
            self.e_auth = self.semantic.vectorize(policy_text)
            self.step_history: List[Dict[str, Any]] = []

            self.core_retail_tools = {
                # Set to 3.0 so pre-auth lookup stays in Tier 1 (< 4.0)
                "find_user_id_by_email": {"s_asset": 3.0, "t_dest": 0.95, "a_max": 8.0, "redact": ["email"]},
                "find_user_id_by_name_zip": {"s_asset": 3.0, "t_dest": 0.95, "a_max": 8.0, "redact": ["zip_code"]},
                "get_user_details": {"s_asset": 7.0, "t_dest": 0.95, "a_max": 7.0, "redact": ["default_address", "payment_methods"]},
                "get_order_details": {"s_asset": 6.0, "t_dest": 0.95, "a_max": 8.0, "redact": ["address", "shipping_address"]},                
                "get_product_details": {"s_asset": 1.5, "t_dest": 1.00, "a_max": 9.0, "redact": []},
                "list_all_product_types": {"s_asset": 1.5, "t_dest": 1.00, "a_max": 9.0, "redact": []},
                "get_item_details": {"s_asset": 1.5, "t_dest": 1.00, "a_max": 9.0, "redact": []},
                "calculate": {"s_asset": 1.0, "t_dest": 1.00, "a_max": 10.0, "redact": []},
                "modify_pending_order_address": {"s_asset": 7.0, "t_dest": 0.90, "a_max": 4.0, "redact": ["address", "payment_history", "new_address"]},
                "modify_user_address": {"s_asset": 7.0, "t_dest": 0.90, "a_max": 4.0, "redact": ["default_address", "payment_methods", "new_address"]},
                "modify_pending_order_items": {"s_asset": 7.0, "t_dest": 0.90, "a_max": 3.0, "redact": ["address", "payment_history", "payment_token"]},
                "modify_pending_order_payment": {"s_asset": 8.5, "t_dest": 0.90, "a_max": 3.0, "redact": ["address", "payment_history", "payment_method_id"]},
                "cancel_pending_order": {"s_asset": 7.5, "t_dest": 0.90, "a_max": 3.0, "redact": ["address", "payment_history"]},
                "return_delivered_order_items": {"s_asset": 8.0, "t_dest": 0.85, "a_max": 3.0, "redact": ["address", "payment_history", "refund_amount"]},
                "exchange_delivered_order_items": {"s_asset": 7.5, "t_dest": 0.85, "a_max": 3.0, "redact": ["address", "payment_history"]},
                "transfer_to_human_agents": {"s_asset": 2.0, "t_dest": 0.95, "a_max": 9.0, "redact": []},
            }

            self.pii_scanner = re.compile(
                r"(?P<CARD>\b(?:\d{4}[- ]?){3}\d{4}\b)|"
                r"(?P<EMAIL>[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)|"
                r"(?P<PHONE>\b(?:\+?1[-.]?)?\(?[0-9]{3}\)?[-.][0-9]{3}[-.][0-9]{4}\b)|"
                r"(?P<SSN>\b\d{3}-\d{2}-\d{4}\b)|"
                r"(?P<ZIP>\b\d{5}(?:-\d{4})?\b)"
            )

            # Formally bounded coefficients: alpha in [0.0, 0.5], beta1 in [2.5, 5.0], beta2 in [1.5, 3.0]
            self.w1, self.w2, self.w3 = 0.5, 0.3, 0.2
            self.alpha, self.beta1, self.beta2 = 0.20, 2.50, 1.50
            self.n_max = 40

    def reset_session(self) -> None:
        self.step_history.clear()

    def sanitize_payload(self, arguments: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        detected = []
        sanitized_args = {}
        for k, v in arguments.items():
            val_str = str(v)
            def _sub(m):
                for group_name, match_val in m.groupdict().items():
                    if match_val:
                        detected.append(group_name)
                        return f"[REDACTED_{group_name}]"
                return "[REDACTED]"
            new_val = self.pii_scanner.sub(_sub, val_str)
            sanitized_args[k] = new_val
        return sanitized_args, list(set(detected))

    def sanitize_output(self, raw_output: str, tool_name: str) -> str:
        """Sanitizes outgoing payloads for both valid JSON strings and Python dataclass reprs."""
        rule = self.core_retail_tools.get(tool_name, {})
        redact_keys = rule.get("redact", [])
        if not redact_keys:
            return raw_output

        # 1. Attempt JSON parsing
        try:
            data = json.loads(raw_output)
            if isinstance(data, dict):
                for k in redact_keys:
                    if k in data:
                        data[k] = "[REDACTED_CONFIDENTIAL]"
                return json.dumps(data)
        except Exception:
            pass

        # 2. Fallback regex scrubbing for Python repr formats (e.g. address=UserAddress(...) or address={...})
        scrubbed = raw_output
        for k in redact_keys:
            scrubbed = re.sub(rf"('{k}'|\"{k}\"|{k})\s*[:=]\s*(\{{.*?\}}|UserAddress\(.*?\)|\[.*?\]|'.*?'|\".*?\")", rf"\1: '[REDACTED_CONFIDENTIAL]'", scrubbed)

        return scrubbed

    def compute_gamma_context(self, hop: int, d_stat: float, d_goal: float) -> float:
        step_features = {"hop": hop, "d_stat": d_stat, "d_goal": d_goal}
        self.step_history.append(step_features)

        window_start = max(0, len(self.step_history) - self.window_size)
        recent = self.step_history[window_start:]

        max_penalty = 0.0
        if recent:
            penalties = [(self.beta1 * s["d_stat"]) + (self.beta2 * s["d_goal"]) for s in recent]
            max_penalty = max(penalties)

        hop_ratio = min(1.0, hop / float(self.n_max))
        gamma = 1.0 + (self.alpha * hop_ratio) + max_penalty
        return round(gamma, 4)

    def intercept(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        auth_verified: bool,
        hop: int,
        current_turn: Optional[int] = None,
        profile_stages: bool = False,
        a_agent: float = 2.0,
        task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        stage_timings = {}
        t_start = time.perf_counter_ns()

        # Track simulation attempts per task across tau2 retries
        task_key = str(task_id or "unassigned")
        if hop == 1:
            RAGAMPepGateway._task_attempts[task_key] = RAGAMPepGateway._task_attempts.get(task_key, 0) + 1
        current_attempt = RAGAMPepGateway._task_attempts.get(task_key, 1)

        t0 = time.perf_counter_ns()
        rule = self.core_retail_tools.get(tool_name, {
            "s_asset": 10.0, "t_dest": 0.0, "a_max": 1.0, "redact": ["*"]
        })

        auth_bootstrap_tools = {
            "find_user_id_by_email",
            "find_user_id_by_name_zip",
            "list_all_product_types",
            "get_product_details",
            "get_item_details",
            "calculate"
        }

        sanitized_args, detected_pii = self.sanitize_payload(arguments)
        # Exempt bootstrap tools and human transfer from PII asset inflation
        if tool_name in auth_bootstrap_tools or tool_name == "transfer_to_human_agents":
            s_asset = rule["s_asset"]
        else:
            s_asset = max(rule["s_asset"], 9.0) if detected_pii else rule["s_asset"]
        t_dest = rule["t_dest"]

        is_mutating = tool_name in MUTATING_TOOLS
        is_bootstrap = tool_name in auth_bootstrap_tools
        turn_idx = current_turn if current_turn is not None else hop

        # Hard invariant breach: only unauthenticated state-mutating actions
        hard_invariant_breach = is_mutating and not auth_verified

        # Map procedural statutory drift (d_stat)
        if auth_verified:
            d_stat = 0.0
            # Instantly flush pre-auth statutory debt from memory window
            for step in self.step_history:
                step["d_stat"] = 0.0
        elif hard_invariant_breach:
            d_stat = 0.85
        elif not is_bootstrap:
            d_stat = 0.40  # Soft auth challenge for private reads
        else:
            d_stat = 0.20  # Benign unauthenticated bootstrap/catalog reads

        d_goal = 0.30 if is_mutating else 0.10
        gamma_context = self.compute_gamma_context(turn_idx, d_stat, d_goal)
        t1 = time.perf_counter_ns()
        if profile_stages:
            stage_timings["stage_1_invariant_checks_us"] = (t1 - t0) / 1000.0

        # Stage 2: Dynamic Risk Math
        t0 = time.perf_counter_ns()
        if hard_invariant_breach:
            rs_base = 10.0
            rs_dyn = 10.0
        else:
            rs_base = round((self.w1 * s_asset) + (self.w2 * (1.0 - t_dest)) + (self.w3 * a_agent), 4)
            rs_dyn = round(min(10.0, rs_base * gamma_context), 2)

        t1 = time.perf_counter_ns()
        if profile_stages:
            stage_timings["stage_2_risk_scoring_us"] = (t1 - t0) / 1000.0

        # Stage 3: Graduated Tier Routing
        t0 = time.perf_counter_ns()
        a_max = rule["a_max"]

        if hard_invariant_breach or rs_dyn >= 9.0:
            tier, status = "Tier 4: Circuit Breaker", "BLOCKED_CIRCUIT_BREAKER"
        elif rs_dyn >= 7.0 or a_agent > a_max:
            tier, status = "Tier 3: HITL Pause", "PAUSED_WAITING_SUPERVISOR"
        elif rs_dyn >= 4.0 or (detected_pii and not is_bootstrap):
            tier, status = "Tier 2: Masked PII", "MASKED_PAYLOAD"
        else:
            tier, status = "Tier 1: Permitted", "PERMITTED"

        t1 = time.perf_counter_ns()
        if profile_stages:
            stage_timings["stage_3_tier_routing_us"] = (t1 - t0) / 1000.0

        # Stage 4: Payload Masking (Only mask arguments if destination is untrusted/external)
        t0 = time.perf_counter_ns()
        is_internal = t_dest >= 0.90
        exec_args = sanitized_args if (status == "MASKED_PAYLOAD" and not is_internal) else arguments
        t1 = time.perf_counter_ns()
        if profile_stages:
            stage_timings["stage_4_payload_masking_us"] = (t1 - t0) / 1000.0

        # Stage 5: Telemetry Logging
        t_end = time.perf_counter_ns()
        latency_us = (t_end - t_start) / 1000.0

        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id or "unassigned",
            "attempt": current_attempt,
            "hop": turn_idx,
            "tool_name": tool_name,
            "auth_verified": auth_verified,
            "s_asset": s_asset,
            "t_dest": t_dest,
            "a_agent": a_agent,
            "d_stat": round(d_stat, 4),
            "d_goal": round(d_goal, 4),
            "gamma_context": gamma_context,
            "rs_base": rs_base,
            "dynamic_risk_score": rs_dyn,
            "w1": self.w1,
            "w2": self.w2,
            "w3": self.w3,
            "beta1": self.beta1,
            "beta2": self.beta2,
            "mitigation_tier": tier,
            "action_status": status,
            "detected_pii": detected_pii,
            "latency_us": round(latency_us, 3)
        }
        with open(self.audit_file_path, "a", encoding="utf-8") as audit_file:
            audit_file.write(json.dumps(audit_entry) + "\n")

        envelope = {
            "action_status": status,
            "mitigation_tier": tier,
            "dynamic_risk_score": rs_dyn,
            "gamma_context": gamma_context,
            "executed_arguments": exec_args,
            "latency_us": latency_us,
        }
        if profile_stages:
            envelope["stage_timings"] = stage_timings

        return envelope


# ==============================================================================
# SECTION 4: TRACK A MICROBENCHMARK ENGINE
# ==============================================================================

def run_track_a_microbenchmark(iterations: int = 10000):
    print("=" * 80)
    print(f" RUNNING TRACK A MICROBENCHMARK ({iterations:,} INVOCATIONS)")
    print("=" * 80)

    gateway = RAGAMPepGateway()
    test_tools = [
        "find_user_id_by_email",
        "get_order_details",
        "modify_pending_order_address",
        "cancel_pending_order",
    ]
    total_latencies = []

    for i in range(iterations):
        tool = test_tools[i % len(test_tools)]
        auth = (i % 3 != 0)
        hop = (i % 12) + 1

        res = gateway.intercept(
            tool_name=tool,
            arguments={"order_id": "123", "email": "test@domain.com"},
            auth_verified=auth,
            hop=hop,
            current_turn=hop,
            profile_stages=True,
        )
        total_latencies.append(res["latency_us"])

    total_latencies.sort()
    avg_total = sum(total_latencies) / len(total_latencies)
    p50_total = total_latencies[int(0.50 * len(total_latencies))]
    p95_total = total_latencies[int(0.95 * len(total_latencies))]
    p99_total = total_latencies[int(0.99 * len(total_latencies))]

    print(f" Overall Total Latency (Mean): {avg_total:6.3f} μs")
    print(f"   - Median (p50)            : {p50_total:6.3f} μs")
    print(f"   - 95th Percentile (p95)   : {p95_total:6.3f} μs")
    print(f"   - 99th Percentile (p99)   : {p99_total:6.3f} μs")
    print("=" * 80)


# ==============================================================================
# SECTION 5: LIVE CLOSED-LOOP RUNNER
# ==============================================================================

def run_closed_loop_simulation(
    agent_llm: str,
    user_llm: str,
    eval_llm: str,
    num_tasks: Optional[int],
    save_dir: str,
    tau2_path: Optional[str] = None,
    auto_resume: bool = True,
    retry_delay: float = 65.0,
):
    repo_root = resolve_tau2_bench_root(tau2_path)
    sys.path.insert(0, str(repo_root / "src"))

    os.environ["TAU2_EVAL_MODEL"] = eval_llm

    try:
        from tau2.data_model.simulation import TextRunConfig
        from tau2.runner.batch import run_domain
        import tau2.domains.retail.environment as retail_env
    except ImportError as e:
        print(f"[Error] Failed to load tau2 modules from {repo_root}: {e}")
        sys.exit(1)

    print("=" * 80)
    print(" LAUNCHING RAGAM CLOSED-LOOP GOVERNED SIMULATION (IN-PROCESS)")
    print(f" Domain: retail | Agent: {agent_llm} | Eval: {eval_llm} | Tasks: {num_tasks or 'ALL (114)'}")
    print("=" * 80)

    policy_text = load_tau2_policy(repo_root)
    interception_latencies = []
    tier_counts = {
        "Tier 1: Permitted": 0,
        "Tier 2: Masked PII": 0,
        "Tier 3: HITL Pause": 0,
        "Tier 4: Circuit Breaker": 0,
    }
    status_counts = {}
    original_use_tool = retail_env.RetailTools.use_tool

    # Resolve simulation save folder under tau2-bench/data/simulations/<save_dir>
    data_dir = repo_root / "data" if (repo_root / "data").exists() else repo_root
    sim_output_dir = (data_dir / "simulations" / save_dir).resolve()
    sim_output_dir.mkdir(parents=True, exist_ok=True)

    def governed_use_tool(self, tool_name: str, **kwargs) -> str:
        # Bypass interception if call originates from benchmark evaluation routines
        stack = inspect.stack()
        if any(f.function in ("evaluate", "eval", "check_reward", "evaluate_simulation", "db_check", "eval_actions") or Path(f.filename).stem in ("evaluator", "evaluation", "eval") for f in stack):
            return original_use_tool(self, tool_name=tool_name, **kwargs)

        if not hasattr(self, "_ragam_session"):
            self._ragam_session = {
                "authenticated": False,
                "hop": 1,
                "gateway": RAGAMPepGateway(
                    policy_text=policy_text,
                    model_name=agent_llm,
                    run_mode="ragam",
                    output_dir=str(sim_output_dir)
                ),
            }

        session = self._ragam_session
        gateway = session["gateway"]

        # Extract active task ID from the execution call stack
        current_task_id = "unassigned"
        for frame_info in inspect.stack():
            locs = frame_info.frame.f_locals
            if "task" in locs:
                t = locs["task"]
                if hasattr(t, "id"):
                    current_task_id = str(t.id)
                    break
                elif isinstance(t, dict) and "id" in t:
                    current_task_id = str(t["id"])
                    break
            elif "simulation" in locs:
                s = locs["simulation"]
                if hasattr(s, "task_id"):
                    current_task_id = str(s.task_id)
                    break

        decision = gateway.intercept(
            tool_name=tool_name,
            arguments=kwargs,
            auth_verified=session["authenticated"],
            hop=session["hop"],
            current_turn=session["hop"],
            profile_stages=True,
            task_id=current_task_id,
        )
        interception_latencies.append(decision["latency_us"])
        session["hop"] += 1

        status = decision["action_status"]
        rs_dyn = decision["dynamic_risk_score"]
        tier = decision["mitigation_tier"]

        if tier in tier_counts:
            tier_counts[tier] += 1
        status_counts[status] = status_counts.get(status, 0) + 1

        # Tier 4 Circuit Breaker
        if status == "BLOCKED_CIRCUIT_BREAKER":
            return (
                f"Error: RAGAM Governance Notice [Tier 4 Circuit Breaker]: Action '{tool_name}' halted "
                f"(Risk Score: {rs_dyn:.2f}). Invariant breach or high-risk anomaly detected."
            )

        # Tier 3 HITL Pause / Challenge State
        if status == "PAUSED_WAITING_SUPERVISOR":
            return (
                f"Error: RAGAM Governance Notice [Tier 3 Enterprise HITL]: Action '{tool_name}' suspended "
                f"(Risk Score: {rs_dyn:.2f}). Authentication or supervisor approval required."
            )

        # Tier 1 & 2 Execution: Run raw functional arguments to prevent breaking internal db queries
        result = original_use_tool(self, tool_name=tool_name, **kwargs)
        res_str = str(result)

        # Authenticate session on valid raw response
        if not res_str.startswith("Error"):
            if tool_name in ["find_user_id_by_email", "find_user_id_by_name_zip"]:
                session["authenticated"] = True
            elif tool_name in ["get_user_details", "get_order_details"]:
                if (isinstance(result, dict) and "user_id" in result) or ('"user_id"' in res_str):
                    session["authenticated"] = True

        # Tier 2: Redact sensitive PII fields before returning to model context & results.json
        if tier == "Tier 2: Masked PII" and not res_str.startswith("Error"):
            result = gateway.sanitize_output(res_str, tool_name)

        return result

    retail_env.RetailTools.use_tool = governed_use_tool

    agent_args = {
        "parallel_tool_calls": False,
        "extra_body": {
            "parallel_tool_calls": False,
            "provider": {
                "sort": "throughput",
                "allow_fallbacks": False,
                "ignore": ["groq"], #to avoid groq function calling errors
            },
        },
    }

    config = TextRunConfig(
        domain="retail",
        agent="llm_agent",
        user="user_simulator",
        llm_agent=agent_llm,
        llm_user=user_llm,
        llm_args_agent=agent_args,
        llm_args_user={"temperature": 0.0},
        review_model=eval_llm,
        max_steps=40,
        max_concurrency=1,
        num_tasks=num_tasks if (num_tasks and num_tasks < 114) else None,
        save_to=save_dir,
        auto_resume=auto_resume,
        retry_delay=retry_delay,
    )

    try:
        run_domain(config)
    finally:
        retail_env.RetailTools.use_tool = original_use_tool

    if interception_latencies:
        interception_latencies.sort()
        avg_lat = sum(interception_latencies) / len(interception_latencies)
        p50 = interception_latencies[int(0.50 * len(interception_latencies))]
        p95 = interception_latencies[int(0.95 * len(interception_latencies))]
        total_time_us = sum(interception_latencies)

        print("\n" + "=" * 80)
        print(f" RAGAM LIVE INLINE OVERHEAD SUMMARY ({len(interception_latencies)} Actions Intercepted)")
        print("=" * 80)
        print(f" Mean Overhead Per Hop      : {avg_lat:6.3f} μs")
        print(f" Median (p50) Overhead      : {p50:6.3f} μs")
        print(f" 95th Percentile (p95)      : {p95:6.3f} μs")
        print(f" Total Gateway Time (Batch) : {total_time_us:6.3f} μs")
        print("-" * 80)
        print(" MITIGATION TIERS APPLIED:")
        for t_name, cnt in tier_counts.items():
            pct = (cnt / len(interception_latencies) * 100.0) if interception_latencies else 0.0
            print(f"   {t_name:<30}: {cnt:>4} ({pct:>5.1f}%)")
        print("=" * 80)

        data_dir = repo_root / "data" if (repo_root / "data").exists() else repo_root
        live_out = (data_dir / "simulations" / save_dir / "ragam_overhead.json").resolve()
        live_out.parent.mkdir(parents=True, exist_ok=True)

        with open(live_out, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "actions_intercepted": len(interception_latencies),
                    "mean_latency_us": round(avg_lat, 3),
                    "p50_latency_us": round(p50, 3),
                    "p95_latency_us": round(p95, 3),
                    "total_gateway_time_us": round(total_time_us, 3),
                    "mitigation_tier_distribution": tier_counts,
                    "action_status_distribution": status_counts,
                },
                f,
                indent=2,
            )
        print(f" Saved live inline overhead metrics to: {live_out}\n")


# ==============================================================================
# SECTION 6: CLI ARGUMENT PARSER & EXECUTION DISPATCHER
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="RAGAM PEP Engine: Run Track A microbenchmarks or live closed-loop simulations."
    )
    parser.add_argument(
        "--track-a",
        action="store_true",
        help="Execute Track A microbenchmark measuring pure rule latency",
    )
    parser.add_argument(
        "--closed-loop",
        action="store_true",
        help="Run live tau2 simulation with inline RAGAM closed-loop interception",
    )
    parser.add_argument(
        "--agent-llm",
        type=str,
        default="openrouter/meta-llama/llama-3.1-8b-instruct",
        help="Agent LLM model identifier",
    )
    parser.add_argument(
        "--user-llm",
        type=str,
        default="openrouter/meta-llama/llama-3.1-8b-instruct",
        help="User simulator LLM model identifier",
    )
    parser.add_argument(
        "--eval-llm",
        type=str,
        default=None,
        help="Evaluation LLM model identifier (defaults to agent-llm if not specified)",
    )
    parser.add_argument(
        "--num-tasks",
        type=int,
        default=None,
        help="Number of retail domain tasks to execute (default: None runs all 114)",
    )
    parser.add_argument(
        "--save-to",
        type=str,
        default="live_llama8b_retail_ragam_governed",
        help="Directory name to store simulation trajectory results",
    )
    parser.add_argument(
        "--tau2-path",
        type=str,
        default=None,
        help="Explicit path to the tau2-bench repository root",
    )
    parser.add_argument(
        "--max-concurrency", 
        type=int, 
        default=1, 
        help="Maximum concurrent simulations",
    )
    parser.add_argument(
        "--auto-resume",
        action="store_true",
        default=True,
        help="Auto resume previous simulation progress if results.json exists",
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=65.0,
        help="Delay in seconds between retries to avoid rate limits",
    )
    args = parser.parse_args()

    if args.track_a:
        run_track_a_microbenchmark()
    elif args.closed_loop:
        eval_model = args.eval_llm or args.agent_llm
        run_closed_loop_simulation(
            agent_llm=args.agent_llm,
            user_llm=args.user_llm,
            eval_llm=eval_model,
            num_tasks=args.num_tasks,
            save_dir=args.save_to,
            tau2_path=args.tau2_path,
            auto_resume=args.auto_resume,
            retry_delay=args.retry_delay,
        )
    else:
        run_track_a_microbenchmark(iterations=1000)


if __name__ == "__main__":
    main()