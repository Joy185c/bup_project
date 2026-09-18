import React from 'react';
import { Card, CardContent } from '../ui/Card';
import { Zap, DollarSign, Activity, Battery } from 'lucide-react';
import type { OptimizeResponse } from '../../types/api.types';

interface KPICardsProps {
  data: OptimizeResponse | null;
}

export function KPICards({ data }: KPICardsProps) {
  if (!data) {
    return (
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="bg-slate-50/50">
            <CardContent className="p-6 flex items-center justify-center text-slate-400 h-[104px]">
              No optimization run yet
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const initialBattery = data.hourly_plan[0]?.battery_kwh ?? 100;
  const finalBattery = data.hourly_plan[23]?.battery_energy_after_kwh ?? 100;

  const kpis = [
    {
      title: 'Total Grid Energy',
      value: `${data.total_grid_kwh.toFixed(1)} kWh`,
      icon: Zap,
      color: 'text-blue-600',
      bg: 'bg-blue-100',
    },
    {
      title: 'Total Energy Cost',
      value: `${data.total_cost_bdt.toFixed(1)} BDT`,
      icon: DollarSign,
      color: 'text-amber-600',
      bg: 'bg-amber-100',
    },
    {
      title: 'Peak Grid Demand',
      value: `${data.peak_grid_kwh.toFixed(1)} kW`,
      icon: Activity,
      color: 'text-red-600',
      bg: 'bg-red-100',
    },
    {
      title: 'Battery Final State',
      value: `${finalBattery.toFixed(1)} kWh`,
      subtext: `Initial: ${initialBattery.toFixed(1)} kWh`,
      icon: Battery,
      color: 'text-green-600',
      bg: 'bg-green-100',
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
      {kpis.map((kpi, i) => (
        <Card key={i}>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className={`flex h-12 w-12 items-center justify-center rounded-lg ${kpi.bg}`}>
                <kpi.icon className={`h-6 w-6 ${kpi.color}`} />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-slate-500">{kpi.title}</p>
                <div className="flex items-baseline">
                  <p className="text-2xl font-semibold text-slate-900">{kpi.value}</p>
                </div>
                {kpi.subtext && (
                  <p className="text-xs text-slate-400 mt-1">{kpi.subtext}</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
