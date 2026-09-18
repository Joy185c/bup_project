import React from 'react';
import { useAppStore } from '../store/appStore';
import { Card, CardContent } from '../components/ui/Card';
import { History, Clock, Zap, DollarSign } from 'lucide-react';
import { Badge } from '../components/ui/Badge';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';

export default function HistoryPage() {
  const history = useAppStore((state) => state.history);
  const setResult = useAppStore((state) => state.setResult);
  const navigate = useNavigate();

  const handleRestore = (entry: any) => {
    setResult(entry.result, entry.request);
    navigate('/plan');
  };

  if (history.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-[50vh] text-slate-500">
        <History className="h-12 w-12 text-slate-300 mb-4" />
        <p>No optimization history found in this session.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Optimization History</h2>
        <p className="text-slate-500 mt-1">Previous runs stored in your local session.</p>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {history.map((entry) => (
          <Card key={entry.id} className="hover:shadow-md transition-shadow">
            <CardContent className="p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex-1 space-y-2">
                <div className="flex items-center space-x-2">
                  <Badge variant="success">Completed</Badge>
                  <span className="text-sm font-medium text-slate-900">{entry.scenario_id}</span>
                  <span className="flex items-center text-xs text-slate-500">
                    <Clock className="h-3 w-3 mr-1" />
                    {new Date(entry.timestamp).toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center space-x-6 text-sm text-slate-600">
                  <span className="flex items-center"><Zap className="h-4 w-4 mr-1 text-blue-500" /> {entry.result.total_grid_kwh.toFixed(1)} kWh</span>
                  <span className="flex items-center"><DollarSign className="h-4 w-4 mr-1 text-amber-500" /> {entry.result.total_cost_bdt.toFixed(1)} BDT</span>
                  <span className="text-slate-400">{entry.operator_notes.length} notes applied</span>
                </div>
              </div>
              <div>
                <Button variant="outline" onClick={() => handleRestore(entry)}>
                  View Plan
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
