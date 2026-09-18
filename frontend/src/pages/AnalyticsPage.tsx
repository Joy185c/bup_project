import React from 'react';
import { useAppStore } from '../store/appStore';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { formatHour } from '../data/sampleScenario';

export default function AnalyticsPage() {
  const lastResult = useAppStore((state) => state.lastResult);

  if (!lastResult) {
    return (
      <div className="flex items-center justify-center h-[50vh] text-slate-500">
        Run an optimization to view analytics.
      </div>
    );
  }

  // Cost data
  const costData = lastResult.hourly_plan.map((h) => {
    // We can infer tariff from sample scenario or just plot cost if we calculate it
    // The backend doesn't explicitly return per-hour cost in this schema, so we calculate it using the known tariff from our sample
    // In a real app we'd get the tariff from the request object, which we have in the store!
    return {
      hour: formatHour(h.hour),
      'Grid Import (kWh)': h.grid_kwh,
    };
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Analytics</h2>
        <p className="text-slate-500 mt-1">Detailed breakdown of the current optimization run.</p>
      </div>

      <div className="grid grid-cols-1 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Grid Consumption Profile</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[400px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={costData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="hour" tick={{ fontSize: 12 }} />
                  <YAxis />
                  <Tooltip cursor={{ fill: '#f1f5f9' }} />
                  <Legend />
                  <Bar dataKey="Grid Import (kWh)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
