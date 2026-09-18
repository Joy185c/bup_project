import React from 'react';
import { Link } from 'react-router-dom';
import { Zap, ArrowRight, ShieldCheck, CheckCircle2 } from 'lucide-react';

export function FinalCTASection() {
  return (
    <section className="py-16 sm:py-20 bg-slate-900 text-white relative overflow-hidden">
      {/* Background Subtle Accent Pattern */}
      <div className="absolute inset-0 bg-[radial-gradient(#15803d_1px,transparent_1px)] [background-size:24px_24px] opacity-20 pointer-events-none" />
      <div className="absolute top-0 right-0 -mr-20 -mt-20 w-80 h-80 rounded-full bg-green-500/10 blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-0 -ml-20 -mb-20 w-80 h-80 rounded-full bg-emerald-500/10 blur-3xl pointer-events-none" />

      <div className="relative z-10 mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 text-center">
        
        <div className="inline-flex items-center gap-2 rounded-full bg-green-500/10 px-3.5 py-1 text-xs font-semibold text-green-300 border border-green-500/30 mb-6">
          <ShieldCheck className="h-4 w-4 text-green-400" />
          <span>Autonomous Microgrid Dispatch</span>
        </div>

        <h2 className="text-3xl font-extrabold tracking-tight sm:text-5xl text-white">
          Ready to optimize campus energy?
        </h2>

        <p className="mt-4 text-base sm:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed">
          Give GridWise an operator instruction and generate a validated 24-hour energy plan.
        </p>

        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to="/optimize"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-xl bg-green-600 px-8 py-4 text-base font-bold text-white shadow-lg shadow-green-900/40 hover:bg-green-500 active:scale-[0.98] transition-all"
          >
            <Zap className="h-5 w-5 fill-current text-green-200" />
            <span>Launch Optimizer</span>
            <ArrowRight className="h-5 w-5" />
          </Link>

          <Link
            to="/dashboard"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-xl bg-slate-800/80 px-6 py-4 text-base font-medium text-slate-200 border border-slate-700 hover:bg-slate-800 hover:text-white transition-all"
          >
            <span>View Telemetry Dashboard</span>
          </Link>
        </div>

        <div className="mt-10 pt-8 border-t border-slate-800/80 flex flex-wrap items-center justify-center gap-6 text-xs text-slate-400">
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="h-3.5 w-3.5 text-green-400" />
            Zero-Trust Guardrail Isolation
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="h-3.5 w-3.5 text-green-400" />
            Coin-OR CBC Solver Integration
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="h-3.5 w-3.5 text-green-400" />
            Independent Physics Replay
          </span>
        </div>

      </div>
    </section>
  );
}
