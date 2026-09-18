import React from 'react';
import { User, Bell, ChevronDown, Menu } from 'lucide-react';
import { useAppStore } from '../../store/appStore';

interface TopHeaderProps {
  onMenuClick?: () => void;
}

export function TopHeader({ onMenuClick }: TopHeaderProps) {
  const lastResult = useAppStore((state) => state.lastResult);

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white/85 backdrop-blur-md px-4 sm:px-6 lg:px-8">
      <div className="flex flex-1 items-center">
        {onMenuClick && (
          <button 
            onClick={onMenuClick}
            className="mr-4 rounded-md p-2 text-slate-500 hover:bg-slate-100 lg:hidden focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
          >
            <span className="sr-only">Open sidebar</span>
            <Menu className="h-6 w-6" aria-hidden="true" />
          </button>
        )}
        <h1 className="text-lg font-semibold text-slate-900 truncate">
          Campus Energy Control
        </h1>
        {lastResult && (
          <div className="ml-4 hidden sm:flex items-center rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
            Scenario: <span className="ml-1 text-slate-900 font-semibold truncate max-w-[150px]">{lastResult.scenario_id}</span>
          </div>
        )}
      </div>
      <div className="flex items-center space-x-2 sm:space-x-4 ml-4">
        <button className="rounded-full p-1 text-slate-400 hover:bg-slate-50 hover:text-slate-500 hidden sm:block">
          <Bell className="h-5 w-5" />
        </button>
        <div className="flex items-center space-x-2 sm:border-l border-slate-200 sm:pl-4">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-green-100 text-green-700">
            <User className="h-5 w-5" />
          </div>
          <span className="text-sm font-medium text-slate-700 hidden sm:block">Admin</span>
          <ChevronDown className="h-4 w-4 text-slate-400 hidden sm:block" />
        </div>
      </div>
    </header>
  );
}
