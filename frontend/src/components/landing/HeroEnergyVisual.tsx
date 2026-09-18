import React, { useState } from 'react';
import { Sun, BatteryCharging, Zap, Building2, Cpu, CheckCircle2, ShieldCheck } from 'lucide-react';

interface NodeDetail {
  id: string;
  title: string;
  value: string;
  unit: string;
  subtext: string;
  badge: string;
  color: string;
}

export function HeroEnergyVisual() {
  const [activeNode, setActiveNode] = useState<string | null>(null);

  return (
    <div className="relative w-full max-w-lg mx-auto lg:max-w-none rounded-2xl bg-gradient-to-b from-white to-slate-50 p-6 sm:p-8 border border-slate-200/90 shadow-xl overflow-hidden">
      {/* Background Microgrid Grid Pattern */}
      <div className="absolute inset-0 bg-[radial-gradient(#15803d_1px,transparent_1px)] [background-size:20px_20px] opacity-[0.05] pointer-events-none" />
      
      {/* Simulation Header Banner */}
      <div className="relative z-10 flex items-center justify-between pb-4 mb-4 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <span className="flex h-2.5 w-2.5 rounded-full bg-green-500 animate-pulse" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-700">Microgrid Telemetry Demo</span>
        </div>
        <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-medium text-slate-500">
          Illustrative Horizon
        </span>
      </div>

      {/* Energy Flow Diagram Container */}
      <div className="relative z-10 grid grid-cols-3 grid-rows-3 gap-3 sm:gap-4 items-center justify-items-center py-2 sm:py-4 min-h-[360px]">
        
        {/* SVG Flow Pathways */}
        <svg
          className="absolute inset-0 h-full w-full pointer-events-none overflow-visible"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <linearGradient id="flowGreen" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#15803d" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#22c55e" stopOpacity="0.4" />
            </linearGradient>
          </defs>

          {/* Lines connecting Perimeter to Center (Center is roughly at 50% 50%) */}
          {/* Top (Solar) to Center */}
          <line
            x1="50%"
            y1="22%"
            x2="50%"
            y2="42%"
            stroke="url(#flowGreen)"
            strokeWidth="2.5"
            strokeDasharray="6 4"
            className="animate-[dash_15s_linear_infinite]"
          />
          {/* Left (Grid) to Center */}
          <line
            x1="26%"
            y1="50%"
            x2="38%"
            y2="50%"
            stroke="url(#flowGreen)"
            strokeWidth="2.5"
            strokeDasharray="6 4"
            className="animate-[dash_15s_linear_infinite]"
          />
          {/* Center to Right (Campus) */}
          <line
            x1="62%"
            y1="50%"
            x2="74%"
            y2="50%"
            stroke="url(#flowGreen)"
            strokeWidth="2.5"
            strokeDasharray="6 4"
            className="animate-[dash_15s_linear_infinite]"
          />
          {/* Bottom (Battery) to Center */}
          <line
            x1="50%"
            y1="58%"
            x2="50%"
            y2="78%"
            stroke="url(#flowGreen)"
            strokeWidth="2.5"
            strokeDasharray="6 4"
            className="animate-[dash_15s_linear_infinite]"
          />
        </svg>

        {/* TOP: Rooftop Solar */}
        <div 
          onMouseEnter={() => setActiveNode('solar')}
          onMouseLeave={() => setActiveNode(null)}
          className={`col-start-2 row-start-1 w-full max-w-[150px] p-3 rounded-xl bg-white border transition-all cursor-pointer shadow-xs ${
            activeNode === 'solar' ? 'border-amber-400 ring-2 ring-amber-100 scale-105' : 'border-slate-200 hover:border-amber-300'
          }`}
        >
          <div className="flex items-center justify-between mb-1">
            <div className="p-1.5 rounded-lg bg-amber-50 text-amber-600">
              <Sun className="h-4 w-4" />
            </div>
            <span className="text-[10px] font-bold text-amber-700 uppercase tracking-wider bg-amber-50 px-1.5 py-0.5 rounded">Solar</span>
          </div>
          <p className="text-xs font-semibold text-slate-800">45.0 <span className="text-[10px] font-normal text-slate-500">kW</span></p>
          <p className="text-[10px] text-slate-500">Clean Generation</p>
        </div>

        {/* LEFT: Utility Grid */}
        <div 
          onMouseEnter={() => setActiveNode('grid')}
          onMouseLeave={() => setActiveNode(null)}
          className={`col-start-1 row-start-2 w-full max-w-[140px] p-3 rounded-xl bg-white border transition-all cursor-pointer shadow-xs ${
            activeNode === 'grid' ? 'border-blue-400 ring-2 ring-blue-100 scale-105' : 'border-slate-200 hover:border-blue-300'
          }`}
        >
          <div className="flex items-center justify-between mb-1">
            <div className="p-1.5 rounded-lg bg-blue-50 text-blue-600">
              <Zap className="h-4 w-4" />
            </div>
            <span className="text-[10px] font-bold text-blue-700 uppercase tracking-wider bg-blue-50 px-1.5 py-0.5 rounded">Grid</span>
          </div>
          <p className="text-xs font-semibold text-slate-800">22.5 <span className="text-[10px] font-normal text-slate-500">kW</span></p>
          <p className="text-[10px] text-slate-500">Tariff: 7.0 ৳/kWh</p>
        </div>

        {/* CENTER: AI ENERGY OPTIMIZER */}
        <div className="col-start-2 row-start-2 w-full max-w-[170px] p-3.5 rounded-2xl bg-gradient-to-b from-green-800 to-green-950 text-white shadow-lg border border-green-700/60 text-center relative group">
          <div className="absolute -inset-1 rounded-2xl bg-green-500/20 blur-xs -z-10 group-hover:bg-green-500/30 transition-colors" />
          <div className="flex justify-center mb-1.5">
            <div className="p-2 rounded-xl bg-green-700/50 text-green-300 border border-green-600/40">
              <Cpu className="h-5 w-5 animate-pulse" />
            </div>
          </div>
          <h4 className="text-xs font-bold tracking-tight text-white uppercase">AI Optimizer</h4>
          <p className="text-[10px] text-green-300 font-mono mt-0.5">MILP • CBC Solver</p>
          <div className="mt-2 inline-flex items-center gap-1 bg-green-900/80 px-2 py-0.5 rounded-full border border-green-600/40 text-[9px] font-medium text-green-200">
            <ShieldCheck className="h-3 w-3 text-green-400" />
            <span>Guarded Balance</span>
          </div>
        </div>

        {/* RIGHT: Campus Load */}
        <div 
          onMouseEnter={() => setActiveNode('campus')}
          onMouseLeave={() => setActiveNode(null)}
          className={`col-start-3 row-start-2 w-full max-w-[140px] p-3 rounded-xl bg-white border transition-all cursor-pointer shadow-xs ${
            activeNode === 'campus' ? 'border-purple-400 ring-2 ring-purple-100 scale-105' : 'border-slate-200 hover:border-purple-300'
          }`}
        >
          <div className="flex items-center justify-between mb-1">
            <div className="p-1.5 rounded-lg bg-purple-50 text-purple-600">
              <Building2 className="h-4 w-4" />
            </div>
            <span className="text-[10px] font-bold text-purple-700 uppercase tracking-wider bg-purple-50 px-1.5 py-0.5 rounded">Demand</span>
          </div>
          <p className="text-xs font-semibold text-slate-800">82.5 <span className="text-[10px] font-normal text-slate-500">kW</span></p>
          <p className="text-[10px] text-slate-500">Campus Facilities</p>
        </div>

        {/* BOTTOM: Battery Storage */}
        <div 
          onMouseEnter={() => setActiveNode('battery')}
          onMouseLeave={() => setActiveNode(null)}
          className={`col-start-2 row-start-3 w-full max-w-[150px] p-3 rounded-xl bg-white border transition-all cursor-pointer shadow-xs ${
            activeNode === 'battery' ? 'border-emerald-400 ring-2 ring-emerald-100 scale-105' : 'border-slate-200 hover:border-emerald-300'
          }`}
        >
          <div className="flex items-center justify-between mb-1">
            <div className="p-1.5 rounded-lg bg-emerald-50 text-emerald-600">
              <BatteryCharging className="h-4 w-4" />
            </div>
            <span className="text-[10px] font-bold text-emerald-700 uppercase tracking-wider bg-emerald-50 px-1.5 py-0.5 rounded">Battery</span>
          </div>
          <p className="text-xs font-semibold text-slate-800">120.0 <span className="text-[10px] font-normal text-slate-500">kWh</span></p>
          <p className="text-[10px] text-emerald-600 font-medium">SoC: 60% • Discharging 15 kW</p>
        </div>

      </div>

      {/* Physics Conservation Equation Bar */}
      <div className="mt-3 pt-3 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px] text-slate-500">
        <div className="flex items-center gap-1.5">
          <CheckCircle2 className="h-3.5 w-3.5 text-green-600" />
          <span className="font-mono text-slate-700 font-medium">Grid (22.5) + Solar (45) + Battery (15) = Demand (82.5) kW</span>
        </div>
        <span className="text-slate-400 font-mono text-[10px]">Tolerance: ±1e-5</span>
      </div>
    </div>
  );
}
