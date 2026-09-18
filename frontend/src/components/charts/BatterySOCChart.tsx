import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import type { OptimizeResponse } from '../../types/api.types';
import { formatHour } from '../../data/sampleScenario';

interface BatterySOCChartProps {
  data: OptimizeResponse | null;
}

export function BatterySOCChart({ data }: BatterySOCChartProps) {
  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Battery State of Charge</CardTitle>
          <p className="text-sm text-slate-500 mt-1">Energy levels throughout the 24-hour cycle.</p>
        </CardHeader>
        <CardContent className="h-[300px] flex items-center justify-center text-slate-400 bg-slate-50/50 rounded-b-xl">
          Run an optimization to view battery metrics.
        </CardContent>
      </Card>
    );
  }

  const chartData = data.hourly_plan.map((h) => ({
    hour: formatHour(h.hour),
    soc: Number(h.battery_energy_after_kwh.toFixed(2)),
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Battery State of Charge (SOC)</CardTitle>
        <p className="text-sm text-slate-500 mt-1">Energy levels throughout the 24-hour cycle.</p>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full mt-4">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis dataKey="hour" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} dy={10} minTickGap={20} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} dx={-10} domain={[0, 'dataMax + 20']} />
              <Tooltip
                contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                itemStyle={{ fontSize: '14px', fontWeight: 500, color: '#16a34a' }}
                formatter={(value: any) => [`${value} kWh`, 'SOC']}
              />
              <ReferenceLine y={20} stroke="#ef4444" strokeDasharray="3 3" label={{ position: 'insideTopLeft', value: 'Min Reserve', fill: '#ef4444', fontSize: 12 }} />
              <Line
                type="monotone"
                dataKey="soc"
                stroke="#16a34a"
                strokeWidth={3}
                dot={{ r: 3, fill: '#16a34a', strokeWidth: 0 }}
                activeDot={{ r: 6, strokeWidth: 0 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
