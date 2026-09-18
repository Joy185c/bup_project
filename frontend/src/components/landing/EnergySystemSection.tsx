import React from 'react';
import { Sun, BatteryCharging, Zap, Building2, Shield, ArrowDownUp, RefreshCw } from 'lucide-react';

const ecosystem = [
  {
    id: 'solar',
    title: 'Rooftop Solar PV',
    subtitle: 'Zero-Emission Generation',
    description: 'On-site campus solar panels generate clean electrical energy during daylight hours. GridWise models solar availability and applies curtailment directives whenever scheduled maintenance or cloud cover requires.',
    icon: Sun,
    color: 'amber',
    stats: 'Time & weather dependent output',
    rules: 'Subject to solar_reduction directives (e.g. 30% reduction)',
  },
  {
    id: 'battery',
    title: 'Battery Energy Storage (BESS)',
    subtitle: 'Strategic Arbitrage & Reserves',
    description: 'Stores excess solar or low-tariff grid energy to discharge during expensive evening peaks. GridWise strictly enforces mutual exclusivity (cannot charge and discharge simultaneously) and end-of-day state-of-charge neutrality.',
    icon: BatteryCharging,
    color: 'emerald',
    stats: 'Dynamic State of Charge [kWh]',
    rules: 'Protected by minimum_battery_reserve and no_charge windows',
  },
  {
    id: 'grid',
    title: 'Utility Grid Import',
    subtitle: 'Tariff-Aware Backup',
    description: 'The utility grid supplies remaining campus demand when solar and battery reserves are depleted. GridWise analyzes time-varying tariffs (BDT/kWh) to minimize electricity costs and avoid high-tariff windows.',
    icon: Zap,
    color: 'blue',
    stats: 'Time-of-Use Tariffs (BDT/kWh)',
    rules: 'Bound by max_grid_window and tariff penalties',
  },
  {
    id: 'campus',
    title: 'Campus Demand',
    subtitle: 'Fixed Load Requirements',
    description: 'The aggregate electrical requirements of university classrooms, research laboratories, computer centers, and dormitories across all 24 hours of the operational day.',
    icon: Building2,
    color: 'purple',
    stats: '24-Hour Load Horizon',
    rules: 'Hourly conservation: Solar + Grid + Discharge = Demand + Charge',
  }
];

export function EnergySystemSection() {
  return (
    <section id="energy-system" className="py-16 sm:py-24 bg-slate-50 border-t border-slate-200/80">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="inline-flex items-center rounded-full bg-slate-200 px-3 py-1 text-xs font-semibold text-slate-700">
            Physical Microgrid Components
          </span>
          <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">
            The Campus Energy Ecosystem
          </h2>
          <p className="mt-4 text-base text-slate-600 leading-relaxed">
            Every kilowatt-hour in GridWise is governed by exact physical conservation laws. 
            The system coordinates on-site generation, storage assets, and utility tariffs in real time.
          </p>
        </div>

        {/* 4 Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {ecosystem.map((item) => (
            <div
              key={item.id}
              className="flex flex-col justify-between rounded-2xl bg-white p-6 border border-slate-200 hover:border-green-300 hover:shadow-lg transition-all"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2.5 rounded-xl bg-slate-100 text-slate-800">
                    <item.icon className="h-6 w-6 text-green-700" />
                  </div>
                  <span className="text-[11px] font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md">
                    Asset
                  </span>
                </div>

                <h3 className="text-base font-bold text-slate-900 mb-1">
                  {item.title}
                </h3>
                <p className="text-xs font-medium text-green-700 mb-3">
                  {item.subtitle}
                </p>

                <p className="text-xs text-slate-600 leading-relaxed mb-4">
                  {item.description}
                </p>
              </div>

              <div className="pt-3 border-t border-slate-100 space-y-1.5 text-[11px]">
                <div className="text-slate-700 font-medium flex items-center gap-1">
                  <RefreshCw className="h-3 w-3 text-green-600" />
                  <span>{item.stats}</span>
                </div>
                <div className="text-slate-500 italic">
                  {item.rules}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Physical Guarantees Strip */}
        <div className="mt-12 rounded-2xl bg-white p-6 border border-slate-200/90 shadow-xs">
          <div className="flex flex-col lg:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-green-100 text-green-800 shrink-0">
                <Shield className="h-6 w-6" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-slate-900">Guaranteed Energy Balance & Asset Protection</h4>
                <p className="text-xs text-slate-600">
                  Binary mutual exclusivity constraints prevent battery charging and discharging simultaneously. End-of-day state-of-charge neutrality prevents battery depletion.
                </p>
              </div>
            </div>
            <div className="shrink-0 flex items-center gap-2 text-xs font-mono bg-slate-100 text-slate-700 px-3 py-1.5 rounded-lg border border-slate-200">
              <ArrowDownUp className="h-3.5 w-3.5 text-green-600" />
              <span>Conservation Check: 100% Passed</span>
            </div>
          </div>
        </div>

      </div>
    </section>
  );
}
