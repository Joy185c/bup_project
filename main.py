#!/usr/bin/env python3
"""
GridWise Energy Optimization Platform — Main CLI & Evaluation Suite.

Usage:
  # Run automated benchmark evaluation against a deployed or local API:
  python3 main.py --base-url http://localhost:8000
  python3 main.py --base-url https://your-deployment.vercel.app

  # Run evaluation on a single case:
  python3 main.py --base-url http://localhost:8000 --case SAMPLE-01

  # Start the local FastAPI server:
  python3 main.py --serve
  python3 main.py --serve --port 8000
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# ANSI Color Codes for terminal formatting
# ---------------------------------------------------------------------------
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def supports_color() -> bool:
    """Return True if stdout supports ANSI color codes."""
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def color(text: str, color_code: str) -> str:
    """Wrap text in color codes if terminal supports it."""
    if supports_color():
        return f"{color_code}{text}{Colors.RESET}"
    return text


# ---------------------------------------------------------------------------
# HTTP Helpers (Pure Python standard library for zero dependencies)
# ---------------------------------------------------------------------------
def http_get(url: str, timeout: float = 10.0) -> Tuple[int, Any, float]:
    """Perform HTTP GET, returning (status_code, json_or_text, elapsed_seconds)."""
    start = time.perf_counter()
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "GridWise-Benchmark/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            elapsed = time.perf_counter() - start
            body = response.read().decode("utf-8")
            try:
                return response.status, json.loads(body), elapsed
            except json.JSONDecodeError:
                return response.status, body, elapsed
    except urllib.error.HTTPError as e:
        elapsed = time.perf_counter() - start
        body = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(body), elapsed
        except Exception:
            return e.code, body, elapsed
    except Exception as e:
        elapsed = time.perf_counter() - start
        return 0, str(e), elapsed


def http_post(url: str, payload: dict, timeout: float = 35.0) -> Tuple[int, Any, float]:
    """Perform HTTP POST with JSON body, returning (status_code, json_or_text, elapsed_seconds)."""
    start = time.perf_counter()
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "GridWise-Benchmark/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            elapsed = time.perf_counter() - start
            body = response.read().decode("utf-8")
            try:
                return response.status, json.loads(body), elapsed
            except json.JSONDecodeError:
                return response.status, body, elapsed
    except urllib.error.HTTPError as e:
        elapsed = time.perf_counter() - start
        body = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(body), elapsed
        except Exception:
            return e.code, body, elapsed
    except Exception as e:
        elapsed = time.perf_counter() - start
        return 0, str(e), elapsed


# ---------------------------------------------------------------------------
# Dataset Discovery & Loading
# ---------------------------------------------------------------------------
DEFAULT_DATASET_PATHS = [
    "test_data/bup_official_dataset",
    "../BUP_CSE_FEST_2026_Participant_Docs/BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json",
    "test_data/BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json",
]


def load_dataset(custom_path: Optional[str] = None) -> Tuple[List[dict], str]:
    """Find and load benchmark dataset."""
    search_paths = [custom_path] if custom_path else DEFAULT_DATASET_PATHS
    for p in search_paths:
        if p and os.path.isfile(p):
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                cases = data.get("cases", [])
                return cases, p
    raise FileNotFoundError(
        f"Could not locate benchmark cases dataset. Checked: {search_paths}"
    )


# ---------------------------------------------------------------------------
# Directive & Physics Verification
# ---------------------------------------------------------------------------
def verify_directive_interpretation(
    expected_list: List[dict], actual_list: List[dict]
) -> Tuple[bool, List[str]]:
    """Compare team directive interpretation with reference ground truth."""
    issues = []
    if len(expected_list) != len(actual_list):
        issues.append(
            f"Expected {len(expected_list)} directive interpretation(s), got {len(actual_list)}"
        )
        return False, issues

    for idx, (exp, act) in enumerate(zip(expected_list, actual_list)):
        prefix = f"Note [{idx}]"
        # 1. Directive type
        if exp.get("directive_type") != act.get("directive_type"):
            issues.append(
                f"{prefix}: directive_type mismatch: expected '{exp.get('directive_type')}', got '{act.get('directive_type')}'"
            )

        # 2. Applies flag
        if exp.get("applies") != act.get("applies"):
            issues.append(
                f"{prefix}: applies mismatch: expected {exp.get('applies')}, got {act.get('applies')}"
            )

        # 3. Structured adjustment
        exp_adj = exp.get("structured_adjustment")
        act_adj = act.get("structured_adjustment")

        if exp.get("directive_type") == "no_op":
            if act_adj is not None:
                issues.append(f"{prefix}: no_op must have null structured_adjustment, got {act_adj}")
        else:
            if act_adj is None:
                issues.append(f"{prefix}: missing structured_adjustment")
            elif isinstance(exp_adj, dict) and isinstance(act_adj, dict):
                # Check hours
                if exp_adj.get("hours") != act_adj.get("hours"):
                    issues.append(
                        f"{prefix}: hours mismatch: expected {exp_adj.get('hours')}, got {act_adj.get('hours')}"
                    )
                # Check factor (within 1e-4)
                if "factor" in exp_adj:
                    if "factor" not in act_adj or abs(exp_adj["factor"] - act_adj["factor"]) > 1e-4:
                        issues.append(
                            f"{prefix}: factor mismatch: expected {exp_adj['factor']}, got {act_adj.get('factor')}"
                        )
                # Check minimum_energy_kwh
                if "minimum_energy_kwh" in exp_adj:
                    if (
                        "minimum_energy_kwh" not in act_adj
                        or abs(exp_adj["minimum_energy_kwh"] - act_adj["minimum_energy_kwh"]) > 1e-4
                    ):
                        issues.append(
                            f"{prefix}: minimum_energy_kwh mismatch: expected {exp_adj['minimum_energy_kwh']}, got {act_adj.get('minimum_energy_kwh')}"
                        )
                # Check max_grid_kwh
                if "max_grid_kwh" in exp_adj:
                    if (
                        "max_grid_kwh" not in act_adj
                        or abs(exp_adj["max_grid_kwh"] - act_adj["max_grid_kwh"]) > 1e-4
                    ):
                        issues.append(
                            f"{prefix}: max_grid_kwh mismatch: expected {exp_adj['max_grid_kwh']}, got {act_adj.get('max_grid_kwh')}"
                        )

    return len(issues) == 0, issues


def verify_hourly_plan_physics(
    input_data: dict, actual_response: dict
) -> Tuple[bool, List[str]]:
    """Validate grid physics, energy balance, battery state transitions and end-of-day neutrality."""
    issues = []
    hourly_plan = actual_response.get("hourly_plan", [])
    input_hours = input_data.get("hours", [])
    battery = input_data.get("battery", {})

    if len(hourly_plan) != 24:
        issues.append(f"hourly_plan must contain exactly 24 entries, found {len(hourly_plan)}")
        return False, issues

    initial_energy = battery.get("initial_energy_kwh", 0.0)
    capacity = battery.get("capacity_kwh", 0.0)
    base_min_energy = battery.get("minimum_energy_kwh", 0.0)
    max_charge = battery.get("max_charge_kwh_per_hour", 0.0)
    max_discharge = battery.get("max_discharge_kwh_per_hour", 0.0)

    prev_energy = initial_energy
    recalc_total_grid = 0.0
    recalc_total_cost = 0.0
    recalc_peak_grid = 0.0

    TOLERANCE = 0.05  # Standard BUP tolerance

    for h_idx in range(24):
        p = hourly_plan[h_idx]
        inp = input_hours[h_idx]

        h = p.get("hour")
        grid = p.get("grid_kwh", 0.0)
        solar_used = p.get("solar_used_kwh", 0.0)
        action = p.get("battery_action", "idle")
        battery_kwh = p.get("battery_kwh", 0.0)
        after_energy = p.get("battery_energy_after_kwh", 0.0)

        demand = inp.get("demand_kwh", 0.0)
        solar_gen = inp.get("solar_kwh", 0.0)
        tariff = inp.get("tariff_bdt_per_kwh", 0.0)

        recalc_total_grid += grid
        recalc_total_cost += grid * tariff
        if grid > recalc_peak_grid:
            recalc_peak_grid = grid

        # 1. Non-negativity
        if grid < -TOLERANCE or solar_used < -TOLERANCE or battery_kwh < -TOLERANCE:
            issues.append(f"Hour {h}: negative energy values detected")

        # 2. Solar usage limit
        if solar_used > solar_gen + TOLERANCE:
            issues.append(
                f"Hour {h}: solar_used ({solar_used}) exceeds solar generated ({solar_gen})"
            )

        # 3. Battery action rate limit
        charge_kwh = battery_kwh if action == "charge" else 0.0
        discharge_kwh = battery_kwh if action == "discharge" else 0.0

        if action == "charge" and charge_kwh > max_charge + TOLERANCE:
            issues.append(f"Hour {h}: charge rate {charge_kwh} exceeds max limit {max_charge}")
        if action == "discharge" and discharge_kwh > max_discharge + TOLERANCE:
            issues.append(f"Hour {h}: discharge rate {discharge_kwh} exceeds max limit {max_discharge}")
        if action == "idle" and battery_kwh > TOLERANCE:
            issues.append(f"Hour {h}: idle battery action with non-zero battery_kwh {battery_kwh}")

        # 4. Hourly Energy Balance: Grid + SolarUsed + Discharge = Demand + Charge
        supply = grid + solar_used + discharge_kwh
        demand_load = demand + charge_kwh
        if abs(supply - demand_load) > TOLERANCE:
            issues.append(
                f"Hour {h}: Energy balance violated! Supply ({supply:.2f}) != Demand ({demand_load:.2f})"
            )

        # 5. Battery state transition: after = prev + charge - discharge
        expected_after = prev_energy + charge_kwh - discharge_kwh
        if abs(after_energy - expected_after) > TOLERANCE:
            issues.append(
                f"Hour {h}: Battery transition error. Expected {expected_after:.2f}, got {after_energy:.2f}"
            )

        # 6. Battery capacity bound
        if after_energy > capacity + TOLERANCE:
            issues.append(
                f"Hour {h}: Battery energy {after_energy:.2f} exceeds capacity {capacity:.2f}"
            )

        prev_energy = after_energy

    # 7. End-of-day neutrality (Hour 23 final energy == initial energy)
    final_energy = hourly_plan[23].get("battery_energy_after_kwh", 0.0)
    if abs(final_energy - initial_energy) > TOLERANCE:
        issues.append(
            f"End-of-day neutrality violated! Initial={initial_energy:.2f} kWh, Final={final_energy:.2f} kWh"
        )

    # 8. Consistency of top-level metrics
    reported_grid = actual_response.get("total_grid_kwh", 0.0)
    reported_cost = actual_response.get("total_cost_bdt", 0.0)
    reported_peak = actual_response.get("peak_grid_kwh", 0.0)

    if abs(reported_grid - recalc_total_grid) > 0.5:
        issues.append(
            f"total_grid_kwh mismatch: reported {reported_grid:.2f}, recalculated {recalc_total_grid:.2f}"
        )
    if abs(reported_cost - recalc_total_cost) > 1.0:
        issues.append(
            f"total_cost_bdt mismatch: reported {reported_cost:.2f}, recalculated {recalc_total_cost:.2f}"
        )
    if abs(reported_peak - recalc_peak_grid) > 0.5:
        issues.append(
            f"peak_grid_kwh mismatch: reported {reported_peak:.2f}, recalculated {recalc_peak_grid:.2f}"
        )

    return len(issues) == 0, issues


# ---------------------------------------------------------------------------
# Runner & Benchmarking Logic
# ---------------------------------------------------------------------------
def run_benchmark(
    base_url: str,
    dataset_path: Optional[str] = None,
    specific_case: Optional[str] = None,
    timeout: float = 30.0,
    verbose: bool = False,
) -> int:
    """Execute evaluation against base_url."""
    # Validate base_url placeholder
    clean_url = base_url.strip()
    if clean_url in ("your-url", "your_url", "<your-url>", "YOUR_URL", "http://your-url"):
        print(
            color("\n❌ Error: 'your-url' appears to be a placeholder!", Colors.RED + Colors.BOLD)
        )
        print(
            "Please provide the actual URL of your running service, for example:\n"
            f"  {color('python3 main.py --base-url http://localhost:8000', Colors.CYAN)}\n"
            f"  {color('python3 main.py --base-url https://gridwise-backend.vercel.app', Colors.CYAN)}\n"
        )
        print(
            "If your local server is not running yet, you can start it with:\n"
            f"  {color('python3 main.py --serve', Colors.GREEN)}\n"
        )
        return 1

    if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
        clean_url = "http://" + clean_url

    clean_url = clean_url.rstrip("/")

    print("=" * 70)
    print(color("⚡ GRIDWISE SMART CAMPUS — BENCHMARK EVALUATOR", Colors.CYAN + Colors.BOLD))
    print(f"Target Base URL: {color(clean_url, Colors.BOLD)}")
    print(f"Timeout:         {timeout}s per request")
    print("=" * 70)

    # 1. Health check
    health_url = f"{clean_url}/health"
    print(f"\n[1/2] Verifying health check ({health_url})...", end=" ", flush=True)
    status_code, body, elapsed = http_get(health_url, timeout=10.0)

    if status_code == 200 and isinstance(body, dict) and body.get("status") == "ok":
        print(color(f"OK ({elapsed*1000:.1f}ms)", Colors.GREEN + Colors.BOLD))
    else:
        print(color(f"FAILED (Status: {status_code})", Colors.RED + Colors.BOLD))
        print(f"  Response: {body}")
        print(
            color(
                "\n⚠️  The target server is not responding with {'status': 'ok'} at /health.",
                Colors.YELLOW,
            )
        )
        print("Please check that the server is active and reachable from this network.")
        return 1

    # 2. Load dataset
    print(f"\n[2/2] Loading official test dataset...")
    try:
        cases, path_used = load_dataset(dataset_path)
        print(f"Loaded {len(cases)} cases from: {color(path_used, Colors.DIM)}")
    except Exception as e:
        print(color(f"❌ Failed to load dataset: {e}", Colors.RED))
        return 1

    if specific_case:
        cases = [c for c in cases if c.get("id") == specific_case]
        if not cases:
            print(color(f"❌ Case ID '{specific_case}' not found in dataset.", Colors.RED))
            return 1
        print(f"Filtered to case: {specific_case}")

    optimize_url = f"{clean_url}/optimize-energy"
    total_cases = len(cases)
    passed_cases = 0
    directive_correct_count = 0
    physics_correct_count = 0
    latencies: List[float] = []

    print("\n" + "-" * 70)
    print(f"{'CASE ID':<14} | {'STATUS':<8} | {'LATENCY':<9} | {'DIRECTIVES':<12} | {'PHYSICS':<8}")
    print("-" * 70)

    for i, case in enumerate(cases):
        case_id = case.get("id", f"CASE-{i+1}")
        input_payload = case.get("input", {})
        expected_output = case.get("expected_output", {})

        status, response_data, elapsed = http_post(
            optimize_url, input_payload, timeout=timeout
        )
        latencies.append(elapsed)

        if status != 200 or not isinstance(response_data, dict):
            status_text = color("FAIL", Colors.RED + Colors.BOLD)
            print(
                f"{case_id:<14} | {status_text:<8} | {elapsed:.2f}s    | HTTP {status:<6} | {'N/A':<8}"
            )
            if verbose:
                err_msg = str(response_data)[:200]
                print(f"   ↳ Error: {err_msg}")
            continue

        # Check directive accuracy
        exp_dir = expected_output.get("directive_interpretation", [])
        act_dir = response_data.get("directive_interpretation", [])
        dir_ok, dir_issues = verify_directive_interpretation(exp_dir, act_dir)
        if dir_ok:
            directive_correct_count += 1
            dir_str = color("PASS", Colors.GREEN)
        else:
            dir_str = color("MISMATCH", Colors.YELLOW)

        # Check physics & constraints
        phys_ok, phys_issues = verify_hourly_plan_physics(input_payload, response_data)
        if phys_ok:
            physics_correct_count += 1
            phys_str = color("PASS", Colors.GREEN)
        else:
            phys_str = color("FAIL", Colors.RED)

        # Overall case pass:
        overall_ok = dir_ok and phys_ok
        if overall_ok:
            passed_cases += 1
            case_status = color("PASS", Colors.GREEN + Colors.BOLD)
        else:
            case_status = color("FAIL", Colors.RED + Colors.BOLD)

        print(f"{case_id:<14} | {case_status:<8} | {elapsed:.2f}s    | {dir_str:<21} | {phys_str:<17}")

        if (not overall_ok or verbose) and (dir_issues or phys_issues):
            for issue in dir_issues:
                print(f"   ↳ [Directive] {issue}")
            for issue in phys_issues:
                print(f"   ↳ [Physics]   {issue}")

    # Latency statistics
    avg_lat = sum(latencies) / len(latencies) if latencies else 0.0
    sorted_lat = sorted(latencies)
    p95_lat = sorted_lat[int(len(sorted_lat) * 0.95)] if sorted_lat else 0.0

    print("=" * 70)
    print(color("📊 EVALUATION SUMMARY SCORECARD", Colors.CYAN + Colors.BOLD))
    print("=" * 70)
    print(f"Total Cases Tested:            {total_cases}")
    print(
        f"Fully Valid Cases (All Rules): {passed_cases}/{total_cases} ({passed_cases/total_cases*100:.1f}%)"
    )
    print(
        f"Directive Semantic Accuracy:   {directive_correct_count}/{total_cases} ({directive_correct_count/total_cases*100:.1f}%)"
    )
    print(
        f"Physics & Constraint Validity: {physics_correct_count}/{total_cases} ({physics_correct_count/total_cases*100:.1f}%)"
    )
    print(f"Average Request Latency:       {avg_lat:.2f}s")
    print(f"p95 Request Latency:           {p95_lat:.2f}s (Rubric target: <= 5.0s)")

    if passed_cases == total_cases:
        print(
            color(
                "\n🎉 OUTSTANDING! 100% of benchmark cases passed all directives and constraints.",
                Colors.GREEN + Colors.BOLD,
            )
        )
        return 0
    else:
        print(
            color(
                f"\n⚠️  {total_cases - passed_cases} case(s) did not fully pass. Check details above.",
                Colors.YELLOW + Colors.BOLD,
            )
        )
        return 1


# ---------------------------------------------------------------------------
# Server Launcher
# ---------------------------------------------------------------------------
def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = True):
    """Launch the FastAPI server via Uvicorn."""
    try:
        import uvicorn
    except ImportError:
        print(color("❌ Uvicorn is required to run the server. Run: pip install uvicorn", Colors.RED))
        sys.exit(1)

    print("=" * 70)
    print(color(f"🚀 Starting GridWise Optimization Backend on {host}:{port}...", Colors.GREEN + Colors.BOLD))
    print(f"Documentation: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs")
    print(f"Health Check:  http://{host if host != '0.0.0.0' else 'localhost'}:{port}/health")
    print("=" * 70)
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="GridWise Smart Campus — Evaluation Harness & Server Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run automated benchmark evaluation against a deployed or local API:
  python3 main.py --base-url http://localhost:8000
  python3 main.py --base-url https://gridwise-backend.vercel.app

  # Evaluate a single case:
  python3 main.py --base-url http://localhost:8000 --case SAMPLE-01

  # Launch the local server:
  python3 main.py --serve
  python3 main.py --serve --port 8000
        """,
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="Base URL of the running GridWise API to evaluate (e.g. http://localhost:8000)",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Path to custom JSON dataset file (default: test_data/bup_official_dataset)",
    )
    parser.add_argument(
        "--case",
        type=str,
        default=None,
        help="Run only a specific case ID (e.g. SAMPLE-01)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="HTTP request timeout in seconds (default: 30.0)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed debug output for failures and adjustments",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Launch the FastAPI server via Uvicorn instead of running the benchmark",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=os.environ.get("HOST", "0.0.0.0"),
        help="Host to bind server (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", "8000")),
        help="Port to bind server (default: 8000)",
    )

    args = parser.parse_args()

    if args.serve:
        run_server(host=args.host, port=args.port)
        return

    if args.base_url:
        exit_code = run_benchmark(
            base_url=args.base_url,
            dataset_path=args.dataset,
            specific_case=args.case,
            timeout=args.timeout,
            verbose=args.verbose,
        )
        sys.exit(exit_code)

    # If neither --serve nor --base-url was given:
    # Check if a local server is currently responding on http://localhost:8000
    print("=" * 70)
    print(color("GridWise Energy Optimization Platform — CLI", Colors.CYAN + Colors.BOLD))
    print("=" * 70)
    print("No option specified. Checking for local server at http://localhost:8000...")
    status_code, body, _ = http_get("http://localhost:8000/health", timeout=1.5)

    if status_code == 200 and isinstance(body, dict) and body.get("status") == "ok":
        print(color("Local server detected on http://localhost:8000!", Colors.GREEN))
        print("Running benchmark evaluation against http://localhost:8000...\n")
        exit_code = run_benchmark(
            base_url="http://localhost:8000",
            dataset_path=args.dataset,
            specific_case=args.case,
            timeout=args.timeout,
            verbose=args.verbose,
        )
        sys.exit(exit_code)
    else:
        print(color("\nNo running server found on http://localhost:8000.", Colors.YELLOW))
        print("To run the evaluation, supply the base URL of your deployed or local service:")
        print(f"  {color('python3 main.py --base-url http://localhost:8000', Colors.CYAN)}")
        print(f"  {color('python3 main.py --base-url https://your-deployment.vercel.app', Colors.CYAN)}")
        print("\nOr start the local FastAPI server directly:")
        print(f"  {color('python3 main.py --serve', Colors.GREEN)}\n")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
