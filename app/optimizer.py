"""
MILP energy optimizer using PuLP + CBC.

Applies directives deterministically, then solves the MILP to minimize
total grid energy cost. Returns a raw plan dict for the independent validator.

Pipeline:
  1. Apply directives to compute effective solar and per-hour constraints
  2. Build and solve MILP with PuLP/CBC (PuLP 3.x API)
  3. Return raw plan (NOT yet validated - caller must validate)
"""
from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass
from typing import Optional

import pulp

from app.schemas import (
    BatterySpec,
    HourData,
    MaxGridWindowDirective,
    MinimumBatteryReserveDirective,
    NoChargeWindowDirective,
    NoDischargeWindowDirective,
    NoOpDirective,
    SolarReductionDirective,
    ValidatedDirective,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Directive application
# ---------------------------------------------------------------------------

@dataclass
class HourConstraints:
    """Per-hour constraints derived from directives."""
    effective_solar: float          # kWh available from solar this hour
    min_battery_energy: float       # minimum battery energy after this hour
    charge_allowed: bool = True     # False if no_charge_window applies
    discharge_allowed: bool = True  # False if no_discharge_window applies
    max_grid_kwh: Optional[float] = None  # grid cap if max_grid_window applies


def apply_directives(
    hours_data: list[HourData],
    battery: BatterySpec,
    directives: list[ValidatedDirective],
) -> list[HourConstraints]:
    """
    Apply validated directives deterministically to build per-hour constraints.

    Multiple directives affecting the same hour are all applied.
    For solar reduction, the most restrictive (lowest factor) wins per hour.
    For battery reserve, the highest reserve wins per hour.
    For grid cap, the lowest cap wins per hour.
    """
    # Sort hours_data by hour for deterministic access
    hours_by_h = {hd.hour: hd for hd in hours_data}

    # Initialize with base values
    constraints: list[HourConstraints] = []
    for h in range(24):
        hd = hours_by_h[h]
        constraints.append(HourConstraints(
            effective_solar=hd.solar_kwh,
            min_battery_energy=battery.minimum_energy_kwh,
        ))

    for directive in directives:
        if isinstance(directive, NoOpDirective):
            continue  # no-op, skip

        if isinstance(directive, SolarReductionDirective):
            for h in directive.hours:
                # Apply reduction: most restrictive factor (lowest) wins
                new_solar = hours_by_h[h].solar_kwh * directive.factor
                constraints[h].effective_solar = min(
                    constraints[h].effective_solar, new_solar
                )

        elif isinstance(directive, MinimumBatteryReserveDirective):
            for h in directive.hours:
                # Most restrictive (highest) reserve wins
                constraints[h].min_battery_energy = max(
                    constraints[h].min_battery_energy,
                    directive.minimum_energy_kwh,
                )

        elif isinstance(directive, NoChargeWindowDirective):
            for h in directive.hours:
                constraints[h].charge_allowed = False

        elif isinstance(directive, NoDischargeWindowDirective):
            for h in directive.hours:
                constraints[h].discharge_allowed = False

        elif isinstance(directive, MaxGridWindowDirective):
            for h in directive.hours:
                # Most restrictive (lowest) grid cap wins
                current = constraints[h].max_grid_kwh
                if current is None:
                    constraints[h].max_grid_kwh = directive.max_grid_kwh
                else:
                    constraints[h].max_grid_kwh = min(current, directive.max_grid_kwh)

    return constraints


# ---------------------------------------------------------------------------
# MILP optimizer
# ---------------------------------------------------------------------------

class OptimizationError(Exception):
    """Raised when the optimizer fails to find a feasible/optimal solution."""
    pass


def solve_milp(
    hours_data: list[HourData],
    battery: BatterySpec,
    constraints: list[HourConstraints],
) -> list[dict]:
    """
    Solve the MILP and return a raw hourly plan (list of dicts).

    Raises OptimizationError if infeasible or solver error.
    Uses PuLP 3.x API (prob.add_variable + COIN_CMD).
    """
    hours_by_h = {hd.hour: hd for hd in hours_data}

    prob = pulp.LpProblem("GridWise_Energy_Optimization", pulp.LpMinimize)

    H = range(24)

    # -----------------------------------------------------------------------
    # Decision variables (using PuLP 3.x prob.add_variable API)
    # -----------------------------------------------------------------------
    grid = [prob.add_variable(f"grid_{h}", lowBound=0.0) for h in H]
    solar_used = [prob.add_variable(f"solar_used_{h}", lowBound=0.0) for h in H]
    charge = [prob.add_variable(f"charge_{h}", lowBound=0.0) for h in H]
    discharge = [prob.add_variable(f"discharge_{h}", lowBound=0.0) for h in H]
    battery_energy = [prob.add_variable(f"battery_energy_{h}", lowBound=0.0) for h in H]

    # Binary variable to prevent simultaneous charge and discharge
    # b[h] = 1 => charging allowed, b[h] = 0 => discharging allowed
    b = [prob.add_variable(f"b_{h}", cat="Binary") for h in H]

    # -----------------------------------------------------------------------
    # Objective: minimize total grid cost
    # -----------------------------------------------------------------------
    prob += pulp.lpSum(
        grid[h] * hours_by_h[h].tariff_bdt_per_kwh
        for h in H
    ), "minimize_grid_cost"

    # -----------------------------------------------------------------------
    # Constraints
    # -----------------------------------------------------------------------
    for h in H:
        hd = hours_by_h[h]
        con = constraints[h]

        # Energy balance: supply must equal demand
        # grid[h] + solar_used[h] + discharge[h] = demand[h] + charge[h]
        prob += (
            grid[h] + solar_used[h] + discharge[h] == hd.demand_kwh + charge[h],
            f"energy_balance_{h}",
        )

        # Solar upper bound (effective after directives)
        prob += solar_used[h] <= con.effective_solar, f"solar_ub_{h}"

        # Charge rate limit
        prob += charge[h] <= battery.max_charge_kwh_per_hour, f"charge_rate_{h}"

        # Discharge rate limit
        prob += discharge[h] <= battery.max_discharge_kwh_per_hour, f"discharge_rate_{h}"

        # Battery transition: E_after = E_before + charge - discharge
        if h == 0:
            e_before = battery.initial_energy_kwh
        else:
            e_before = battery_energy[h - 1]

        prob += (
            battery_energy[h] == e_before + charge[h] - discharge[h],
            f"battery_transition_{h}",
        )

        # Battery bounds: min <= E_after <= capacity
        prob += battery_energy[h] >= con.min_battery_energy, f"battery_min_{h}"
        prob += battery_energy[h] <= battery.capacity_kwh, f"battery_max_{h}"

        # Binary mutex: prevent simultaneous charge and discharge
        # charge[h] <= max_charge * b[h]
        # discharge[h] <= max_discharge * (1 - b[h])
        prob += charge[h] <= battery.max_charge_kwh_per_hour * b[h], f"mutex_charge_{h}"
        prob += discharge[h] <= battery.max_discharge_kwh_per_hour * (1 - b[h]), f"mutex_discharge_{h}"

        # Directive: no charge window
        if not con.charge_allowed:
            prob += charge[h] == 0.0, f"no_charge_{h}"

        # Directive: no discharge window
        if not con.discharge_allowed:
            prob += discharge[h] == 0.0, f"no_discharge_{h}"

        # Directive: max grid window
        if con.max_grid_kwh is not None:
            prob += grid[h] <= con.max_grid_kwh, f"max_grid_{h}"

    # End-of-day neutrality: battery must return to initial state
    prob += (
        battery_energy[23] == battery.initial_energy_kwh,
        "end_of_day_neutrality",
    )

    # -----------------------------------------------------------------------
    # Solve using bundled CBC solver
    # -----------------------------------------------------------------------
    logger.info("Starting CBC MILP solve...")

    # Use the available solver: prefer COIN_CMD (external CBC in PATH),
    # fall back to PULP_CBC_CMD (bundled CBC which ships with PuLP)
    available = pulp.listSolvers(onlyAvailable=True)
    if "COIN_CMD" in available:
        solver = pulp.COIN_CMD(msg=0)
    else:
        # PULP_CBC_CMD uses bundled CBC - suppress deprecation for production use
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            solver = pulp.PULP_CBC_CMD(msg=0)  # type: ignore[attr-defined]

    status = prob.solve(solver)
    solver_status = pulp.LpStatus[prob.status]

    logger.info("Solver status: %s (code %d)", solver_status, status)

    if prob.status != pulp.LpStatusOptimal:
        raise OptimizationError(
            f"MILP solver did not find optimal solution. "
            f"Status: {solver_status}. "
            "This may mean the constraints are infeasible given the scenario data and directives."
        )

    # -----------------------------------------------------------------------
    # Extract results
    # -----------------------------------------------------------------------
    plan = []
    for h in H:
        g = pulp.value(grid[h]) or 0.0
        s = pulp.value(solar_used[h]) or 0.0
        c = pulp.value(charge[h]) or 0.0
        d = pulp.value(discharge[h]) or 0.0
        e = pulp.value(battery_energy[h]) or 0.0

        plan.append({
            "hour": h,
            "grid_kwh": max(0.0, g),
            "solar_used_kwh": max(0.0, s),
            "charge_kwh": max(0.0, c),
            "discharge_kwh": max(0.0, d),
            "battery_energy_after_kwh": max(0.0, e),
        })

    return plan
