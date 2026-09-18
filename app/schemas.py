"""
Pydantic v2 schemas for request/response validation.
These implement the exact GridWise challenge API contract.
"""
from __future__ import annotations

import math
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class HourData(BaseModel):
    """Energy data for a single hour (0–23)."""

    hour: int = Field(..., ge=0, le=23)
    demand_kwh: float = Field(..., ge=0.0)
    solar_kwh: float = Field(..., ge=0.0)
    tariff_bdt_per_kwh: float = Field(..., ge=0.0)

    @model_validator(mode="after")
    def check_finite(self) -> "HourData":
        for field_name in ("demand_kwh", "solar_kwh", "tariff_bdt_per_kwh"):
            val = getattr(self, field_name)
            if not math.isfinite(val):
                raise ValueError(f"{field_name} must be finite, got {val}")
        return self


class BatterySpec(BaseModel):
    """Battery specification."""

    capacity_kwh: float = Field(..., gt=0.0)
    initial_energy_kwh: float = Field(..., ge=0.0)
    minimum_energy_kwh: float = Field(..., ge=0.0)
    max_charge_kwh_per_hour: float = Field(..., gt=0.0)
    max_discharge_kwh_per_hour: float = Field(..., gt=0.0)

    @model_validator(mode="after")
    def check_bounds(self) -> "BatterySpec":
        for field_name in (
            "capacity_kwh",
            "initial_energy_kwh",
            "minimum_energy_kwh",
            "max_charge_kwh_per_hour",
            "max_discharge_kwh_per_hour",
        ):
            val = getattr(self, field_name)
            if not math.isfinite(val):
                raise ValueError(f"{field_name} must be finite, got {val}")

        if self.minimum_energy_kwh > self.capacity_kwh:
            raise ValueError(
                "minimum_energy_kwh must be <= capacity_kwh, "
                f"got {self.minimum_energy_kwh} > {self.capacity_kwh}"
            )
        if self.initial_energy_kwh > self.capacity_kwh:
            raise ValueError(
                "initial_energy_kwh must be <= capacity_kwh, "
                f"got {self.initial_energy_kwh} > {self.capacity_kwh}"
            )
        if self.initial_energy_kwh < self.minimum_energy_kwh:
            raise ValueError(
                "initial_energy_kwh must be >= minimum_energy_kwh, "
                f"got {self.initial_energy_kwh} < {self.minimum_energy_kwh}"
            )
        return self


class OptimizeRequest(BaseModel):
    """POST /optimize-energy request body."""

    scenario_id: str = Field(..., min_length=1)
    operator_notes: Annotated[list[str], Field(min_length=1, max_length=3)]
    hours: list[HourData] = Field(...)
    battery: BatterySpec

    @model_validator(mode="after")
    def check_hours(self) -> "OptimizeRequest":
        if len(self.hours) != 24:
            raise ValueError(
                f"hours must contain exactly 24 entries, got {len(self.hours)}"
            )
        hour_values = [h.hour for h in self.hours]
        if sorted(hour_values) != list(range(24)):
            raise ValueError(
                "hours must contain exactly one entry for each hour 0..23"
            )
        return self


# ---------------------------------------------------------------------------
# LLM / directive schemas (internal)
# ---------------------------------------------------------------------------

# Directive type literal
DirectiveType = Literal[
    "solar_reduction",
    "minimum_battery_reserve",
    "no_charge_window",
    "no_discharge_window",
    "max_grid_window",
    "no_op",
]

ALLOWED_DIRECTIVE_TYPES: frozenset[str] = frozenset(
    [
        "solar_reduction",
        "minimum_battery_reserve",
        "no_charge_window",
        "no_discharge_window",
        "max_grid_window",
        "no_op",
    ]
)


class LLMNoteInterpretation(BaseModel):
    """Raw LLM output for a single operator note (treated as untrusted)."""

    note_index: int
    applies: bool
    directive_type: str
    hours: Optional[list[int]] = None
    factor: Optional[float] = None
    minimum_energy_kwh: Optional[float] = None
    max_grid_kwh: Optional[float] = None
    explanation: str


class LLMResponse(BaseModel):
    """Complete LLM response for all operator notes."""

    interpretations: list[LLMNoteInterpretation]


# ---------------------------------------------------------------------------
# Validated directives (post-guardrails, used for optimization)
# ---------------------------------------------------------------------------


class SolarReductionDirective(BaseModel):
    directive_type: Literal["solar_reduction"] = "solar_reduction"
    hours: list[int]
    factor: float  # 0..1


class MinimumBatteryReserveDirective(BaseModel):
    directive_type: Literal["minimum_battery_reserve"] = "minimum_battery_reserve"
    hours: list[int]
    minimum_energy_kwh: float


class NoChargeWindowDirective(BaseModel):
    directive_type: Literal["no_charge_window"] = "no_charge_window"
    hours: list[int]


class NoDischargeWindowDirective(BaseModel):
    directive_type: Literal["no_discharge_window"] = "no_discharge_window"
    hours: list[int]


class MaxGridWindowDirective(BaseModel):
    directive_type: Literal["max_grid_window"] = "max_grid_window"
    hours: list[int]
    max_grid_kwh: float


class NoOpDirective(BaseModel):
    directive_type: Literal["no_op"] = "no_op"


ValidatedDirective = Union[
    SolarReductionDirective,
    MinimumBatteryReserveDirective,
    NoChargeWindowDirective,
    NoDischargeWindowDirective,
    MaxGridWindowDirective,
    NoOpDirective,
]


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class StructuredAdjustment(BaseModel):
    """Directive-specific adjustment data for the response."""

    hours: Optional[list[int]] = None
    factor: Optional[float] = None
    minimum_energy_kwh: Optional[float] = None
    max_grid_kwh: Optional[float] = None


class DirectiveInterpretationResponse(BaseModel):
    """One interpreted operator note in the response."""

    note_index: int
    applies: bool
    directive_type: str
    structured_adjustment: Optional[StructuredAdjustment]
    explanation: str


class HourlyPlan(BaseModel):
    """Optimization result for a single hour."""

    hour: int
    grid_kwh: float
    solar_used_kwh: float
    battery_action: Literal["charge", "discharge", "idle"]
    battery_kwh: float
    battery_energy_after_kwh: float


class OptimizeResponse(BaseModel):
    """POST /optimize-energy response body."""

    scenario_id: str
    directive_interpretation: list[DirectiveInterpretationResponse]
    hourly_plan: list[HourlyPlan]
    total_grid_kwh: float
    total_cost_bdt: float
    peak_grid_kwh: float
    plan_summary: str
