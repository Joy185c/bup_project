import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AICopilot } from '../components/optimization/AICopilot';
import { ProgressSteps } from '../components/optimization/ProgressSteps';
import { DirectiveCard } from '../components/optimization/DirectiveCard';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { optimizeEnergy } from '../services/api';
import { useAppStore } from '../store/appStore';
import { SAMPLE_HOURS, SAMPLE_BATTERY, SAMPLE_SCENARIO_ID } from '../data/sampleScenario';
import { AlertTriangle, ShieldCheck, ArrowRight } from 'lucide-react';
import { Button } from '../components/ui/Button';

type OptStatus = 'idle' | 'understanding' | 'validating' | 'building' | 'solving' | 'verifying' | 'complete' | 'error';

export default function OptimizePage() {
  const navigate = useNavigate();
  const setResult = useAppStore((state) => state.setResult);
  const [status, setStatus] = useState<OptStatus>('idle');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  
  // Local state for the latest interpretation display
  const [latestDirectives, setLatestDirectives] = useState<any[]>([]);

  const handleOptimize = async (notes: string[]) => {
    setErrorMsg(null);
    setLatestDirectives([]);
    
    // Simulate pipeline visually for better UX, though backend does it all synchronously
    setStatus('understanding');
    
    const request = {
      scenario_id: SAMPLE_SCENARIO_ID,
      operator_notes: notes,
      hours: SAMPLE_HOURS,
      battery: SAMPLE_BATTERY,
    };

    try {
      // Small visual delays
      await new Promise(r => setTimeout(r, 600));
      setStatus('validating');
      await new Promise(r => setTimeout(r, 500));
      setStatus('building');
      await new Promise(r => setTimeout(r, 400));
      setStatus('solving');
      
      const result = await optimizeEnergy(request);
      
      setStatus('verifying');
      await new Promise(r => setTimeout(r, 800));
      
      setStatus('complete');
      setResult(result, request);
      setLatestDirectives(result.directive_interpretation);
      
    } catch (err: any) {
      setStatus('error');
      setErrorMsg(err.message || 'An unexpected error occurred.');
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in duration-500">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Run Optimization</h2>
        <p className="text-slate-500 mt-1">Provide natural language instructions to guide the mathematical solver.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div>
          <AICopilot onOptimize={handleOptimize} isLoading={status !== 'idle' && status !== 'complete' && status !== 'error'} />
          
          <Card className="mt-8">
            <CardHeader>
              <CardTitle>Optimization Pipeline</CardTitle>
            </CardHeader>
            <CardContent>
              <ProgressSteps status={status} />
              
              {errorMsg && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start text-red-700 text-sm">
                  <AlertTriangle className="h-5 w-5 mr-3 flex-shrink-0" />
                  <div>
                    <p className="font-semibold">Optimization Failed</p>
                    <p className="mt-1">{errorMsg}</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div>
          {status === 'complete' && latestDirectives.length > 0 ? (
            <div className="space-y-6 animate-in slide-in-from-right-4 duration-500">
              <Card className="border-green-200 bg-green-50/30">
                <CardHeader className="pb-3 border-b border-green-100">
                  <div className="flex items-center space-x-2 text-green-800">
                    <ShieldCheck className="h-5 w-5" />
                    <CardTitle className="text-green-800">Verified Directives</CardTitle>
                  </div>
                  <p className="text-sm text-green-700/80">These constraints were successfully validated and applied to the MILP solver.</p>
                </CardHeader>
                <CardContent className="pt-4 space-y-4">
                  {latestDirectives.map((d, i) => (
                    <DirectiveCard key={i} directive={d} />
                  ))}
                  
                  <div className="pt-4 flex justify-end">
                    <Button onClick={() => navigate('/plan')} variant="primary">
                      View Detailed Plan
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <div className="h-full border-2 border-dashed border-slate-200 rounded-xl flex flex-col items-center justify-center p-12 text-center bg-slate-50/50">
              <ShieldCheck className="h-12 w-12 text-slate-300 mb-4" />
              <h3 className="text-lg font-medium text-slate-900 mb-2">Awaiting Instructions</h3>
              <p className="text-slate-500 text-sm max-w-sm">
                The LLM interpretation and validated constraints will appear here after optimization completes.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
