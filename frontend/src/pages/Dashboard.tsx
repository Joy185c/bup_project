import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Zap } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { KPICards } from '../components/plan/KPICards';
import { EnergyFlowChart } from '../components/charts/EnergyFlowChart';
import { BatterySOCChart } from '../components/charts/BatterySOCChart';
import { useAppStore } from '../store/appStore';

export default function Dashboard() {
  const lastResult = useAppStore((state) => state.lastResult);

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-2xl bg-slate-900 px-8 py-12 shadow-xl sm:px-12 sm:py-16">
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-green-300 via-green-600 to-transparent"></div>
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center space-x-2 rounded-full bg-green-500/20 px-3 py-1 text-sm font-medium text-green-300 border border-green-500/30 mb-6">
            <span className="flex h-2 w-2 rounded-full bg-green-400 animate-pulse"></span>
            <span>Optimization Engine Online</span>
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-5xl mb-4">
            Smart Energy, Optimized by AI
          </h2>
          <p className="text-lg text-slate-300 mb-8 max-w-xl">
            Turn natural-language operator instructions into safe, mathematically optimized energy plans for your campus.
          </p>
          <div className="flex flex-col sm:flex-row gap-4">
            <Link to="/optimize">
              <Button size="lg" className="w-full sm:w-auto bg-green-600 hover:bg-green-500 text-white border-0 shadow-[0_0_15px_rgba(22,163,74,0.5)]">
                <Zap className="mr-2 h-5 w-5" />
                Optimize Energy
              </Button>
            </Link>
            {lastResult && (
              <Link to="/plan">
                <Button variant="outline" size="lg" className="w-full sm:w-auto text-slate-200 border-slate-600 hover:bg-slate-800 hover:text-white bg-slate-800/50 backdrop-blur-sm">
                  View Energy Plan
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-900">Current Status</h3>
        </div>
        
        <KPICards data={lastResult} />
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <EnergyFlowChart data={lastResult} />
          <BatterySOCChart data={lastResult} />
        </div>
      </div>
    </div>
  );
}
