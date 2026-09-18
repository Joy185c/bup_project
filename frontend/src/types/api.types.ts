// Exact API types derived from app/schemas.py

export interface HourData {
  hour: number; // 0–23
  demand_kwh: number;
  solar_kwh: number;
  tariff_bdt_per_kwh: number;
}

export interface BatterySpec {
  capacity_kwh: number;
  initial_energy_kwh: number;
  minimum_energy_kwh: number;
  max_charge_kwh_per_hour: number;
  max_discharge_kwh_per_hour: number;
}

export interface OptimizeRequest {
  scenario_id: string;
  operator_notes: string[]; // 1–3 items
  hours: HourData[];        // exactly 24
  battery: BatterySpec;
}

// Response types
export interface StructuredAdjustment {
  hours: number[] | null;
  factor: number | null;
  minimum_energy_kwh: number | null;
  max_grid_kwh: number | null;
}

export interface DirectiveInterpretation {
  note_index: number;
  applies: boolean;
  directive_type:
    | 'solar_reduction'
    | 'minimum_battery_reserve'
    | 'no_charge_window'
    | 'no_discharge_window'
    | 'max_grid_window'
    | 'no_op';
  structured_adjustment: StructuredAdjustment | null;
  explanation: string;
}

export type BatteryAction = 'charge' | 'discharge' | 'idle';

export interface HourlyPlan {
  hour: number;
  grid_kwh: number;
  solar_used_kwh: number;
  battery_action: BatteryAction;
  battery_kwh: number;
  battery_energy_after_kwh: number;
}

export interface OptimizeResponse {
  scenario_id: string;
  directive_interpretation: DirectiveInterpretation[];
  hourly_plan: HourlyPlan[];
  total_grid_kwh: number;
  total_cost_bdt: number;
  peak_grid_kwh: number;
  plan_summary: string;
}

// API error shape
export interface ApiError {
  error: string;
  message: string;
  details?: unknown[];
}

// App-level history entry
export interface HistoryEntry {
  id: string;
  timestamp: string;
  scenario_id: string;
  operator_notes: string[];
  result: OptimizeResponse;
  request: OptimizeRequest;
}
