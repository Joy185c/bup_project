"""
Tests for guardrails.py

All guardrail validation logic is tested here without LLM calls.
"""
import pytest

from app.guardrails import GuardrailError, validate_llm_output
from app.schemas import BatterySpec, LLMNoteInterpretation, LLMResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def make_interp(**kwargs) -> LLMNoteInterpretation:
    defaults = dict(
        note_index=0,
        applies=True,
        directive_type="no_op",
        hours=None,
        factor=None,
        minimum_energy_kwh=None,
        max_grid_kwh=None,
        explanation="test",
    )
    defaults.update(kwargs)
    # fix applies for no_op
    if defaults["directive_type"] == "no_op":
        defaults["applies"] = False
    return LLMNoteInterpretation(**defaults)


def make_llm_response(interps: list[LLMNoteInterpretation]) -> LLMResponse:
    return LLMResponse(interpretations=interps)


# ---------------------------------------------------------------------------
# Valid cases
# ---------------------------------------------------------------------------

class TestValidCases:
    def test_valid_solar_reduction(self):
        battery = make_battery()
        interp = make_interp(
            note_index=0,
            applies=True,
            directive_type="solar_reduction",
            hours=[10, 11, 12],
            factor=0.5,
            explanation="50% solar reduction from 10am-1pm",
        )
        result = validate_llm_output(make_llm_response([interp]), 1, battery)
        assert len(result) == 1
        assert result[0].directive_type == "solar_reduction"

    def test_valid_minimum_battery_reserve(self):
        battery = make_battery()
        interp = make_interp(
            note_index=0,
            applies=True,
            directive_type="minimum_battery_reserve",
            hours=[18, 19, 20],
            minimum_energy_kwh=50.0,
            explanation="50 kWh reserve during peak",
        )
        result = validate_llm_output(make_llm_response([interp]), 1, battery)
        assert result[0].directive_type == "minimum_battery_reserve"

    def test_valid_no_charge_window(self):
        battery = make_battery()
        interp = make_interp(
            note_index=0,
            applies=True,
            directive_type="no_charge_window",
            hours=[17, 18, 19, 20],
            explanation="No charge during peak tariff",
        )
        result = validate_llm_output(make_llm_response([interp]), 1, battery)
        assert result[0].directive_type == "no_charge_window"

    def test_valid_no_discharge_window(self):
        battery = make_battery()
        interp = make_interp(
            note_index=0,
            applies=True,
            directive_type="no_discharge_window",
            hours=[0, 1, 2, 3],
            explanation="No discharge overnight",
        )
        result = validate_llm_output(make_llm_response([interp]), 1, battery)
        assert result[0].directive_type == "no_discharge_window"

    def test_valid_max_grid_window(self):
        battery = make_battery()
        interp = make_interp(
            note_index=0,
            applies=True,
            directive_type="max_grid_window",
            hours=[17, 18, 19],
            max_grid_kwh=80.0,
            explanation="Cap grid at 80 kWh",
        )
        result = validate_llm_output(make_llm_response([interp]), 1, battery)
        assert result[0].directive_type == "max_grid_window"

    def test_valid_no_op(self):
        battery = make_battery()
        interp = make_interp(
            note_index=0,
            applies=False,
            directive_type="no_op",
            explanation="No applicable directive",
        )
        result = validate_llm_output(make_llm_response([interp]), 1, battery)
        assert result[0].directive_type == "no_op"

    def test_valid_multiple_notes(self):
        battery = make_battery()
        interps = [
            make_interp(note_index=0, applies=True, directive_type="solar_reduction",
                        hours=[10, 11], factor=0.7, explanation="solar reduction"),
            make_interp(note_index=1, applies=False, directive_type="no_op",
                        explanation="no op"),
            make_interp(note_index=2, applies=True, directive_type="no_charge_window",
                        hours=[17, 18], explanation="no charge"),
        ]
        result = validate_llm_output(make_llm_response(interps), 3, battery)
        assert len(result) == 3


# ---------------------------------------------------------------------------
# Invalid factor
# ---------------------------------------------------------------------------

class TestInvalidFactor:
    def test_factor_above_1(self):
        battery = make_battery()
        interp = make_interp(
            note_index=0, applies=True,
            directive_type="solar_reduction",
            hours=[10, 11], factor=1.5,
            explanation="bad factor",
        )
        with pytest.raises(GuardrailError, match="factor"):
            validate_llm_output(make_llm_response([interp]), 1, battery)

    def test_factor_negative(self):
        battery = make_battery()
        interp = make_interp(
            note_index=0, applies=True,
            directive_type="solar_reduction",
            hours=[10, 11], factor=-0.1,
            explanation="bad factor",
        )
        with pytest.raises(GuardrailError, match="factor"):
            validate_llm_output(make_llm_response([interp]), 1, battery)

    def test_factor_missing_for_solar_reduction(self):
        battery = make_battery()
        interp = make_interp(
            note_index=0, applies=True,
            directive_type="solar_reduction",
            hours=[10, 11], factor=None,
            explanation="missing factor",
        )
        with pytest.raises(GuardrailError, match="factor"):
            validate_llm_output(make_llm_response([interp]), 1, battery)


# ---------------------------------------------------------------------------
# Invalid hours
# ---------------------------------------------------------------------------

class TestInvalidHours:
    def test_hour_out_of_range_high(self):
        battery = make_battery()
        interp = make_interp(
            note_index=0, applies=True,
            directive_type="no_charge_window",
            hours=[24], explanation="bad hour",
        )
        with pytest.raises(GuardrailError, match="out of range"):
            validate_llm_output(make_llm_response([interp]), 1, battery)

    def test_hour_out_of_range_negative(self):
        battery = make_battery()
        interp = make_interp(
            note_index=0, applies=True,
            directive_type="no_charge_window",
            hours=[-1], explanation="bad hour",
        )
        with pytest.raises(GuardrailError, match="out of range"):
            validate_llm_output(make_llm_response([interp]), 1, battery)

    def test_hours_not_sorted(self):
        battery = make_battery()
        interp = make_interp(
            note_index=0, applies=True,
            directive_type="no_charge_window",
            hours=[12, 10, 11], explanation="unsorted",
        )
        with pytest.raises(GuardrailError, match="sorted"):
            validate_llm_output(make_llm_response([interp]), 1, battery)

    def test_hours_duplicate(self):
        battery = make_battery()
        interp = make_interp(
            note_index=0, applies=True,
            directive_type="no_charge_window",
            hours=[10, 10, 11], explanation="duplicate",
        )
        with pytest.raises(GuardrailError, match="unique"):
            validate_llm_output(make_llm_response([interp]), 1, battery)

    def test_hours_empty(self):
        battery = make_battery()
        interp = make_interp(
            note_index=0, applies=True,
            directive_type="no_charge_window",
            hours=[], explanation="empty hours",
        )
        with pytest.raises(GuardrailError, match="empty"):
            validate_llm_output(make_llm_response([interp]), 1, battery)

    def test_hours_missing_for_non_no_op(self):
        battery = make_battery()
        interp = make_interp(
            note_index=0, applies=True,
            directive_type="no_charge_window",
            hours=None, explanation="missing hours",
        )
        with pytest.raises(GuardrailError, match="requires hours"):
            validate_llm_output(make_llm_response([interp]), 1, battery)


# ---------------------------------------------------------------------------
# Duplicate note index
# ---------------------------------------------------------------------------

class TestDuplicateNoteIndex:
    def test_duplicate_note_index(self):
        battery = make_battery()
        interps = [
            make_interp(note_index=0, applies=False, directive_type="no_op",
                        explanation="dup1"),
            make_interp(note_index=0, applies=False, directive_type="no_op",
                        explanation="dup2"),
        ]
        with pytest.raises(GuardrailError, match="Duplicate"):
            validate_llm_output(make_llm_response(interps), 2, battery)


# ---------------------------------------------------------------------------
# Missing interpretation
# ---------------------------------------------------------------------------

class TestMissingInterpretation:
    def test_fewer_interpretations_than_notes(self):
        battery = make_battery()
        interps = [
            make_interp(note_index=0, applies=False, directive_type="no_op",
                        explanation="only one"),
        ]
        with pytest.raises(GuardrailError, match="Expected exactly 2"):
            validate_llm_output(make_llm_response(interps), 2, battery)

    def test_more_interpretations_than_notes(self):
        battery = make_battery()
        interps = [
            make_interp(note_index=0, applies=False, directive_type="no_op",
                        explanation="first"),
            make_interp(note_index=1, applies=False, directive_type="no_op",
                        explanation="extra"),
        ]
        with pytest.raises(GuardrailError, match="Expected exactly 1"):
            validate_llm_output(make_llm_response(interps), 1, battery)


# ---------------------------------------------------------------------------
# Invalid directive type
# ---------------------------------------------------------------------------

class TestInvalidDirective:
    def test_unsupported_directive_type(self):
        battery = make_battery()
        interp = make_interp(
            note_index=0, applies=True,
            directive_type="demand_response",  # not supported
            hours=[10], explanation="unsupported",
        )
        with pytest.raises(GuardrailError, match="not allowed"):
            validate_llm_output(make_llm_response([interp]), 1, battery)


# ---------------------------------------------------------------------------
# Invalid no_op semantics
# ---------------------------------------------------------------------------

class TestInvalidNoOpSemantics:
    def test_no_op_with_applies_true(self):
        battery = make_battery()
        interp = LLMNoteInterpretation(
            note_index=0,
            applies=True,  # wrong!
            directive_type="no_op",
            hours=None,
            factor=None,
            minimum_energy_kwh=None,
            max_grid_kwh=None,
            explanation="no_op but applies=true",
        )
        with pytest.raises(GuardrailError, match="applies=false"):
            validate_llm_output(make_llm_response([interp]), 1, battery)

    def test_non_no_op_with_applies_false(self):
        battery = make_battery()
        interp = LLMNoteInterpretation(
            note_index=0,
            applies=False,  # wrong!
            directive_type="no_charge_window",
            hours=[10, 11],
            factor=None,
            minimum_energy_kwh=None,
            max_grid_kwh=None,
            explanation="non-no_op but applies=false",
        )
        with pytest.raises(GuardrailError, match="applies=true"):
            validate_llm_output(make_llm_response([interp]), 1, battery)

    def test_no_op_with_hours_set(self):
        battery = make_battery()
        interp = LLMNoteInterpretation(
            note_index=0,
            applies=False,
            directive_type="no_op",
            hours=[10, 11],  # should be None
            factor=None,
            minimum_energy_kwh=None,
            max_grid_kwh=None,
            explanation="no_op with hours",
        )
        with pytest.raises(GuardrailError, match="hours"):
            validate_llm_output(make_llm_response([interp]), 1, battery)


# ---------------------------------------------------------------------------
# Invalid reserve
# ---------------------------------------------------------------------------

class TestInvalidReserve:
    def test_reserve_exceeds_capacity(self):
        battery = make_battery(capacity=100.0)
        interp = make_interp(
            note_index=0, applies=True,
            directive_type="minimum_battery_reserve",
            hours=[18], minimum_energy_kwh=150.0,  # exceeds capacity
            explanation="reserve too high",
        )
        with pytest.raises(GuardrailError, match="capacity"):
            validate_llm_output(make_llm_response([interp]), 1, battery)

    def test_reserve_negative(self):
        battery = make_battery()
        interp = make_interp(
            note_index=0, applies=True,
            directive_type="minimum_battery_reserve",
            hours=[18], minimum_energy_kwh=-10.0,
            explanation="negative reserve",
        )
        with pytest.raises(GuardrailError, match="non-negative"):
            validate_llm_output(make_llm_response([interp]), 1, battery)

    def test_reserve_missing(self):
        battery = make_battery()
        interp = make_interp(
            note_index=0, applies=True,
            directive_type="minimum_battery_reserve",
            hours=[18], minimum_energy_kwh=None,
            explanation="missing reserve",
        )
        with pytest.raises(GuardrailError, match="minimum_energy_kwh"):
            validate_llm_output(make_llm_response([interp]), 1, battery)

    def test_max_grid_negative(self):
        battery = make_battery()
        interp = make_interp(
            note_index=0, applies=True,
            directive_type="max_grid_window",
            hours=[17], max_grid_kwh=-5.0,
            explanation="negative grid cap",
        )
        with pytest.raises(GuardrailError, match="non-negative"):
            validate_llm_output(make_llm_response([interp]), 1, battery)
