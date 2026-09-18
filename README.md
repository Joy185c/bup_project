# GridWise Smart Campus Energy Optimization

> **AI-powered energy scheduling backend** for the GridWise Hackathon Challenge.
> Converts natural-language operator notes into deterministically validated MILP-optimized energy plans.

---

## Table of Contents

1. [Problem Overview](#problem-overview)
2. [Architecture](#architecture)
3. [Why LLM is Used](#why-llm-is-used)
4. [LLM → Guardrails → Optimizer Flow](#llm--guardrails--optimizer-flow)
5. [Supported Directives](#supported-directives)
6. [Optimization Formulation](#optimization-formulation)
7. [API Documentation](#api-documentation)
8. [Setup](#setup)
9. [Environment Variables](#environment-variables)
10. [Run Command](#run-command)
11. [Test Command](#test-command)
12. [Docker](#docker)
13. [Sample Request / Response](#sample-request--response)
14. [Security](#security)
15. [Limitations](#limitations)
16. [Dependency List](#dependency-list)
17. [MOCK_LLM Explanation](#mock_llm-explanation)

---

## Problem Overview

University campuses consume electricity from multiple sources:
- **Solar panels** (variable output, weather/time dependent)
- **Grid** (priced at time-varying tariffs in BDT/kWh)
- **Battery storage** (charge when cheap, discharge when expensive)

**The challenge**: given 24 hours of demand, solar, and tariff data, plus a battery specification, and **natural-language operator notes**, produce the lowest-cost 24-hour energy plan that satisfies all constraints.

Operator notes are real-world instructions like:
- *"Reduce solar output by 30% from 11 AM to 2 PM due to inverter maintenance"*
- *"Maintain at least 40 kWh in the battery during peak hours 6–9 PM"*
- *"Do not charge the battery from 5 PM to 9 PM"*

---

## Architecture

```
POST /optimize-energy
        │
        ▼
┌─────────────────────────┐
│  1. Request Validation   │  Pydantic v2 (structural + semantic)
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│  2. LLM Interpretation  │  OpenAI structured JSON output
│     (llm.py)            │  Converts natural language → directive JSON
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│  3. Guardrails          │  Deterministic validation of LLM output
│     (guardrails.py)     │  Rejects invalid/unsafe interpretations
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│  4. Directive Application│  Translates directives to per-hour constraints
│     (optimizer.py)      │
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│  5. MILP Optimization   │  PuLP + CBC solver minimizes grid cost
│     (optimizer.py)      │
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│  6. Plan Validation     │  Independent replay of all constraints
│     (validator.py)      │  Rejects invalid solver outputs
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│  7. JSON Response       │  Structured response with plan + summary
└─────────────────────────┘
```

---

## Why LLM is Used

The LLM solves the **natural language understanding** problem that deterministic code cannot solve generally:

1. **Ambiguity resolution**: "peak hours" could mean different things in different contexts
2. **Unit inference**: distinguishing "30% reduction" (factor=0.70) from "keep 30%" (factor=0.30)
3. **Time format parsing**: "1 PM to 3 PM" → `[13, 14]`, "10pm to 6am" → cross-midnight range
4. **Semantic understanding**: "do not charge during high-tariff evening" → `no_charge_window` directive

The LLM is **NOT** used to optimize the schedule. It only translates operator intent into structured JSON. The actual cost optimization is done deterministically by the MILP solver.

---

## LLM → Guardrails → Optimizer Flow

### Step 1: LLM Interpretation

The LLM receives:
- System prompt defining exactly the 6 supported directive types and their semantics
- User prompt with numbered operator notes

The LLM responds with structured JSON using OpenAI's `json_schema` response format (strict mode), producing exactly one interpretation per note.

Example LLM output:
```json
{
  "interpretations": [
    {
      "note_index": 0,
      "applies": true,
      "directive_type": "solar_reduction",
      "hours": [11, 12, 13],
      "factor": 0.7,
      "minimum_energy_kwh": null,
      "max_grid_kwh": null,
      "explanation": "30% reduction means keeping 70% (factor=0.7) from 11 AM to 2 PM (hours 11, 12, 13)"
    }
  ]
}
```

### Step 2: Guardrails (13 deterministic checks)

Every field of LLM output is validated:
- Exactly N interpretations for N notes
- Note indexes are exactly 0..N-1, no duplicates
- `directive_type` must be one of the 6 allowed types
- Hours: unique, sorted, integers in [0..23]
- `solar_reduction` factor: finite, in [0..1]
- `minimum_battery_reserve`: finite, non-negative, ≤ battery capacity
- `max_grid_kwh`: finite, non-negative
- `no_op` must have `applies=false` and no adjustment fields
- Non-`no_op` must have `applies=true`

**Failure = controlled HTTP 500 with no optimization attempted**

### Step 3: Directive Application

Directives are applied deterministically to compute per-hour constraints:
- Multiple overlapping directives: most restrictive wins (lowest solar factor, highest reserve, lowest grid cap)
- Results are `HourConstraints` objects used directly in the MILP model

### Step 4: MILP Optimization

The CBC solver minimizes total grid cost subject to all constraints. Battery charge/discharge mutex is enforced with binary variables.

### Step 5: Independent Validation

A separate replay function recalculates every constraint from scratch on the solver output. Any violation rejects the plan before it reaches the client.

---

## Supported Directives

| Directive | Effect | LLM Output Fields |
|-----------|--------|-------------------|
| `solar_reduction` | `effective_solar[h] = solar[h] × factor` | `hours`, `factor` (0..1) |
| `minimum_battery_reserve` | `battery_after[h] >= max(base_min, directive_min)` | `hours`, `minimum_energy_kwh` |
| `no_charge_window` | `charge[h] = 0` | `hours` |
| `no_discharge_window` | `discharge[h] = 0` | `hours` |
| `max_grid_window` | `grid[h] <= max_grid_kwh` | `hours`, `max_grid_kwh` |
| `no_op` | No effect | None |

**Time ranges are start-inclusive, end-exclusive:**
- "1 PM to 3 PM" → hours `[13, 14]`
- "80% reduction" → `factor = 0.2`

---

## Optimization Formulation

### Objective

```
minimize Σ(h=0..23) grid[h] × tariff[h]
```

### Decision Variables

| Variable | Domain | Description |
|----------|--------|-------------|
| `grid[h]` | ≥ 0 | Grid energy drawn (kWh) |
| `solar_used[h]` | ≥ 0 | Solar energy used (kWh) |
| `charge[h]` | ≥ 0 | Battery charge (kWh) |
| `discharge[h]` | ≥ 0 | Battery discharge (kWh) |
| `battery_energy[h]` | ≥ 0 | Battery state after hour h (kWh) |
| `b[h]` | {0,1} | 1=charging, 0=discharging (mutex) |

### Constraints

| Constraint | Formula |
|------------|---------|
| Energy balance | `grid[h] + solar_used[h] + discharge[h] = demand[h] + charge[h]` |
| Battery transition | `E[h] = E[h-1] + charge[h] - discharge[h]` |
| Battery minimum | `E[h] >= min_energy[h]` |
| Battery capacity | `E[h] <= capacity` |
| Charge rate | `charge[h] <= max_charge_per_hour` |
| Discharge rate | `discharge[h] <= max_discharge_per_hour` |
| Solar availability | `solar_used[h] <= effective_solar[h]` |
| No grid export | `grid[h] >= 0` |
| End-of-day neutrality | `E[23] = initial_energy` |
| Charge mutex | `charge[h] <= max_charge × b[h]` |
| Discharge mutex | `discharge[h] <= max_discharge × (1 - b[h])` |

---

## API Documentation

### GET /health

Returns server health status.

**Response:**
```json
{"status": "ok"}
```

### POST /optimize-energy

**Request:**
```json
{
  "scenario_id": "campus-2024-weekday-01",
  "operator_notes": [
    "Reduce solar output by 30% from 11 AM to 2 PM.",
    "Maintain at least 40 kWh in battery from 6 PM to 9 PM.",
    "Do not charge the battery from 5 PM to 9 PM."
  ],
  "hours": [
    {"hour": 0, "demand_kwh": 45.0, "solar_kwh": 0.0, "tariff_bdt_per_kwh": 5.0},
    ...
  ],
  "battery": {
    "capacity_kwh": 200.0,
    "initial_energy_kwh": 100.0,
    "minimum_energy_kwh": 20.0,
    "max_charge_kwh_per_hour": 50.0,
    "max_discharge_kwh_per_hour": 50.0
  }
}
```

**Response:**
```json
{
  "scenario_id": "campus-2024-weekday-01",
  "directive_interpretation": [
    {
      "note_index": 0,
      "applies": true,
      "directive_type": "solar_reduction",
      "structured_adjustment": {"hours": [11, 12, 13], "factor": 0.7},
      "explanation": "..."
    }
  ],
  "hourly_plan": [
    {
      "hour": 0,
      "grid_kwh": 45.0,
      "solar_used_kwh": 0.0,
      "battery_action": "idle",
      "battery_kwh": 0.0,
      "battery_energy_after_kwh": 100.0
    }
  ],
  "total_grid_kwh": 1234.5,
  "total_cost_bdt": 12345.0,
  "peak_grid_kwh": 95.0,
  "plan_summary": "Optimized 24-hour plan..."
}
```

**Error Responses:**
- `400 Bad Request`: Malformed or structurally invalid request
- `500 Internal Server Error`: LLM failure, guardrail violation, optimization failure, or plan validation failure

---

## Setup

### Prerequisites
- Python 3.12+
- OpenAI API key

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd gridwise-energy-optimization

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate
# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes (for real LLM) | — | OpenAI API key |
| `LLM_MODEL` | No | `gpt-4o` | OpenAI model to use |
| `MOCK_LLM` | No | `false` | Use mock LLM for local testing only |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |

> ⚠️ **MOCK_LLM must be `false` for hackathon submissions.** The mock only uses keyword matching and is not suitable for production.

---

## Run Command

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

For development with auto-reload:
```bash
uvicorn app.main:app --reload --port 8000
```

---

## Test Command

```bash
# Run all tests (uses MOCK_LLM=true automatically)
pytest -q

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_guardrails.py -v
pytest tests/test_optimizer.py -v
pytest tests/test_api.py -v
```

---

## Docker

### Build

```bash
docker build -t gridwise-energy-optimizer .
```

### Run

```bash
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_key_here \
  -e LLM_MODEL=gpt-4o \
  -e MOCK_LLM=false \
  gridwise-energy-optimizer
```

> ✅ API key is injected at runtime. It is never baked into the image.

### Test with Docker

```bash
# Health check
curl http://localhost:8000/health

# Optimization
curl -X POST http://localhost:8000/optimize-energy \
  -H "Content-Type: application/json" \
  -d @sample_request.json
```

---

## Sample Request / Response

### curl Example

```bash
# Health check
curl http://localhost:8000/health

# POST optimize-energy
curl -X POST http://localhost:8000/optimize-energy \
  -H "Content-Type: application/json" \
  -d @sample_request.json | python -m json.tool
```

See [`sample_request.json`](sample_request.json) for a complete 24-hour scenario with 3 operator notes:
1. Solar reduction during inverter maintenance
2. Battery reserve during peak hours
3. No-charge window during high-tariff period

---

## Security

- **API keys are never logged** — only initialization status is logged
- **Stack traces are never returned** to clients — only controlled error messages
- **LLM output is untrusted** — 13 deterministic guardrail checks before optimization
- **Solver output is untrusted** — independent replay validator before response
- **Secrets are environment variables** — never hardcoded or baked into Docker images
- **No raw internal state** is exposed in error responses

---

## Limitations

1. **Single LLM call per request** — complex notes may require clarification that the system cannot provide
2. **CBC solver timeout** — infeasible scenarios (e.g., demand exceeds all sources) will return a 500 error
3. **No persistence** — each request is stateless; no historical data is used
4. **24-hour fixed horizon** — multi-day optimization is not supported
5. **MOCK_LLM keyword matching** — the mock interpreter is simplistic and not suitable for production
6. **English-only notes** — the LLM prompt and system are designed for English-language operator notes

---

## Dependency List

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | 0.111.0 | Web framework |
| `uvicorn[standard]` | 0.30.1 | ASGI server |
| `pydantic` | 2.7.4 | Data validation |
| `openai` | 1.35.0 | LLM API client |
| `pulp` | 2.8.0 | MILP modeling |
| `python-dotenv` | 1.0.1 | Environment variable loading |
| `pytest` | 8.2.2 | Testing framework |
| `httpx` | 0.27.0 | HTTP client for tests |

---

## MOCK_LLM Explanation

`MOCK_LLM=true` enables a **keyword-based mock interpreter** for local development and CI testing without requiring an OpenAI API key.

### When to use MOCK_LLM=true
- Running `pytest` in CI/CD
- Local development without API key
- Debugging optimizer or guardrails logic

### When to use MOCK_LLM=false (default)
- All production deployments
- Hackathon submissions
- Actual operator note interpretation

### What the mock does
The mock uses simple regex pattern matching to detect directive keywords (solar, battery, charge, discharge, grid cap) and extract hours/values. It is **not** a substitute for real LLM understanding of complex or ambiguous notes.

> ⚠️ The actual hackathon submission **must** use `MOCK_LLM=false` with a valid `OPENAI_API_KEY`.
