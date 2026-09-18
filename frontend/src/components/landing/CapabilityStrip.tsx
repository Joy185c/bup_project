import React from 'react';
import { Calendar, Brain, ShieldAlert, Cpu, CheckCircle2 } from 'lucide-react';

const capabilities = [
  {
    title: '24-Hour Planning',
    desc: 'Plans every hour of the day.',
    detail: 'Full discrete dispatch horizon from hour 0 to 23 with dynamic time-varying tariff evaluation.',
    icon: Calendar,
  },
  {
    title: 'AI Directive Parsing',
    desc: 'Understands natural-language operator instructions.',
    detail: 'Zero-ambiguity semantic mapping powered by Groq and OpenAI with strict JSON schemas.',
    icon: Brain,
  },
  {
    title: 'Constraint Validation',
    desc: 'Prevents invalid directives from reaching optimizer.',
    detail: '13 deterministic guardrails reject out-of-bound hours, negative reserves, or unsafe parameters.',
    icon: ShieldAlert,
  },
  {
    title: 'MILP Optimization',
    desc: 'Minimizes grid electricity cost while respecting constraints.',
    detail: 'Mixed-Integer Linear Programming with PuLP & Coin-OR CBC branch-and-cut solver.',
    icon: Cpu,
  },
  {
    title: 'Plan Validation',
    desc: 'Validates final schedule before returning it.',
    detail: 'Independent post-solve replay guarantees strict physical conservation within 1e-5 tolerance.',
    icon: CheckCircle2,
  },
];

export function CapabilityStrip() {
  return (
    <section id="capabilities" className="py-14 bg-white border-t border-slate-200/80">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 pb-4 border-b border-slate-100">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-green-700 font-mono">
              Engine Specifications
            </span>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">
              Core System Capabilities
            </h2>
          </div>
          <p className="text-xs text-slate-500 mt-2 md:mt-0 max-w-md">
            Built with mathematical rigor and zero-trust software engineering standards for mission-critical campus infrastructure.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-5">
          {capabilities.map((item) => (
            <div
              key={item.title}
              className="rounded-xl bg-slate-50 p-5 border border-slate-200/80 hover:border-green-300 hover:bg-green-50/20 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="p-2 w-fit rounded-lg bg-white border border-slate-200 text-green-700 shadow-xs mb-3">
                  <item.icon className="h-5 w-5" />
                </div>
                <h3 className="text-sm font-bold text-slate-900 mb-1">
                  {item.title}
                </h3>
                <p className="text-xs font-medium text-green-800 mb-2">
                  {item.desc}
                </p>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  {item.detail}
                </p>
              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
