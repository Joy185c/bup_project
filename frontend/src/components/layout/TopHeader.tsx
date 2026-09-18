import React from 'react';
import { User, Bell, ChevronDown } from 'lucide-react';
import { useAppStore } from '../../store/appStore';

export function TopHeader() {
  const lastResult = useAppStore((state) => state.lastResult);

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-8">
      <div className="flex flex-1 items-center">
        <h1 className="text-lg font-semibold text-slate-900">
          Campus Energy Control
        </h1>
        {lastResult && (
          <div className="ml-6 flex items-center rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
            Scenario: <span className="ml-1 text-slate-900 font-semibold">{lastResult.scenario_id}</span>
          </div>
        )}
      </div>
      <div className="flex items-center space-x-4">
        <button className="rounded-full p-1 text-slate-400 hover:bg-slate-50 hover:text-slate-500">
          <Bell className="h-5 w-5" />
        </button>
        <div className="flex items-center space-x-2 border-l border-slate-200 pl-4">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-green-100 text-green-700">
            <User className="h-5 w-5" />
          </div>
          <span className="text-sm font-medium text-slate-700">Admin</span>
          <ChevronDown className="h-4 w-4 text-slate-400" />
        </div>
      </div>
    </header>
  );
}
