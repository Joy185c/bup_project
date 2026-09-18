"""
Tests for optimizer.py and validator.py

Tests the MILP optimization, directive application, and independent plan validation.
All tests bypass the LLM and use validated directives directly.
"""
import pytest

from app.optimizer import (
    HourConstraints,
    OptimizationError,
    apply_directives,
    solve_milp,
)
from app.schemas import (
    BatterySpec,
    HourData,
    MaxGridWindowDirective,
    MinimumBatteryReserveDirective,
    NoChargeWindowDirective,
    NoDischargeWindowDirective,
    NoOpDirective,
    SolarReductionDirective,
)
from app.validator import PlanValidationError, validate_plan

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

TOL = 1e-4


def make_battery(
    capacity=200.0,
    initial=100.0,
    minimum=20.0,
    max_charge=50.0,
    max_discharge=50.0,
) -> BatterySpec:
    return BatterySpec(
        capacity_kwh=capacity,
        initial_energy_kwh=initial,
        minimum_energy_kwh=minimum,
        max_charge_kwh_per_hour=max_charge,
        max_discharge_kwh_per_hour=max_discharge,
    )


def make_hours(
    demand=50.0,
    solar=0.0,
    tariff=10.0,
) -> list[HourData]:
    """Make 24 identical hours."""
    return [
        HourData(hour=h, demand_kwh=demand, solar_kwh=solar, tariff_bdt_per_kwh=tariff)
        for h in range(24)
    ]


def make_hours_varying() -> list[HourData]:
    """24 hours with varying demand, solar, tariff."""
    hours = []
    for h in range(24):
        solar = max(0, 40 - abs(h - 12) * 5)  # peaks at noon
        demand = 60 + (20 if 8 <= h <= 20 else 0)  # higher demand daytime
        tariff = 14.0 if 17 <= h <= 20 else 8.0
        hours.append(HourData(hour=h, demand_kwh=demand, solar_kwh=solar, tariff_bdt_per_kwh=tariff))
    return hours


def solve_no_directives(hours, battery) -> list[dict]:
    constraints = apply_directives(hours, battery, [NoOpDirective()])
    return solve_milp(hours, battery, constraints)


def get_hour(plan: list[dict], h: int) -> dict:
    return next(e for e in plan if e["hour"] == h)


# ---------------------------------------------------------------------------
# Basic energy balance
# ---------------------------------------------------------------------------

class TestEnergyBalance:
    def test_energy_balance_all_hours(self):
        hours = make_hours(demand=50.0, solar=0.0, tariff=10.0)
        battery = make_battery()
        plan = solve_no_directives(hours, battery)

        for entry in plan:
            h = entry["hour"]
            hd = hours[h]
            supply = entry["grid_kwh"] + entry["solar_used_kwh"] + entry["discharge_kwh"]
            demand_plus_charge = hd.demand_kwh + entry["charge_kwh"]
            assert abs(supply - demand_plus_charge) < TOL, (
                f"Hour {h}: balance error {abs(supply - demand_plus_charge)}"
            )

    def test_solar_fully_used_when_available(self):
        """With zero tariff, solar should be used first to reduce grid."""
        hours = make_hours(demand=30.0, solar=50.0, tariff=10.0)
        battery = make_battery()
        plan = solve_no_directives(hours, battery)

        for entry in plan:
            # Solar is more than enough for demand, so grid should be near 0
            assert entry["solar_used_kwh"] <= 50.0 + TOL
            assert entry["grid_kwh"] >= -TOL


# ---------------------------------------------------------------------------
# Solar
# ---------------------------------------------------------------------------

class TestSolar:
    def test_solar_never_exceeds_effective(self):
        hours = make_hours_varying()
        battery = make_battery()
        constraints = apply_directives(hours, battery, [
            SolarReductionDirective(hours=[11, 12, 13], factor=0.5)
        ])
        plan = solve_milp(hours, battery, constraints)

        for entry in plan:
            h = entry["hour"]
            assert entry["solar_used_kwh"] <= constraints[h].effective_solar + TOL

    def test_solar_reduction_applied(self):
        """After solar reduction, solar_used cannot exceed reduced amount."""
        hours = make_hours(demand=50.0, solar=100.0, tariff=10.0)
        battery = make_battery()
        constraints = apply_directives(hours, battery, [
            SolarReductionDirective(hours=list(range(24)), factor=0.3)
        ])
        plan = solve_milp(hours, battery, constraints)

        for entry in plan:
            # Effective solar = 100 * 0.3 = 30 kWh
            assert entry["solar_used_kwh"] <= 30.0 + TOL


# ---------------------------------------------------------------------------
# Battery charging
# ---------------------------------------------------------------------------

class TestBatteryCharging:
    def test_battery_charges_when_cheap(self):
        """Battery should charge during cheap hours."""
        hours = []
        for h in range(24):
            tariff = 2.0 if h < 8 else 20.0  # very cheap at night
            solar = 0.0
            hours.append(HourData(hour=h, demand_kwh=20.0, solar_kwh=solar, tariff_bdt_per_kwh=tariff))

        battery = make_battery(capacity=200.0, initial=50.0, minimum=0.0, max_charge=50.0, max_discharge=50.0)
        plan = solve_no_directives(hours, battery)

        # Should charge at some cheap hours
        charge_hours = [e for e in plan if e["charge_kwh"] > TOL]
        assert len(charge_hours) > 0

    def test_charge_rate_not_exceeded(self):
        hours = make_hours_varying()
        battery = make_battery(max_charge=30.0)
        plan = solve_no_directives(hours, battery)

        for entry in plan:
            assert entry["charge_kwh"] <= battery.max_charge_kwh_per_hour + TOL


# ---------------------------------------------------------------------------
# Battery discharging
# ---------------------------------------------------------------------------

class TestBatteryDischarging:
    def test_discharge_rate_not_exceeded(self):
        hours = make_hours_varying()
        battery = make_battery(max_discharge=25.0)
        plan = solve_no_directives(hours, battery)

        for entry in plan:
            assert entry["discharge_kwh"] <= battery.max_discharge_kwh_per_hour + TOL

    def test_no_simultaneous_charge_discharge(self):
        hours = make_hours_varying()
        battery = make_battery()
        plan = solve_no_directives(hours, battery)

        for entry in plan:
            # Cannot have significant charge AND discharge simultaneously
            assert not (entry["charge_kwh"] > TOL and entry["discharge_kwh"] > TOL), (
                f"Hour {entry['hour']}: simultaneous charge={entry['charge_kwh']:.4f} "
                f"discharge={entry['discharge_kwh']:.4f}"
            )


# ---------------------------------------------------------------------------
# Battery capacity / minimum
# ---------------------------------------------------------------------------

class TestBatteryBounds:
    def test_battery_never_exceeds_capacity(self):
        hours = make_hours_varying()
        battery = make_battery(capacity=150.0, initial=100.0)
        plan = solve_no_directives(hours, battery)

        for entry in plan:
            assert entry["battery_energy_after_kwh"] <= battery.capacity_kwh + TOL

    def test_battery_minimum_respected(self):
        hours = make_hours_varying()
        battery = make_battery(minimum=40.0, initial=80.0)
        constraints = apply_directives(hours, battery, [NoOpDirective()])
        plan = solve_milp(hours, battery, constraints)

        for entry in plan:
            assert entry["battery_energy_after_kwh"] >= battery.minimum_energy_kwh - TOL

    def test_battery_minimum_reserve_directive(self):
        hours = make_hours_varying()
        battery = make_battery(minimum=20.0, initial=100.0)
        reserve_hours = [18, 19, 20]
        constraints = apply_directives(hours, battery, [
            MinimumBatteryReserveDirective(hours=reserve_hours, minimum_energy_kwh=80.0)
        ])
        plan = solve_milp(hours, battery, constraints)

        for h in reserve_hours:
            entry = get_hour(plan, h)
            assert entry["battery_energy_after_kwh"] >= 80.0 - TOL


# ---------------------------------------------------------------------------
# No-charge window
# ---------------------------------------------------------------------------

class TestNoChargeWindow:
    def test_no_charge_window_respected(self):
        hours = make_hours_varying()
        battery = make_battery()
        no_charge_hours = [17, 18, 19, 20]
        constraints = apply_directives(hours, battery, [
            NoChargeWindowDirective(hours=no_charge_hours)
        ])
        plan = solve_milp(hours, battery, constraints)

        for h in no_charge_hours:
            entry = get_hour(plan, h)
            assert entry["charge_kwh"] < TOL, (
                f"Hour {h}: charge={entry['charge_kwh']:.6f} but no_charge_window active"
            )


# ---------------------------------------------------------------------------
# No-discharge window
# ---------------------------------------------------------------------------

class TestNoDischargeWindow:
    def test_no_discharge_window_respected(self):
        hours = make_hours_varying()
        battery = make_battery()
        no_discharge_hours = [0, 1, 2, 3, 4, 5]
        constraints = apply_directives(hours, battery, [
            NoDischargeWindowDirective(hours=no_discharge_hours)
        ])
        plan = solve_milp(hours, battery, constraints)

        for h in no_discharge_hours:
            entry = get_hour(plan, h)
            assert entry["discharge_kwh"] < TOL, (
                f"Hour {h}: discharge={entry['discharge_kwh']:.6f} but no_discharge_window active"
            )


# ---------------------------------------------------------------------------
# Grid cap
# ---------------------------------------------------------------------------

class TestGridCap:
    def test_max_grid_window_respected(self):
        hours = make_hours(demand=100.0, solar=0.0, tariff=10.0)
        battery = make_battery(capacity=300.0, initial=200.0, minimum=0.0,
                               max_charge=50.0, max_discharge=50.0)
        grid_cap_hours = [10, 11, 12]
        constraints = apply_directives(hours, battery, [
            MaxGridWindowDirective(hours=grid_cap_hours, max_grid_kwh=70.0)
        ])
        plan = solve_milp(hours, battery, constraints)

        for h in grid_cap_hours:
            entry = get_hour(plan, h)
            assert entry["grid_kwh"] <= 70.0 + TOL, (
                f"Hour {h}: grid={entry['grid_kwh']:.4f} exceeds cap 70 kWh"
            )


# ---------------------------------------------------------------------------
# End-of-day neutrality
# ---------------------------------------------------------------------------

class TestEndOfDayNeutrality:
    def test_final_battery_equals_initial(self):
        hours = make_hours_varying()
        battery = make_battery(initial=100.0)
        plan = solve_no_directives(hours, battery)

        final = get_hour(plan, 23)["battery_energy_after_kwh"]
        assert abs(final - battery.initial_energy_kwh) < TOL, (
            f"End-of-day: final={final:.4f}, initial={battery.initial_energy_kwh:.4f}"
        )

    def test_neutrality_with_varying_directives(self):
        hours = make_hours_varying()
        battery = make_battery(initial=80.0)
        constraints = apply_directives(hours, battery, [
            NoChargeWindowDirective(hours=[17, 18, 19, 20]),
            SolarReductionDirective(hours=[11, 12, 13], factor=0.5),
        ])
        plan = solve_milp(hours, battery, constraints)

        final = get_hour(plan, 23)["battery_energy_after_kwh"]
        assert abs(final - battery.initial_energy_kwh) < TOL


# ---------------------------------------------------------------------------
# Independent validator tests
# ---------------------------------------------------------------------------

class TestValidator:
    def test_validator_passes_valid_plan(self):
        hours = make_hours_varying()
        battery = make_battery()
        constraints = apply_directives(hours, battery, [NoOpDirective()])
        plan = solve_milp(hours, battery, constraints)
        # Should not raise
        validate_plan(hours, battery, constraints, plan)

    def test_validator_rejects_wrong_length(self):
        hours = make_hours_varying()
        battery = make_battery()
        constraints = apply_directives(hours, battery, [NoOpDirective()])
        plan = solve_milp(hours, battery, constraints)
        with pytest.raises(PlanValidationError, match="24"):
            validate_plan(hours, battery, constraints, plan[:20])

    def test_validator_rejects_energy_balance_violation(self):
        hours = make_hours_varying()
        battery = make_battery()
        constraints = apply_directives(hours, battery, [NoOpDirective()])
        plan = solve_milp(hours, battery, constraints)
        # Artificially corrupt a plan entry
        corrupted = [dict(e) for e in plan]
        corrupted[5]["grid_kwh"] += 100.0  # break energy balance at hour 5
        with pytest.raises(PlanValidationError):
            validate_plan(hours, battery, constraints, corrupted)

    def test_validator_rejects_capacity_violation(self):
        hours = make_hours_varying()
        battery = make_battery(capacity=200.0)
        constraints = apply_directives(hours, battery, [NoOpDirective()])
        plan = solve_milp(hours, battery, constraints)
        # Force battery over capacity by adjusting both charge and battery energy
        # to avoid triggering transition check first
        corrupted = [dict(e) for e in plan]
        # Set battery energy to 250 and adjust charge accordingly so transition passes
        prev_battery = plan[9]["battery_energy_after_kwh"]
        orig_charge = corrupted[10]["charge_kwh"]
        orig_discharge = corrupted[10]["discharge_kwh"]
        corrupted[10]["battery_energy_after_kwh"] = 250.0
        # Adjust charge to satisfy transition: 250 = prev + charge - discharge
        corrupted[10]["charge_kwh"] = 250.0 - prev_battery + orig_discharge
        with pytest.raises(PlanValidationError):
            validate_plan(hours, battery, constraints, corrupted)

    def test_validator_rejects_neutrality_violation(self):
        hours = make_hours_varying()
        battery = make_battery(initial=100.0)
        constraints = apply_directives(hours, battery, [NoOpDirective()])
        plan = solve_milp(hours, battery, constraints)
        # Change final battery energy (adjust charge to keep transition valid,
        # so the neutrality check fires)
        corrupted = [dict(e) for e in plan]
        prev_battery = plan[22]["battery_energy_after_kwh"]
        orig_discharge = corrupted[23]["discharge_kwh"]
        corrupted[23]["battery_energy_after_kwh"] = 150.0
        # Adjust charge: 150 = prev + charge - discharge => charge = 150 - prev + discharge
        corrupted[23]["charge_kwh"] = 150.0 - prev_battery + orig_discharge
        with pytest.raises(PlanValidationError):
            validate_plan(hours, battery, constraints, corrupted)


# ---------------------------------------------------------------------------
# Directive application
# ---------------------------------------------------------------------------

class TestDirectiveApplication:
    def test_solar_reduction_applied_correctly(self):
        hours = make_hours(solar=100.0)
        battery = make_battery()
        constraints = apply_directives(hours, battery, [
            SolarReductionDirective(hours=[5, 6, 7], factor=0.2)
        ])
        for h in [5, 6, 7]:
            assert abs(constraints[h].effective_solar - 20.0) < TOL
        for h in [0, 1, 2, 3, 4, 8]:
            assert abs(constraints[h].effective_solar - 100.0) < TOL

    def test_overlapping_solar_reductions_use_most_restrictive(self):
        hours = make_hours(solar=100.0)
        battery = make_battery()
        constraints = apply_directives(hours, battery, [
            SolarReductionDirective(hours=[10, 11], factor=0.5),
            SolarReductionDirective(hours=[10, 12], factor=0.3),
        ])
        # Hour 10 has both, most restrictive is 0.3
        assert abs(constraints[10].effective_solar - 30.0) < TOL
        # Hour 11 only has 0.5
        assert abs(constraints[11].effective_solar - 50.0) < TOL
        # Hour 12 only has 0.3
        assert abs(constraints[12].effective_solar - 30.0) < TOL
