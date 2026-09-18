import React from 'react';
import { ShieldCheck, Zap, BrainCircuit, Activity } from 'lucide-react';
import { cn } from '../../utils/cn';

interface ProgressStepsProps {
  status: 'idle' | 'understanding' | 'validating' | 'building' | 'solving' | 'verifying' | 'complete' | 'error';
}

export function ProgressSteps({ status }: ProgressStepsProps) {
  const steps = [
    { id: 'understanding', name: 'Understanding operator instructions', icon: BrainCircuit },
    { id: 'validating', name: 'Validating AI directives', icon: ShieldCheck },
    { id: 'building', name: 'Building energy constraints', icon: Activity },
    { id: 'solving', name: 'Solving optimization model', icon: Zap },
    { id: 'verifying', name: 'Verifying final plan', icon: ShieldCheck },
  ];

  const getStepStatus = (stepId: string) => {
    if (status === 'idle') return 'pending';
    if (status === 'error') return 'error';
    if (status === 'complete') return 'complete';
    
    const currentIndex = steps.findIndex(s => s.id === status);
    const stepIndex = steps.findIndex(s => s.id === stepId);
    
    if (stepIndex < currentIndex) return 'complete';
    if (stepIndex === currentIndex) return 'current';
    return 'pending';
  };

  return (
    <div className="space-y-4 py-4">
      {steps.map((step, index) => {
        const stepStatus = getStepStatus(step.id);
        return (
          <div key={step.id} className="flex items-center space-x-3">
            <div className={cn(
              "flex h-8 w-8 items-center justify-center rounded-full border-2 transition-colors duration-300",
              stepStatus === 'complete' ? "border-green-500 bg-green-500 text-white" :
              stepStatus === 'current' ? "border-green-500 text-green-600 bg-green-50 animate-pulse" :
              stepStatus === 'error' ? "border-red-500 text-red-500 bg-red-50" :
              "border-slate-200 text-slate-400 bg-slate-50"
            )}>
              <step.icon className="h-4 w-4" />
            </div>
            <div className="flex-1">
              <span className={cn(
                "text-sm font-medium transition-colors duration-300",
                stepStatus === 'complete' ? "text-slate-900" :
                stepStatus === 'current' ? "text-green-700 font-semibold" :
                stepStatus === 'error' ? "text-red-600" :
                "text-slate-500"
              )}>
                {step.name}
              </span>
            </div>
            {stepStatus === 'current' && (
              <div className="flex space-x-1">
                <div className="h-1.5 w-1.5 rounded-full bg-green-500 animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="h-1.5 w-1.5 rounded-full bg-green-500 animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="h-1.5 w-1.5 rounded-full bg-green-500 animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
