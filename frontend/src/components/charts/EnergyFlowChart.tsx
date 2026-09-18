import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import type { OptimizeResponse } from '../../types/api.types';
import { formatHour } from '../../data/sampleScenario';

interface EnergyFlowChartProps {
  data: OptimizeResponse | null;
}

export function EnergyFlowChart({ data }: EnergyFlowChartProps) {
  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>24-Hour Energy Flow</CardTitle>
          <p className="text-sm text-slate-500 mt-1">Optimized energy distribution across the campus.</p>
        </CardHeader>
        <CardContent className="h-[300px] flex items-center justify-center text-slate-400 bg-slate-50/50 rounded-b-xl">
          Run an optimization to view the energy flow visualization.
        </CardContent>
      </Card>
    );
  }

  const chartData = data.hourly_plan.map((h) => ({
    hour: formatHour(h.hour),
    'Grid Import (kWh)': Number(h.grid_kwh.toFixed(2)),
    'Solar Used (kWh)': Number(h.solar_used_kwh.toFixed(2)),
    'Battery Discharged (kWh)': h.battery_action === 'discharge' ? Number(h.battery_kwh.toFixed(2)) : 0,
    'Battery Charged (kWh)': h.battery_action === 'charge' ? Number(h.battery_kwh.toFixed(2)) : 0,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>24-Hour Energy Flow</CardTitle>
        <p className="text-sm text-slate-500 mt-1">Optimized energy distribution across the campus.</p>
      </CardHeader>
      <CardContent>
        <div className="h-[350px] w-full mt-4">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorGrid" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorSolar" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis dataKey="hour" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} dy={10} minTickGap={20} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} dx={-10} />
              <Tooltip
                contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                itemStyle={{ fontSize: '14px', fontWeight: 500 }}
              />
              <Legend wrapperStyle={{ paddingTop: '20px' }} />
              
              <Area type="monotone" dataKey="Grid Import (kWh)" stackId="1" stroke="#3b82f6" fill="url(#colorGrid)" strokeWidth={2} />
              <Area type="monotone" dataKey="Solar Used (kWh)" stackId="1" stroke="#f59e0b" fill="url(#colorSolar)" strokeWidth={2} />
              <Area type="monotone" dataKey="Battery Discharged (kWh)" stackId="1" stroke="#10b981" fill="#10b981" fillOpacity={0.3} strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
