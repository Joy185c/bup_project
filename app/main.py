"""
GridWise Smart Campus Energy Optimization - FastAPI Application.

Pipeline for POST /optimize-energy:
  1. Request validation (Pydantic)
  2. LLM operator-note interpretation
  3. Deterministic guardrails validation
  4. Directive application
  5. MILP optimization (PuLP + CBC)
  6. Independent plan validation
  7. Response construction
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import LOG_LEVEL
from app.guardrails import GuardrailError, validate_llm_output
from app.llm import interpret_operator_notes
from app.optimizer import HourConstraints, OptimizationError, apply_directives, solve_milp
from app.schemas import (
    BatterySpec,
    DirectiveInterpretationResponse,
    HourlyPlan,
    LLMNoteInterpretation,
    MaxGridWindowDirective,
    MinimumBatteryReserveDirective,
    NoChargeWindowDirective,
    NoDischargeWindowDirective,
    NoOpDirective,
    OptimizeRequest,
    OptimizeResponse,
    SolarReductionDirective,
    StructuredAdjustment,
    ValidatedDirective,
)
from app.validator import PlanValidationError, validate_plan

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="GridWise Smart Campus Energy Optimization",
    description=(
        "AI-powered energy scheduling backend that uses LLM-interpreted "
        "operator notes combined with MILP optimization to minimize grid costs."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return HTTP 400 for Pydantic validation errors instead of FastAPI's default 422."""
    logger.warning("Request validation error: %s", str(exc)[:500])
    # Convert Pydantic errors to JSON-serializable form (ctx may contain exceptions)
    safe_errors = []
    for err in exc.errors():
        safe_err = {
            "type": err.get("type"),
            "loc": list(err.get("loc", [])),
            "msg": err.get("msg"),
        }
        # Include url if present
        if "url" in err:
            safe_err["url"] = err["url"]
        safe_errors.append(safe_err)
    return JSONResponse(
        status_code=400,
        content={
            "error": "invalid_request",
            "message": "Request validation failed",
            "details": safe_errors,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Return HTTP 500 for unexpected errors. NEVER expose secrets or stack traces."""
    logger.error("Unhandled exception: %s", type(exc).__name__, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An internal error occurred. Check server logs for details.",
        },
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/optimize-energy", response_model=OptimizeResponse)
async def optimize_energy(request: OptimizeRequest):
    """
    Main optimization endpoint.

    Accepts natural-language operator notes and energy scenario data,
    returns an optimized 24-hour energy plan.
    """
    scenario_id = request.scenario_id
    logger.info("Processing optimization request for scenario: %s", scenario_id)

    # ------------------------------------------------------------------
    # Step 1: LLM interpretation of operator notes
    # ------------------------------------------------------------------
    try:
        llm_response = interpret_operator_notes(request.operator_notes)
    except Exception as exc:
        logger.error("LLM interpretation failed [%s]: %s", type(exc).__name__, str(exc)[:300])
        return JSONResponse(
            status_code=500,
            content={
                "error": "llm_error",
                "message": "Failed to interpret operator notes. Check server logs.",
            },
        )

    # ------------------------------------------------------------------
    # Step 2: Deterministic guardrails
    # ------------------------------------------------------------------
    try:
        validated_directives = validate_llm_output(
            llm_response,
            num_notes=len(request.operator_notes),
            battery=request.battery,
        )
    except GuardrailError as exc:
        logger.error("Guardrail validation failed: %s", exc.message)
        return JSONResponse(
            status_code=500,
            content={
                "error": "guardrail_error",
                "message": f"LLM output failed safety validation: {exc.message}",
            },
        )

    # ------------------------------------------------------------------
    # Step 3: Directive application
    # ------------------------------------------------------------------
    hour_constraints = apply_directives(
        hours_data=request.hours,
        battery=request.battery,
        directives=validated_directives,
    )

    # ------------------------------------------------------------------
    # Step 4: MILP optimization
    # ------------------------------------------------------------------
    try:
        raw_plan = solve_milp(
            hours_data=request.hours,
            battery=request.battery,
            constraints=hour_constraints,
        )
    except OptimizationError as exc:
        logger.error("Optimization failed: %s", str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "error": "optimization_error",
                "message": str(exc),
            },
        )

    # ------------------------------------------------------------------
    # Step 5: Independent plan validation
    # ------------------------------------------------------------------
    try:
        validate_plan(
            hours_data=request.hours,
            battery=request.battery,
            constraints=hour_constraints,
            raw_plan=raw_plan,
        )
    except PlanValidationError as exc:
        logger.error("Plan validation failed: %s", exc.message)
        return JSONResponse(
            status_code=500,
            content={
                "error": "plan_validation_error",
                "message": f"Optimizer produced an invalid plan: {exc.message}",
            },
        )

    # ------------------------------------------------------------------
    # Step 6: Build response
    # ------------------------------------------------------------------
    directive_interpretation = _build_directive_interpretation(
        llm_response.interpretations,
        validated_directives,
    )

    hourly_plan = _build_hourly_plan(raw_plan)

    total_grid_kwh = round(sum(h.grid_kwh for h in hourly_plan), 4)
    total_cost_bdt = _calculate_total_cost(raw_plan, request.hours)
    peak_grid_kwh = round(max(h.grid_kwh for h in hourly_plan), 4)

    plan_summary = _generate_plan_summary(
        scenario_id=scenario_id,
        hourly_plan=hourly_plan,
        total_grid_kwh=total_grid_kwh,
        total_cost_bdt=total_cost_bdt,
        peak_grid_kwh=peak_grid_kwh,
        directives=validated_directives,
        notes=request.operator_notes,
    )

    logger.info(
        "Optimization complete for %s: total_grid=%.2f kWh, total_cost=%.2f BDT",
        scenario_id,
        total_grid_kwh,
        total_cost_bdt,
    )

    return OptimizeResponse(
        scenario_id=scenario_id,
        directive_interpretation=directive_interpretation,
        hourly_plan=hourly_plan,
        total_grid_kwh=total_grid_kwh,
        total_cost_bdt=total_cost_bdt,
        peak_grid_kwh=peak_grid_kwh,
        plan_summary=plan_summary,
    )


# ---------------------------------------------------------------------------
# Response builders
# ---------------------------------------------------------------------------

def _build_directive_interpretation(
    llm_interps: list[LLMNoteInterpretation],
    validated: list[ValidatedDirective],
) -> list[DirectiveInterpretationResponse]:
    """Build the directive_interpretation response array."""
    result = []
    # llm_interps and validated are aligned (both sorted by note_index)
    sorted_interps = sorted(llm_interps, key=lambda x: x.note_index)

    for interp, directive in zip(sorted_interps, validated):
        structured_adjustment = _build_structured_adjustment(directive)
        result.append(DirectiveInterpretationResponse(
            note_index=interp.note_index,
            applies=interp.applies,
            directive_type=interp.directive_type,
            structured_adjustment=structured_adjustment,
            explanation=interp.explanation,
        ))

    return result


def _build_structured_adjustment(
    directive: ValidatedDirective,
) -> Optional[StructuredAdjustment]:
    """Convert a validated directive to the structured_adjustment response format."""
    if isinstance(directive, NoOpDirective):
        return None
    elif isinstance(directive, SolarReductionDirective):
        return StructuredAdjustment(hours=directive.hours, factor=directive.factor)
    elif isinstance(directive, MinimumBatteryReserveDirective):
        return StructuredAdjustment(
            hours=directive.hours,
            minimum_energy_kwh=directive.minimum_energy_kwh,
        )
    elif isinstance(directive, (NoChargeWindowDirective, NoDischargeWindowDirective)):
        return StructuredAdjustment(hours=directive.hours)
    elif isinstance(directive, MaxGridWindowDirective):
        return StructuredAdjustment(
            hours=directive.hours,
            max_grid_kwh=directive.max_grid_kwh,
        )
    return None


def _build_hourly_plan(raw_plan: list[dict]) -> list[HourlyPlan]:
    """Convert raw solver plan to HourlyPlan response objects."""
    hourly: list[HourlyPlan] = []
    for entry in sorted(raw_plan, key=lambda x: x["hour"]):
        c = entry["charge_kwh"]
        d = entry["discharge_kwh"]

        tol = 1e-5
        if c > tol:
            action = "charge"
            battery_kwh = round(c, 4)
        elif d > tol:
            action = "discharge"
            battery_kwh = round(d, 4)
        else:
            action = "idle"
            battery_kwh = 0.0

        hourly.append(HourlyPlan(
            hour=entry["hour"],
            grid_kwh=round(entry["grid_kwh"], 4),
            solar_used_kwh=round(entry["solar_used_kwh"], 4),
            battery_action=action,
            battery_kwh=battery_kwh,
            battery_energy_after_kwh=round(entry["battery_energy_after_kwh"], 4),
        ))
    return hourly


def _calculate_total_cost(raw_plan: list[dict], hours_data) -> float:
    """Calculate total grid cost in BDT from the validated plan."""
    hours_by_h = {hd.hour: hd for hd in hours_data}
    total = sum(
        entry["grid_kwh"] * hours_by_h[entry["hour"]].tariff_bdt_per_kwh
        for entry in raw_plan
    )
    return round(total, 4)


def _generate_plan_summary(
    scenario_id: str,
    hourly_plan: list[HourlyPlan],
    total_grid_kwh: float,
    total_cost_bdt: float,
    peak_grid_kwh: float,
    directives: list[ValidatedDirective],
    notes: list[str],
) -> str:
    """Generate a concise human-readable summary of the optimization result."""
    active_directives = [
        d for d in directives if not isinstance(d, NoOpDirective)
    ]
    solar_hours = sum(1 for h in hourly_plan if h.solar_used_kwh > 0.01)
    charge_hours = sum(1 for h in hourly_plan if h.battery_action == "charge")
    discharge_hours = sum(1 for h in hourly_plan if h.battery_action == "discharge")

    directive_types = [type(d).__name__.replace("Directive", "") for d in active_directives]
    directive_str = ", ".join(directive_types) if directive_types else "none"

    return (
        f"Scenario '{scenario_id}': Optimized 24-hour energy plan with "
        f"{len(notes)} operator note(s) applied ({len(active_directives)} active directive(s): {directive_str}). "
        f"Total grid draw: {total_grid_kwh:.2f} kWh at total cost {total_cost_bdt:.2f} BDT. "
        f"Peak grid hour: {peak_grid_kwh:.2f} kWh. "
        f"Solar used in {solar_hours} hour(s). "
        f"Battery charged in {charge_hours} hour(s), discharged in {discharge_hours} hour(s)."
    )

import os
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if not os.path.exists(frontend_dist):
    frontend_dist = os.path.join(os.path.dirname(__file__), "..", "public")

if os.path.exists(frontend_dist):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    
    @app.get("/{catchall:path}")
    async def serve_spa(catchall: str):
        file_path = os.path.join(frontend_dist, catchall)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
