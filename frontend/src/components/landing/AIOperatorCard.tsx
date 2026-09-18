import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, ShieldCheck, ArrowRight, CheckCircle2, Clock, BatteryCharging, Sun, ZapOff } from 'lucide-react';

interface ScenarioDemo {
  id: string;
  tabLabel: string;
  note: string;
  directiveType: string;
  timeWindow: string;
  hoursArray: string;
  parameterLabel: string;
  parameterValue: string;
  guardrailStatus: string;
  explanation: string;
  icon: React.ElementType;
}

const sampleNotes: ScenarioDemo[] = [
  {
    id: 'battery-reserve',
    tabLabel: 'Battery Reserve',
    note: 'Keep at least 50% of the battery capacity stored from 1 PM to 5 PM.',
    directiveType: 'minimum_battery_reserve',
    timeWindow: '13:00 – 17:00 (Hours 13, 14, 15, 16)',
    hoursArray: '[13, 14, 15, 16]',
    parameterLabel: 'Minimum Energy',
    parameterValue: '100.0 kWh (50% of 200 kWh battery capacity)',
    guardrailStatus: 'Passed all 13 checks (bounds, monotonicity, capacity ceiling)',
    explanation: '50% of 200 kWh battery capacity equals 100 kWh reserve requirement across the specified afternoon peak window.',
    icon: BatteryCharging,
  },
  {
    id: 'solar-reduction',
    tabLabel: 'Solar Curtailment',
    note: 'Reduce solar panel output by 30% from 11 AM to 2 PM due to scheduled maintenance.',
    directiveType: 'solar_reduction',
    timeWindow: '11:00 – 14:00 (Hours 11, 12, 13)',
    hoursArray: '[11, 12, 13]',
    parameterLabel: 'Effective Solar Factor',
    parameterValue: '0.70 (keeps 70% of baseline generation)',
    guardrailStatus: 'Passed all 13 checks (factor in [0, 1], finite float, hour bounds)',
    explanation: 'A 30% reduction keeps 70% available solar (factor=0.70) during start-inclusive, end-exclusive hours [11, 12, 13].',
    icon: Sun,
  },
  {
    id: 'no-charge',
    tabLabel: 'Peak Tariff Avoidance',
    note: 'Do not charge the battery from 5 PM to 9 PM as grid tariffs are at their peak.',
    directiveType: 'no_charge_window',
    timeWindow: '17:00 – 21:00 (Hours 17, 18, 19, 20)',
    hoursArray: '[17, 18, 19, 20]',
    parameterLabel: 'Charge Ceiling',
    parameterValue: '0.0 kWh/hour',
    guardrailStatus: 'Passed all 13 checks (null field purity, valid hour window)',
    explanation: 'Forces charge[h] = 0 across peak grid tariff hours to prevent expensive arbitrage cycles.',
    icon: ZapOff,
  }
];

export function AIOperatorCard() {
  const [selectedScenario, setSelectedScenario] = useState<ScenarioDemo>(sampleNotes[0]);
  const IconComponent = selectedScenario.icon;

  return (
    <div className="w-full rounded-2xl bg-white border border-slate-200/90 shadow-lg p-6 sm:p-8 relative overflow-hidden">
      {/* Demonstration disclaimer badge */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 mb-6 border-b border-slate-100">
        <div>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-green-50 px-3 py-1 text-xs font-semibold text-green-700 border border-green-200">
            <Sparkles className="h-3.5 w-3.5 text-green-600" />
            Live AI Directive Pipeline
          </span>
          <h3 className="text-lg font-bold text-slate-900 mt-1">Natural-Language Operator Parsing</h3>
        </div>
        <span className="text-[11px] text-slate-400 font-medium">
          Demonstration Schema • Strict JSON Mode
        </span>
      </div>

      {/* Scenario Selector Tabs */}
      <div className="flex flex-wrap gap-2 mb-6">
        {sampleNotes.map((scenario) => (
          <button
            key={scenario.id}
            onClick={() => setSelectedScenario(scenario)}
            className={`inline-flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs font-semibold transition-all cursor-pointer ${
              selectedScenario.id === scenario.id
                ? 'bg-green-700 text-white shadow-xs'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200/70'
            }`}
          >
            <scenario.icon className="h-3.5 w-3.5" />
            <span>{scenario.tabLabel}</span>
          </button>
        ))}
      </div>

      {/* Side-by-Side: Operator Note -> AI Interpretation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
        
        {/* Left: Raw Operator Note Box */}
        <div className="flex flex-col justify-between rounded-xl bg-slate-50 p-5 border border-slate-200/80">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Step 1: Raw Operator Note</span>
              <span className="text-[10px] font-mono text-slate-400">INPUT</span>
            </div>
            <blockquote className="rounded-lg bg-white p-4 text-sm font-medium text-slate-800 border-l-4 border-green-600 shadow-xs italic">
              "{selectedScenario.note}"
            </blockquote>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-200/60 flex items-center justify-between text-xs text-slate-500">
            <span className="flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5 text-green-600" />
              Passed to LLM (Groq / OpenAI)
            </span>
            <span className="font-mono text-[11px] text-green-700 font-medium">json_schema strict</span>
          </div>
        </div>

        {/* Right: Guarded Structured Output */}
        <div className="rounded-xl bg-slate-900 text-white p-5 border border-slate-800 shadow-inner flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-green-400 flex items-center gap-1.5">
                <ShieldCheck className="h-4 w-4 text-green-400" />
                Step 2: Guarded Directive
              </span>
              <span className="inline-flex items-center gap-1 rounded bg-green-500/20 px-2 py-0.5 text-[10px] font-medium text-green-300 border border-green-500/30">
                <CheckCircle2 className="h-3 w-3" />
                Validated
              </span>
            </div>

            <div className="space-y-2.5 font-mono text-xs">
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">directive_type:</span>
                <span className="text-green-300 font-semibold">{selectedScenario.directiveType}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">hours:</span>
                <span className="text-amber-300">{selectedScenario.hoursArray}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">{selectedScenario.parameterLabel}:</span>
                <span className="text-white font-semibold">{selectedScenario.parameterValue}</span>
              </div>
            </div>

            <p className="mt-3 text-xs text-slate-300 font-sans leading-relaxed">
              <strong className="text-green-300">Semantic Rationale:</strong> {selectedScenario.explanation}
            </p>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-400 font-sans">
            <span className="flex items-center gap-1 text-green-400">
              <CheckCircle2 className="h-3 w-3" />
              13 Zero-Trust Checks Passed
            </span>
            <span className="text-slate-500 font-mono">Pydantic v2 Verified</span>
          </div>
        </div>

      </div>

      {/* Action Footer linking to the real optimizer */}
      <div className="mt-6 pt-5 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-3">
        <p className="text-xs text-slate-500 text-center sm:text-left">
          Ready to run custom operator notes through the actual MILP solver?
        </p>
        <Link
          to="/optimize"
          className="inline-flex items-center gap-2 text-xs font-semibold text-green-700 hover:text-green-800 group"
        >
          <span>Open Live Optimizer with Real Scenario</span>
          <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-1 transition-transform" />
        </Link>
      </div>
    </div>
  );
}
