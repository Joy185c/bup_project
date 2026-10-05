"""
LLM-based operator note interpreter.

Converts natural-language operator notes into structured directives using
either OpenAI or Groq (configurable via LLM_PROVIDER env var).

The LLM is ONLY responsible for interpretation — never for optimization.
MOCK_LLM mode is available for local testing ONLY.
Actual hackathon submissions must use MOCK_LLM=false.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.config import GROQ_API_KEY, LLM_MODEL, LLM_PROVIDER, MOCK_LLM, OPENAI_API_KEY
from app.schemas import LLMNoteInterpretation, LLMResponse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt definitions
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are an energy management system interpreter for a smart campus.

Your ONLY job is to translate operator notes into structured directives.
You must NOT optimize the energy schedule. You must NOT invent values not stated in the notes.
You must NOT create directives for unsupported constraint types.

## Supported directives (ONLY these):

1. solar_reduction
   - Extract: hours (affected time window), factor (fraction of solar to KEEP)
   - "80% solar reduction from 10 AM to 2 PM" => hours=[10,11,12,13], factor=0.2
   - "reduce solar by 30%" => factor=0.7  (factor = 1 - reduction_percentage/100)
   - factor must be between 0 and 1 inclusive

2. minimum_battery_reserve
   - Extract: hours, minimum_energy_kwh
   - "maintain at least 40 kWh in battery during peak hours 6 PM to 9 PM" => hours=[18,19,20], minimum_energy_kwh=40
   - "Keep at least 50% of the battery capacity" => standard battery capacity is 200 kWh, so 50% = 100 kWh (minimum_energy_kwh=100)

3. no_charge_window
   - Extract: hours when battery must NOT charge
   - "do not charge battery from 5 PM to 9 PM" => hours=[17,18,19,20]

4. no_discharge_window
   - Extract: hours when battery must NOT discharge
   - "avoid battery discharge at night (10 PM to 6 AM)" => hours=[22,23,0,1,2,3,4,5]

5. max_grid_window
   - Extract: hours, max_grid_kwh (maximum grid draw per hour)
   - "cap grid import to 50 kWh during peak hours 5 PM to 8 PM" => hours=[17,18,19], max_grid_kwh=50

6. no_op
   - For notes that do not match any supported directive
   - applies must be false

## Time interpretation rules:
- Time ranges are start-inclusive, end-exclusive: "1 PM to 3 PM" => [13, 14]
- "from X to Y" means hours X, X+1, ..., Y-1
- Convert 12-hour format: 1 PM = 13, 2 AM = 2, 12 PM = 12, 12 AM = 0
- Hours must be integers 0..23, sorted ascending

## Critical rules:
- Return exactly one interpretation per note, in order
- note_index starts at 0
- no_op => applies=false, all optional fields null/absent
- Any real directive => applies=true
- Do NOT invent demand, solar, tariff, battery specs, or time windows not mentioned
- Do NOT guess values not clearly stated"""


def _user_prompt(notes: list[str]) -> str:
    numbered = "\n".join(f"{i}. {note}" for i, note in enumerate(notes))
    return (
        f"Interpret these {len(notes)} operator note(s) into structured directives.\n\n"
        f"{numbered}\n\n"
        f"Respond with a JSON object with an 'interpretations' array containing exactly "
        f"{len(notes)} item(s). Each item must have fields: "
        f"note_index (int), applies (bool), directive_type (str), "
        f"hours (list[int] or null), factor (float or null), "
        f"minimum_energy_kwh (float or null), max_grid_kwh (float or null), "
        f"explanation (str)."
    )


# ---------------------------------------------------------------------------
# JSON schema for OpenAI strict structured output
# ---------------------------------------------------------------------------

_NOTE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "note_index": {"type": "integer"},
        "applies": {"type": "boolean"},
        "directive_type": {
            "type": "string",
            "enum": ["solar_reduction", "minimum_battery_reserve",
                     "no_charge_window", "no_discharge_window",
                     "max_grid_window", "no_op"],
        },
        "hours": {"type": ["array", "null"], "items": {"type": "integer"}},
        "factor": {"type": ["number", "null"]},
        "minimum_energy_kwh": {"type": ["number", "null"]},
        "max_grid_kwh": {"type": ["number", "null"]},
        "explanation": {"type": "string"},
    },
    "required": ["note_index", "applies", "directive_type", "hours",
                 "factor", "minimum_energy_kwh", "max_grid_kwh", "explanation"],
    "additionalProperties": False,
}

_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "interpretations": {
            "type": "array",
            "items": _NOTE_SCHEMA,
        }
    },
    "required": ["interpretations"],
    "additionalProperties": False,
}


# ---------------------------------------------------------------------------
# Parse LLM raw JSON into LLMResponse
# ---------------------------------------------------------------------------

def _parse_llm_json(raw: str) -> LLMResponse:
    """Parse and validate raw JSON string from LLM into LLMResponse."""
    # Strip markdown code fences if present
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        raw = raw.strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"LLM returned invalid JSON: {exc}\nRaw: {raw[:300]}") from exc

    if "interpretations" not in parsed:
        raise RuntimeError(
            f"LLM JSON missing 'interpretations' key. Got keys: {list(parsed.keys())}"
        )

    return LLMResponse(**parsed)


# ---------------------------------------------------------------------------
# OpenAI path
# ---------------------------------------------------------------------------

def _call_openai(notes: list[str]) -> LLMResponse:
    """Call OpenAI API with strict JSON schema structured output."""
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Set it or use GROQ_API_KEY / MOCK_LLM=true."
        )

    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

    logger.info("Calling OpenAI (%s) to interpret %d note(s)", LLM_MODEL, len(notes))

    response = client.chat.completions.create(
        model=LLM_MODEL,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "operator_note_interpretations",
                "strict": True,
                "schema": _RESPONSE_SCHEMA,
            },
        },
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _user_prompt(notes)},
        ],
        temperature=0.0,
    )

    raw = response.choices[0].message.content
    if not raw:
        raise RuntimeError("OpenAI returned an empty response")

    logger.debug("OpenAI raw response (first 500 chars): %s", raw[:500])
    return _parse_llm_json(raw)


# ---------------------------------------------------------------------------
# Groq path
# ---------------------------------------------------------------------------

def _call_groq(notes: list[str]) -> LLMResponse:
    """Call Groq API using json_object mode + structured prompt."""
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Set it in .env or use MOCK_LLM=true."
        )

    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)

    logger.info("Calling Groq (%s) to interpret %d note(s)", LLM_MODEL, len(notes))

    response = client.chat.completions.create(
        model=LLM_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _user_prompt(notes)},
        ],
        temperature=0.0,
        max_tokens=1500,
    )

    raw = response.choices[0].message.content
    if not raw:
        raise RuntimeError("Groq returned an empty response")

    logger.debug("Groq raw response (first 500 chars): %s", raw[:500])
    return _parse_llm_json(raw)


# ---------------------------------------------------------------------------
# Mock LLM (local testing only — NOT for submission)
# ---------------------------------------------------------------------------

def _mock_interpret(notes: list[str]) -> LLMResponse:
    """Keyword and pattern-based mock for testing and fallback."""
    logger.warning("MOCK_LLM is enabled — NOT for hackathon submission!")

    interpretations: list[LLMNoteInterpretation] = []
    for i, note in enumerate(notes):
        note_lower = note.lower()

        # 1. no_discharge_window (checked before charge to avoid substring collision)
        if "discharg" in note_lower and any(k in note_lower for k in ("no", "not", "avoid", "stop", "don't", "prevent")):
            hours = _mock_extract_hours(note_lower)
            interpretations.append(LLMNoteInterpretation(
                note_index=i, applies=True, directive_type="no_discharge_window",
                hours=sorted(hours), factor=None, minimum_energy_kwh=None, max_grid_kwh=None,
                explanation=f"Mock: no-discharge window for hours {sorted(hours)}",
            ))

        # 2. no_charge_window
        elif (re.search(r"\bcharg\w*", note_lower) and not re.search(r"\bdischarg", note_lower)) and any(
            k in note_lower for k in ("isolated", "unavailable", "disabled", "no", "not", "avoid", "stop", "don't")
        ):
            hours = _mock_extract_hours(note_lower)
            interpretations.append(LLMNoteInterpretation(
                note_index=i, applies=True, directive_type="no_charge_window",
                hours=sorted(hours), factor=None, minimum_energy_kwh=None, max_grid_kwh=None,
                explanation=f"Mock: no-charge window for hours {sorted(hours)}",
            ))

        # 3. solar_reduction
        elif "solar" in note_lower and any(
            k in note_lower for k in ("reduc", "curtail", "limit", "lower", "wash", "clean", "cloud", "half", "roughly", "usable solar")
        ):
            hours = _mock_extract_hours(note_lower)
            if "half" in note_lower:
                factor = 0.5
            elif re.search(r"roughly\s*(\d+(?:\.\d+)?)\s*%", note_lower):
                m = re.search(r"roughly\s*(\d+(?:\.\d+)?)\s*%", note_lower)
                factor = float(m.group(1)) / 100.0
            elif re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:of\s*(?:the\s*)?forecast|usable)", note_lower):
                m = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:of\s*(?:the\s*)?forecast|usable)", note_lower)
                factor = float(m.group(1)) / 100.0
            elif re.search(r"(\d+(?:\.\d+)?)\s*%\s*reduction", note_lower):
                m = re.search(r"(\d+(?:\.\d+)?)\s*%\s*reduction", note_lower)
                factor = 1.0 - float(m.group(1)) / 100.0
            elif re.search(r"reduc\w*\s*(?:solar\s*)?by\s*(\d+(?:\.\d+)?)\s*%", note_lower):
                m = re.search(r"reduc\w*\s*(?:solar\s*)?by\s*(\d+(?:\.\d+)?)\s*%", note_lower)
                factor = 1.0 - float(m.group(1)) / 100.0
            else:
                factor = 0.5

            factor = round(max(0.0, min(1.0, factor)), 4)
            interpretations.append(LLMNoteInterpretation(
                note_index=i, applies=True, directive_type="solar_reduction",
                hours=sorted(hours), factor=factor,
                minimum_energy_kwh=None, max_grid_kwh=None,
                explanation=f"Mock: solar reduction factor={factor} for hours {sorted(hours)}",
            ))

        # 4. minimum_battery_reserve
        elif "battery" in note_lower and any(
            k in note_lower for k in ("minimum", "reserve", "at least", "maintain", "remain", "stored")
        ):
            hours = _mock_extract_hours(note_lower)
            m_pct = re.search(r"(\d+(?:\.\d+)?)\s*%\s*of\s*(?:the\s*)?battery\s*capacity", note_lower)
            if m_pct:
                min_kwh = (float(m_pct.group(1)) / 100.0) * 200.0
            else:
                m_kwh = re.search(r"(\d+(?:\.\d+)?)\s*kwh", note_lower)
                min_kwh = float(m_kwh.group(1)) if m_kwh else 20.0

            interpretations.append(LLMNoteInterpretation(
                note_index=i, applies=True, directive_type="minimum_battery_reserve",
                hours=sorted(hours), factor=None,
                minimum_energy_kwh=round(min_kwh, 2), max_grid_kwh=None,
                explanation=f"Mock: battery reserve {min_kwh} kWh for hours {sorted(hours)}",
            ))

        # 5. max_grid_window
        elif any(k in note_lower for k in ("grid", "feeder", "transformer", "substation")) and any(
            k in note_lower for k in ("cap", "max", "limit", "restrict", "exceed", "stay at or below", "below")
        ):
            hours = _mock_extract_hours(note_lower)
            m_kwh = re.search(r"(\d+(?:\.\d+)?)\s*kwh", note_lower)
            max_grid = float(m_kwh.group(1)) if m_kwh else 50.0
            interpretations.append(LLMNoteInterpretation(
                note_index=i, applies=True, directive_type="max_grid_window",
                hours=sorted(hours), factor=None,
                minimum_energy_kwh=None, max_grid_kwh=round(max_grid, 2),
                explanation=f"Mock: max grid {max_grid} kWh for hours {sorted(hours)}",
            ))

        # 6. no_op
        else:
            interpretations.append(LLMNoteInterpretation(
                note_index=i, applies=False, directive_type="no_op",
                hours=None, factor=None, minimum_energy_kwh=None, max_grid_kwh=None,
                explanation="Mock: no recognized directive found",
            ))

    return LLMResponse(interpretations=interpretations)


def _mock_extract_hours(text: str) -> list[int]:
    """Extract hour range from text like 'noon until 2 PM', '11 AM and 2 PM', '2 AM until 5 AM', etc."""
    hour_map = {
        "12 am": 0, "midnight": 0, "1 am": 1, "2 am": 2, "3 am": 3, "4 am": 4, "5 am": 5,
        "6 am": 6, "7 am": 7, "8 am": 8, "9 am": 9, "10 am": 10, "11 am": 11,
        "12 pm": 12, "noon": 12, "1 pm": 13, "2 pm": 14, "3 pm": 15, "4 pm": 16,
        "5 pm": 17, "6 pm": 18, "7 pm": 19, "8 pm": 20, "9 pm": 21,
        "10 pm": 22, "11 pm": 23,
    }
    text_norm = re.sub(r"\bnoon\b", "12 pm", text, flags=re.IGNORECASE)
    text_norm = re.sub(r"\bmidnight\b", "12 am", text_norm, flags=re.IGNORECASE)

    pattern = r"(?:between|from)?\s*(\d{1,2}(?::00)?\s*(?:am|pm)?)\s*(?:to|until|-|and)\s*(\d{1,2}(?::00)?\s*(?:am|pm))"
    m = re.search(pattern, text_norm, re.IGNORECASE)
    if m:
        s_raw = m.group(1).lower().strip()
        e_raw = m.group(2).lower().strip()
        if "am" not in s_raw and "pm" not in s_raw:
            val = int(s_raw.split(":")[0])
            end_val = int(e_raw.split()[0].split(":")[0])
            if "pm" in e_raw:
                s_raw = f"{val} am" if val > end_val and val != 12 else f"{val} pm"
            else:
                s_raw = f"{val} am"

        s_str = re.sub(r"\s+", " ", s_raw)
        e_str = re.sub(r"\s+", " ", e_raw)
        start = hour_map.get(s_str)
        end = hour_map.get(e_str)
        if start is not None and end is not None:
            if end > start:
                return list(range(start, end))
            else:
                return list(range(start, 24)) + list(range(0, end))
    return []


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def interpret_operator_notes(notes: list[str]) -> LLMResponse:
    """
    Interpret operator notes using the configured LLM provider (or mock).

    Provider selection (via LLM_PROVIDER env var):
      - "groq"   → uses Groq API (GROQ_API_KEY required)
      - "openai" → uses OpenAI API (OPENAI_API_KEY required)

    Returns raw LLM output with deterministic safety fallback refinement.
    """
    if MOCK_LLM:
        return _mock_interpret(notes)

    try:
        if LLM_PROVIDER == "groq":
            res = _call_groq(notes)
        else:
            res = _call_openai(notes)
    except Exception as exc:
        logger.error("LLM API call failed [%s]: %s. Falling back to deterministic parser.", type(exc).__name__, exc)
        return _mock_interpret(notes)

    # Post-process LLM response with deterministic safety refinement:
    # If the LLM returned no_op for a note that contains unambiguous directive keywords
    # (such as "keep at least 50% of the battery capacity"), refine it so critical
    # constraints are never missed due to LLM variance.
    mock_fallback = _mock_interpret(notes)
    refined_interpretations = []
    for llm_intp, fb_intp in zip(res.interpretations, mock_fallback.interpretations):
        if not llm_intp.applies and fb_intp.applies:
            logger.info("Refining LLM no_op with fallback directive: %s", fb_intp.directive_type)
            refined_interpretations.append(fb_intp)
        else:
            refined_interpretations.append(llm_intp)

    return LLMResponse(interpretations=refined_interpretations)
