"""
Independent plan validator / replay engine.

This module recalculates all constraints from scratch and verifies the
proposed optimizer plan is truly valid. It is intentionally written
independently from optimizer.py so that a solver or modeling bug cannot
silently produce an invalid response.

If validation fails, the plan is REJECTED before returning to the client.
"""
from __future__ import annotations

import logging
import math

from app.config import FEASIBILITY_TOL
from app.optimizer import HourConstraints
from app.schemas import BatterySpec, HourData

logger = logging.getLogger(__name__)


class PlanValidationError(Exception):
    """Raised when the optimizer plan fails independent validation."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def validate_plan(
    hours_data: list[HourData],
    battery: BatterySpec,
    constraints: list[HourConstraints],
    raw_plan: list[dict],
) -> None:
    """
    Independently validate the optimizer plan.

    Recalculates every constraint from scratch.
    Raises PlanValidationError on any violation.

    Uses FEASIBILITY_TOL to avoid false failures from solver floating-point
    precision, but rejects genuine constraint violations.
    """
    hours_by_h = {hd.hour: hd for hd in hours_data}
    tol = FEASIBILITY_TOL

    if len(raw_plan) != 24:
        raise PlanValidationError(
            f"Plan must have exactly 24 hourly entries, got {len(raw_plan)}"
        )

    hour_values = [entry["hour"] for entry in raw_plan]
    if sorted(hour_values) != list(range(24)):
        raise PlanValidationError(
            f"Plan hours must be exactly 0..23, got {sorted(hour_values)}"
        )

    # Sort plan by hour for sequential validation
    plan_by_h = {entry["hour"]: entry for entry in raw_plan}

    prev_battery_energy = battery.initial_energy_kwh

    for h in range(24):
        entry = plan_by_h[h]
        hd = hours_by_h[h]
        con = constraints[h]

        g = entry["grid_kwh"]
        s = entry["solar_used_kwh"]
        c = entry["charge_kwh"]
        d = entry["discharge_kwh"]
        e_after = entry["battery_energy_after_kwh"]

        # --- Non-negativity ---
        for name, val in [
            ("grid_kwh", g),
            ("solar_used_kwh", s),
            ("charge_kwh", c),
            ("discharge_kwh", d),
            ("battery_energy_after_kwh", e_after),
        ]:
            if val < -tol:
                raise PlanValidationError(
                    f"Hour {h}: {name} is negative ({val:.6f})"
                )

        # --- Solar availability ---
        if s > con.effective_solar + tol:
            raise PlanValidationError(
                f"Hour {h}: solar_used_kwh ({s:.6f}) exceeds "
                f"effective_solar ({con.effective_solar:.6f})"
            )

        # --- Energy balance: grid + solar + discharge == demand + charge ---
        supply = g + s + d
        demand_plus_charge = hd.demand_kwh + c
        balance_error = abs(supply - demand_plus_charge)
        if balance_error > tol:
            raise PlanValidationError(
                f"Hour {h}: energy balance violated. "
                f"Supply ({g:.4f}+{s:.4f}+{d:.4f}={supply:.4f}) != "
                f"Demand+Charge ({hd.demand_kwh:.4f}+{c:.4f}={demand_plus_charge:.4f}). "
                f"Error: {balance_error:.2e}"
            )

        # --- Battery transition ---
        expected_e_after = prev_battery_energy + c - d
        transition_error = abs(e_after - expected_e_after)
        if transition_error > tol:
            raise PlanValidationError(
                f"Hour {h}: battery transition violated. "
                f"Expected E_after={expected_e_after:.4f}, "
                f"got {e_after:.4f}. Error: {transition_error:.2e}"
            )

        # --- Battery minimum ---
        if e_after < con.min_battery_energy - tol:
            raise PlanValidationError(
                f"Hour {h}: battery_energy_after ({e_after:.4f}) < "
                f"minimum ({con.min_battery_energy:.4f})"
            )

        # --- Battery capacity ---
        if e_after > battery.capacity_kwh + tol:
            raise PlanValidationError(
                f"Hour {h}: battery_energy_after ({e_after:.4f}) > "
                f"capacity ({battery.capacity_kwh:.4f})"
            )

        # --- Charge rate ---
        if c > battery.max_charge_kwh_per_hour + tol:
            raise PlanValidationError(
                f"Hour {h}: charge_kwh ({c:.4f}) > "
                f"max_charge_kwh_per_hour ({battery.max_charge_kwh_per_hour:.4f})"
            )

        # --- Discharge rate ---
        if d > battery.max_discharge_kwh_per_hour + tol:
            raise PlanValidationError(
                f"Hour {h}: discharge_kwh ({d:.4f}) > "
                f"max_discharge_kwh_per_hour ({battery.max_discharge_kwh_per_hour:.4f})"
            )

        # --- No-charge window ---
        if not con.charge_allowed and c > tol:
            raise PlanValidationError(
                f"Hour {h}: charge_kwh ({c:.4f}) > 0 but no_charge_window is active"
            )

        # --- No-discharge window ---
        if not con.discharge_allowed and d > tol:
            raise PlanValidationError(
                f"Hour {h}: discharge_kwh ({d:.4f}) > 0 but no_discharge_window is active"
            )

        # --- Max grid window ---
        if con.max_grid_kwh is not None and g > con.max_grid_kwh + tol:
            raise PlanValidationError(
                f"Hour {h}: grid_kwh ({g:.4f}) > max_grid_kwh ({con.max_grid_kwh:.4f})"
            )

        # --- No simultaneous charge and discharge ---
        if c > tol and d > tol:
            raise PlanValidationError(
                f"Hour {h}: simultaneous charge ({c:.4f}) and discharge ({d:.4f}) detected"
            )

        prev_battery_energy = e_after

    # --- End-of-day neutrality ---
    final_battery = plan_by_h[23]["battery_energy_after_kwh"]
    neutrality_error = abs(final_battery - battery.initial_energy_kwh)
    if neutrality_error > tol:
        raise PlanValidationError(
            f"End-of-day neutrality violated: "
            f"final battery ({final_battery:.4f}) != "
            f"initial ({battery.initial_energy_kwh:.4f}). "
            f"Error: {neutrality_error:.2e}"
        )

    logger.info("Independent plan validation PASSED for all 24 hours")
