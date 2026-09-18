"""
Deterministic guardrails for LLM output validation.

ALL LLM output is treated as UNTRUSTED. This module validates the raw LLM
response before any optimizer interaction occurs. If validation fails, a
controlled error is raised — we never silently repair or guess values.
"""
from __future__ import annotations

import math
import logging
from typing import Optional

from app.schemas import (
    ALLOWED_DIRECTIVE_TYPES,
    BatterySpec,
    LLMNoteInterpretation,
    LLMResponse,
    MaxGridWindowDirective,
    MinimumBatteryReserveDirective,
    NoChargeWindowDirective,
    NoDischargeWindowDirective,
    NoOpDirective,
    SolarReductionDirective,
    ValidatedDirective,
)

logger = logging.getLogger(__name__)


class GuardrailError(Exception):
    """Raised when LLM output fails deterministic validation."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def validate_llm_output(
    llm_response: LLMResponse,
    num_notes: int,
    battery: BatterySpec,
) -> list[ValidatedDirective]:
    """
    Validate raw LLM interpretations and convert to typed directives.

    Raises GuardrailError on any validation failure.
    Returns a list of ValidatedDirective (one per note, in order).
    """
    interps = llm_response.interpretations

    # 1. Exactly one interpretation per note
    if len(interps) != num_notes:
        raise GuardrailError(
            f"Expected exactly {num_notes} interpretation(s) from LLM, "
            f"got {len(interps)}"
        )

    # 2. note_index values must be exactly 0..N-1
    # 3. No duplicate note indexes
    seen_indexes: set[int] = set()
    for interp in interps:
        if interp.note_index < 0 or interp.note_index >= num_notes:
            raise GuardrailError(
                f"note_index {interp.note_index} is out of range [0, {num_notes - 1}]"
            )
        if interp.note_index in seen_indexes:
            raise GuardrailError(
                f"Duplicate note_index {interp.note_index} in LLM response"
            )
        seen_indexes.add(interp.note_index)

    expected = set(range(num_notes))
    if seen_indexes != expected:
        missing = expected - seen_indexes
        raise GuardrailError(
            f"Missing note_index values: {sorted(missing)}"
        )

    # Sort interpretations by note_index so we process in order
    sorted_interps = sorted(interps, key=lambda x: x.note_index)

    validated: list[ValidatedDirective] = []
    for interp in sorted_interps:
        directive = _validate_single(interp, battery)
        validated.append(directive)

    logger.info("Guardrails passed: %d directive(s) validated", len(validated))
    return validated


def _validate_single(
    interp: LLMNoteInterpretation,
    battery: BatterySpec,
) -> ValidatedDirective:
    """Validate a single interpretation and return a typed directive."""

    dtype = interp.directive_type

    # 4. directive_type must be allowed
    if dtype not in ALLOWED_DIRECTIVE_TYPES:
        raise GuardrailError(
            f"note_index {interp.note_index}: directive_type '{dtype}' is not allowed. "
            f"Allowed types: {sorted(ALLOWED_DIRECTIVE_TYPES)}"
        )

    # 11. no_op => applies=false
    if dtype == "no_op" and interp.applies:
        raise GuardrailError(
            f"note_index {interp.note_index}: directive_type 'no_op' must have applies=false"
        )

    # 12. non-no_op => applies=true
    if dtype != "no_op" and not interp.applies:
        raise GuardrailError(
            f"note_index {interp.note_index}: directive_type '{dtype}' must have applies=true"
        )

    # 13. no_op must not contain adjustment values
    if dtype == "no_op":
        if interp.hours is not None:
            raise GuardrailError(
                f"note_index {interp.note_index}: no_op must not have hours set"
            )
        if interp.factor is not None:
            raise GuardrailError(
                f"note_index {interp.note_index}: no_op must not have factor set"
            )
        if interp.minimum_energy_kwh is not None:
            raise GuardrailError(
                f"note_index {interp.note_index}: no_op must not have minimum_energy_kwh set"
            )
        if interp.max_grid_kwh is not None:
            raise GuardrailError(
                f"note_index {interp.note_index}: no_op must not have max_grid_kwh set"
            )
        return NoOpDirective()

    # All non-no_op directives require hours
    hours = _validate_hours(interp)

    # Directive-specific validation
    if dtype == "solar_reduction":
        return _validate_solar_reduction(interp, hours)
    elif dtype == "minimum_battery_reserve":
        return _validate_minimum_battery_reserve(interp, hours, battery)
    elif dtype == "no_charge_window":
        return NoChargeWindowDirective(hours=hours)
    elif dtype == "no_discharge_window":
        return NoDischargeWindowDirective(hours=hours)
    elif dtype == "max_grid_window":
        return _validate_max_grid_window(interp, hours)
    else:
        # Should not reach here due to allowed type check above
        raise GuardrailError(
            f"note_index {interp.note_index}: unhandled directive_type '{dtype}'"
        )


def _validate_hours(interp: LLMNoteInterpretation) -> list[int]:
    """Validate hours field: required, unique, sorted, integers 0..23."""
    idx = interp.note_index

    if interp.hours is None:
        raise GuardrailError(
            f"note_index {idx}: directive_type '{interp.directive_type}' requires hours to be set"
        )

    hours = interp.hours

    if len(hours) == 0:
        raise GuardrailError(
            f"note_index {idx}: hours list is empty"
        )

    # 5. hours must be unique
    if len(hours) != len(set(hours)):
        raise GuardrailError(
            f"note_index {idx}: hours must be unique, got duplicates in {hours}"
        )

    # 7. hours must be between 0 and 23
    for h in hours:
        if not isinstance(h, int):
            raise GuardrailError(
                f"note_index {idx}: hours must be integers, got {h!r} (type {type(h).__name__})"
            )
        if h < 0 or h > 23:
            raise GuardrailError(
                f"note_index {idx}: hour {h} is out of range [0, 23]"
            )

    # 6. hours must be sorted ascending
    if hours != sorted(hours):
        raise GuardrailError(
            f"note_index {idx}: hours must be sorted ascending, got {hours}"
        )

    return hours


def _validate_solar_reduction(
    interp: LLMNoteInterpretation, hours: list[int]
) -> SolarReductionDirective:
    idx = interp.note_index

    if interp.factor is None:
        raise GuardrailError(
            f"note_index {idx}: solar_reduction requires factor to be set"
        )

    factor = interp.factor

    # 8. solar factor must be finite and 0..1
    if not math.isfinite(factor):
        raise GuardrailError(
            f"note_index {idx}: solar_reduction factor must be finite, got {factor}"
        )
    if factor < 0.0 or factor > 1.0:
        raise GuardrailError(
            f"note_index {idx}: solar_reduction factor must be in [0, 1], got {factor}"
        )

    return SolarReductionDirective(hours=hours, factor=factor)


def _validate_minimum_battery_reserve(
    interp: LLMNoteInterpretation, hours: list[int], battery: BatterySpec
) -> MinimumBatteryReserveDirective:
    idx = interp.note_index

    if interp.minimum_energy_kwh is None:
        raise GuardrailError(
            f"note_index {idx}: minimum_battery_reserve requires minimum_energy_kwh to be set"
        )

    reserve = interp.minimum_energy_kwh

    # 9. reserve must be finite, non-negative, and <= battery capacity
    if not math.isfinite(reserve):
        raise GuardrailError(
            f"note_index {idx}: minimum_energy_kwh must be finite, got {reserve}"
        )
    if reserve < 0.0:
        raise GuardrailError(
            f"note_index {idx}: minimum_energy_kwh must be non-negative, got {reserve}"
        )
    if reserve > battery.capacity_kwh:
        raise GuardrailError(
            f"note_index {idx}: minimum_energy_kwh {reserve} exceeds battery capacity "
            f"{battery.capacity_kwh}"
        )

    return MinimumBatteryReserveDirective(hours=hours, minimum_energy_kwh=reserve)


def _validate_max_grid_window(
    interp: LLMNoteInterpretation, hours: list[int]
) -> MaxGridWindowDirective:
    idx = interp.note_index

    if interp.max_grid_kwh is None:
        raise GuardrailError(
            f"note_index {idx}: max_grid_window requires max_grid_kwh to be set"
        )

    max_grid = interp.max_grid_kwh

    # 10. max_grid_kwh must be finite and non-negative
    if not math.isfinite(max_grid):
        raise GuardrailError(
            f"note_index {idx}: max_grid_kwh must be finite, got {max_grid}"
        )
    if max_grid < 0.0:
        raise GuardrailError(
            f"note_index {idx}: max_grid_kwh must be non-negative, got {max_grid}"
        )

    return MaxGridWindowDirective(hours=hours, max_grid_kwh=max_grid)
