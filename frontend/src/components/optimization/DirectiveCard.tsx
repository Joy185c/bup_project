import React from 'react';
import { Badge } from '../ui/Badge';
import { CheckCircle2, XCircle } from 'lucide-react';
import type { DirectiveInterpretation } from '../../types/api.types';
import { formatHour } from '../../data/sampleScenario';

interface DirectiveCardProps {
  directive: DirectiveInterpretation;
}

export function DirectiveCard({ directive }: DirectiveCardProps) {
  const getDirectiveBadge = (type: string) => {
    switch (type) {
      case 'solar_reduction': return <Badge variant="warning">Solar Reduction</Badge>;
      case 'minimum_battery_reserve': return <Badge variant="info">Min Reserve</Badge>;
      case 'no_charge_window': return <Badge variant="danger">No Charge</Badge>;
      case 'no_discharge_window': return <Badge variant="success">No Discharge</Badge>;
      case 'max_grid_window': return <Badge variant="danger">Grid Cap</Badge>;
      case 'no_op': return <Badge variant="default">No Action</Badge>;
      default: return <Badge>{type}</Badge>;
    }
  };

  const formatHoursList = (hours: number[] | null | undefined) => {
    if (!hours || hours.length === 0) return 'All day';
    if (hours.length === 1) return formatHour(hours[0]);
    // Simplistic consecutive check
    const sorted = [...hours].sort((a, b) => a - b);
    let isConsecutive = true;
    for (let i = 1; i < sorted.length; i++) {
      if (sorted[i] !== sorted[i - 1] + 1) {
        isConsecutive = false;
        break;
      }
    }
    if (isConsecutive) {
      return `${formatHour(sorted[0])} – ${formatHour(sorted[sorted.length - 1] + 1)}`;
    }
    return sorted.map(formatHour).join(', ');
  };

  return (
    <div className="border border-slate-200 rounded-lg p-4 bg-white shadow-sm flex flex-col sm:flex-row sm:items-start gap-4">
      <div className="mt-1 flex-shrink-0">
        {directive.applies ? (
          <CheckCircle2 className="h-6 w-6 text-green-500" />
        ) : (
          <XCircle className="h-6 w-6 text-slate-300" />
        )}
      </div>
      <div className="flex-1 space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          {getDirectiveBadge(directive.directive_type)}
          <span className="text-sm font-medium text-slate-700">Note {directive.note_index + 1}</span>
        </div>
        <p className="text-sm text-slate-600 bg-slate-50 p-2 rounded border border-slate-100">
          "{directive.explanation}"
        </p>
        
        {directive.applies && directive.structured_adjustment && (
          <div className="grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-slate-100">
            <div className="text-xs">
              <span className="text-slate-500 block">Active Hours:</span>
              <span className="font-medium text-slate-900">{formatHoursList(directive.structured_adjustment.hours)}</span>
            </div>
            
            {directive.structured_adjustment.factor !== null && (
              <div className="text-xs">
                <span className="text-slate-500 block">Factor:</span>
                <span className="font-medium text-slate-900">{(directive.structured_adjustment.factor * 100).toFixed(0)}% retention</span>
              </div>
            )}
            
            {directive.structured_adjustment.minimum_energy_kwh !== null && (
              <div className="text-xs">
                <span className="text-slate-500 block">Min Reserve:</span>
                <span className="font-medium text-slate-900">{directive.structured_adjustment.minimum_energy_kwh} kWh</span>
              </div>
            )}
            
            {directive.structured_adjustment.max_grid_kwh !== null && (
              <div className="text-xs">
                <span className="text-slate-500 block">Grid Cap:</span>
                <span className="font-medium text-slate-900">{directive.structured_adjustment.max_grid_kwh} kWh</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
