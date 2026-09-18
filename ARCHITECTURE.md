# GridWise Architecture Document

## System Overview

GridWise is a microservice that accepts energy scenario data and natural-language operator notes, then returns an AI-assisted, MILP-optimized 24-hour energy plan.

---

## Component Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         GridWise Backend                                  │
│                                                                           │
│  ┌─────────────┐     ┌──────────────┐     ┌───────────────────────────┐ │
│  │  FastAPI     │     │  schemas.py  │     │  config.py                │ │
│  │  main.py     │────▶│  Pydantic v2 │     │  Env vars, tolerances     │ │
│  │              │     │  validation  │     └───────────────────────────┘ │
│  └──────┬───────┘     └──────────────┘                                   │
│         │                                                                 │
│         │ operator notes (list[str])                                      │
│         ▼                                                                 │
│  ┌─────────────┐                                                         │
│  │   llm.py    │ ──── OpenAI API ────▶ Structured JSON                   │
│  │ LLM Interp. │     (temperature=0)   (json_schema strict)              │
│  └──────┬───────┘                                                         │
│         │ LLMResponse (untrusted)                                         │
│         ▼                                                                 │
│  ┌─────────────┐                                                         │
│  │guardrails.py│ 13 deterministic checks                                 │
│  │ Validation  │ → raises GuardrailError on failure                      │
│  └──────┬───────┘                                                         │
│         │ list[ValidatedDirective]                                        │
│         ▼                                                                 │
│  ┌──────────────────────────────────────────┐                            │
│  │            optimizer.py                   │                            │
│  │  ┌─────────────────────────────────────┐ │                            │
│  │  │  apply_directives()                 │ │                            │
│  │  │  Builds list[HourConstraints]       │ │                            │
│  │  │  (effective_solar, reserves, caps)  │ │                            │
│  │  └─────────────────┬───────────────────┘ │                            │
│  │                    │                      │                            │
│  │  ┌─────────────────▼───────────────────┐ │                            │
│  │  │  solve_milp()                       │ │                            │
│  │  │  PuLP + CBC MILP solver             │ │                            │
│  │  │  Binary variables for mutex         │ │                            │
│  │  │  Minimizes Σ(grid×tariff)           │ │                            │
│  │  └─────────────────┬───────────────────┘ │                            │
│  └────────────────────┼─────────────────────┘                            │
│                       │ raw_plan (list[dict])                             │
│                       ▼                                                   │
│  ┌─────────────────────────────────────────┐                             │
│  │  validator.py                            │                             │
│  │  Independent replay of all constraints   │                             │
│  │  Rejects invalid solver output           │                             │
│  └──────────────────────┬──────────────────┘                             │
│                         │ validated plan                                  │
│                         ▼                                                 │
│  ┌─────────────┐                                                         │
│  │  Response   │ OptimizeResponse (Pydantic)                             │
│  │  Builder    │ scenario_id, directives, hourly_plan, totals, summary   │
│  └─────────────┘                                                         │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Request → Response

```
HTTP POST /optimize-energy
    │
    ├── [400] Pydantic validation fails
    │
    ▼
LLMResponse = interpret_operator_notes(notes)
    │
    ├── [500] LLM API error / empty response / JSON parse error
    │
    ▼
validated_directives = validate_llm_output(llm_response, N, battery)
    │
    ├── [500] GuardrailError: any of 13 checks fail
    │
    ▼
hour_constraints = apply_directives(hours, battery, directives)
    │   (pure deterministic transformation, no external calls)
    │
    ▼
raw_plan = solve_milp(hours, battery, constraints)
    │
    ├── [500] OptimizationError: infeasible / solver error
    │
    ▼
validate_plan(hours, battery, constraints, raw_plan)
    │
    ├── [500] PlanValidationError: independent validation fails
    │
    ▼
HTTP 200 OptimizeResponse
```

---

## Module Responsibilities

| Module | Responsibility | External Calls |
|--------|---------------|----------------|
| `config.py` | Load env vars, set tolerances | None |
| `schemas.py` | Pydantic models for all data structures | None |
| `llm.py` | Convert natural language → structured directives | OpenAI API |
| `guardrails.py` | Validate LLM output (13 checks) | None |
| `optimizer.py` | Apply directives, run MILP | PuLP/CBC (local) |
| `validator.py` | Independently replay & verify plan | None |
| `main.py` | FastAPI routes, error handling, orchestration | All above |

---

## MILP Model Structure

### Variables (per hour × 24 hours = 144+ variables total)

```
Continuous:
  grid[0..23]              ≥ 0    Grid import (kWh)
  solar_used[0..23]        ≥ 0    Solar energy used (kWh)
  charge[0..23]            ≥ 0    Battery charge (kWh)
  discharge[0..23]         ≥ 0    Battery discharge (kWh)
  battery_energy[0..23]    ≥ 0    Battery state-of-charge after hour (kWh)

Binary:
  b[0..23]                 ∈ {0,1}  1=charging mode, 0=discharging mode
```

### Constraints (per hour, 24 hours each)

```
Energy balance:    grid[h] + solar_used[h] + discharge[h] = demand[h] + charge[h]
Battery transition: battery_energy[h] = battery_energy[h-1] + charge[h] - discharge[h]
Battery minimum:   battery_energy[h] >= effective_minimum[h]
Battery capacity:  battery_energy[h] <= capacity
Charge rate:       charge[h] <= max_charge
Discharge rate:    discharge[h] <= max_discharge
Solar availability: solar_used[h] <= effective_solar[h]
Mutex charge:      charge[h] <= max_charge × b[h]
Mutex discharge:   discharge[h] <= max_discharge × (1 - b[h])
[+ directive constraints: no_charge, no_discharge, max_grid]

Global:
End-of-day:        battery_energy[23] = initial_energy
```

### Objective

```
minimize Σ(h=0..23) grid[h] × tariff[h]
```

---

## Security Architecture

```
LLM Output (UNTRUSTED)
    │
    ├── guardrails.py (validate all fields)
    │       ├── Type checks
    │       ├── Range checks
    │       ├── Consistency checks
    │       └── Semantic checks
    │
    ▼ (only if all 13 checks pass)
Optimizer (TRUSTED input)
    │
    ▼
Solver Output (UNTRUSTED - solver bugs possible)
    │
    ├── validator.py (independent replay)
    │       ├── Energy balance
    │       ├── Battery transitions
    │       ├── All constraint checks
    │       └── End-of-day neutrality
    │
    ▼ (only if all checks pass)
API Response (VALIDATED)
```

No secrets, stack traces, or internal state appear in any API response.

---

## Floating-Point Tolerance Strategy

- **Internal solver tolerance**: `1e-5` (FEASIBILITY_TOL)
- **Rounding for response**: 4 decimal places
- **Intermediate solver constraints**: NOT rounded (native float precision)

This avoids false validation failures from CBC's ~1e-9 numerical precision while still catching genuine constraint violations (e.g., a 10 kWh energy balance error).

---

## Deployment

```
Docker Container
┌─────────────────────────────────────────┐
│  python:3.12-slim                       │
│  + coinor-cbc (CBC solver)              │
│  + Python dependencies                  │
│                                         │
│  uvicorn app.main:app                   │
│  --host 0.0.0.0                         │
│  --port 8000                            │
│                                         │
│  Secrets: injected as env vars          │
│  (never baked into image)               │
└─────────────────────────────────────────┘
```
